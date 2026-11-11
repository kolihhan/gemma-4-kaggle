#!/usr/bin/env python3
"""Read-only, GPU-free audit of a completed private paired Gemma 31B pilot.

Outputs only safe counters; never print prompts, commands, patches, task text,
reference answers, grader text, or trace paths.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import shlex

ARMS = ("v2_5min", "public_prompt_5min")
TOOLS = frozenset(("read_file", "edit_file", "write_file", "run_command",
                   "submit_patch", "get_status", "get_code_neighbors",
                   "search_similar_code", "get_code_subgraph"))


def test_invocation(command: object) -> bool:
    """Possible test invocation, not proof a test ran or passed."""
    if not isinstance(command, str):
        return False
    try:
        words = shlex.split(command)
    except ValueError:
        return False
    if not words or words[0] in ("echo", "grep", "cat", "rg", "printf"):
        return False
    for index, word in enumerate(words):
        if word in ("pytest", "py.test", "tox", "nox") and (
            index == 0 or words[index-1] in ("&&", ";", "|", "run")
        ):
            return True
        if (word in ("python", "python3") and words[index+1:index+3]
                in (["-m", "pytest"], ["-m", "unittest"])):
            return True
    return False


def read_safe_results(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("version") != "public-prompt-v2-paired-clean-v1":
        raise ValueError("not expected frozen pilot")
    rows = data.get("results")
    if not isinstance(rows, list) or len(rows) != 6:
        raise ValueError("expected exactly six results")
    pairs: set[tuple[str, str]] = set()
    for row in rows:
        if not isinstance(row, dict) or row.get("arm") not in ARMS:
            raise ValueError("invalid arm")
        tid = row.get("instance_id")
        if not isinstance(tid, str) or not re.fullmatch(r"(fastapi|rich|requests)_[0-9]+", tid):
            raise ValueError("invalid public development ID")
        key = (row["arm"], tid)
        if key in pairs:
            raise ValueError("duplicate paired result")
        pairs.add(key)
        if not isinstance(row.get("resolved"), bool) or not isinstance(row.get("has_patch"), bool):
            raise ValueError("missing correctness or patch flag")
    ids = {tid for _, tid in pairs}
    if len(ids) != 3 or pairs != {(arm, tid) for arm in ARMS for tid in ids}:
        raise ValueError("paired tasks mismatch")
    return rows


def trace_for(root: Path, arm: str, task_id: str) -> Path | None:
    matches = []
    for path in root.rglob("trace_*.json"):
        if path.name != f"trace_{task_id}.json":
            continue
        is_treatment = "public-prompt" in path.relative_to(root).parts
        if is_treatment == (arm == "public_prompt_5min"):
            matches.append(path)
    if len(matches) > 1:
        raise ValueError("ambiguous trace")
    return matches[0] if matches else None


def reduce_trace(path: Path) -> dict:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict) or not isinstance(obj.get("steps"), list):
        raise ValueError("unexpected trace schema")
    actions = []
    for step in obj["steps"]:
        if not isinstance(step, dict) or not isinstance(step.get("tool_calls"), list):
            continue
        for call in step["tool_calls"]:
            if not isinstance(call, dict):
                continue
            tool = call.get("function_name")
            if tool not in TOOLS:
                continue
            arguments = call.get("arguments") or {}
            command = arguments.get("command") if isinstance(arguments, dict) else None
            kind = ("possible_test" if tool == "run_command" and test_invocation(command)
                    else "edit" if tool in ("edit_file", "write_file") else tool)
            actions.append(kind)
    edits = [i for i, kind in enumerate(actions) if kind == "edit"]
    tests = [i for i, kind in enumerate(actions) if kind == "possible_test"]
    counts = Counter(actions)
    return {
        "trace_found": True,
        "known_tool_calls": len(actions),
        "edits": len(edits),
        "first_edit_call": (edits[0] + 1) if edits else None,
        "possible_test_invocations": len(tests),
        "possible_test_after_edit": bool(edits and any(t > edits[0] for t in tests)),
        "possible_repair_after_test": bool(any(e > t for t in tests for e in edits)),
        "submit_patch_calls": counts["submit_patch"],
        "reads": counts["read_file"],
        "graph_lookups": sum(counts[x] for x in (
            "get_code_neighbors", "search_similar_code", "get_code_subgraph")),
        "commands_other": counts["run_command"],
    }


def audit(root: Path) -> dict:
    rows = read_safe_results(root / "paired_prompt_v2_31b_results.json")
    reports = []
    for row in rows:
        path = trace_for(root, row["arm"], row["instance_id"])
        mech = reduce_trace(path) if path else {"trace_found": False}
        reports.append({
            "arm": row["arm"],
            "instance_id": row["instance_id"],
            "resolved": row["resolved"],
            "has_patch": row["has_patch"],
            "grader_test_exit_code": row.get("test_exit_code"),
            "tool_calls_scorer": row.get("tool_calls"),
            "duration_seconds": row.get("duration_seconds"),
            **mech,
        })
    return {
        "version": "paired-31b-trace-mechanism-readonly-v1",
        "source_run_id": 43057377220,
        "model_task_evaluations": 6,
        "new_model_inference": False,
        "new_official_submission": False,
        "raw_content_exported": False,
        "classification_limit": "Grader exit 1 cannot distinguish semantic errors, setup, or underspecified issues. Missing traces are UNOBSERVED, not zero calls. Possible test invocation does not prove execution or relevance.",
        "by_arm": {arm: {
            "evaluated": sum(r["arm"] == arm for r in reports),
            "resolved": sum(r["arm"] == arm and r["resolved"] for r in reports),
            "patched": sum(r["arm"] == arm and r["has_patch"] for r in reports),
            "traces_found": sum(r["arm"] == arm and r["trace_found"] for r in reports),
        } for arm in ARMS},
        "tasks": reports,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("SAFE_PAIRED_TRACE_AUDIT=" + json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
