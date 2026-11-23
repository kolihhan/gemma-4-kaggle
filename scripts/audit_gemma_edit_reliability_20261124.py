"""Audit existing private Gemma 31B tool edits without publishing any task content.

Inputs: read-only output of the completed paired private Kaggle kernel.
Outputs: safe aggregate counts; no raw issue, path, patch, command, arguments,
tool observations, trace file names, or gold reference material. CPU only.
"""
from __future__ import annotations

from collections import Counter
import argparse
import json
from pathlib import Path
import re

ARMS = ("champion_4min", "behavioral_4min")
EXPECTED_VERSION = "behavioral-probe-31b-4min-paired-v1"
SUMMARY = "paired_behavioral_probe31b_4min_results.json"
REQUIRED = {
    "edit_file": ("filepath", "old_string", "new_string"),
    "write_file": ("filepath", "content"),
    "read_file": ("filepath",),
    "run_command": ("command",),
}
EDIT_TOOLS = {"edit_file", "write_file"}
KNOWN_TOOLS = EDIT_TOOLS | {"read_file", "run_command", "get_status",
                            "get_code_neighbors", "search_similar_code",
                            "get_code_subgraph", "submit_patch"}


def safe_result_rows(data: dict) -> list[dict]:
    if data.get("version") != EXPECTED_VERSION or data.get("status") != "completed":
        raise ValueError("wrong or incomplete frozen private paired run")
    rows = data.get("results")
    if not isinstance(rows, list) or len(rows) != 16:
        raise ValueError("expected 16 actual result rows")
    keys = []
    for row in rows:
        if not isinstance(row, dict) or row.get("arm") not in ARMS:
            raise ValueError("wrong arm")
        tid = row.get("instance_id")
        if not isinstance(tid, str) or not re.fullmatch(r"(fastapi|rich|requests)_\d+", tid):
            raise ValueError("bad task id")
        if type(row.get("resolved")) is not bool or type(row.get("has_patch")) is not bool:
            raise ValueError("unverified grader resolution or patch")
        keys.append((tid, row["arm"]))
    ids = {x[0] for x in keys}
    if len(ids) != 8 or len(set(keys)) != 16 or set(keys) != {
        (tid, arm) for tid in ids for arm in ARMS
    }:
        raise ValueError("not genuinely matched issue arms")
    return rows


def trace_for(root: Path, arm: str, task_id: str) -> Path | None:
    matches = []
    for p in root.rglob("trace_*.json"):
        if p.name != f"trace_{task_id}.json":
            continue
        # The existing paired renderer writes the treatment under
        # results_dir / "public-prompt"; the control at results root.
        treatment = "public-prompt" in p.relative_to(root).parts
        if treatment == (arm == "behavioral_4min"):
            matches.append(p)
    if len(matches) > 1:
        raise ValueError("ambiguous task trace")
    return matches[0] if matches else None


def _observe(observation: object) -> tuple[str, str]:
    """Classify an observation, never return arbitrary text."""
    obj = observation
    if isinstance(obj, list):
        if len(obj) != 1:
            return ("unknown", "UNKNOWN")
        obj = obj[0]
    if isinstance(obj, dict) and "content" in obj and "status" not in obj:
        obj = obj["content"]
    if isinstance(obj, dict) and "text" in obj and "status" not in obj:
        obj = obj["text"]
    if isinstance(obj, str):
        try:
            obj = json.loads(obj)
        except (ValueError, TypeError):
            return ("unknown", "UNKNOWN")
    if not isinstance(obj, dict):
        return ("unknown", "UNKNOWN")
    if "result" in obj and isinstance(obj["result"], dict) and "status" not in obj:
        obj = obj["result"]
    status = obj.get("status")
    if status not in ("ok", "error"):
        return ("unknown", "UNKNOWN")
    if status == "ok":
        return ("ok", "OK")
    typ = str(obj.get("error_type", ""))
    msg = str(obj.get("error_message", "")).lower()
    if ("mandatory input parameters" in msg or "required parameter" in msg
            or "missing required" in msg):
        category = "DISPATCH_MISSING_ARGS"
    elif typ == "FileEditError":
        category = "EDIT_MATCH_OR_VALIDATION"
    elif typ in ("ValidationError", "TypeError", "ValueError"):
        category = "VALIDATION"
    elif typ == "TimeoutExceeded":
        category = "COMMAND_TIMEOUT"
    elif typ == "CommandError":
        category = "COMMAND_NONZERO"
    else:
        category = "OTHER_TOOL_ERROR"
    return ("error", category)


