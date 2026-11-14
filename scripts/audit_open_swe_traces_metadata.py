"""Metadata-only probe of NVIDIA Open-SWE-Traces for verified repair data.

Fetches tiny public dataset-viewer samples. Never logs or persists issue text,
agent messages, shell commands, reference/model patches, or raw dataset rows.
This is source/format validation, not a training run or a proof of independence.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import re
from urllib.parse import urlencode
from urllib.request import Request, urlopen

DATASET = "nvidia/Open-SWE-Traces"
API = "https://datasets-server.huggingface.co"
EXCLUDE_REPOS = frozenset({
    "fastapi/fastapi", "textualize/rich", "psf/requests", "encode/httpx"
})
ALLOWED_LICENSES = frozenset({
    "mit", "apache-2.0", "bsd-2-clause", "bsd-3-clause"
})


def get_json(path: str, params: dict[str, object]) -> dict:
    req = Request(API + path + "?" + urlencode(params),
                  headers={"User-Agent": "Gemma4-ReadOnly-Research/1.0"})
    with urlopen(req, timeout=28) as response:
        obj = json.load(response)
    if not isinstance(obj, dict):
        raise ValueError("invalid dataset API object")
    return obj


def sample_grade(row: dict) -> str:
    """Conservative format gate: not an assertion that this item is trainable."""
    if not isinstance(row, dict) or type(row.get("resolved")) is not int:
        return "missing_resolved_label"
    if row["resolved"] != 1:
        return "not_verified_success"
    repo = row.get("repo")
    if not isinstance(repo, str) or "/" not in repo:
        return "missing_repo"
    if repo.lower() in EXCLUDE_REPOS:
        return "public_eval_repo_excluded"
    if str(row.get("language", "")).lower() != "python":
        return "non_python"
    if str(row.get("license", "")).lower() not in ALLOWED_LICENSES:
        return "unknown_repo_license"

    metadata = row.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}
    patch_obj = row.get("model_patch", metadata.get("model_patch"))
    patch = patch_obj.get("patch") if isinstance(patch_obj, dict) else patch_obj
    if not isinstance(patch, str) or not patch.strip().startswith("diff --git "):
        return "no_verified_model_diff"
    trace = row.get("messages", row.get("trajectory"))
    if not isinstance(trace, list) or len(trace) < 3:
        return "no_complete_trace"
    roles = {t.get("role") for t in trace if isinstance(t, dict)}
    if not {"assistant", "tool"}.issubset(roles):
        return "no_observed_tool_feedback"
    if not row.get("trajectory_id"):
        return "missing_trajectory_identity"
    return "candidate_for_private_deep_audit"


ADK_NATIVE_TOOLS = frozenset({
    "read_file", "run_command", "edit_file", "write_file", "get_status",
    "submit_patch", "search_similar_code", "get_code_neighbors", "get_code_subgraph",
})


def native_tool_schema_count(row: dict) -> tuple[int, int]:
    """Count only exact declared tool-name overlaps, never tool definitions."""
    tools = row.get("tools")
    if not isinstance(tools, list):
        return (0, 0)
    names = set()
    for definition in tools[:64]:
        try:
            definition = json.loads(definition) if isinstance(definition, str) else definition
        except (json.JSONDecodeError, TypeError):
            continue
        if not isinstance(definition, dict):
            continue
        descriptor = definition.get("function", definition)
        if not isinstance(descriptor, dict):
            continue
        name = descriptor.get("name")
        if isinstance(name, str):
            names.add(name)
    return (len(names), len(names & ADK_NATIVE_TOOLS))


def pick_splits(splits: list, limit: int = 4) -> list[dict]:
    """Choose one small viewer probe from distinct configs, not a random sample."""
    # Open-SWE-Traces uses versioned configs (v2.0) with AGENT-named
    # splits (openhands/sweagent/etc.), not a conventional train split.
    # Prefer the latest available version to avoid mixing duplicate
    # trajectories across dataset releases. No hidden/test split sampled.
    versions = sorted(
        {str(x.get("config")) for x in splits if isinstance(x, dict)
         and re.match(r"^v[0-9]+[.][0-9]+$", str(x.get("config", "")))},
        key=lambda s: tuple(int(p) for p in s[1:].split(".")),
        reverse=True,
    )
    if not versions:
        return []
    version = versions[0]
    choices = []
    seen = set()
    for item in splits:
        if not isinstance(item, dict) or not item.get("split"):
            continue
        config = str(item.get("config"))
        split = str(item["split"])
        if config != version or split in seen or item.get("num_examples") == 0:
            continue
        if any(bad in split.lower() for bad in ("test", "holdout", "validation")):
            continue
        seen.add(split)
        choices.append({"config": config, "split": split})
        if len(choices) == limit:
            break
    return choices


def run(limit: int = 4, length: int = 6) -> dict:
    splits_payload = get_json("/splits", {"dataset": DATASET})
    splits = splits_payload.get("splits", [])
    if not isinstance(splits, list):
        raise ValueError("missing splits")
    selected = pick_splits(splits, limit)
    catalog = {
        "split_count": len(splits),
        "split_catalog": [{"config": str(x.get("config", "")),
                           "split": str(x.get("split", "")),
                           "num_examples": x.get("num_examples")}
                          for x in splits[:30] if isinstance(x, dict)],
        "split_api_keys": sorted(splits_payload.keys()),
        "split_pending_count": len(splits_payload.get("pending", []))
            if isinstance(splits_payload.get("pending"), list) else None,
        "split_failed_count": len(splits_payload.get("failed", []))
            if isinstance(splits_payload.get("failed"), list) else None,
        "parquet_file_count": None,
        "parquet_api_keys": [],
    }
    if not selected:
        # Some very large Hub datasets expose Parquet shard indexes but no
        # dataset-viewer rows; that is not a zero-success finding.
        try:
            parquet = get_json("/parquet", {"dataset": DATASET})
            catalog["parquet_api_keys"] = sorted(parquet.keys())
            files = parquet.get("parquet_files", [])
            catalog["parquet_file_count"] = len(files) if isinstance(files, list) else None
            if isinstance(files, list):
                selected = pick_splits([
                    {"config": f.get("config"), "split": f.get("split"),
                     "num_examples": f.get("num_rows", 1)}
                    for f in files if isinstance(f, dict)
                ], limit)
        except (OSError, ValueError, KeyError):
            catalog["parquet_metadata_accessible"] = False
    probes = []
    global_qualified_issues: set[str] = set()
    global_qualified_repos: set[str] = set()
    global_qualified_trajectories: set[str] = set()
    global_qualified_rows = global_adk_native_rows = 0
    for item in selected:
        entry = {"config": item["config"], "split": item["split"]}
        try:
            data = get_json("/rows", {"dataset": DATASET, "config": item["config"],
                                      "split": item["split"], "offset": 0, "length": length})
            rows = data.get("rows", [])
            if not isinstance(rows, list) or not rows:
                raise ValueError("no visible sample rows")
            buckets: Counter[str] = Counter()
            field_sets: Counter[str] = Counter()
            passing_repos: set[str] = set()
            passing_ids: set[str] = set()
            declared_tools = native_overlap = 0
            passing_with_catalog = passing_with_adk_native_schema = 0
            for record in rows:
                row = record.get("row", {}) if isinstance(record, dict) else {}
                gate = sample_grade(row)
                buckets[gate] += 1
                if gate == "candidate_for_private_deep_audit":
                    global_qualified_rows += 1
                    global_qualified_issues.add(str(row.get("instance_id")
                                                    or row["trajectory_id"]))
                    global_qualified_repos.add(str(row["repo"]).lower())
                    global_qualified_trajectories.add(str(row["trajectory_id"]))
                    passing_repos.add(str(row["repo"]).lower())
                    passing_ids.add(str(row["instance_id"]) if row.get("instance_id")
                                    else str(row["trajectory_id"]))
                    count, overlap = native_tool_schema_count(row)
                    declared_tools += count
                    native_overlap += overlap
                    passing_with_catalog += int(count > 0)
                    passing_with_adk_native_schema += int(overlap > 0)
                    global_adk_native_rows += int(overlap > 0)
                for key in ("resolved", "repo", "language", "license", "trajectory_id",
                            "metadata", "messages", "trajectory", "model_patch", "tools"):
                    if key in row:
                        field_sets[key] += 1
            entry.update({"sampled": len(rows), "quality_gate_counts": dict(buckets),
                          "field_present_counts": dict(field_sets),
                          "passing_distinct_repo_count": len(passing_repos),
                          "passing_distinct_task_count": len(passing_ids),
                          "passing_with_declared_tool_catalog": passing_with_catalog,
                          "passing_with_any_exact_adk_tool_schema": passing_with_adk_native_schema,
                          "declared_catalog_tool_names_total": declared_tools,
                          "exact_adk_tool_schema_names_total": native_overlap,
                          "status": "sampled"})
        except (OSError, ValueError, KeyError) as exc:
            # No private exception text or traceback: one small failure per config.
            entry.update({"sampled": 0, "status": type(exc).__name__})
        probes.append(entry)
    return {
        "dataset": DATASET,
        "scope": "PUBLIC_VIEWER_METADATA_ONLY_NONRANDOM_FIRST_ROWS",
        "configs_selected": len(selected),
        "catalog": catalog,
        "catalog_state": "viewer_splits" if catalog["split_count"]
            else "parquet_fallback" if selected else "no_previewable_splits",
        "rows_total_in_sample": sum(p["sampled"] for p in probes),
        "qualified_trajectory_rows": global_qualified_rows,
        "qualified_unique_issue_count": len(global_qualified_issues),
        "qualified_unique_repo_count": len(global_qualified_repos),
        "qualified_unique_trajectory_ids": len(global_qualified_trajectories),
        "qualified_trajectory_rows_with_exact_adk_tool_schema": global_adk_native_rows,
        "probes": probes,
        "filters": {"allowed_repo_license": sorted(ALLOWED_LICENSES),
                    "excluded_public_eval_repos": sorted(EXCLUDE_REPOS),
                    "requires_verified_resolved": True, "requires_model_patch": True,
                    "requires_tool_trace": True},
        "candidate_records_exported": 0,
        "data_used_for_training": False,
        "full_dataset_scanned": False,
        "model_correctness_proven": False,
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--configs", type=int, default=4)
    p.add_argument("--rows", type=int, default=6)
    args = p.parse_args()
    if not 1 <= args.configs <= 4 or not 1 <= args.rows <= 10:
        raise SystemExit("safe query cap exceeded")
    print("GEMMA_EXTERNAL_SWE_METADATA_PROBE=" +
          json.dumps(run(args.configs, args.rows), sort_keys=True), flush=True)
