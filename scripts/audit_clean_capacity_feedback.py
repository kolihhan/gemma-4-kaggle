#!/usr/bin/env python3
"""Read existing private 12B/31B Kaggle traces and emit safe aggregate feedback.

Never export issue text, prompts, commands, tool observations, patches, trace paths,
or grader content. A trace-less record means UNOBSERVED, never "no testing".
No inference, training, GPU, Kaggle submission, or modification of frozen candidates.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

from scripts.audit_paired_31b_feedback_v2 import reduce_feedback
from scripts.render_matched_12b_31b_private import ARMS, FROZEN

EXPECTED_IDS = frozenset(task for task, _repo in FROZEN)
SAFE_KEYS = (
    "trace_found", "recorded_action_count", "first_edit_action",
    "total_edit_actions", "explicit_or_inline_tests", "tests_after_first_edit",
    "nonzero_test_then_edit", "nonzero_commands_followed_by_edit",
    "nonzero_commands_after_last_edit",
    "nonzero_commands_followed_by_submit_without_edit",
    "unclassified_opaque_commands", "submit_tool_calls",
    "command_class_counts", "tests_with_structured_exit",
    "all_command_structured_exit",
)


def load_arm(root: Path, arm: str) -> list[dict]:
    summary_path = root / arm / f"capacity_{arm}_results.json"
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    if payload.get("status") != "completed" or payload.get("model") != ARMS[arm]:
        raise ValueError("completed frozen model result required")
    if payload.get("requested") != len(EXPECTED_IDS):
        raise ValueError("wrong frozen denominator")
    records = payload.get("results")
    if not isinstance(records, list) or len(records) != len(EXPECTED_IDS):
        raise ValueError("wrong result record count")
    seen = set()
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("invalid result")
        task_id = record.get("instance_id")
        if task_id not in EXPECTED_IDS or task_id in seen:
            raise ValueError("missing, duplicate or unexpected task")
        seen.add(task_id)
        if record.get("status") != "completed":
            raise ValueError("do not drop failed/errored tasks")
        if not isinstance(record.get("resolved"), bool) or not isinstance(record.get("has_patch"), bool):
            raise ValueError("missing correctness flag")
        if not isinstance(record.get("patch_chars"), int) or record["patch_chars"] < 0:
            raise ValueError("bad patch size")
        if not isinstance(record.get("duration_seconds"), (int, float)):
            raise ValueError("missing elapsed time")
        if not isinstance(record.get("tool_calls"), int):
            raise ValueError("missing tool usage")
    if seen != EXPECTED_IDS:
        raise ValueError("frozen task mismatch")
    return records


def trace_stats(root: Path, arm: str, instance_id: str) -> dict:
    folder = root / arm
    matched = list(folder.rglob(f"trace_{instance_id}.json"))
    if len(matched) > 1:
        raise ValueError("ambiguous trace files")
    if not matched:
        return {"trace_found": False}
    original = json.loads(matched[0].read_text(encoding="utf-8"))
    summary = reduce_feedback(original)
    return {key: summary[key] for key in SAFE_KEYS if key in summary}


def audit(root: Path) -> dict:
    records = {arm: load_arm(root, arm) for arm in ARMS}
    by_task = {}
    for arm in ARMS:
        for record in records[arm]:
            task_id = record["instance_id"]
            by_task.setdefault(task_id, {})[arm] = {
                "resolved": record["resolved"],
                "has_patch": record["has_patch"],
                "grader_exit_code": record.get("test_exit_code"),
                "tool_calls": record["tool_calls"],
                "duration_seconds": round(record["duration_seconds"], 3),
                "feedback": trace_stats(root, arm, task_id),
            }
    wins31 = sum(by_task[t]["v2_31b"]["resolved"] and
                 not by_task[t]["v2_12b"]["resolved"] for t in EXPECTED_IDS)
    wins12 = sum(by_task[t]["v2_12b"]["resolved"] and
                 not by_task[t]["v2_31b"]["resolved"] for t in EXPECTED_IDS)
    by_arm = {}
    for arm in ARMS:
        rs = records[arm]
        by_arm[arm] = {
            "task_count": len(rs),
            "resolved": sum(r["resolved"] for r in rs),
            "patched": sum(r["has_patch"] for r in rs),
            "total_duration_seconds": round(sum(r["duration_seconds"] for r in rs), 3),
            "total_tool_calls": sum(r["tool_calls"] for r in rs),
            "traces_found": sum(by_task[t][arm]["feedback"]["trace_found"]
                                for t in EXPECTED_IDS),
            "explicit_or_inline_tests": sum(
                by_task[t][arm]["feedback"].get("explicit_or_inline_tests", 0)
                for t in EXPECTED_IDS),
        }
    return {
        "version": "clean-capacity-feedback-existing-only-v1",
        "source_action": 43168183720,
        "no_gpu_inference_training_or_submission": True,
        "raw_private_data_exported": False,
        "by_arm": by_arm,
        "paired": {"31b_only_resolved": wins31,
                   "12b_only_resolved": wins12,
                   "both_resolved": sum(all(by_task[t][a]["resolved"] for a in ARMS)
                                        for t in EXPECTED_IDS),
                   "both_failed": sum(not any(by_task[t][a]["resolved"] for a in ARMS)
                                      for t in EXPECTED_IDS)},
        "tasks": {t: by_task[t] for t in sorted(EXPECTED_IDS)},
        "limitations": (
            "4 already-inspected public-development issues, not an independent holdout; "
            "model-visible nonzero shell exits are not automatically failed tests; "
            "grader exit is not model-visible; absent trace means unobserved. "
            "Do not infer a submission score or model superiority from this panel."
        ),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    report = audit(a.root)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("SAFE_REAL_CAPACITY_FEEDBACK=" + json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