def _arg_shape(tool: str, args: object) -> str:
    if tool not in REQUIRED:
        return "not_applicable"
    if not isinstance(args, dict):
        return "invalid_non_object"
    required = REQUIRED[tool]
    if any(key not in args or not isinstance(args[key], str) for key in required):
        return "invalid_missing_or_wrong_type"
    if tool == "edit_file" and not args["old_string"]:
        return "invalid_empty_target"
    if tool == "run_command" and not args["command"].strip():
        return "invalid_empty_command"
    if tool in EDIT_TOOLS and any(k not in set(required) | {"allow_multiple"} for k in args):
        return "unexpected_keys_present"
    return "apparently_valid"


def reduce_trace(trace: dict) -> dict:
    if not isinstance(trace, dict) or not isinstance(trace.get("steps"), list):
        raise ValueError("trace schema unknown")
    counts = Counter()
    ordinal = 0
    first_edit = None
    first_submit = None
    last_edit = None
    for step in trace["steps"]:
        if not isinstance(step, dict) or not isinstance(step.get("tool_calls"), list):
            continue
        calls = [c for c in step["tool_calls"] if isinstance(c, dict)]
        # The step-level observation cannot reliably be assigned to one
        # tool when parallel function calls are present.
        observable = len(calls) == 1
        for call in calls:
            name = call.get("function_name")
            if name not in KNOWN_TOOLS:
                continue
            ordinal += 1
            counts["tool_events"] += 1
            counts["tool_" + name] += 1
            if name in EDIT_TOOLS:
                counts["edit_events"] += 1
                first_edit = first_edit or ordinal
                last_edit = ordinal
                shape = _arg_shape(name, call.get("arguments"))
                counts["edit_arg_" + shape] += 1
                status, category = _observe(step.get("observation")) if observable else ("unknown", "UNKNOWN")
                counts["edit_observation_" + status] += 1
                if status == "error":
                    counts["edit_error_" + category] += 1
                if shape != "apparently_valid":
                    counts["edit_shape_anomaly_events"] += 1
            if name == "run_command":
                if _arg_shape(name, call.get("arguments")) != "apparently_valid":
                    counts["run_command_arg_anomaly_events"] += 1
            if name == "submit_patch":
                first_submit = first_submit or ordinal
                counts["submit_requests"] += 1
                status, cat = _observe(step.get("observation")) if observable else ("unknown", "UNKNOWN")
                counts["submit_observation_" + status] += 1
    return {
        "trace_found": True, "trace_tool_events": counts["tool_events"],
        "first_edit_event": first_edit, "last_edit_event": last_edit,
        "first_submit_event": first_submit,
        "edit_events": counts["edit_events"],
        "edit_argument_anomalies": counts["edit_shape_anomaly_events"],
        "edit_arg_invalid_non_object": counts["edit_arg_invalid_non_object"],
        "edit_arg_invalid_missing_or_wrong_type": counts["edit_arg_invalid_missing_or_wrong_type"],
        "edit_arg_invalid_empty_target": counts["edit_arg_invalid_empty_target"],
        "edit_arg_unexpected_keys_present": counts["edit_arg_unexpected_keys_present"],
        "edit_file_events": counts["tool_edit_file"],
        "write_file_events": counts["tool_write_file"],
        "edit_confirmed_ok": counts["edit_observation_ok"],
        "edit_confirmed_error": counts["edit_observation_error"],
        "edit_observation_unknown": counts["edit_observation_unknown"],
        "edit_dispatch_missing_args": counts["edit_error_DISPATCH_MISSING_ARGS"],
        "edit_match_or_validation_errors": counts["edit_error_EDIT_MATCH_OR_VALIDATION"],
        "edit_other_errors": counts["edit_observation_error"]
            - counts["edit_error_DISPATCH_MISSING_ARGS"]
            - counts["edit_error_EDIT_MATCH_OR_VALIDATION"],
        "submit_requests": counts["submit_requests"],
        "submit_confirmed_ok": counts["submit_observation_ok"],
        "submit_observation_unknown": counts["submit_observation_unknown"],
        "run_command_events": counts["tool_run_command"],
        "run_command_arg_anomalies": counts["run_command_arg_anomaly_events"],
        "read_file_events": counts["tool_read_file"],
    }


