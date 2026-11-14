"""Strict SWE-agent -> Gemma ADK action-schema feasibility test.

This bridge DOES NOT generate training records. It never runs tool calls, carries
external tool replies into ADK, or treats source 'resolved' as local reward.
External tool semantics are often not equivalent even when names align.
"""
from __future__ import annotations

from collections import Counter
import json
from pathlib import PurePosixPath
import re

from scripts.audit_open_swe_traces_metadata import sample_grade

ADK_TOOLS = {"run_command", "edit_file", "read_file", "write_file", "submit_patch"}


def _safe_path(value: object) -> str | None:
    if not isinstance(value, str) or not value or len(value) > 400:
        return None
    if "\x00" in value or "\\" in value:
        return None
    if value.startswith("/workspace/"):
        value = value.removeprefix("/workspace/")
    elif value.startswith("/testbed/"):
        # SWE-agent edit_anthropic is documented to use this root.
        # Target ADK materializes the task checkout at /workspace.
        # This is a *path translation*, not proof of tool/result equivalence.
        value = value.removeprefix("/testbed/")
    elif value.startswith("/"):
        return None
    parts = value.split("/")
    if any(p in ("", ".", "..") for p in parts):
        return None
    if not PurePosixPath(value).parts:
        return None
    return value


def path_category(value: object) -> str:
    """Aggregate source path *type* only; never return actual path components."""
    if not isinstance(value, str):
        return "missing_or_nonstring"
    if not value:
        return "empty"
    if "\\\\" in value or "\\x00" in value or any(x in ("..", ".") for x in value.split("/")):
        return "unsafe_or_traversal"
    if value.startswith("/workspace/"):
        return "workspace_absolute"
    if value.startswith("/testbed/"):
        return "sweagent_testbed_absolute"
    if value.startswith("/"):
        return "other_absolute"
    return "relative"


def source_editor_shape(event: object) -> tuple[str, str]:
    if not isinstance(event, dict) or not isinstance(event.get("function"), dict):
        return ("malformed", "missing_or_nonstring")
    raw = event["function"].get("arguments")
    try:
        args = json.loads(raw) if isinstance(raw, str) else raw
    except (ValueError, TypeError):
        return ("malformed", "missing_or_nonstring")
    if not isinstance(args, dict):
        return ("malformed", "missing_or_nonstring")
    action = args.get("command")
    if action not in {"view", "create", "insert", "str_replace"}:
        action = "other"
    return (action, path_category(args.get("path")))


def _response_is_adk_contract(content: object) -> bool:
    """Native ADK returns a JSON object with status and action-specific keys.

    A superficial status key alone is NOT sufficient for true feedback parity.
    Treat any foreign feedback as unverified unless a future per-tool semantic
    translator is proven.
    """
    if not isinstance(content, str):
        return False
    try:
        value = json.loads(content)
    except (ValueError, TypeError):
        return False
    return (isinstance(value, dict) and value.get("status") in {"ok", "error"})


def action_meta(event: object) -> tuple[str, dict | None, str]:
    """Return strict mapped action in-memory; never emit raw arguments to logs."""
    if not isinstance(event, dict):
        return ("invalid", None, "not_object")
    fn = event.get("function")
    if not isinstance(fn, dict):
        return ("invalid", None, "missing_function")
    name = fn.get("name")
    raw = fn.get("arguments")
    if not isinstance(name, str):
        return ("invalid", None, "missing_name")
    if isinstance(raw, str):
        try:
            args = json.loads(raw)
        except (ValueError, TypeError):
            return (name, None, "arguments_not_json")
    else:
        args = raw
    if not isinstance(args, dict):
        return (name, None, "arguments_not_object")

    if name == "bash":
        if set(args) != {"command"} or not isinstance(args["command"], str):
            return (name, None, "bash_bad_signature")
        command = args["command"]
        if not command.strip() or len(command) > 4000 or "\x00" in command:
            return (name, None, "bash_invalid_command")
        # Syntax-only match. The external shell cwd, permissions, timeout,
        # output truncation and command effects are NOT established identical.
        return (name, {"name": "run_command", "args": {"command": command}},
                "mapped_action_semantics_unverified")

    if name == "submit":
        if args:
            return (name, None, "submit_extra_arguments")
        return (name, {"name": "submit_patch", "args": {}},
                "mapped_submit_lifecycle_unverified")

    if name != "str_replace_editor":
        return (name, None, "unsupported_external_tool")

    cmd = args.get("command")
    filepath = _safe_path(args.get("path"))
    if filepath is None:
        return (name, None, "editor_unsafe_or_missing_path")
    if cmd == "str_replace":
        if set(args) != {"command", "path", "old_str", "new_str"}:
            return (name, None, "editor_nonminimal_signature")
        before, after = args["old_str"], args["new_str"]
        if (not isinstance(before, str) or not before or
            not isinstance(after, str) or len(before) > 12000 or len(after) > 12000):
            return (name, None, "editor_invalid_replacement")
        return (name, {"name": "edit_file",
                       "args": {"filepath": filepath, "old_string": before,
                                "new_string": after, "allow_multiple": False}},
                "mapped_editor_matching_and_root_unverified")
    if cmd == "view":
        # SWE-agent's unbounded view may produce much larger output than
        # ADK's capped read_file. Do not translate it as equivalent.
        return (name, None, "view_output_truncation_mismatch")
    if cmd in {"create", "insert"}:
        return (name, None, "editor_write_semantics_unverified")
    return (name, None, "editor_unknown_command")


