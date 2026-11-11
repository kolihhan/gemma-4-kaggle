#!/usr/bin/env python3
"""Read existing private Gemma 31B paired traces; export safe feedback evidence.

No issue text, prompts, commands, observations, patches, reference solutions,
logs or tokens may appear in stdout or JSON. This is NOT model inference.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
import json
from pathlib import Path
import shlex
from typing import Any

from scripts.audit_paired_31b_existing_traces import (
    ARMS, read_safe_results, trace_for,
)

EDIT_TOOLS = frozenset({"edit_file", "write_file"})
WRAPPERS = frozenset({"uv", "poetry", "pdm", "pipenv"})
RUNNERS = frozenset({"pytest", "py.test", "tox", "nox", "nosetests"})
SEPARATORS = frozenset({"&&", ";", "||", "|"})
CATEGORIES = frozenset({
    "explicit_test", "inline_assert", "compile_lint",
    "git_inspect", "source_read", "source_mutation",
    "dependency_setup", "opaque_python", "other",
    "unavailable",
})


def _parts(command: object, depth: int = 0) -> list[list[str]]:
    """Tokenize shell commands without ever returning a loggable source string."""
    if not isinstance(command, str) or not command.strip() or depth > 3:
        return []
    try:
        tokens = shlex.split(command)
    except ValueError:
        return []
    if tokens and tokens[0].rsplit("/", 1)[-1] in ("bash", "sh") and (
        len(tokens) == 3 and tokens[1] in ("-c", "-lc")
    ):
        return _parts(tokens[2], depth + 1)
    segments: list[list[str]] = [[]]
    for token in tokens:
        if token in SEPARATORS:
            segments.append([])
        else:
            segments[-1].append(token)
    return [s for s in segments if s]


def _classify_tokens(tokens: list[str]) -> str:
    if not tokens:
        return "unavailable"
    t = list(tokens)
    while t and ("=" in t[0] and not t[0].startswith("-") and
                 t[0].split("=", 1)[0].replace("_", "").isalnum()):
        t.pop(0)
    if t and t[0] == "env":
        t.pop(0)
        while t and "=" in t[0] and not t[0].startswith("-"):
            t.pop(0)
    if not t:
        return "other"
    exe = t[0].rsplit("/", 1)[-1]
    if exe == "cd":
        return "source_read"
    if exe in WRAPPERS and len(t) >= 3 and t[1] == "run":
        t = t[2:]
        exe = t[0].rsplit("/", 1)[-1]
    if exe in RUNNERS or (exe in ("python", "python3") and
                         len(t) >= 3 and t[1] == "-m" and
                         t[2] in ("pytest", "unittest", "tox")):
        return "explicit_test"
    if exe == "make" and len(t) > 1 and t[1] in ("test", "tests", "check"):
        return "explicit_test"
    if exe in ("npm", "yarn", "pnpm") and len(t) > 1 and t[1] in ("test", "run") and (
        t[1] == "test" or len(t) > 2 and t[2] == "test"
    ):
        return "explicit_test"
    if exe in ("python", "python3") and len(t) >= 3 and t[1] == "-c":
        try:
            node = ast.parse(t[2])
        except SyntaxError:
            return "opaque_python"
        if any(isinstance(x, ast.Assert) for x in ast.walk(node)):
            return "inline_assert"
        # Calls to pytest.main inside Python -c are test-like.
        if any(isinstance(x, ast.Call) and
               isinstance(x.func, ast.Attribute) and x.func.attr == "main" and
               isinstance(x.func.value, ast.Name) and x.func.value.id == "pytest"
               for x in ast.walk(node)):
            return "explicit_test"
        if any(isinstance(x, (ast.Call, ast.Assign, ast.AugAssign))
               for x in ast.walk(node)):
            return "opaque_python"
    if exe in ("python", "python3") and len(t) > 1 and t[1] in ("-m", "-c"):
        if len(t) > 2 and t[2] in ("compileall", "py_compile"):
            return "compile_lint"
        return "opaque_python"
    if exe in ("ruff", "flake8", "mypy", "pyright"):
        return "compile_lint"
    if exe == "git" and len(t) >= 2 and t[1] in ("diff", "status", "show", "log"):
        return "git_inspect"
    if exe in ("cat", "head", "tail", "sed", "rg", "grep", "ls", "find", "pwd"):
        if exe == "sed" and any(x.startswith("-i") for x in t[1:]):
            return "source_mutation"
        return "source_read"
    if exe in ("pip", "pip3") or (exe in ("python", "python3") and
                                   len(t) > 2 and t[1:3] == ["-m", "pip"]):
        return "dependency_setup"
    if exe in ("patch",) or (exe == "git" and len(t)>1 and t[1] == "apply"):
        return "source_mutation"
    if exe in ("python", "python3", "bash", "sh") or exe.endswith(".py"):
        return "opaque_python"
    return "other"


def command_class(command: object) -> str:
    """Return one allowlisted label; unknown shell structures remain ambiguous."""
    segments = _parts(command)
    if not segments:
        return "unavailable"
    labels = [_classify_tokens(s) for s in segments]
    if "explicit_test" in labels:
        return "explicit_test"
    if "inline_assert" in labels:
        return "inline_assert"
    if "source_mutation" in labels:
        return "source_mutation"
    return labels[-1]


def observation_exit(observation: object, is_parallel_step: bool = False) -> str:
    """Read only structured numeric exit metadata; do not inspect message text."""
    if is_parallel_step or not isinstance(observation, dict):
        return "unknown"
    content = observation.get("content")
    if isinstance(content, str):
        try:
            obj = json.loads(content)
        except (ValueError, TypeError):
            obj = {}
    elif isinstance(content, dict):
        obj = content
    else:
        obj = {}
    if not isinstance(obj, dict):
        return "unknown"
    value: Any = obj.get("exit_code")
    if value is None and isinstance(obj.get("details"), dict):
        value = obj["details"].get("exit_code")
    if isinstance(value, int) and not isinstance(value, bool):
        return "zero" if value == 0 else "nonzero"
    return "unknown"


def reduce_feedback(trace: dict) -> dict:
    if not isinstance(trace, dict) or not isinstance(trace.get("steps"), list):
        raise ValueError("unsupported trace structure")
    calls: list[dict] = []
    multi_call_steps = 0
    for step in trace["steps"]:
        if not isinstance(step, dict):
            continue
        event_calls = step.get("tool_calls")
        if not isinstance(event_calls, list):
            continue
        parallel = len(event_calls) > 1
        multi_call_steps += int(parallel)
        for call in event_calls:
            if not isinstance(call, dict):
                continue
            tool = call.get("function_name")
            if not isinstance(tool, str):
                continue
            if tool == "run_command":
                args = call.get("arguments")
                command = args.get("command") if isinstance(args, dict) else None
                category = command_class(command)
            elif tool in EDIT_TOOLS:
                category = "edit"
            elif tool == "submit_patch":
                category = "submit"
            else:
                category = "other_tool"
            code = observation_exit(step.get("observation"), parallel)
            calls.append({"category": category, "exit": code})
    counter = Counter(c["category"] for c in calls)
    shell_classes = {k: counter[k] for k in sorted(CATEGORIES)}
    edit_positions = [i for i,c in enumerate(calls) if c["category"] in ("edit", "source_mutation")]
    test_positions = [i for i,c in enumerate(calls) if c["category"] in ("explicit_test", "inline_assert")]
    fail_test_positions = [i for i in test_positions if calls[i]["exit"] == "nonzero"]
    explicit_test_exit = Counter(calls[i]["exit"] for i in test_positions)
    command_indices = [i for i,c in enumerate(calls) if c["category"] in CATEGORIES]
    command_exits = Counter(calls[i]["exit"] for i in command_indices)
    return {
        "trace_found": True,
        "recorded_action_count": len(calls),
        "parallel_call_steps": multi_call_steps,
        "first_edit_action": edit_positions[0]+1 if edit_positions else None,
        "total_edit_actions": len(edit_positions),
        "command_class_counts": {k:v for k,v in shell_classes.items() if v>0},
        "explicit_or_inline_tests": len(test_positions),
        "tests_after_first_edit": sum(bool(edit_positions and i>edit_positions[0]) for i in test_positions),
        "tests_with_structured_exit": dict(sorted(explicit_test_exit.items())),
        "nonzero_test_then_edit": sum(any(j>i for j in edit_positions) for i in fail_test_positions),
        "all_command_structured_exit": dict(sorted(command_exits.items())),
        "last_observed_test_exit": calls[test_positions[-1]]["exit"] if test_positions else "no_explicit_test",
        "unclassified_opaque_commands": shell_classes["opaque_python"]+shell_classes["other"]+shell_classes["unavailable"],
        "submit_tool_calls": counter["submit"],
    }


def audit(root: Path) -> dict:
    records = read_safe_results(root/"paired_prompt_v2_31b_results.json")
    out = []
    for record in records:
        path = trace_for(root, record["arm"], record["instance_id"])
        stats = reduce_feedback(json.loads(path.read_text(encoding="utf-8"))) if path else {"trace_found":False}
        out.append({
            "arm": record["arm"],
            "instance_id":record["instance_id"],
            "resolved":record["resolved"],
            "grader_test_exit_code":record.get("test_exit_code"),
            **stats,
        })
    return {
        "version":"gemma-paired-private-feedback-audit-v2",
        "source_action":43057377220,
        "new_inference":False,
        "new_competition_submission":False,
        "raw_competition_content_exported":False,
        "limitations":(
           "Structured exit codes may be absent; an explicit test-like command is not proof "
           "the relevant test passed or ran. Opaque Python commands may contain tests. "
           "The grader exit code is not model-visible feedback. No root-cause or "
           "semantic-correctness label can be inferred from command names alone."
        ),
        "by_arm": {arm:{
            "tasks":sum(x["arm"]==arm for x in out),
            "resolved":sum(x["arm"]==arm and x["resolved"] for x in out),
            "traces_found":sum(x["arm"]==arm and x["trace_found"] for x in out),
            "explicit_or_inline_tests":sum(x.get("explicit_or_inline_tests",0) for x in out if x["arm"]==arm),
            "opaque_commands":sum(x.get("unclassified_opaque_commands",0) for x in out if x["arm"]==arm),
        } for arm in ARMS},
        "tasks":out,
    }


def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    report=audit(args.root)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("SAFE_GEMMA_FEEDBACK_AUDIT="+json.dumps(report,sort_keys=True))


if __name__=="__main__":
    main()
