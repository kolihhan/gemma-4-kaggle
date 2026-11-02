"""Leakage-bounded helpers for deterministic verifier-LoRA supervision.

This module does not read blind tasks or hidden test patches. It validates a
frozen training-only verification plan and converts deterministic evidence from
base and gold-patched training workspaces into the normalized record contract
consumed by ``scripts/build_verifier_sft.py``.
"""

from __future__ import annotations

import ast
import csv
import json
from pathlib import Path
import shlex
import sys
from typing import Any


TARGET_PLAN_VERSION = "verifier-lora-v0-targeted-tests"
DIFF_COMMAND = "git diff --check && git diff"


def find_reference_patch_dir(roots: list[Path]) -> Path:
    """Find the nearest ancestor secret dir containing only reference-patch data.

    Discovery checks for ``perfect_submission.*`` directly and never consults
    hidden verifier files when deciding which secret mount to use.
    """
    seen: set[Path] = set()
    for root in roots:
        try:
            resolved = Path(root).resolve()
        except Exception:
            continue
        for ancestor in [resolved, *resolved.parents]:
            candidate = ancestor / "secret"
            if candidate in seen:
                continue
            seen.add(candidate)
            if (
                (candidate / "perfect_submission.parquet").is_file()
                or (candidate / "perfect_submission.csv").is_file()
            ):
                return candidate
    raise FileNotFoundError("perfect_submission reference-patch secret directory not found")


def load_reference_patch_map(secret_dir: Path) -> dict[str, str]:
    """Load only training reference patches from perfect_submission.

    The competition secret bundle also contains hidden verifier test evidence in
    other files. This loader intentionally never opens those files.
    """
    secret_dir = Path(secret_dir)
    parquet_path = secret_dir / "perfect_submission.parquet"
    csv_path = secret_dir / "perfect_submission.csv"
    patch_map: dict[str, str] = {}

    if parquet_path.is_file():
        import pandas as pd

        frame = pd.read_parquet(parquet_path)
        for row in frame.to_dict(orient="records"):
            instance_id = str(row.get("id") or row.get("instance_id") or "").strip()
            patch = str(row.get("prediction") or row.get("patch") or "")
            if instance_id and patch:
                patch_map[instance_id] = patch
    elif csv_path.is_file():
        try:
            csv.field_size_limit(sys.maxsize)
        except OverflowError:
            csv.field_size_limit(2**31 - 1)
        with csv_path.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                instance_id = str(row.get("id") or row.get("instance_id") or "").strip()
                patch = str(row.get("prediction") or row.get("patch") or "")
                if instance_id and patch:
                    patch_map[instance_id] = patch
    else:
        raise FileNotFoundError(
            f"perfect_submission reference-patch bundle not found under {secret_dir}"
        )

    if not patch_map:
        raise ValueError("perfect_submission contains no reference patches")
    return patch_map


def _classify_verification(command: str) -> str:
    if not isinstance(command, str) or not command.strip():
        return "not_test"
    try:
        tokens = shlex.split(command)
    except ValueError:
        return "unsafe"
    if not tokens or any(token in {"&&", "||", "|", ";", "`"} for token in tokens):
        return "unsafe"

    executable = tokens[0].rsplit("/", 1)[-1]
    if executable in {"python", "python3"} and len(tokens) == 3 and tokens[1] == "-c":
        try:
            tree = ast.parse(tokens[2])
        except SyntaxError:
            return "unsafe"
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


def _is_behavioral_failure(command: str, evidence: dict[str, Any]) -> bool:
    """Return true only when a frozen inline assertion failed as intended.

    v0 safe-stop labels intentionally require ``python -c`` assertions. A
    generic non-zero process status is not enough because import failures,
    missing files, collection errors, and setup failures are infrastructure
    evidence rather than evidence that the target behavior is still broken.
    """
    try:
        tokens = shlex.split(command)
    except ValueError:
        return False
    if (
        len(tokens) != 3
        or tokens[0].rsplit("/", 1)[-1] not in {"python", "python3"}
        or tokens[1] != "-c"
    ):
        return False
    return evidence.get("exit_code") == 1 and "AssertionError" in str(evidence.get("output", ""))


def load_targeted_test_plan(plan_json: str, clean_training_ids: set[str]) -> dict[str, str]:
    """Validate a frozen targeted verification plan against gold-clean training IDs."""
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
        if not isinstance(command, str) or _classify_verification(command) != "targeted":
            raise ValueError(f"{instance_id}: command is not a safe targeted verification gate")
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


