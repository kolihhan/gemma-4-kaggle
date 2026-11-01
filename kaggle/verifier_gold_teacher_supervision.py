"""Leakage-bounded helpers for deterministic verifier-LoRA supervision.

This module does not read blind tasks or hidden test patches. It validates a
frozen training-only targeted-test plan and converts deterministic evidence from
a gold-patched training workspace into the normalized record contract consumed
by ``scripts/build_verifier_sft.py``.
"""

from __future__ import annotations

import json
import shlex
from typing import Any


TARGET_PLAN_VERSION = "verifier-lora-v0-targeted-tests"
DIFF_COMMAND = "git diff --check && git diff"


def _classify_pytest(command: str) -> str:
    if not isinstance(command, str) or not command.strip():
        return "not_test"
    if any(token in command for token in (";", "&&", "||", "|", "`", "$((", "$(")):
        return "unsafe"
    try:
        tokens = shlex.split(command)
    except ValueError:
        return "unsafe"

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


def load_targeted_test_plan(plan_json: str, clean_training_ids: set[str]) -> dict[str, str]:
    """Validate a frozen targeted-test plan against gold-clean training IDs."""
    try:
        payload = json.loads(plan_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid targeted-test plan JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("targeted-test plan must be an object")
    if payload.get("version") != TARGET_PLAN_VERSION:
        raise ValueError(f"unexpected targeted-test plan version: {payload.get('version')!r}")
    if payload.get("status") != "frozen":
        raise ValueError("targeted-test plan must be frozen")
    targets = payload.get("targets")
    if not isinstance(targets, list) or not targets:
        raise ValueError("targeted-test plan has no targets")

    result: dict[str, str] = {}
    for item in targets:
        if not isinstance(item, dict):
            raise ValueError("targeted-test plan target must be an object")
        instance_id = item.get("instance_id")
        command = item.get("command")
        if not isinstance(instance_id, str) or not instance_id:
            raise ValueError("targeted-test plan target has no instance_id")
        if instance_id in result:
            raise ValueError(f"duplicate targeted-test task: {instance_id}")
        if instance_id not in clean_training_ids:
            raise ValueError(f"targeted-test task is not gold-clean training data: {instance_id}")
        if not isinstance(command, str) or _classify_pytest(command) != "targeted":
            raise ValueError(f"{instance_id}: command is not a safe targeted pytest gate")
        result[instance_id] = command
    return result


def _normalize_evidence(name: str, value: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} evidence must be an object")
    exit_code = value.get("exit_code")
    output = value.get("output", "")
    if not isinstance(exit_code, int) or isinstance(exit_code, bool):
        raise ValueError(f"{name} evidence has invalid exit_code")
    if not isinstance(output, str):
        raise ValueError(f"{name} evidence output must be text")
    return {"exit_code": exit_code, "output": output}


def build_teacher_supervision_record(
    *,
    instance_id: str,
    problem_description: str,
    targeted_command: str,
    pre_diff: dict[str, Any],
    targeted_test: dict[str, Any],
    final_diff: dict[str, Any],
) -> dict[str, Any]:
    """Build one normalized record from deterministic gold-workspace evidence.

    A record is auto-approved only when both diff gates and the targeted pytest
    gate return zero, the patch diff is non-empty, and the targeted test leaves
    that diff unchanged. Failed or unstable evidence is retained for audit but
    never gets a positive label or submit action.
    """
    if not isinstance(instance_id, str) or not instance_id:
        raise ValueError("instance_id is required")
    if not isinstance(problem_description, str) or not problem_description.strip():
        raise ValueError("problem_description is required")
    if _classify_pytest(targeted_command) != "targeted":
        raise ValueError("targeted_command must be a safe targeted pytest gate")

    pre = _normalize_evidence("pre_diff", pre_diff)
    test = _normalize_evidence("targeted_test", targeted_test)
    final = _normalize_evidence("final_diff", final_diff)

    all_exit_zero = pre["exit_code"] == test["exit_code"] == final["exit_code"] == 0
    diff_empty = not pre["output"].strip() or not final["output"].strip()
    diff_changed_during_test = pre["output"] != final["output"]
    approved = all_exit_zero and not diff_empty and not diff_changed_during_test

    steps: list[dict[str, Any]] = [
        {
            "tool": "run_command",
            "arguments": {"command": DIFF_COMMAND},
            "assistant_text": "Inspect the current patch before verification.",
            "result": pre,
        },
        {
            "tool": "run_command",
            "arguments": {"command": targeted_command},
            "assistant_text": "Run the smallest task-relevant regression test.",
            "result": test,
        },
        {
            "tool": "run_command",
            "arguments": {"command": DIFF_COMMAND},
            "assistant_text": "Re-check patch integrity immediately before submission.",
            "result": final,
        },
    ]
    if approved:
        steps.append(
            {
                "tool": "submit_patch",
                "arguments": {},
                "assistant_text": "The targeted gate passed and the final diff is clean; submit.",
            }
        )

    audit_flags = [
        f"failed_{name}"
        for name, evidence in (
            ("pre_diff", pre),
            ("targeted_test", test),
            ("final_diff", final),
        )
        if evidence["exit_code"] != 0
    ]
    if diff_empty:
        audit_flags.append("empty_diff")
    if diff_changed_during_test:
        audit_flags.append("diff_changed_during_test")

    return {
        "instance_id": instance_id,
        "approved": approved,
        "label": "verified_submit" if approved else None,
        "source": "gold_patch_targeted_test",
        "problem_description": problem_description.strip(),
        "steps": steps,
        "audit_flags": audit_flags,
    }
