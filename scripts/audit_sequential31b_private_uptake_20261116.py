#!/usr/bin/env python3
"""Read-only privacy-preserving audit of a FINISHED private 31B SequentialAgent kernel.

Input remains on an authorized runner. Stdout contains ONLY aggregate allowlisted
booleans/counters (never task IDs, paths, commands, issue text, model outputs,
tool arguments, patches, raw traces, or reference answers).
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

from scripts.audit_paired_31b_feedback_v2 import command_class

VERSION = "gemma-sequential-native-verify-20261116-v0"
MODEL = "gemma-4-31b-it-qat-w4a16-ct"
STAGES = {"staged_coder": "coder", "mandatory_native_verifier": "verifier"}
MARKER_KEYS = ("agent_name", "author", "agent", "agent_id", "stage", "name")
EDIT = {"edit_file", "write_file"}
TEST = {"explicit_test", "inline_assert"}
SCHEMA_KEYS = ("steps", "events")


def _stage(step: dict) -> str | None:
    """Stage attribution ONLY from a structured exact-name marker, not prompts."""
    for key in MARKER_KEYS:
        value = step.get(key)
        if type(value) is str and value in STAGES:
            return STAGES[value]
    return None


def _trace(root: Path, issue_id: str) -> dict:
    """Expected trace filename follows pre-existing frozen private scorer layout."""
    found = [p for p in root.rglob("trace_*.json")
             if p.name == "trace_" + issue_id + ".json"]
    if not found:
        return {"found": False, "schema": False}
    if len(found) != 1:
        return {"found": False, "schema": False, "ambiguous": True}
    try:
        obj = json.loads(found[0].read_text(encoding="utf8"))
    except (OSError, ValueError, UnicodeError):
        return {"found": True, "schema": False}
    steps = obj.get("steps") if isinstance(obj, dict) else None
    if not isinstance(steps, list):
        return {"found": True, "schema": False}

    events = []
    marker_steps = Counter()
    for step in steps:
        if not isinstance(step, dict):
            continue
        tag = _stage(step)
        if tag:
            marker_steps[tag] += 1
        calls = step.get("tool_calls")
        if not isinstance(calls, list):
            continue
        for item in calls:
            if not isinstance(item, dict):
                continue
            fn = item.get("function_name")
            if fn not in ("run_command", *EDIT, "submit_patch", "read_file",
                          "get_status", "write_file", "get_code_neighbors",
                          "search_similar_code", "get_code_subgraph"):
                continue
            category = "other"
            if fn in EDIT:
                category = "edit"
            elif fn == "run_command":
                args = item.get("arguments")
                cmd = args.get("command") if isinstance(args, dict) else None
                category = command_class(cmd)
            elif fn == "submit_patch":
                category = "submit"
            events.append((tag, category))

    edit_indices = [i for i, (_, kind) in enumerate(events) if kind == "edit"]
    test_indices = [i for i, (_, kind) in enumerate(events) if kind in TEST]
    verifier_test_indices = [i for i, (tag, kind) in enumerate(events)
                             if tag == "verifier" and kind in TEST]
    verifier_edits = [i for i, (tag, kind) in enumerate(events)
                      if tag == "verifier" and kind == "edit"]
    return {
        "found": True, "schema": True,
        "stage_marker_coder": bool(marker_steps["coder"]),
        "stage_marker_verifier": bool(marker_steps["verifier"]),
        "verifier_tool_event": any(tag == "verifier" for tag, _ in events),
        "verifier_recognized_test": bool(verifier_test_indices),
        "any_recognized_test": bool(test_indices),
        "recognized_test_after_first_edit": bool(
            edit_indices and any(i > edit_indices[0] for i in test_indices)),
        "verifier_reedit_after_recognized_test": any(
            e > t for e in verifier_edits for t in verifier_test_indices),
        "opaque_command_present": any(kind in ("opaque_python", "other",
                                              "unavailable") for _, kind in events),
        "note": "Raw trace events can duplicate; never treated as scorer tool-call counts.",
    }


def audit(root: Path) -> dict:
    summary = root / "native_sequential31b_matched_results.json"
    if not summary.is_file():
        return {"status": "UNAVAILABLE", "reason": "scorer_summary_not_found"}
    obj = json.loads(summary.read_text(encoding="utf8"))
    rows = obj.get("results")
    if (obj.get("version") != VERSION or obj.get("model") != MODEL
            or not isinstance(rows, list) or len(rows) != 3
            or any(type(r.get("resolved")) is not bool for r in rows)):
        return {"status": "UNKNOWN", "reason": "scorer_contract_mismatch"}
    ids = [r.get("instance_id") for r in rows]
    if (not all(type(x) is str and x.startswith(
            ("fastapi_", "rich_", "requests_")) for x in ids)
            or len(set(ids)) != 3):
        return {"status": "UNKNOWN", "reason": "task_identity_contract_mismatch"}

    stats = [_trace(root, issue_id) for issue_id in ids]
    keys = ("found", "schema", "stage_marker_coder", "stage_marker_verifier",
            "verifier_tool_event", "verifier_recognized_test",
            "any_recognized_test", "recognized_test_after_first_edit",
            "verifier_reedit_after_recognized_test", "opaque_command_present")
    count = {key + "_tasks": sum(bool(x.get(key)) for x in stats) for key in keys}
    total_calls = sum(r.get("tool_calls") for r in rows
                      if type(r.get("tool_calls")) is int)
    correct_count = sum(r["resolved"] for r in rows)
    reviewed = count["stage_marker_verifier_tasks"]
    # A recognized command is not proof it executed successfully or addressed
    # the issue. No structured reviewer marker means UNKNOWN, not absence.
    confidence = ("TRACE_MARKER_AND_TEST_COMMAND_OBSERVED"
                  if count["verifier_recognized_test_tasks"] > 0
                  else "NO_RECOGNIZED_TEST_WITH_MARKER"
                  if reviewed == 3 and count["schema_tasks"] == 3
                  else "UNKNOWN_STAGE_OR_TRACE_SCHEMA")
    return {
        "version": "gemma-seq31b-existing-private-safe-audit-v1",
        "status": "COMPLETE_METADATA_ONLY",
        "private_grader_matched_n": len(rows),
        "resolved": correct_count,
        "scorer_tool_calls": total_calls,
        "uptake_evidence": confidence,
        "counts": count,
        "no_new_inference": True,
        "no_training": True,
        "no_official_submission": True,
        "raw_private_content_exported": False,
        "limitation": (
            "Structured stage markers may be absent even when stages ran. "
            "An explicit test-like command is not proof of execution, passing, "
            "issue relevance or model feedback consumption. Opaque commands "
            "can include tests. Printed counters do not give hidden Kaggle score."
        ),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    args = ap.parse_args()
    try:
        result = audit(args.root)
    except BaseException as exc:
        # No exception message or path: could contain private issue/test text.
        result = {"status": "UNKNOWN", "reason": "safe_reducer_exception",
                  "exception_class": type(exc).__name__,
                  "no_new_inference": True, "raw_private_content_exported": False}
    print("GEMMA_SEQ31B_SAFE_UPTAKE=" + json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
