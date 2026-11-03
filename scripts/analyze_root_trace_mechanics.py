#!/usr/bin/env python3
"""Reduce SWE agent traces to compact evidence/edit/verification mechanics.

The output deliberately excludes raw messages, tool arguments, observations,
patches, problem statements, and source snippets. It is intended for post-hoc
mechanism analysis on already-inspected development runs.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import shlex
from collections import Counter
from pathlib import Path
from typing import Any


EDIT_TOOLS = {
    "apply_patch",
    "edit_file",
    "replace_text",
    "write_file",
    "write_text_file",
    "create_file",
}
LOCALIZATION_TOOLS = {"search_similar_code", "get_code_neighbors", "get_code_subgraph"}
SOURCE_EXTENSIONS = (
    "py", "pyi", "toml", "yaml", "yml", "ini", "cfg", "js", "jsx", "ts", "tsx",
    "java", "go", "rs", "c", "h", "cc", "cpp", "hpp", "rb", "php", "vue", "html", "css",
)
SOURCE_PATH_RE = re.compile(
    r"(?P<path>[A-Za-z0-9_./-]+\.(?:" + "|".join(SOURCE_EXTENSIONS) + r"))\b"
)


def classify_test_command(command: str) -> str:
    """Classify a verification command as targeted, broad, or not_test."""
    if not isinstance(command, str) or not command.strip():
        return "not_test"
    try:
        tokens = shlex.split(command)
    except ValueError:
        return "not_test"
    if not tokens or any(token in {"&&", "||", "|", ";", "`"} for token in tokens):
        return "not_test"

    executable = tokens[0].rsplit("/", 1)[-1]
    if executable in {"python", "python3"} and len(tokens) == 3 and tokens[1] == "-c":
        try:
            tree = ast.parse(tokens[2])
        except SyntaxError:
            return "not_test"
        return "targeted" if any(isinstance(node, ast.Assert) for node in ast.walk(tree)) else "not_test"

    pytest_index = None
    for index, token in enumerate(tokens):
        if token.rsplit("/", 1)[-1] in {"pytest", "py.test"}:
            pytest_index = index
            break
    if pytest_index is None:
        return "not_test"

    positional: list[str] = []
    args = tokens[pytest_index + 1 :]
    skip_next = False
    options_with_values = {
        "-k", "-m", "--maxfail", "--tb", "--junitxml", "--rootdir", "--confcutdir",
    }
    for token in args:
        if skip_next:
            skip_next = False
            continue
        if token in options_with_values:
            skip_next = True
            continue
        if token.startswith("-"):
            continue
        positional.append(token)

    if not positional:
        return "broad"
    broad_roots = {".", "./", "tests", "tests/", "test", "test/"}
    for target in positional:
        clean = target.rstrip("/")
        if "::" in target or clean.endswith(".py"):
            return "targeted"
        if target not in broad_roots and clean not in {"tests", "test", "."}:
            return "targeted"
    return "broad"


def _decode_observation(observation: Any) -> dict[str, Any]:
    if not isinstance(observation, dict):
        return {}
    content = observation.get("content")
    if isinstance(content, str):
        try:
            decoded = json.loads(content)
        except json.JSONDecodeError:
            decoded = {}
    elif isinstance(content, dict):
        decoded = dict(content)
    else:
        decoded = {}
    details = decoded.get("details")
    if isinstance(details, dict):
        for key in ("exit_code", "status"):
            if key not in decoded and key in details:
                decoded[key] = details[key]
    return decoded


def _exit_code(result: dict[str, Any]) -> int | None:
    value = result.get("exit_code")
    if isinstance(value, bool):
        return int(value)
    return value if isinstance(value, int) else None


def _command(arguments: dict[str, Any]) -> str:
    value = arguments.get("command") if isinstance(arguments, dict) else None
    return value if isinstance(value, str) else ""


def _looks_like_source_script_mutation(command: str) -> bool:
    """Conservatively detect command-side writes to source/config files.

    Generated data such as ``openapi.json`` is intentionally excluded by the
    source-extension allow-list. Ambiguous commands return False.
    """
    if not command or not SOURCE_PATH_RE.search(command):
        return False
    lowered = command.lower()
    if re.search(r"\b(?:sed\s+-i|perl\s+-pi|git\s+apply|patch\s)\b", lowered):
        return True
    if re.search(r">>?\s*[\"']?[A-Za-z0-9_./-]+\.(?:" + "|".join(SOURCE_EXTENSIONS) + r")\b", command):
        return True
    python_write_markers = (
        ".write_text(", ".write_bytes(", ".writelines(", "open(", "open (",
    )
    if any(marker in lowered for marker in python_write_markers):
        if re.search(r"[\"'][wax+][bt]?[\"']", lowered) or any(
            marker in lowered for marker in (".write_text(", ".write_bytes(", ".writelines(")
        ):
            return True
    return False


def _normalize_tool_steps(trace: dict[str, Any], author: str) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for trace_step in trace.get("steps") or []:
        if not isinstance(trace_step, dict):
            continue
        if (trace_step.get("extra") or {}).get("author") != author:
            continue
        calls = trace_step.get("tool_calls") or []
        if not isinstance(calls, list):
            continue
        result = _decode_observation(trace_step.get("observation"))
        for call in calls:
            if not isinstance(call, dict):
                continue
            tool = call.get("function_name")
            arguments = call.get("arguments")
            if not isinstance(tool, str) or not tool:
                continue
            if not isinstance(arguments, dict):
                arguments = {}
            normalized.append({"tool": tool, "arguments": arguments, "result": result})
    return normalized


def _action_kind(step: dict[str, Any]) -> str:
    tool = step["tool"]
    if tool in EDIT_TOOLS:
        return "edit"
    if tool in LOCALIZATION_TOOLS:
        return "localize"
    if tool == "read_file":
        return "read"
    if tool == "submit_patch":
        return "submit"
    if tool != "run_command":
        return "other"
    command = _command(step["arguments"])
    test_kind = classify_test_command(command)
    if test_kind == "targeted":
        return "targeted_test"
    if test_kind == "broad":
        return "broad_test"
    if "git diff --check" in command:
        return "diff_check"
    if "git diff" in command:
        return "diff"
    if "git status" in command:
        return "status"
    if _looks_like_source_script_mutation(command):
        return "script_edit"
    return "command"


def analyze_trace(instance_id: str, trace: dict[str, Any], resolved: bool, author: str) -> dict[str, Any]:
    steps = _normalize_tool_steps(trace, author)
    actions = [(_action_kind(step), _exit_code(step["result"])) for step in steps]
    mutation_indices = [i for i, (kind, _) in enumerate(actions) if kind in {"edit", "script_edit"}]
    targeted = [(i, code) for i, (kind, code) in enumerate(actions) if kind == "targeted_test"]
    broad = [(i, code) for i, (kind, code) in enumerate(actions) if kind == "broad_test"]
    submits = [i for i, (kind, _) in enumerate(actions) if kind == "submit"]

    first_mutation = mutation_indices[0] if mutation_indices else None
    pre_edit_targeted = bool(
        first_mutation is not None and any(index < first_mutation for index, _ in targeted)
    )

    failed_after_edit = []
    if first_mutation is not None:
        failed_after_edit = [
            (index, code)
            for index, code in targeted
            if index > first_mutation and code not in (None, 0)
        ]
    first_failed_index = failed_after_edit[0][0] if failed_after_edit else None
    repair_indices = (
        [index for index in mutation_indices if first_failed_index is not None and index > first_failed_index]
        if first_failed_index is not None
        else []
    )
    repair_index = repair_indices[0] if repair_indices else None
    retest_after_repair = bool(
        repair_index is not None and any(index > repair_index for index, _ in targeted)
    )

    submit_after_failed = False
    for submit_index in submits:
        prior_tests = [(index, code) for index, code in targeted if index < submit_index]
        if prior_tests and prior_tests[-1][1] not in (None, 0):
            submit_after_failed = True
            break

    counts = Counter(kind for kind, _ in actions)
    return {
        "instance_id": instance_id,
        "resolved": resolved,
        "tool_call_count": len(actions),
        "mutation_count": len(mutation_indices),
        "direct_edit_count": counts["edit"],
        "script_mutation_count": counts["script_edit"],
        "targeted_test_count": len(targeted),
        "broad_test_count": len(broad),
        "localization_tool_count": counts["localize"],
        "submit_count": len(submits),
        "pre_edit_targeted_evidence": pre_edit_targeted,
        "failed_targeted_after_edit": bool(failed_after_edit),
        "repair_after_failed_targeted": bool(repair_indices),
        "targeted_retest_after_repair": retest_after_repair,
        "failed_targeted_no_repair": bool(failed_after_edit and not repair_indices),
        "final_targeted_exit": targeted[-1][1] if targeted else None,
        "submit_after_failed_targeted": submit_after_failed,
        "action_counts": dict(sorted(counts.items())),
    }


def load_results(path: Path) -> dict[str, bool]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    results = payload.get("results")
    if not isinstance(results, list):
        raise ValueError("results JSON has no results[]")
    resolved: dict[str, bool] = {}
    for item in results:
        if not isinstance(item, dict):
            raise ValueError("results entry is not an object")
        instance_id = item.get("instance_id")
        value = item.get("resolved")
        if not isinstance(instance_id, str) or not isinstance(value, bool):
            raise ValueError("results entry has invalid instance_id/resolved")
        if instance_id in resolved:
            raise ValueError(f"duplicate result: {instance_id}")
        resolved[instance_id] = value
    return resolved


def aggregate(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    boolean_fields = (
        "pre_edit_targeted_evidence",
        "failed_targeted_after_edit",
        "repair_after_failed_targeted",
        "targeted_retest_after_repair",
        "failed_targeted_no_repair",
        "submit_after_failed_targeted",
    )
    numeric_fields = (
        "tool_call_count",
        "mutation_count",
        "direct_edit_count",
        "script_mutation_count",
        "targeted_test_count",
        "broad_test_count",
        "localization_tool_count",
        "submit_count",
    )
    action_totals: Counter[str] = Counter()
    for task in tasks:
        action_totals.update(task["action_counts"])
    return {
        "tasks": len(tasks),
        "resolved": sum(task["resolved"] for task in tasks),
        **{field: sum(bool(task[field]) for task in tasks) for field in boolean_fields},
        **{f"total_{field}": sum(int(task[field]) for task in tasks) for field in numeric_fields},
        "tasks_with_no_targeted_test": sum(task["targeted_test_count"] == 0 for task in tasks),
        "tasks_with_final_targeted_pass": sum(task["final_targeted_exit"] == 0 for task in tasks),
        "action_totals": dict(sorted(action_totals.items())),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace_dir", type=Path)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--author", default="swe_e4b_coder")
    args = parser.parse_args(argv)

    resolved_by_id = load_results(args.results)
    trace_files = {
        path.stem.removeprefix("trace_"): path
        for path in args.trace_dir.glob("trace_*.json")
    }
    if set(trace_files) != set(resolved_by_id):
        missing = sorted(set(resolved_by_id) - set(trace_files))
        extras = sorted(set(trace_files) - set(resolved_by_id))
        raise SystemExit(f"trace/results mismatch: missing={missing!r} extras={extras!r}")

    tasks = []
    for instance_id in sorted(trace_files):
        trace = json.loads(trace_files[instance_id].read_text(encoding="utf-8"))
        tasks.append(analyze_trace(instance_id, trace, resolved_by_id[instance_id], args.author))

    output = {
        "version": "root-trace-mechanics-v1",
        "author": args.author,
        "aggregate": aggregate(tasks),
        "tasks": tasks,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"version": output["version"], "aggregate": output["aggregate"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
