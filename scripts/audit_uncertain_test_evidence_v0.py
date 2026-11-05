#!/usr/bin/env python3
"""Sensitivity audit: could the conservative trace classifier have missed tests?

Read already completed *development* traces inside a private Kaggle retrieval
workflow. Output only aggregate counters. NEVER emit raw commands, task IDs,
messages, observations, prompts, patches, or an agent score prediction.

This does not re-run a model, change a submission, or certify test relevance.
"""
from __future__ import annotations

import argparse
import json
import re
import shlex
from pathlib import Path

from scripts import analyze_root_trace_mechanics as mechanics


def plausible_test_invocation(command: str, depth: int = 0) -> bool:
    """Only flag a command segment that appears to *invoke* a test runner.

    Intentionally broad enough for a conservative uncertainty bound, not proof
    of executed tests or a valid exit code. A grep/echo/cat mentioning pytest
    is never an invocation. The main classifier remains authoritative.
    """
    if not isinstance(command, str) or not command.strip() or depth > 3:
        return False
    try:
        tokens = shlex.split(command)
    except ValueError:
        return False
    if not tokens:
        return False
    if tokens[0].rsplit("/", 1)[-1] in {"bash", "sh"} and len(tokens) == 3 and tokens[1] in {"-lc", "-c"}:
        return plausible_test_invocation(tokens[2], depth + 1)
    sections: list[list[str]] = [[]]
    for tok in tokens:
        if tok in {"&&", "||", ";", "|"}:
            sections.append([])
        else:
            sections[-1].append(tok)
    for section in sections:
        if not section:
            continue
        while section and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.+", section[0]):
            section = section[1:]
        if not section:
            continue
        if section[0] in {"env"}:
            section = section[1:]
            while section and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.+", section[0]):
                section = section[1:]
        if not section:
            continue
        if section[0] in {"uv", "poetry", "pipenv", "pdm"} and len(section) > 2 and section[1] == "run":
            section = section[2:]
        executable = section[0].rsplit("/", 1)[-1]
        if executable in {"pytest", "py.test", "tox", "nox", "nosetests"}:
            return True
        if executable in {"python", "python3", "python3.10", "python3.11", "python3.12"} and len(section) > 2 and section[1] == "-m":
            if section[2] in {"pytest", "unittest", "nose", "tox"}:
                return True
        if executable == "make" and len(section) >= 2 and section[1] in {"test", "tests", "check"}:
            return True
        if executable == "hatch" and len(section) >= 2 and section[1] in {"test", "run"}:
            if section[1] == "test" or (len(section) >= 3 and section[2].startswith("test")):
                return True
        if executable == "coverage" and len(section) >= 4 and section[1:3] == ["run", "-m"] and section[3] in {"pytest", "unittest"}:
            return True
    return False


def reduce_one(trace: dict, author: str) -> dict[str, int | bool]:
    steps = mechanics._normalize_tool_steps(trace, author)
    records = []
    first_edit = None
    for i, step in enumerate(steps):
        kind = mechanics._action_kind(step, shell_chain_v2=True)
        candidate = False
        if step["tool"] == "run_command" and kind == "other_command":
            candidate = plausible_test_invocation(mechanics._command(step["arguments"]))
        if first_edit is None and kind in {"edit", "script_edit"}:
            first_edit = i
        records.append((kind, candidate))
    recognized_tests = [
        i for i, (kind, _) in enumerate(records)
        if kind in {"targeted_test", "broad_test"}
    ]
    uncertain_tests = [i for i, (_, maybe) in enumerate(records) if maybe]
    return {
        "recognized_test_calls": len(recognized_tests),
        "unclassified_possible_test_calls": len(uncertain_tests),
        "has_recognized_test": bool(recognized_tests),
        "has_possible_unclassified_test": bool(uncertain_tests),
        "has_any_candidate_test": bool(recognized_tests or uncertain_tests),
        "recognized_pre_edit_test": bool(first_edit is not None and any(i < first_edit for i in recognized_tests)),
        "unclassified_possible_pre_edit_test": bool(first_edit is not None and any(i < first_edit for i in uncertain_tests)),
        "has_mutation": first_edit is not None,
    }


def audit(trace_dir: Path, results_path: Path, author: str = "swe_e4b_coder") -> dict:
    outcome = mechanics.load_results(results_path)
    paths = {p.stem.removeprefix("trace_"): p for p in trace_dir.glob("trace_*.json")}
    if set(paths) != set(outcome):
        raise ValueError("results and trace IDs differ; fail closed")
    if len(paths) != 17:
        raise ValueError("expected exactly 17 already-inspected development tasks")
    rows = [reduce_one(json.loads(paths[key].read_text(encoding="utf-8")), author)
            for key in sorted(paths)]
    totals = {
        "tasks": len(rows),
        "recognized_test_calls": sum(r["recognized_test_calls"] for r in rows),
        "unclassified_possible_test_calls": sum(r["unclassified_possible_test_calls"] for r in rows),
        "tasks_with_recognized_test": sum(r["has_recognized_test"] for r in rows),
        "tasks_with_possible_unclassified_test": sum(r["has_possible_unclassified_test"] for r in rows),
        "tasks_without_any_recognized_or_candidate_test": sum(not r["has_any_candidate_test"] for r in rows),
        "tasks_with_recognized_pre_edit_test": sum(r["recognized_pre_edit_test"] for r in rows),
        "tasks_with_unclassified_possible_pre_edit_test": sum(r["unclassified_possible_pre_edit_test"] for r in rows),
        "tasks_with_mutation": sum(r["has_mutation"] for r in rows),
        "resolved": sum(outcome.values()),
    }
    return {
        "version": "trace-test-invocation-sensitivity-v0",
        "source": "existing inspected E4B development traces only",
        "classifier": "v2 recognized tests plus non-executed uncertainty check for test runner invocations in other_command",
        "limits": "possible != executed, relevant, or passed; hidden 31B tasks not observed",
        "raw_commands_or_task_text_included": False,
        "new_model_run": False,
        "new_submission": False,
        "totals": totals,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--traces", type=Path, required=True)
    p.add_argument("--results", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    result = audit(args.traces, args.results)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("TEST_INVOCATION_SENSITIVITY", json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
