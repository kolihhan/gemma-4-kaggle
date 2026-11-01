#!/usr/bin/env python3
"""Extract auditable verifier-only supervision candidates from SWE trace JSON.

This is a curation helper, not an auto-labeler. Every extracted record is
``approved: false``. It preserves verifier tool arguments/results, records
behavioral audit flags, and deliberately excludes coder steps. A candidate must
still pass the stricter ``build_verifier_sft.py`` contract after explicit
approval before it can enter verifier LoRA SFT.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from scripts.build_verifier_sft import EDIT_TOOLS, classify_test_command


PROBLEM_RE = re.compile(
    r"Problem Statement:\s*\n(?P<body>.*?)(?=\n## Task Budget\b)",
    flags=re.DOTALL,
)


def extract_problem_description(task_prompt: str) -> str:
    if not isinstance(task_prompt, str):
        raise ValueError("task prompt is not text")
    match = PROBLEM_RE.search(task_prompt)
    if not match:
        raise ValueError("trace has no parsable problem statement")
    body = match.group("body").strip()
    if not body:
        raise ValueError("trace has an empty problem statement")
    return body


def _decode_observation(observation: Any) -> dict[str, Any]:
    if not isinstance(observation, dict):
        return {}
    content = observation.get("content")
    if isinstance(content, str):
        try:
            decoded = json.loads(content)
        except json.JSONDecodeError:
            decoded = {"raw": content}
    elif isinstance(content, dict):
        decoded = dict(content)
    else:
        decoded = {}

    # CommandError responses in SWE traces often keep the actual exit code
    # inside details; normalize it to the top level for downstream contracts.
    details = decoded.get("details")
    if isinstance(details, dict):
        if "exit_code" not in decoded and "exit_code" in details:
            decoded["exit_code"] = details["exit_code"]
        if "stdout" not in decoded and "stdout" in details:
            decoded["stdout"] = details["stdout"]
        if "stderr" not in decoded and "stderr" in details:
            decoded["stderr"] = details["stderr"]
    return decoded


def _task_prompt(trace: dict[str, Any]) -> str:
    for step in trace.get("steps") or []:
        if not isinstance(step, dict):
            continue
        extra = step.get("extra") or {}
        if (
            step.get("source") == "user"
            or extra.get("event_type") == "task_prompt"
        ):
            message = step.get("message")
            if isinstance(message, str) and "Problem Statement:" in message:
                return message
    raise ValueError("trace has no task prompt with problem statement")


def _verifier_steps(trace: dict[str, Any]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for trace_step in trace.get("steps") or []:
        if not isinstance(trace_step, dict):
            continue
        author = (trace_step.get("extra") or {}).get("author")
        if author != "swe_e4b_verifier":
            continue
        tool_calls = trace_step.get("tool_calls") or []
        if not isinstance(tool_calls, list):
            continue
        result = _decode_observation(trace_step.get("observation"))
        assistant_text = trace_step.get("message")
        if not isinstance(assistant_text, str):
            assistant_text = ""
        for call in tool_calls:
            if not isinstance(call, dict):
                continue
            tool = call.get("function_name")
            arguments = call.get("arguments")
            if not isinstance(tool, str) or not tool:
                continue
            if not isinstance(arguments, dict):
                arguments = {}
            step = {
                "tool": tool,
                "arguments": arguments,
                "assistant_text": assistant_text,
            }
            if result:
                step["result"] = result
            normalized.append(step)
    return normalized


def _exit_code(step: dict[str, Any]) -> int | None:
    result = step.get("result")
    if not isinstance(result, dict):
        return None
    value = result.get("exit_code")
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _command(step: dict[str, Any]) -> str:
    arguments = step.get("arguments")
    if not isinstance(arguments, dict):
        return ""
    command = arguments.get("command")
    return command if isinstance(command, str) else ""


def _audit(steps: list[dict[str, Any]]) -> tuple[list[str], str | None]:
    flags: set[str] = set()
    test_events: list[tuple[int, str, int | None]] = []
    submit_indices: list[int] = []
    successful_repairs = 0
    first_diff = None
    final_diff_checks: list[int] = []

    for index, step in enumerate(steps):
        tool = step.get("tool")
        if tool == "submit_patch":
            submit_indices.append(index)
        if tool in EDIT_TOOLS:
            result = step.get("result") or {}
            if result.get("status") == "ok":
                successful_repairs += 1
        if tool != "run_command":
            continue
        command = _command(step)
        if "git diff" in command and first_diff is None:
            first_diff = index
        if "git diff --check" in command and "git diff" in command and _exit_code(step) == 0:
            final_diff_checks.append(index)
        classification = classify_test_command(command)
        if classification in {"broad", "targeted"}:
            test_events.append((index, classification, _exit_code(step)))
            if classification == "broad":
                flags.add("broad_pytest")

    if successful_repairs > 1:
        flags.add("multiple_repairs")

    first_behavior = None
    for index, step in enumerate(steps):
        classification = (
            classify_test_command(_command(step))
            if step.get("tool") == "run_command"
            else "not_test"
        )
        if step.get("tool") in EDIT_TOOLS or classification in {"broad", "targeted"}:
            first_behavior = index
            break
    if first_behavior is not None and (first_diff is None or first_diff > first_behavior):
        flags.add("missing_initial_diff_inspection")

    suggested_label = None
    if test_events:
        last_test_index, last_test_kind, last_exit = test_events[-1]
        submits_after = [i for i in submit_indices if i > last_test_index]
        if submits_after and last_exit not in (None, 0):
            flags.add("submit_after_failed_test")
        if submits_after and last_test_kind == "targeted" and last_exit == 0:
            suggested_label = "verified_submit"
            submit_index = submits_after[0]
            if not any(last_test_index < i < submit_index for i in final_diff_checks):
                flags.add("missing_final_diff_check")
        elif not submit_indices and last_test_kind == "targeted" and last_exit not in (None, 0):
            suggested_label = "safe_stop"

    if not any(kind == "targeted" for _, kind, _ in test_events):
        flags.add("no_targeted_pytest")
    if not steps:
        flags.add("no_verifier_tool_steps")

    return sorted(flags), suggested_label


def extract_candidate(instance_id: str, trace: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(instance_id, str) or not instance_id:
        raise ValueError("instance_id is required")
    if not isinstance(trace, dict):
        raise ValueError("trace must be an object")
    problem_description = extract_problem_description(_task_prompt(trace))
    steps = _verifier_steps(trace)
    audit_flags, suggested_label = _audit(steps)
    return {
        "instance_id": instance_id,
        "approved": False,
        "label": None,
        "suggested_label": suggested_label,
        "source": "base_trace_curated_candidate",
        "problem_description": problem_description,
        "steps": steps,
        "audit_flags": audit_flags,
    }


def _load_training_ids(path: Path) -> list[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    tasks = payload.get("tasks")
    if not isinstance(tasks, list):
        raise ValueError("training manifest has no tasks[]")
    ids = [
        item.get("instance_id")
        for item in tasks
        if isinstance(item, dict) and isinstance(item.get("instance_id"), str)
    ]
    if len(ids) != len(tasks) or len(ids) != len(set(ids)):
        raise ValueError("training manifest has invalid or duplicate instance IDs")
    return ids


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace_dir", type=Path)
    parser.add_argument(
        "--train-manifest",
        type=Path,
        default=Path("docs/evaluation/verifier-lora-train-subset-v0.json"),
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    training_ids = _load_training_ids(args.train_manifest)
    trace_files = {
        path.stem.removeprefix("trace_"): path
        for path in args.trace_dir.glob("trace_*.json")
    }
    missing = [instance_id for instance_id in training_ids if instance_id not in trace_files]
    extras = sorted(set(trace_files) - set(training_ids))
    if missing or extras:
        raise SystemExit(
            f"trace/manifest mismatch: missing={missing!r} extras={extras!r}"
        )

    candidates = []
    for instance_id in training_ids:
        trace = json.loads(trace_files[instance_id].read_text(encoding="utf-8"))
        candidates.append(extract_candidate(instance_id, trace))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for candidate in candidates:
            handle.write(json.dumps(candidate, ensure_ascii=False, sort_keys=True) + "\n")

    flag_counts: dict[str, int] = {}
    for candidate in candidates:
        for flag in candidate["audit_flags"]:
            flag_counts[flag] = flag_counts.get(flag, 0) + 1
    print(
        json.dumps(
            {
                "status": "completed",
                "candidates": len(candidates),
                "approved": 0,
                "suggested_labels": {
                    label: sum(c.get("suggested_label") == label for c in candidates)
                    for label in ("verified_submit", "safe_stop")
                },
                "audit_flags": dict(sorted(flag_counts.items())),
                "output": str(args.output),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
