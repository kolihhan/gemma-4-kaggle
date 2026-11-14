"""Audit completed Gemma reproduce-first 31B traces without new inference or raw-data export."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

from scripts.audit_paired_31b_feedback_v2 import reduce_feedback

SOURCE_RUN = 43547354883
TASKS = ("fastapi_15800", "rich_3518", "rich_4075", "fastapi_14492")
ARMS = ("champion", "repro_first")
VERSION = "gemma-31b-repro-first-20261114"
TREATMENT_SHA = "8d25aafe6e11fc6045243d23fb2ab80fedd583feaa095a0e2799e338897052c0"
TOOL_ALLOWLIST = {
    "read_file", "edit_file", "write_file", "run_command", "submit_patch",
    "get_status", "get_code_neighbors", "search_similar_code", "get_code_subgraph",
}


def submit_call_diagnostics(trace: dict) -> dict:
    """Categorize actual submit tool responses without exporting their payloads."""
    statuses = Counter()
    patch_nonempty = 0
    max_streak = streak = 0
    ambiguous_parallel = 0
    for step in trace.get("steps", []):
        if not isinstance(step, dict):
            continue
        calls = [c for c in step.get("tool_calls", []) if isinstance(c, dict)]
        for call in calls:
            if call.get("function_name") != "submit_patch":
                streak = 0
                continue
            streak += 1
            max_streak = max(max_streak, streak)
            if len(calls) != 1:
                statuses["unknown_parallel"] += 1
                ambiguous_parallel += 1
                continue
            observation = step.get("observation")
            content = observation.get("content", observation) if isinstance(observation, dict) else None
            if isinstance(content, str):
                try:
                    content = json.loads(content)
                except (ValueError, TypeError):
                    content = None
            if not isinstance(content, dict):
                statuses["unknown"] += 1
                continue
            state = content.get("status")
            statuses[state if state in ("ok", "error", "timeout") else "unknown"] += 1
            patch_nonempty += int(isinstance(content.get("patch_size"), int)
                                  and content["patch_size"] > 0)
    return {"submit_response_states": dict(sorted(statuses.items())),
            "submit_patch_nonempty_responses": patch_nonempty,
            "max_consecutive_submit_calls": max_streak,
            "parallel_submit_attribution_ambiguous": ambiguous_parallel}


def safe_trace(path: Path) -> dict:
    trace = json.loads(path.read_text(encoding="utf-8"))
    metrics = reduce_feedback(trace)
    kinds = Counter(
        call.get("function_name")
        for step in trace.get("steps", [])
        if isinstance(step, dict)
        for call in step.get("tool_calls", [])
        if isinstance(call, dict) and call.get("function_name") in TOOL_ALLOWLIST
    )
    return {
        "trace_found": True,
        **submit_call_diagnostics(trace),
        "first_edit_action": metrics["first_edit_action"],
        "edit_actions": metrics["total_edit_actions"],
        "explicit_or_inline_tests": metrics["explicit_or_inline_tests"],
        "tests_after_first_edit": metrics["tests_after_first_edit"],
        "nonzero_test_then_edit": metrics["nonzero_test_then_edit"],
        "nonzero_commands_followed_by_edit": metrics["nonzero_commands_followed_by_edit"],
        "command_class_counts": metrics["command_class_counts"],
        "all_command_structured_exit": metrics["all_command_structured_exit"],
        "opaque_commands": metrics["unclassified_opaque_commands"],
        "read_calls": kinds["read_file"],
        "graph_calls": sum(kinds[k] for k in
            ("get_code_neighbors", "search_similar_code", "get_code_subgraph")),
        "command_calls": kinds["run_command"],
        "submit_calls": kinds["submit_patch"],
    }


def audit(root: Path) -> dict:
    summaries = list(root.rglob("repro_first_summary.json"))
    if len(summaries) != 1:
        raise ValueError("expected exactly one private summary")
    source = json.loads(summaries[0].read_text(encoding="utf-8"))
    if (source.get("version") != VERSION or source.get("status") != "completed"
            or source.get("treatment_zip_sha256") != TREATMENT_SHA
            or tuple(source.get("selected_public_dev_ids", ())) != TASKS
            or source.get("total_evaluations") != 8):
        raise ValueError("source run or candidate mismatch")
    rows = source.get("results")
    if not isinstance(rows, list) or len(rows) != 8:
        raise ValueError("incomplete run")
    indexed = {}
    for row in rows:
        key = (row.get("arm"), row.get("instance_id"))
        if (key in indexed or key[0] not in ARMS or key[1] not in TASKS
                or not isinstance(row.get("resolved"), bool)
                or not isinstance(row.get("has_patch"), bool)
                or row.get("status") != "completed"):
            raise ValueError("invalid trial")
        indexed[key] = row
    if set(indexed) != {(arm, task) for arm in ARMS for task in TASKS}:
        raise ValueError("missing trial")
    traces = {}
    for path in root.rglob("trace_*.json"):
        name = path.name
        if name not in {f"trace_{task}.json" for task in TASKS}:
            continue
        is_treatment = "public-prompt" in path.relative_to(root).parts
        arm = "repro_first" if is_treatment else "champion"
        task = name[6:-5]
        key = (arm, task)
        if key in traces:
            raise ValueError("ambiguous private trace; cannot trust arm attribution")
        traces[key] = path
    out = []
    for arm in ARMS:
        for task in TASKS:
            record = indexed[(arm, task)]
            path = traces.get((arm, task))
            out.append({
                "arm": arm, "task": task, "resolved": record["resolved"],
                "has_patch": record["has_patch"],
                "grader_exit": record.get("test_exit_code"),
                "tool_calls": record.get("tool_calls"),
                "elapsed_s": round(record["duration_seconds"], 2),
                **(safe_trace(path) if path else {"trace_found": False}),
            })
    return {
        "version": "gemma-31b-repro-first-existing-trace-audit-v1",
        "source_run": SOURCE_RUN, "new_gpu_inference": False,
        "new_submission": False, "private_content_exported": False,
        "by_arm": {
            arm: {
                "resolved": sum(x["resolved"] for x in out if x["arm"] == arm),
                "traces_found": sum(x["trace_found"] for x in out if x["arm"] == arm),
                "read_calls": sum(x.get("read_calls", 0) for x in out if x["arm"] == arm),
                "graph_calls": sum(x.get("graph_calls", 0) for x in out if x["arm"] == arm),
                "explicit_or_inline_tests": sum(
                    x.get("explicit_or_inline_tests", 0) for x in out if x["arm"] == arm),
                "opaque_commands": sum(x.get("opaque_commands", 0) for x in out if x["arm"] == arm),
            } for arm in ARMS
        },
        "tasks": out,
        "limitations": (
            "Opaque commands can hide verification; model-visible feedback is not the "
            "grader exit. Four reused development tasks cannot measure transfer."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    report = audit(args.root)
    print("GEMMA_REPRO_FIRST_EXISTING_SAFE_AUDIT=" +
          json.dumps(report, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
