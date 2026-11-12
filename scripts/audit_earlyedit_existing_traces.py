"""Classify already-finished paired 31B traces without leaking raw task content.

No inference, training, patch reproduction, or model evaluation. Read exact
Kaggle output folder after completion; publish only allowlisted metadata.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
from typing import Any

from scripts.audit_paired_31b_feedback_v2 import reduce_feedback
from scripts.render_earlyedit_v2_paired_31b import PLAN_FILE, validate_plan

ARMS = ("v2_5min", "early_edit_5min")
PERMITTED = {
    "trace_found",
    "recorded_action_count",
    "first_edit_action",
    "total_edit_actions",
    "explicit_or_inline_tests",
    "tests_after_first_edit",
    "nonzero_test_then_edit",
    "nonzero_commands_after_last_edit",
    "nonzero_commands_followed_by_edit",
    "submit_tool_calls",
    "unclassified_opaque_commands",
    "tests_with_structured_exit",
}
VERSION = "earlyedit-v2-existing-traces-safe-v1"
RESULT = "earlyedit_v2_31b_results.json"


def locate_trace(root: Path, task_id: str, arm: str) -> Path | None:
    # The legacy paired renderer has a separate 'public-prompt' results dir
    # for the treatment. That directory name is an internal implementation
    # detail, not an indication of which prompt was actually used.
    matches = []
    for path in root.rglob(f"trace_{task_id}.json"):
        relative = path.relative_to(root)
        treatment_dir = "public-prompt" in relative.parts
        if treatment_dir == (arm == "early_edit_5min"):
            matches.append(path)
    if len(matches) > 1:
        raise ValueError("ambiguous treatment/control trace layout")
    return matches[0] if matches else None


def safe_stats(trace_path: Path | None) -> dict[str, Any]:
    if trace_path is None:
        return {"trace_found": False}
    trace = json.loads(trace_path.read_text(encoding="utf-8"))
    stats = reduce_feedback(trace)
    return {key: stats[key] for key in PERMITTED if key in stats}


def audit(root: Path, manifest: Path) -> dict[str, Any]:
    plan = json.loads(manifest.read_text(encoding="utf-8"))
    expected = validate_plan(plan)
    payload = json.loads((root / RESULT).read_text(encoding="utf-8"))
    if payload.get("version") != plan["version"]:
        raise ValueError("wrong paired experiment version")
    if payload.get("status") != "completed":
        raise ValueError("paired model evaluation is not complete")
    if payload.get("model") != plan["model"]:
        raise ValueError("wrong paired model")
    if payload.get("selected_public_dev_ids") != expected:
        raise ValueError("wrong frozen task denominator")
    rows = payload.get("results")
    if payload.get("total_evaluations") != 8 or not isinstance(rows, list) or len(rows) != 8:
        raise ValueError("missing or extra evaluation")
    indexed = {}
    for row in rows:
        if not isinstance(row, dict) or row.get("arm") not in ARMS:
            raise ValueError("unrecognized arm")
        key = (row.get("arm"), row.get("instance_id"))
        if key[1] not in expected or key in indexed:
            raise ValueError("duplicate or unexpected task result")
        if row.get("status") not in ("completed", "error"):
            raise ValueError("unknown result status")
        indexed[key] = row
    if set(indexed) != {(arm,task) for arm in ARMS for task in expected}:
        raise ValueError("incomplete pair")
    by_arm = {}
    details = []
    for arm in ARMS:
        processed = []
        for task in expected:
            row = indexed[(arm,task)]
            stat = safe_stats(locate_trace(root,task,arm))
            item = {
                "arm": arm,
                "instance_id": task,
                "resolved": row.get("resolved") is True,
                "has_patch": row.get("has_patch") is True,
                "tool_calls": row.get("tool_calls") if isinstance(row.get("tool_calls"), int) else None,
                "duration_seconds": row.get("duration_seconds") if isinstance(row.get("duration_seconds"), (float,int)) else None,
                "feedback": stat,
            }
            processed.append(item)
            details.append(item)
        by_arm[arm] = {
            "task_count": len(processed),
            "resolved": sum(i["resolved"] for i in processed),
            "patched": sum(i["has_patch"] for i in processed),
            "traces_found": sum(i["feedback"].get("trace_found") is True for i in processed),
            "first_edits_observed": [i["feedback"].get("first_edit_action") for i in processed],
            "tasks_first_edit_by_call_10": sum(
                i["feedback"].get("first_edit_action") is not None
                and i["feedback"]["first_edit_action"] <= 10
                for i in processed
            ),
            "recognized_explicit_tests": sum(i["feedback"].get("explicit_or_inline_tests",0) for i in processed),
        }
    return {
        "version": VERSION, "source_gpu_run": 43178431152,
        "new_gpu_inference_training_or_competition_submission": False,
        "raw_private_data_exported": False,
        "by_arm": by_arm, "tasks": details,
        "limitations": (
            "Only four previously-screened public development tasks. "
            "Recorded actions differ from scorer tool calls; unknown/opaque shell "
            "commands may hide validation checks. First-edit timing and correctness "
            "do not establish causal intervention or official leaderboard lift."
        ),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, type=Path)
    ap.add_argument("--manifest", type=Path, default=Path(PLAN_FILE))
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    report = audit(args.root,args.manifest)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("SAFE_EARLYEDIT_EXISTING_TRACE_AUDIT="+json.dumps(report,sort_keys=True))


if __name__ == "__main__":
    main()
