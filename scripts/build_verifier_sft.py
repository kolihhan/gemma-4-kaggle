#!/usr/bin/env python3
"""Build leakage-safe verifier SFT examples from explicitly curated trajectories.

This builder intentionally does *not* parse raw evaluator traces into positive
supervision. A human/automated curation step must first normalize a trajectory
and mark it ``approved: true``. The builder then enforces the verifier-v0
behavioral contract before emitting chat-template-compatible JSONL.

Expected normalized record shape::

    {
      "instance_id": "rich_1234",
      "approved": true,
      "label": "verified_submit" | "safe_stop",
      "source": "base_trace_curated" | "gold_verification_curated" | ...,
      "problem_description": "...",
      "steps": [
        {
          "tool": "run_command",
          "arguments": {"command": "git diff --check && git diff"},
          "assistant_text": "",
          "result": {"exit_code": 0, "output": "..."}
        }
      ]
    }

The output format uses ``messages`` plus ``tools`` and is suitable for passing
to a Hugging Face tokenizer chat template / TRL SFT pipeline after normal
model-specific preprocessing.
"""

from __future__ import annotations

import argparse
import json
import shlex
from pathlib import Path
from typing import Any, Iterable


class SupervisionError(ValueError):
    """Raised when a candidate supervision record violates the v0 contract."""


FORBIDDEN_REFERENCE_KEYS = {
    "reference_patch",
    "reference_solution",
    "gold_patch",
    "solution_patch",
    "test_patch",
}

EDIT_TOOLS = {
    "apply_patch",
    "edit_file",
    "replace_text",
    "write_file",
    "write_text_file",
    "create_file",
}

ALLOWED_LABELS = {"verified_submit", "safe_stop"}


def classify_test_command(command: str) -> str:
    """Classify pytest commands as targeted, broad, or not_test.

    A test-file path or explicit pytest node is treated as targeted. Bare
    pytest, repo-root pytest, and ``pytest tests`` are intentionally treated as
    broad because v0 supervision is meant to teach the smallest relevant gate.
    """

    if not isinstance(command, str) or not command.strip():
        return "not_test"
    try:
        tokens = shlex.split(command)
    except ValueError:
        tokens = command.split()

    pytest_index = None
    for index, token in enumerate(tokens):
        name = token.rsplit("/", 1)[-1]
        if name in {"pytest", "py.test"}:
            pytest_index = index
            break
    if pytest_index is None:
        return "not_test"

    positional: list[str] = []
    args = tokens[pytest_index + 1 :]
    skip_next = False
    options_with_values = {
        "-k",
        "-m",
        "--maxfail",
        "--tb",
        "--junitxml",
        "--rootdir",
        "--confcutdir",
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


def _find_forbidden_key(value: Any) -> str | None:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key) in FORBIDDEN_REFERENCE_KEYS:
                return str(key)
            found = _find_forbidden_key(child)
            if found:
                return found
    elif isinstance(value, list):
        for child in value:
            found = _find_forbidden_key(child)
            if found:
                return found
    return None


def _command(step: dict[str, Any]) -> str:
    arguments = step.get("arguments")
    if not isinstance(arguments, dict):
        return ""
    value = arguments.get("command")
    return value if isinstance(value, str) else ""


def _exit_code(step: dict[str, Any]) -> int | None:
    result = step.get("result")
    if not isinstance(result, dict):
        return None
    value = result.get("exit_code")
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    raise SupervisionError(f"invalid exit_code: {value!r}")


def _is_diff_inspection(step: dict[str, Any]) -> bool:
    if step.get("tool") != "run_command":
        return False
    command = _command(step)
    return "git diff" in command


def _validate_step_shape(instance_id: str, step: Any, index: int) -> dict[str, Any]:
    if not isinstance(step, dict):
        raise SupervisionError(f"{instance_id}: step {index} is not an object")
    tool = step.get("tool")
    if not isinstance(tool, str) or not tool:
        raise SupervisionError(f"{instance_id}: step {index} has no tool")
    arguments = step.get("arguments", {})
    if not isinstance(arguments, dict):
        raise SupervisionError(f"{instance_id}: step {index} arguments must be an object")
    text = step.get("assistant_text", "")
    if not isinstance(text, str):
        raise SupervisionError(f"{instance_id}: step {index} assistant_text must be text")
    result = step.get("result")
    if result is not None and not isinstance(result, dict):
        raise SupervisionError(f"{instance_id}: step {index} result must be an object")
    return step