def trace_gate(row: dict) -> dict:
    if sample_grade(row) != "candidate_for_private_deep_audit":
        return {"status": "source_failed_admission", "action_total": 0}
    counts: Counter[str] = Counter()
    mapped: Counter[str] = Counter()
    reasons: Counter[str] = Counter()
    editor_modes: Counter[str] = Counter()
    editor_paths: Counter[str] = Counter()
    total = 0
    native_feedback_like = foreign_feedback = 0
    trace = row["messages"]
    for message in trace[:1200]:
        if not isinstance(message, dict):
            continue
        if message.get("role") == "tool":
            foreign_feedback += 1
            native_feedback_like += int(_response_is_adk_contract(message.get("content")))
        if message.get("role") != "assistant":
            continue
        calls = message.get("tool_calls", [])
        if not isinstance(calls, list):
            reasons["tool_calls_not_list"] += 1
            continue
        for call in calls:
            total += 1
            if total > 600:
                reasons["trajectory_tool_budget_exceeded"] += 1
                break
            name, mapped_action, reason = action_meta(call)
            counts[name if name in {"bash", "str_replace_editor", "submit"} else "other"] += 1
            if name == "str_replace_editor":
                mode, category = source_editor_shape(call)
                editor_modes[mode] += 1
                editor_paths[category] += 1
            reasons[reason] += 1
            if mapped_action is not None:
                mapped[mapped_action["name"]] += 1
            # Never persist mapped_action: values may contain source commands/patches.
        if total > 600:
            break
    mapped_total = sum(mapped.values())
    fully_syntax_mappable = (total > 0 and mapped_total == total)
    # External role-tool messages are not matched to native ADK feedback
    # semantics. This gate deliberately cannot approve an SFT trajectory.
    return {
        "status": "metadata_only_audit",
        "action_total": total,
        "mapped_action_count": mapped_total,
        "source_tools": dict(counts),
        "adk_action_counts": dict(mapped),
        "rejection_and_uncertainty_reasons": dict(reasons),
        "editor_command_modes": dict(editor_modes),
        "editor_path_categories": dict(editor_paths),
        "foreign_tool_replies": foreign_feedback,
        "adk_status_shaped_replies": native_feedback_like,
        "all_action_syntax_convertible": fully_syntax_mappable,
        "feedback_semantically_equivalent_verified": False,
        "full_training_trace_approved": False,
    }


def summarize(rows: list[dict]) -> dict:
    eligible = 0
    summed: Counter[str] = Counter()
    source: Counter[str] = Counter()
    target: Counter[str] = Counter()
    reasons: Counter[str] = Counter()
    editor_modes: Counter[str] = Counter()
    editor_paths: Counter[str] = Counter()
    complete = 0
    for wrapper in rows:
        row = wrapper.get("row", {}) if isinstance(wrapper, dict) else {}
        if sample_grade(row) != "candidate_for_private_deep_audit":
            continue
        eligible += 1
        audit = trace_gate(row)
        for key in ("action_total", "mapped_action_count", "foreign_tool_replies",
                    "adk_status_shaped_replies"):
            summed[key] += audit[key]
        source.update(audit["source_tools"])
        target.update(audit["adk_action_counts"])
        reasons.update(audit["rejection_and_uncertainty_reasons"])
        editor_modes.update(audit["editor_command_modes"])
        editor_paths.update(audit["editor_path_categories"])
        complete += int(audit["all_action_syntax_convertible"])
    return {
        "source": "nvidia/Open-SWE-Traces/v2.0/sweagent",
        "probe": "rows 6..17, fixed before inspection",
        "sampled_rows": len(rows),
        "eligible_source_rows": eligible,
        "total_actions": summed["action_total"],
        "mapped_action_syntax_count": summed["mapped_action_count"],
        "external_tool_names": dict(source),
        "adk_action_names": dict(target),
        "mapping_gates": dict(reasons),
        "editor_command_modes": dict(editor_modes),
        "editor_path_categories": dict(editor_paths),
        "fully_syntax_mappable_rows": complete,
        "foreign_feedback_rows": summed["foreign_tool_replies"],
        "adk_status_shaped_reply_rows": summed["adk_status_shaped_replies"],
        "feedback_equivalence_approved": 0,
        "trainable_trajectories_approved": 0,
        "has_saved_source_commands": False,
        "has_saved_tool_responses": False,
        "actual_tool_execution": False,
        "model_training_performed": False,
    }


if __name__ == "__main__":
    from scripts.audit_open_swe_traces_metadata import DATASET, get_json
    # Viewer occasionally times out on giant serialized trajectories;
    # read the *same fixed cohort* as two smaller slices. No replacements.
    from urllib.error import URLError
    rows = []
    for offset in (6, 12):
        last = None
        for attempt in range(2):
            try:
                data = get_json("/rows", {"dataset": DATASET, "config": "v2.0",
                                          "split": "sweagent", "offset": offset,
                                          "length": 6})
                chunk = data.get("rows", [])
                if not isinstance(chunk, list) or len(chunk) != 6:
                    raise ValueError("partial public source batch")
                rows.extend(chunk)
                last = None
                break
            except (TimeoutError, URLError) as exc:
                last = type(exc).__name__
        if last is not None:
            raise SystemExit("fixed source batch unavailable: " + last)
    if len(rows) != 12:
        raise SystemExit("fixed 12-row cohort unavailable: stop")
    print("GEMMA_SWEAGENT_ADK_ACTION_BRIDGE=" + json.dumps(summarize(rows),sort_keys=True),flush=True)
    print("NO_TRAINING_NO_GPU_NO_OFFICIAL_SUBMISSION=TRUE")
