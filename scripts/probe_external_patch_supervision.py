"""Private, non-exporting patch-oriented SFT source feasibility probe.

Shows schema & size aggregates on a fixed external public sample, never raw
prompt, patch, repository path, tool call, tool result or training example.
"""
from __future__ import annotations

from collections import Counter
import json
import re

from scripts.audit_open_swe_traces_metadata import DATASET, get_json, sample_grade


def _patch(row: dict) -> str | None:
    metadata = row.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}
    object_ = row.get("model_patch", metadata.get("model_patch"))
    value = object_.get("patch") if isinstance(object_, dict) else object_
    return value if isinstance(value, str) else None


def _bucket(num: int) -> str:
    if num == 0:
        return "zero"
    if num < 1000:
        return "1-999"
    if num < 5000:
        return "1000-4999"
    if num < 20000:
        return "5000-19999"
    return "20000+"


def check_row(row: dict) -> dict:
    if sample_grade(row) != "candidate_for_private_deep_audit":
        return {"status": "source_not_admitted"}
    users = [x.get("content") for x in row["messages"]
             if isinstance(x, dict) and x.get("role") == "user"]
    user_strings = [s for s in users if isinstance(s, str) and s.strip()]
    patch = _patch(row)
    if patch is None:
        return {"status": "missing_model_patch"}
    diff_headers = re.findall(r"^diff --git a/(.*?) b/(.*?)$", patch, flags=re.M)
    paths_consistent = bool(diff_headers) and all(
        a == b and len(a) < 400 and ".." not in a.split("/") for a, b in diff_headers)
    metadata = row.get("metadata")
    meta_keys = sorted(x for x in metadata if isinstance(x, str)
                       and x in {"category", "model_patch", "reference_patch",
                                 "base_commit", "base_commit_sha",
                                 "instance_id", "test_results", "repo_name",
                                 "snapshot_id"}) if isinstance(metadata, dict) else []
    return {
        "status": "admitted_source_row",
        "user_messages": len(users),
        "nonempty_text_user_messages": len(user_strings),
        "prompt_size_bucket": _bucket(sum(len(s) for s in user_strings)),
        "patch_size_bucket": _bucket(len(patch)),
        "diff_header_count": len(diff_headers),
        "diff_headers_valid": paths_consistent,
        "metadata_field_names_allowlisted": meta_keys,
        "prompt_and_model_patch_present": bool(user_strings and paths_consistent),
        "whole_episode_context_sufficient_proven": False,
        "patch_replayed_against_source_snapshot": False,
        "final_model_patch_training_approval": False,
    }


def summarize(rows: list) -> dict:
    source = 0
    prompt_patches = 0
    prompt_sizes = Counter()
    patch_sizes = Counter()
    metadata_fields = Counter()
    diff_file_buckets = Counter()
    users = Counter()
    for record in rows:
        row = record.get("row", {}) if isinstance(record, dict) else {}
        entry = check_row(row)
        if entry["status"] != "admitted_source_row":
            continue
        source += 1
        prompt_patches += int(entry["prompt_and_model_patch_present"])
        prompt_sizes[entry["prompt_size_bucket"]] += 1
        patch_sizes[entry["patch_size_bucket"]] += 1
        diff_file_buckets[_bucket(entry["diff_header_count"])] += 1
        users[entry["nonempty_text_user_messages"]] += 1
        metadata_fields.update(entry["metadata_field_names_allowlisted"])
    return {
        "source": DATASET + "/v2.0/sweagent",
        "fixed_source_offsets": [6, 12],
        "sampled": len(rows),
        "source_success_admitted": source,
        "prompt_and_patch_present": prompt_patches,
        "prompt_char_buckets": dict(prompt_sizes),
        "model_patch_char_buckets": dict(patch_sizes),
        "patch_file_count_buckets": dict(diff_file_buckets),
        "text_user_message_counts": {str(k):v for k,v in users.items()},
        "metadata_field_presence_counts": dict(metadata_fields),
        "source_code_replay_confirmed": 0,
        "ADK_policy_training_approved": 0,
        "raw_training_examples_exported": 0,
        "source_tasks_used_for_training": 0,
        "has_independent_swegemma_grader": False,
    }


if __name__ == "__main__":
    rows = []
    for offset in (6, 12):
        # Separate bounded viewer requests; no new task substitution.
        response = get_json("/rows", {"dataset": DATASET, "config": "v2.0",
                                      "split": "sweagent", "offset": offset, "length": 6})
        batch = response.get("rows")
        if not isinstance(batch, list) or len(batch) != 6:
            raise SystemExit("source batch unavailable")
        rows.extend(batch)
    print("GEMMA_PATCH_ONLY_EXTERNAL_SCHEMA_PROBE="+json.dumps(summarize(rows),sort_keys=True),flush=True)
    print("NO_RAW_DATA_NO_GPU_NO_ADAPTER_NO_KAGGLE_SUBMISSION=TRUE",flush=True)