def _validate_behavior(instance_id: str, label: str, steps: list[dict[str, Any]]) -> None:
    if not steps:
        raise SupervisionError(f"{instance_id}: no curated steps")

    inspect_indices = [index for index, item in enumerate(steps) if _is_diff_inspection(item)]
    if not inspect_indices:
        raise SupervisionError(f"{instance_id}: missing initial git diff inspection")

    first_behavior_index = None
    for index, item in enumerate(steps):
        tool = item["tool"]
        classification = classify_test_command(_command(item)) if tool == "run_command" else "not_test"
        if tool in EDIT_TOOLS or classification in {"targeted", "broad"}:
            first_behavior_index = index
            break
    if first_behavior_index is not None and inspect_indices[0] > first_behavior_index:
        raise SupervisionError(f"{instance_id}: verification/edit occurs before diff inspection")

    repair_indices = [index for index, item in enumerate(steps) if item["tool"] in EDIT_TOOLS]
    if len(repair_indices) > 1:
        raise SupervisionError(f"{instance_id}: more than one repair in positive supervision")

    targeted: list[tuple[int, int]] = []
    broad_indices: list[int] = []
    submit_indices: list[int] = []
    final_diff_indices: list[int] = []

    for index, item in enumerate(steps):
        tool = item["tool"]
        if tool == "submit_patch":
            submit_indices.append(index)
            continue
        if tool != "run_command":
            continue

        command = _command(item)
        classification = classify_test_command(command)
        if classification == "broad":
            broad_indices.append(index)
        elif classification == "targeted":
            exit_code = _exit_code(item)
            if exit_code is None:
                raise SupervisionError(
                    f"{instance_id}: targeted verification has no exit_code"
                )
            targeted.append((index, exit_code))

        if "git diff --check" in command and "git diff" in command:
            code = _exit_code(item)
            if code == 0:
                final_diff_indices.append(index)

    if broad_indices:
        raise SupervisionError(
            f"{instance_id}: positive supervision contains broad pytest; targeted verification required"
        )
    if not targeted:
        raise SupervisionError(f"{instance_id}: targeted verification required")

    if repair_indices:
        repair_index = repair_indices[0]
        failed_before = any(index < repair_index and code != 0 for index, code in targeted)
        retest_after = [(index, code) for index, code in targeted if index > repair_index]
        if not failed_before:
            raise SupervisionError(
                f"{instance_id}: repair lacks failing targeted evidence"
            )
        if not retest_after:
            raise SupervisionError(
                f"{instance_id}: repair is not followed by targeted retest"
            )

    last_target_index, last_target_code = targeted[-1]

    if label == "verified_submit":
        if len(submit_indices) != 1:
            raise SupervisionError(
                f"{instance_id}: verified_submit requires exactly one submit_patch"
            )
        submit_index = submit_indices[0]
        if submit_index != len(steps) - 1:
            raise SupervisionError(f"{instance_id}: submit_patch must be the final tool action")
        if last_target_index > submit_index:
            raise SupervisionError(f"{instance_id}: targeted verification occurs after submit")
        if last_target_code != 0:
            raise SupervisionError(
                f"{instance_id}: submit after failing targeted verification is forbidden"
            )
        if not any(last_target_index < index < submit_index for index in final_diff_indices):
            raise SupervisionError(
                f"{instance_id}: verified submit requires a passing final git diff --check"
            )
    elif label == "safe_stop":
        if submit_indices:
            raise SupervisionError(f"{instance_id}: safe_stop must not submit")
        if last_target_code == 0:
            raise SupervisionError(
                f"{instance_id}: safe_stop requires unresolved failing targeted evidence"
            )
    else:
        raise SupervisionError(f"{instance_id}: unsupported label {label!r}")


def _tool_schema(name: str) -> dict[str, Any]:
    if name == "run_command":
        parameters = {
            "type": "object",
            "properties": {"command": {"type": "string"}},
            "required": ["command"],
            "additionalProperties": True,
        }
        description = "Run a command in the current repository workspace."
    elif name == "submit_patch":
        parameters = {"type": "object", "properties": {}, "additionalProperties": True}
        description = "Submit the current verified working-tree patch."
    else:
        parameters = {"type": "object", "additionalProperties": True}
        description = f"Verifier workspace tool: {name}."
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": parameters,
        },
    }