def _evidence_steps(
    targeted_command: str,
    pre: dict[str, Any],
    test: dict[str, Any],
    final: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "tool": "run_command",
            "arguments": {"command": DIFF_COMMAND},
            "assistant_text": "Inspect the current patch before verification.",
            "result": pre,
        },
        {
            "tool": "run_command",
            "arguments": {"command": targeted_command},
            "assistant_text": "Run the smallest task-relevant regression check.",
            "result": test,
        },
        {
            "tool": "run_command",
            "arguments": {"command": DIFF_COMMAND},
            "assistant_text": "Re-check the working tree after verification.",
            "result": final,
        },
    ]


def build_teacher_safe_stop_record(
    *,
    instance_id: str,
    problem_description: str,
    targeted_command: str,
    pre_diff: dict[str, Any],
    targeted_test: dict[str, Any],
    final_diff: dict[str, Any],
) -> dict[str, Any]:
    """Build safe-stop supervision from a clean base state with behavioral failure."""
    if not isinstance(instance_id, str) or not instance_id:
        raise ValueError("instance_id is required")
    if not isinstance(problem_description, str) or not problem_description.strip():
        raise ValueError("problem_description is required")
    if _classify_verification(targeted_command) != "targeted":
        raise ValueError("targeted_command must be a safe targeted verification gate")

    pre = _normalize_evidence("pre_diff", pre_diff)
    test = _normalize_evidence("targeted_test", targeted_test)
    final = _normalize_evidence("final_diff", final_diff)

    diff_clean = not pre["output"].strip() and not final["output"].strip()
    diff_stable = pre["output"] == final["output"]
    diff_checks_pass = pre["exit_code"] == 0 and final["exit_code"] == 0
    targeted_behavior_failed = _is_behavioral_failure(targeted_command, test)
    approved = diff_clean and diff_stable and diff_checks_pass and targeted_behavior_failed

    audit_flags: list[str] = []
    if pre["exit_code"] != 0:
        audit_flags.append("failed_pre_diff")
    if final["exit_code"] != 0:
        audit_flags.append("failed_final_diff")
    if test["exit_code"] == 0:
        audit_flags.append("targeted_test_unexpectedly_passed")
    elif not targeted_behavior_failed:
        audit_flags.append("non_behavioral_targeted_failure")
    if pre["output"].strip() or final["output"].strip():
        audit_flags.append("dirty_base_diff")
    if not diff_stable:
        audit_flags.append("base_diff_changed_during_test")

    return {
        "instance_id": instance_id,
        "example_id": f"{instance_id}:base-fail",
        "approved": approved,
        "label": "safe_stop" if approved else None,
        "source": "base_targeted_failure",
        "problem_description": problem_description.strip(),
        "steps": _evidence_steps(targeted_command, pre, test, final),
        "audit_flags": audit_flags,
    }


def build_teacher_supervision_record(
    *,
    instance_id: str,
    problem_description: str,
    targeted_command: str,
    pre_diff: dict[str, Any],
    targeted_test: dict[str, Any],
    final_diff: dict[str, Any],
) -> dict[str, Any]:
    """Build verified-submit supervision from deterministic gold-workspace evidence."""
    if not isinstance(instance_id, str) or not instance_id:
        raise ValueError("instance_id is required")
    if not isinstance(problem_description, str) or not problem_description.strip():
        raise ValueError("problem_description is required")
    if _classify_verification(targeted_command) != "targeted":
        raise ValueError("targeted_command must be a safe targeted verification gate")

    pre = _normalize_evidence("pre_diff", pre_diff)
    test = _normalize_evidence("targeted_test", targeted_test)
    final = _normalize_evidence("final_diff", final_diff)

    all_exit_zero = pre["exit_code"] == test["exit_code"] == final["exit_code"] == 0
    diff_empty = not pre["output"].strip() or not final["output"].strip()
    diff_changed_during_test = pre["output"] != final["output"]
    approved = all_exit_zero and not diff_empty and not diff_changed_during_test

    steps = _evidence_steps(targeted_command, pre, test, final)
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
        "example_id": f"{instance_id}:gold-pass",
        "approved": approved,
        "label": "verified_submit" if approved else None,
        "source": "gold_patch_targeted_test",
        "problem_description": problem_description.strip(),
        "steps": steps,
        "audit_flags": audit_flags,
    }
