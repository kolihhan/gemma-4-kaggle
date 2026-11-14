"""Read-only join: NVIDIA Open-SWE-Traces -> SWE-rebench-V2 source provenance.

No code, task ID, prompts, gold patches, test patches, or source diff exported.
The join is only a *prerequisite* for independent patch/test replay; not a
passing benchmark result or a positive training sample approval.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from collections import Counter
import json
import re

from scripts.audit_open_swe_traces_metadata import DATASET, get_json, sample_grade

SOURCE = "nebius/SWE-rebench-V2"


def filtered_join(source_row: dict) -> str:
    task = source_row.get("instance_id")
    if not isinstance(task, str) or not 4 <= len(task) <= 150:
        return "invalid_source_instance_id"
    if any(ord(c) < 32 for c in task):
        return "invalid_source_instance_id"
    # Correct SQL string-literal escaping; no query fragments from source.
    query = '"instance_id"=\'' + task.replace("'", "''") + "\'"
    try:
        data = get_json("/filter", {"dataset": SOURCE, "config": "default", "split": "train",
                                    "where": query, "offset": 0, "length": 2})
    except (OSError, ValueError, KeyError):
        return "filter_unavailable"
    if data.get("partial") is True:
        return "partial_index_unreliable"
    rows = data.get("rows")
    if not isinstance(rows, list):
        return "unexpected_filter_schema"
    if not rows:
        return "not_found_or_index_gap"
    if len(rows) != 1:
        return "duplicate_source_match"
    row = rows[0].get("row") if isinstance(rows[0], dict) else None
    if not isinstance(row, dict) or row.get("instance_id") != task:
        return "mismatched_instance_id"
    if str(row.get("repo", "")).lower() != str(source_row.get("repo","")).lower():
        return "mismatched_repository"
    if str(row.get("license", "")).lower() != str(source_row.get("license","")).lower():
        return "mismatched_license"
    commit = row.get("base_commit")
    if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit):
        return "missing_base_commit"
    tests = row.get("FAIL_TO_PASS")
    if not isinstance(tests, list) or len(tests) == 0:
        return "missing_fail_to_pass"
    if not isinstance(row.get("test_patch"), str) or not row["test_patch"].strip():
        return "missing_test_patch"
    if not isinstance(row.get("problem_statement"), str) or not row["problem_statement"].strip():
        return "missing_problem_statement"
    if not isinstance(row.get("image_name"), str) or not row["image_name"]:
        return "missing_replay_image"
    return "source_context_found_replay_pending"


def collect_source() -> list[dict]:
    selected = []
    for offset in (6, 12):
        payload = get_json("/rows", {"dataset": DATASET, "config": "v2.0",
                                     "split": "sweagent", "offset": offset, "length": 6})
        batch = payload.get("rows")
        if not isinstance(batch, list) or len(batch) != 6:
            raise RuntimeError("fixed source cohort incomplete")
        for item in batch:
            row = item.get("row") if isinstance(item, dict) else None
            if isinstance(row, dict) and sample_grade(row) == "candidate_for_private_deep_audit":
                selected.append({"instance_id": row.get("instance_id"),
                                 "repo": row.get("repo"), "license": row.get("license")})
    if len(selected) != 8:
        raise RuntimeError("source cohort quality denominator changed; stop")
    if len({x["instance_id"] for x in selected}) != 8:
        raise RuntimeError("duplicate public source task IDs; stop")
    return selected


def run() -> dict:
    selected = collect_source()
    # No shared log messages with task IDs. The source values are used only
    # for public HF /filter equality matches, then immediately discarded.
    with ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(filtered_join, selected))
    return {
        "cohort": "NVIDIA Open-SWE-Traces v2.0 SWE-agent rows 6..17, fixed source",
        "source_candidate_success": len(selected),
        "join_counts": dict(Counter(results)),
        "matched_with_replay_prerequisites": results.count("source_context_found_replay_pending"),
        "local_checkouts_created": 0,
        "patches_applied": 0,
        "test_suites_executed": 0,
        "approved_train_examples": 0,
        "raw_task_text_or_patches_exported": False,
        "reference_gold_patches_used_as_targets": False,
    }


if __name__ == "__main__":
    print("GEMMA_EXTERNAL_SOURCE_REPLAY_JOIN=" + json.dumps(run(),sort_keys=True),flush=True)
    print("NO_GPU_NO_TRAINING_NO_KAGGLE_SUBMISSION=TRUE")
