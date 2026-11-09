"""Evidence gate for a single exploratory official V2 toolcap60 submission.

This is not a proof of increased SWE resolution. It rejects unseen
regressions or non-exercised tool cap changes on the frozen 4-task pilot.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

VERSION = "v2-toolcap-31b-paired-pilot-v1"
MODEL = "gemma-4-31b-it-qat-w4a16-ct"
ARMS = ("baseline_v2_28", "v2_60_calls")


def assess(document: dict, expected_manifest: dict) -> dict:
    if document.get("status") != "completed" or document.get("version") != VERSION:
        raise ValueError("pilot not terminal or unexpected evaluator version")
    if document.get("model") != MODEL:
        raise ValueError("pilot model mismatch")
    ids = document.get("instance_ids")
    rows = document.get("records")
    if not isinstance(ids, list) or len(ids) != 4 or len(set(ids)) != 4:
        raise ValueError("pilot denominator incomplete")
    if (not isinstance(rows, list) or len(rows) != 8
            or expected_manifest.get("version") != VERSION
            or expected_manifest.get("arms") != list(ARMS)):
        raise ValueError("evaluation row count or manifest invalid")
    excluded = set(expected_manifest["exclusions"])
    if set(ids) & excluded:
        raise ValueError("pilot reuses previously inspected task")
    for arm in ARMS:
        matched = [r for r in rows if r.get("arm") == arm]
        if len(matched) != 4 or {r.get("instance_id") for r in matched} != set(ids):
            raise ValueError("paired task coverage incorrect")
        if any(r.get("status") != "completed" or not isinstance(
                r.get("resolved"), bool) or not isinstance(
                r.get("duration_seconds"), (int, float)) or
                not isinstance(r.get("tool_calls"), int) for r in matched):
            raise ValueError("evaluation incomplete or ungraded")
    base = [r for r in rows if r["arm"] == ARMS[0]]
    treatment = [r for r in rows if r["arm"] == ARMS[1]]
    base_correct = sum(r["resolved"] for r in base)
    alt_correct = sum(r["resolved"] for r in treatment)
    base_seconds = sum(r["duration_seconds"] for r in base)
    alt_seconds = sum(r["duration_seconds"] for r in treatment)
    call_cap_exercised = any(r["tool_calls"] > 28 for r in treatment)
    allowed = (
        alt_correct >= base_correct
        and (call_cap_exercised or alt_correct > base_correct)
        and alt_seconds <= base_seconds * 1.25
    )
    return {
        "status": "ELIGIBLE_EXPLORATORY_SUBMISSION" if allowed else "BLOCKED_NO_ADDED_VALUE",
        "proven_stronger": False,
        "base_resolved": base_correct,
        "treatment_resolved": alt_correct,
        "base_seconds": round(base_seconds, 2),
        "treatment_seconds": round(alt_seconds, 2),
        "treatment_tool_cap_exercised": call_cap_exercised,
        "no_known_regression_on_four_tasks": alt_correct >= base_correct,
        "within_25pct_time_overhead": alt_seconds <= base_seconds * 1.25,
        "sample_size": 4,
        "result_interpretation": "One small public development pilot; official score remains independent evidence",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metrics", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    outcome = assess(json.loads(args.metrics.read_text()),
                     json.loads(args.manifest.read_text()))
    print("TOOLCAP60_PRIVATE_PILOT_GATE="+json.dumps(outcome,sort_keys=True))
    if outcome["status"] != "ELIGIBLE_EXPLORATORY_SUBMISSION":
        raise SystemExit("NOT_SUBMITTED_BECAUSE_EXPERIMENT_GATE_FAILED")


if __name__=="__main__":
    main()