def _messages_for_record(
    record: dict[str, Any], verifier_template: str, steps: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    problem = record["problem_description"]
    try:
        system_text = verifier_template.format(problem_description=problem)
    except (KeyError, ValueError) as exc:
        raise SupervisionError(f"invalid verifier template: {exc}") from exc

    messages: list[dict[str, Any]] = [{"role": "system", "content": system_text}]
    for index, item in enumerate(steps):
        call_id = f"call_{index:03d}"
        assistant: dict[str, Any] = {
            "role": "assistant",
            "content": item.get("assistant_text", ""),
            "tool_calls": [
                {
                    "id": call_id,
                    "type": "function",
                    "function": {
                        "name": item["tool"],
                        "arguments": item.get("arguments", {}),
                    },
                }
            ],
        }
        messages.append(assistant)
        if "result" in item:
            messages.append(
                {
                    "role": "tool",
                    "name": item["tool"],
                    "tool_call_id": call_id,
                    "content": json.dumps(
                        item["result"], ensure_ascii=False, sort_keys=True
                    ),
                }
            )
    return messages


def build_examples(
    records: Iterable[dict[str, Any]],
    *,
    allowed_training_ids: set[str],
    forbidden_ids: set[str],
    verifier_template: str,
) -> list[dict[str, Any]]:
    """Validate curated records and emit deterministic SFT examples."""

    overlap = allowed_training_ids & forbidden_ids
    if overlap:
        raise SupervisionError(
            f"training/forbidden ID sets overlap: {sorted(overlap)}"
        )
    if "{problem_description}" not in verifier_template:
        raise SupervisionError("verifier template must contain {problem_description}")

    examples: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in records:
        if not isinstance(raw, dict):
            raise SupervisionError("supervision record is not an object")
        forbidden_key = _find_forbidden_key(raw)
        if forbidden_key:
            raise SupervisionError(
                f"record contains forbidden reference-solution field: {forbidden_key}"
            )

        instance_id = raw.get("instance_id")
        if not isinstance(instance_id, str) or not instance_id:
            raise SupervisionError("record has no instance_id")
        if instance_id in seen:
            raise SupervisionError(f"duplicate supervision record: {instance_id}")
        seen.add(instance_id)

        if raw.get("approved") is not True:
            raise SupervisionError(
                f"{instance_id}: raw/unapproved trace cannot enter SFT; approved must be true"
            )
        if instance_id in forbidden_ids:
            raise SupervisionError(f"{instance_id}: forbidden/blind ID cannot enter SFT")
        if instance_id not in allowed_training_ids:
            raise SupervisionError(f"{instance_id}: ID is not in the approved training subset")

        label = raw.get("label")
        if label not in ALLOWED_LABELS:
            raise SupervisionError(f"{instance_id}: unsupported label {label!r}")
        source = raw.get("source")
        if not isinstance(source, str) or not source:
            raise SupervisionError(f"{instance_id}: missing curated source")
        problem = raw.get("problem_description")
        if not isinstance(problem, str) or not problem.strip():
            raise SupervisionError(f"{instance_id}: missing problem_description")

        raw_steps = raw.get("steps")
        if not isinstance(raw_steps, list):
            raise SupervisionError(f"{instance_id}: steps must be a list")
        steps = [
            _validate_step_shape(instance_id, item, index)
            for index, item in enumerate(raw_steps)
        ]
        _validate_behavior(instance_id, label, steps)

        tool_names = sorted({item["tool"] for item in steps})
        examples.append(
            {
                "instance_id": instance_id,
                "label": label,
                "source": source,
                "messages": _messages_for_record(raw, verifier_template, steps),
                "tools": [_tool_schema(name) for name in tool_names],
            }
        )
    return examples


def _load_records(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    stripped = text.lstrip()
    if not stripped:
        return []
    if stripped.startswith("[") or stripped.startswith("{"):
        payload = json.loads(text)
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict) and isinstance(payload.get("records"), list):
            return payload["records"]
        raise SupervisionError("JSON input must be a list or an object with records[]")

    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise SupervisionError(f"JSONL line {line_number} is not an object")
        records.append(value)
    return records


def _ids_from_tasks_manifest(path: Path) -> set[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    tasks = payload.get("tasks")
    if not isinstance(tasks, list):
        raise SupervisionError(f"manifest has no tasks[]: {path}")
    ids = {
        str(item.get("instance_id"))
        for item in tasks
        if isinstance(item, dict) and item.get("instance_id")
    }
    if len(ids) != len(tasks):
        raise SupervisionError(f"manifest has invalid/duplicate task IDs: {path}")
    return ids


def _blind_ids_from_contract(path: Path) -> set[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    section = payload.get("blind_evaluation") or {}
    raw = section.get("instance_ids") or []
    if not isinstance(raw, list):
        raise SupervisionError("blind_evaluation.instance_ids must be a list")
    return {str(value) for value in raw}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("records", type=Path, help="approved normalized JSON/JSONL trajectories")
    parser.add_argument(
        "--train-manifest",
        type=Path,
        default=Path("docs/evaluation/verifier-lora-train-subset-v0.json"),
    )
    parser.add_argument(
        "--eval-contract",
        type=Path,
        default=Path("docs/evaluation/verifier-lora-eval-contract-v1.json"),
    )
    parser.add_argument(
        "--blind-reservation",
        type=Path,
        default=Path("docs/evaluation/verifier-lora-blind-reservation-v0.json"),
    )
    parser.add_argument(
        "--verifier-prompt",
        type=Path,
        default=Path("submission/prompts/verifier.md"),
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    allowed = _ids_from_tasks_manifest(args.train_manifest)
    forbidden = _blind_ids_from_contract(args.eval_contract)
    if args.blind_reservation.exists():
        forbidden |= _ids_from_tasks_manifest(args.blind_reservation)
    verifier_template = args.verifier_prompt.read_text(encoding="utf-8")
    records = _load_records(args.records)
    examples = build_examples(
        records,
        allowed_training_ids=allowed,
        forbidden_ids=forbidden,
        verifier_template=verifier_template,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for example in examples:
            handle.write(json.dumps(example, ensure_ascii=False, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "status": "completed",
                "records": len(records),
                "examples": len(examples),
                "output": str(args.output),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
