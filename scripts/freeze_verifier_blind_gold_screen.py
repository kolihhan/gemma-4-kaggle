#!/usr/bin/env python3
"""Freeze a completed blind gold-control sweep without exposing blind content.

The freezer accepts only the already-reserved metadata denominator and a
structured automated gold-control result. It refuses partial, confounded, or
mismatched sweeps and writes only denominator/provenance metadata. Raw
reference patches and task content never enter the frozen screen or evaluation
contract.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any


class BlindFreezeError(ValueError):
    """Raised when blind gold-control evidence is unsafe or inconsistent."""


def _contains_raw_reference_patch(value: Any) -> bool:
    if isinstance(value, dict):
        return any(
            key == "reference_patch" or _contains_raw_reference_patch(child)
            for key, child in value.items()
        )
    if isinstance(value, list):
        return any(_contains_raw_reference_patch(item) for item in value)
    return False


def _reservation_items(reservation: dict[str, Any]) -> list[dict[str, str]]:
    if reservation.get("version") != "verifier-lora-v0-blind-reservation":
        raise BlindFreezeError(
            f"unexpected blind reservation version: {reservation.get('version')!r}"
        )
    raw = reservation.get("tasks")
    if not isinstance(raw, list) or not raw:
        raise BlindFreezeError("blind reservation has no tasks")

    items: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in raw:
        if not isinstance(item, dict):
            raise BlindFreezeError("blind reservation task must be an object")
        instance_id = item.get("instance_id")
        repo = item.get("repo")
        if not isinstance(instance_id, str) or not instance_id:
            raise BlindFreezeError("blind reservation task has invalid instance_id")
        if not isinstance(repo, str) or not repo:
            raise BlindFreezeError(f"{instance_id}: blind reservation task has invalid repo")
        if instance_id in seen:
            raise BlindFreezeError(f"duplicate blind reservation task: {instance_id}")
        seen.add(instance_id)
        items.append({"instance_id": instance_id, "repo": repo})
    return items


def _validate_contract(eval_contract: dict[str, Any]) -> None:
    if eval_contract.get("version") != "verifier-lora-v0-eval-contract-v1":
        raise BlindFreezeError(
            f"unexpected eval contract version: {eval_contract.get('version')!r}"
        )
    blind = eval_contract.get("blind_evaluation")
    if not isinstance(blind, dict):
        raise BlindFreezeError("eval contract has no blind_evaluation object")
    if blind.get("status") != "pending_freeze":
        raise BlindFreezeError("blind evaluation is not pending_freeze")
    if blind.get("instance_ids") not in ([], None):
        raise BlindFreezeError("pending blind evaluation already contains instance IDs")
    if blind.get("automated_gold_control_only") is not True:
        raise BlindFreezeError("blind contract must permit automated gold-control only")
    if blind.get("base_failure_traces_uninspected_before_adapter_freeze") is not True:
        raise BlindFreezeError("blind failure-trace protection is not enabled")
    promotion = eval_contract.get("promotion")
    if not isinstance(promotion, dict) or promotion.get("requires_frozen_blind_evaluation") is not True:
        raise BlindFreezeError("promotion contract does not require frozen blind evaluation")


def freeze_blind(
    reservation: dict[str, Any],
    sweep: dict[str, Any],
    eval_contract: dict[str, Any],
    source_run_id: int,
    source_artifact_id: int,
    source_artifact_digest: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Validate a clean blind sweep, then return frozen screen + contract copies."""

    if not all(isinstance(value, dict) for value in (reservation, sweep, eval_contract)):
        raise BlindFreezeError("reservation, sweep, and eval contract must be objects")
    if _contains_raw_reference_patch(sweep):
        raise BlindFreezeError("sweep contains raw reference_patch leakage")

    items = _reservation_items(reservation)
    _validate_contract(eval_contract)
    expected_ids = [item["instance_id"] for item in items]
    expected_set = set(expected_ids)
    expected_repo = {item["instance_id"]: item["repo"] for item in items}
    expected_count = len(items)

    if sweep.get("version") != "verifier-lora-v0":
        raise BlindFreezeError(f"unexpected sweep version: {sweep.get('version')!r}")
    if sweep.get("status") != "completed":
        raise BlindFreezeError("blind gold-control sweep is not completed")
    if sweep.get("control") != "gold_reference_patch":
        raise BlindFreezeError("unexpected blind sweep control")
    if sweep.get("requested") != expected_count or sweep.get("completed") != expected_count:
        raise BlindFreezeError(
            "blind gold-control denominator incomplete: "
            f"requested={sweep.get('requested')!r} completed={sweep.get('completed')!r} "
            f"expected={expected_count}"
        )

    results = sweep.get("results")
    if not isinstance(results, list) or len(results) != expected_count:
        raise BlindFreezeError("blind gold-control results do not match reservation denominator")

    by_id: dict[str, dict[str, Any]] = {}
    for result in results:
        if not isinstance(result, dict):
            raise BlindFreezeError("blind gold-control result must be an object")
        instance_id = result.get("instance_id")
        repo = result.get("repo")
        if not isinstance(instance_id, str) or not instance_id:
            raise BlindFreezeError("blind gold-control result has invalid instance_id")
        if instance_id in by_id:
            raise BlindFreezeError(f"duplicate blind gold-control result: {instance_id}")
        if repo != expected_repo.get(instance_id):
            raise BlindFreezeError(
                f"{instance_id}: result repo {repo!r} does not match blind reservation"
            )
        by_id[instance_id] = result

    actual_set = set(by_id)
    if actual_set != expected_set:
        raise BlindFreezeError(
            "blind denominator IDs differ from reservation: "
            f"missing={sorted(expected_set - actual_set)!r} "
            f"extra={sorted(actual_set - expected_set)!r}"
        )

    clean_ids_sorted = sorted(
        instance_id
        for instance_id, result in by_id.items()
        if result.get("status") == "completed"
        and result.get("resolved") is True
        and result.get("test_exit_code") == 0
    )
    clean_set = set(clean_ids_sorted)
    confounded_ids = sorted(expected_set - clean_set)

    if sweep.get("clean_instance_ids") != clean_ids_sorted or sweep.get("confounded_instance_ids") != confounded_ids:
        raise BlindFreezeError("blind gold-control summary IDs do not match recomputed results")
    if sweep.get("clean") != len(clean_ids_sorted) or sweep.get("confounded") != len(confounded_ids):
        raise BlindFreezeError("blind gold-control summary counts do not match recomputed results")
    if confounded_ids:
        raise BlindFreezeError(
            "blind reservation contains confounded candidates; replace them deterministically before freeze: "
            f"{confounded_ids!r}"
        )

    if not isinstance(source_run_id, int) or source_run_id <= 0:
        raise BlindFreezeError("source_run_id must be a positive integer")
    if not isinstance(source_artifact_id, int) or source_artifact_id <= 0:
        raise BlindFreezeError("source_artifact_id must be a positive integer")
    if not isinstance(source_artifact_digest, str) or not source_artifact_digest:
        raise BlindFreezeError("source_artifact_digest is required")

    screen = {
        "version": "verifier-lora-v0-blind-gold-screen",
        "status": "frozen",
        "source_reservation": "docs/evaluation/verifier-lora-blind-reservation-v0.json",
        "source_run_id": source_run_id,
        "source_artifact_id": source_artifact_id,
        "source_artifact_digest": source_artifact_digest,
        "selection_rule": "all reserved candidates must pass automated gold-control with resolved=true and test_exit_code=0",
        "instance_ids": expected_ids,
        "counts": {
            "requested": expected_count,
            "clean": expected_count,
            "confounded": 0,
        },
    }

    updated = copy.deepcopy(eval_contract)
    blind = updated["blind_evaluation"]
    blind["status"] = "frozen"
    blind["instance_ids"] = expected_ids
    blind["gold_screen_source"] = "docs/evaluation/verifier-lora-blind-gold-screen-v0.json"
    blind["gold_screen_run_id"] = source_run_id
    blind["gold_screen_artifact_id"] = source_artifact_id
    blind["gold_screen_artifact_digest"] = source_artifact_digest

    return screen, updated


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sweep", type=Path)
    parser.add_argument(
        "--reservation",
        type=Path,
        default=Path("docs/evaluation/verifier-lora-blind-reservation-v0.json"),
    )
    parser.add_argument(
        "--eval-contract",
        type=Path,
        default=Path("docs/evaluation/verifier-lora-eval-contract-v1.json"),
    )
    parser.add_argument("--source-run-id", type=int, required=True)
    parser.add_argument("--source-artifact-id", type=int, required=True)
    parser.add_argument("--source-artifact-digest", required=True)
    parser.add_argument(
        "--screen-output",
        type=Path,
        default=Path("docs/evaluation/verifier-lora-blind-gold-screen-v0.json"),
    )
    parser.add_argument("--contract-output", type=Path, required=True)
    args = parser.parse_args(argv)

    screen, contract = freeze_blind(
        json.loads(args.reservation.read_text(encoding="utf-8")),
        json.loads(args.sweep.read_text(encoding="utf-8")),
        json.loads(args.eval_contract.read_text(encoding="utf-8")),
        args.source_run_id,
        args.source_artifact_id,
        args.source_artifact_digest,
    )
    args.screen_output.parent.mkdir(parents=True, exist_ok=True)
    args.contract_output.parent.mkdir(parents=True, exist_ok=True)
    args.screen_output.write_text(json.dumps(screen, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.contract_output.write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(screen, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