def audit(root: Path) -> dict:
    rows = safe_result_rows(json.loads((root / SUMMARY).read_text(encoding="utf-8")))
    reports = []
    for row in rows:
        p = trace_for(root, row["arm"], row["instance_id"])
        stats = reduce_trace(json.loads(p.read_text(encoding="utf-8"))) if p else {
            "trace_found": False
        }
        reports.append({
            "arm": row["arm"], "resolved": row["resolved"],
            "has_patch": row["has_patch"],
            "tool_calls_scorer": row.get("tool_calls"),
            "duration_seconds": row.get("duration_seconds"),
            **stats,
        })
    result = {}
    for arm in ARMS:
        selected = [r for r in reports if r["arm"] == arm]
        visible = [r for r in selected if r["trace_found"]]
        result[arm] = {
            "evaluated": len(selected),
            "resolved": sum(r["resolved"] for r in selected),
            "final_patch_present": sum(r["has_patch"] for r in selected),
            "traces_found": len(visible),
            "traces_with_explicit_submit": sum(r.get("submit_requests", 0) > 0 for r in visible),
            "traces_with_edit_argument_anomalies": sum(r.get("edit_argument_anomalies", 0) > 0 for r in visible),
            "total_scorer_tool_calls": sum(r.get("tool_calls_scorer") or 0 for r in selected),
            "total_task_seconds": round(sum(r.get("duration_seconds") or 0 for r in selected), 2),
            "over_4min_task_record_seconds": sum((r.get("duration_seconds") or 0) > 240 for r in selected),
            "from_traces_only": {
                key: sum(r.get(key, 0) for r in visible)
                for key in (
                    "trace_tool_events", "edit_events", "edit_argument_anomalies",
                    "edit_arg_invalid_non_object", "edit_arg_invalid_missing_or_wrong_type",
                    "edit_arg_invalid_empty_target", "edit_arg_unexpected_keys_present",
                    "edit_file_events", "write_file_events",
                    "edit_confirmed_ok", "edit_confirmed_error",
                    "edit_observation_unknown", "edit_dispatch_missing_args",
                    "edit_match_or_validation_errors", "edit_other_errors",
                    "submit_requests", "submit_confirmed_ok",
                    "submit_observation_unknown", "run_command_events",
                    "run_command_arg_anomalies", "read_file_events",
                )
            },
        }
    return {
        "version": "gemma-private-edit-reliability-audit-v1",
        "source_kernel": "kolihhan/gemma4-behavioral-paired-20261123-v1",
        "paired_issues": 8,
        "model_task_evaluations": 16,
        "results_by_arm": result,
        "raw_private_content_exported": False,
        "gpu_inference_launched": False,
        "competition_submission_created": False,
        "limitations": (
            "Only recorded tool events; duplicated callbacks/parallel observations can "
            "make event totals differ from physical scorer tool calls. Missing trace "
            "or response remains unknown; final patch presence is NOT patch correctness. "
            "Cannot attribute hidden scorer failure to tool editing without complete evidence."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    report = audit(args.root)
    print("GEMMA_EDIT_RELIABILITY_SAFE_AUDIT=" + json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
