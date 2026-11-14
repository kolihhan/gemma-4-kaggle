"""Eight-task source-version join against bounded remote SWE-rebench-V2 Parquet.

Source NVIDIA v2.0/sweagent rows 6..17 fixed prior to this experiment.
Reads only instance_id and matched row group's provenance columns over HTTP
Range, never the benchmark gold patch column. No public logging of tasks,
IDs, prompts, code, tests, commits, source paths, URL redirects or tokens.
Not a patch replay or a model/SFT experiment.
"""
from __future__ import annotations

from collections import Counter
import json
from pathlib import PurePosixPath
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from scripts.probe_external_source_join import collect_source
from scripts.probe_swe_rebench_parquet_access import URL

COLUMNS = ("instance_id", "repo", "license", "base_commit", "image_name",
           "FAIL_TO_PASS", "test_patch", "problem_statement")
SIZE_CAP_BYTES = 130_000_000
MAX_GROUPS = 350
MAX_SOURCE_ROWS = 50_000


def verify_replay_metadata(record: dict, source: dict) -> str:
    if record.get("instance_id") != source.get("instance_id"):
        return "id_mismatch"
    if str(record.get("repo", "")).casefold() != str(source.get("repo", "")).casefold():
        return "repo_mismatch"
    if str(record.get("license", "")).casefold() != str(source.get("license", "")).casefold():
        return "license_mismatch"
    commit = record.get("base_commit")
    if not isinstance(commit, str) or re.fullmatch("[a-fA-F0-9]{40}", commit) is None:
        return "missing_base_commit"
    checks = record.get("FAIL_TO_PASS")
    if not isinstance(checks, list) or not checks or not all(isinstance(x,str) and x for x in checks):
        return "missing_fail_to_pass"
    if not isinstance(record.get("test_patch"), str) or not record["test_patch"].strip():
        return "missing_test_patch"
    if not isinstance(record.get("problem_statement"), str) or not record["problem_statement"].strip():
        return "missing_problem_statement"
    if not isinstance(record.get("image_name"), str) or not record["image_name"].strip():
        return "missing_image"
    return "matched_replay_metadata_not_executed"


def may_contain(stats: object, targets: set[str]) -> bool:
    """Use only valid UTF-8 min/max statistics; otherwise conservatively scan."""
    if stats is None or not getattr(stats, "has_min_max", False):
        return True
    minimum, maximum = getattr(stats, "min", None), getattr(stats, "max", None)
    if isinstance(minimum, bytes):
        minimum = minimum.decode("utf-8", errors="replace")
    if isinstance(maximum, bytes):
        maximum = maximum.decode("utf-8", errors="replace")
    if not isinstance(minimum, str) or not isinstance(maximum, str) or minimum > maximum:
        return True
    return any(minimum <= x <= maximum for x in targets)


def frozen_revision() -> str:
    uri = "https://huggingface.co/api/datasets/nebius/SWE-rebench-V2"
    with urlopen(Request(uri, headers={"User-Agent":"GemmaResearchParquet/1.0"}),
                 timeout=30) as res:
        item = json.load(res)
    value = item.get("sha")
    if not isinstance(value, str) or not re.fullmatch("[a-f0-9]{40}", value):
        raise ValueError("source Git revision unavailable")
    return value


def join() -> dict:
    selected = collect_source()
    if len(selected) != 8 or len({r["instance_id"] for r in selected}) != 8:
        raise ValueError("frozen source denominator invalid")
    rev = frozen_revision()
    # Binding to the exact HF dataset Git SHA makes repeated reads stable;
    # neither task IDs nor gold labels are shared outside the runner.
    parquet_url = URL.replace("/resolve/main/", "/resolve/" + rev + "/")
    import fsspec
    import pyarrow.parquet as pq

    found: dict[str, list[dict]] = {row["instance_id"]: [] for row in selected}
    wanted = set(found)
    candidate_groups = skipped_groups = 0
    total_rows = 0
    compressed_projected = 0
    with fsspec.open(parquet_url, mode="rb", block_size=1 << 16,
                     cache_type="none", timeout=40) as handle:
        pf = pq.ParquetFile(handle)
        if pf.metadata.num_row_groups > MAX_GROUPS or pf.metadata.num_rows > MAX_SOURCE_ROWS:
            raise ValueError("unexpectedly large source schema")
        if not set(COLUMNS).issubset(pf.schema_arrow.names):
            raise ValueError("source provenance fields missing")
        for group_ix in range(pf.metadata.num_row_groups):
            meta = pf.metadata.row_group(group_ix)
            idx = next((i for i in range(meta.num_columns)
                        if meta.column(i).path_in_schema == "instance_id"), None)
            stats = meta.column(idx).statistics if idx is not None else None
            if not may_contain(stats, wanted):
                skipped_groups += 1
                continue
            candidate_groups += 1
            ids = pf.read_row_group(group_ix, columns=["instance_id"]).column("instance_id").to_pylist()
            hits = [(pos, val) for pos, val in enumerate(ids) if val in wanted]
            if not hits:
                continue
            # Pre-calculate metadata byte budget for only the row groups
            # with matching IDs; gold 'patch' column is NEVER requested.
            group_bytes = sum(int(meta.column(i).total_compressed_size)
                              for i in range(meta.num_columns)
                              if any(meta.column(i).path_in_schema == name or
                                     meta.column(i).path_in_schema.startswith(name + ".")
                                     for name in COLUMNS))
            compressed_projected += group_bytes
            if compressed_projected > SIZE_CAP_BYTES:
                raise ValueError("source join byte budget exceeded")
            data = pf.read_row_group(group_ix, columns=list(COLUMNS))
            assert len(data) == len(ids)
            for pos, key in hits:
                record = {c: data[c][pos].as_py() for c in COLUMNS}
                found[key].append(record)
            total_rows += len(hits)
    result = Counter()
    for source in selected:
        matching = found[source["instance_id"]]
        if len(matching) > 1:
            result["duplicate_instance_id"] += 1
        elif not matching:
            result["not_in_parquet_source"] += 1
        else:
            result[verify_replay_metadata(matching[0], source)] += 1
    return {
        "status": "PARQUET_SOURCE_JOIN_COMPLETED",
        "cohort": "NVIDIA v2.0/sweagent public rows 6..17, eight frozen eligible",
        "source_revision_frozen": bool(rev),
        "dataset": "nebius/SWE-rebench-V2",
        "source_rows": len(selected),
        "parquet_row_groups_skipped_by_stats": skipped_groups,
        "parquet_row_groups_scanned_for_ids": candidate_groups,
        "matched_raw_rows": total_rows,
        "matched_provenance_categories": dict(result),
        "compressed_projected_bytes_for_matching_groups": compressed_projected,
        "test_patch_content_logged": False,
        "source_ids_or_commits_logged": False,
        "gold_patch_column_read": False,
        "test_patches_applied": 0,
        "source_git_checkouts_created": 0,
        "independent_grader_verified": 0,
        "approved_training_examples": 0,
        "model_trained": False,
    }


if __name__ == "__main__":
    try:
        out = join()
        print("GEMMA_SWE_REBENCH_PARQUET_JOIN=" + json.dumps(out,sort_keys=True),flush=True)
    except Exception as exc:
        # Dataset-viewer signed URLs sometimes include tokens; never repr(exc).
        print("GEMMA_SWE_REBENCH_PARQUET_JOIN_BLOCKED=" +
              json.dumps({"exception_class":type(exc).__name__,
                          "source_data_or_url_logged": False}),flush=True)
        raise SystemExit(1) from None
