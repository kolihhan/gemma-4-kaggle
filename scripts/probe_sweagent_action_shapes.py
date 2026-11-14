"""Bounded, read-only Open-SWE-Traces v2.0 SWE-agent action SHAPE probe.

Only prints whitelisted key names, role counts, tool names and argument-key names.
Never exposes command bodies, model traces, prompts, code, issue text or task IDs.
"""
from __future__ import annotations

import json
from collections import Counter
from scripts.audit_open_swe_traces_metadata import get_json, sample_grade, DATASET

ROLE_ALLOW = {"user", "assistant", "tool", "system", "developer"}
KNOWN_TOOLS = {"bash", "str_replace_editor", "submit"}


def safe_keys(value: object) -> list[str]:
    if not isinstance(value, dict):
        return []
    return sorted(k for k in value if isinstance(k, str)
                  and k in {"role", "content", "tool_calls", "tool_call_id",
                            "function_call", "name", "arguments", "function",
                            "type", "id", "metadata", "status", "message"})[:20]


def parse_call(value: object) -> tuple[str, str, tuple[str, ...]]:
    if not isinstance(value, dict):
        return ("invalid_structure", "unknown", ())
    function = value.get("function", {})
    if not isinstance(function, dict):
        function = {}
    name = function.get("name") or value.get("name")
    if not isinstance(name, str) or name not in KNOWN_TOOLS:
        name = "unknown_tool"
    arguments = function.get("arguments", value.get("arguments"))
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments)
        except (ValueError, TypeError):
            return (name, "unparseable_json", ())
    if not isinstance(arguments, dict):
        return (name, "not_dict", ())
    permitted = {"command", "path", "old_str", "new_str",
                 "file_text", "insert_line", "view_range", "message", "is_input", "timeout"}
    keys = tuple(sorted(k for k in arguments if k in permitted))
    return (name, "json_object", keys)


def summarize(rows: list) -> dict:
    qual = 0
    roles: Counter[str] = Counter()
    observed_call_layout: Counter[str] = Counter()
    calls: Counter[str] = Counter()
    call_schema: Counter[str] = Counter()
    message_shapes: Counter[str] = Counter()
    tool_reply_shapes: Counter[str] = Counter()
    for item in rows:
        row = item.get("row", {}) if isinstance(item, dict) else {}
        if sample_grade(row) != "candidate_for_private_deep_audit":
            continue
        qual += 1
        messages = row.get("messages", [])
        for m in messages[:1000]:
            if not isinstance(m, dict):
                continue
            role = m.get("role", "unknown")
            role = role if role in ROLE_ALLOW else "other"
            roles[role] += 1
            message_shapes[",".join(safe_keys(m))] += 1
            if role == "tool":
                tool_reply_shapes[",".join(safe_keys(m))] += 1
            tool_calls = m.get("tool_calls")
            if isinstance(tool_calls, list):
                observed_call_layout["list_tool_calls"] += len(tool_calls)
                for event in tool_calls:
                    name, parse_status, keys = parse_call(event)
                    calls[name] += 1
                    call_schema["|".join((name, parse_status, ",".join(keys)))] += 1
            if isinstance(m.get("function_call"), dict):
                observed_call_layout["function_call"] += 1
                name, parse_status, keys = parse_call(m["function_call"])
                calls[name] += 1
                call_schema["|".join((name, parse_status, ",".join(keys)))] += 1
    return {
        "qualified_rows": qual,
        "message_roles": dict(roles),
        "message_key_shapes": dict(message_shapes.most_common(8)),
        "tool_reply_key_shapes": dict(tool_reply_shapes.most_common(6)),
        "call_layout": dict(observed_call_layout),
        "observed_tool_names": dict(calls),
        "call_arg_key_shapes": dict(call_schema.most_common(20)),
        "raw_values_exported": False,
        "adk_action_conversion_proven": False,
    }


if __name__ == "__main__":
    raw = get_json("/rows", {"dataset": DATASET, "config": "v2.0", "split": "sweagent",
                              "offset": 6, "length": 12})
    rows = raw.get("rows", [])
    if not isinstance(rows, list) or len(rows) != 12:
        raise SystemExit("must obtain all 12 prespecified rows")
    print("GEMMA_SWEAGENT_ACTION_SHAPES=" + json.dumps(summarize(rows), sort_keys=True), flush=True)
    print("NO_GPU_NO_TRAINING_NO_COMPETITION_SUBMISSION=TRUE",flush=True)
