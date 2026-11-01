#!/usr/bin/env python3
"""Freeze a completed training-side gold-control sweep into metadata only.

The output intentionally contains task IDs and provenance only. It never copies
per-task verifier output, reference-patch hashes, test output, or raw patches.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


class GoldScreenError(ValueError):
    """Raised when the training gold-control evidence is incomplete or inconsistent."""


def _has_raw_reference_patch(value: Any) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "reference_patch":
                return True
            if _has_raw_reference_patch(child):
                return True
    elif isinstance(value, list):
        return any(_has_raw_reference_patch(item) for item in value)
    return False


def _training_items(training_manifest: dict[str, Any]) -> list[dict[str, str]]:
    if training_manifest.get("version") != "verifier-lora-v0-train-harvest":
        raise GoldScreenError(
            f"unexpected training manifest version: {training_manifest.get('version')!r}"
        )
    raw = training_manifest.get("tasks")
    if not isinstance(raw, list) or not raw:
        raise GoldScreenError("training manifest has no tasks")

    items: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in raw:
        if not isinstance(item, dict):
            raise GoldScreenError("training task must be an object")
        instance_id = item.get("instance_id")
        repo = item.get("repo")
        if not isinstance(instance_id, str) or not instance_id:
            raise GoldScreenError("training task has invalid instance_id")
        if not isinstance(repo, str) or not repo:
            raise GoldScreenError(f"{instance_id}: training task has invalid repo")
        if instance_id in seen:
            raise GoldScreenError(f"duplicate training task: {instance_id}")
        seen.add(instance_id)
        items.append({"instance_id": instance_id, "repo": repo})
    return items


def freeze_screen(
    training_manifest: dict[str, Any],
    sweep: dict[str, Any],
    source_run_id: int,
    source_artifact_id: int,
    source_artifact_digest: str,
) -> dict[str, Any]:
    """Validate one complete sweep and return its frozen metadata denominator."""

    if not isinstance(training_manifest, dict) or not isinstance(sweep, dict):
        raise GoldScreenError("training manifest and sweep must be objects")
    if _has_raw_reference_patch(sweep):
        raise GoldScreenError("sweep contains raw reference_patch leakage")

    training_items = _training_items(training_manifest)
    expected_ids = [item["instance_id"] for item in training_items]
    expected_set = set(expected_ids)
    expected_repo = {item["instance_id"]: item["repo"] for item in training_items}
    expected_count = len(expected_ids)

    if sweep.get("version") != "verifier-lora-v0":
        raise GoldScreenError(f"unexpected sweep version: {sweep.get('version')!r}")
    if sweep.get("status") != "completed":
        raise GoldScreenError("gold-control sweep is not completed")
    if sweep.get("control") != "gold_reference_patch":
        raise GoldScreenError("unexpected sweep control")
    if sweep.get("requested") != expected_count or sweep.get("completed") != expected_count:
        raise GoldScreenError(
            f"gold-control denominator incomplete: requested={sweep.get('requested')!r} "
            f"completed={sweep.get('completed')!r} expected={expected_count}"
        )

    results = sweep.get("results")
    if not isinstance(results, list) or len(results) != expected_count:
        raise GoldScreenError("gold-control results do not match the training denominator")

    by_id: dict[str, dict[str, Any]] = {}
    for item in results:
        if not isinstance(item, dict):
            raise GoldScreenError("gold-control result must be an object")
        instance_id = item.get("instance_id")
        repo = item.get("repo")
        if not isinstance(instance_id, str) or not instance_id:
            raise GoldScreenError("gold-control result has invalid instance_id")
        if instance_id in by_id:
            raise GoldScreenError(f"duplicate gold-control result: {instance_id}")
        if repo != expected_repo.get(instance_id):
            raise GoldScreenError(
                f"{instance_id}: result repo {repo!r} does not match frozen training manifest"
            )
        by_id[instance_id] = item

    actual_set = set(by_id)
    if actual_set != expected_set:
        raise GoldScreenError(
            "gold-control denominator IDs differ from frozen training subset: "
            f"missing={sorted(expected_set - actual_set)!r} "
            f"extra={sorted(actual_set - expected_set)!r}"
        )

    clean_ids = sorted(
        instance_id
        for instance_id, item in by_id.items()
        if item.get("status") == "completed"
        and item.get("resolved") is True
        and item.get("test_exit_code") == 0
    )
    clean_set = set(clean_ids)
    confounded_ids = sorted(expected_set - clean_set)

    reported_clean = sweep.get("clean_instance_ids")
    reported_confounded = sweep.get("confounded_instance_ids")
    if reported_clean != clean_ids or reported_confounded != confounded_ids:
        raise GoldScreenError(
            "gold-control summary clean/confounded IDs do not match recomputed results"
        )
    if sweep.get("clean") != len(clean_ids) or sweep.get("confounded") != len(confounded_ids):
        raise GoldScreenError(
            "gold-control summary counts do not match recomputed results"
        )

    if not isinstance(source_run_id, int) or source_run_id <= 0:
        raise GoldScreenError("source_run_id must be a positive integer")
    if not isinstance(source_artifact_id, int) or source_artifact_id <= 0:
        raise GoldScreenError("source_artifact_id must be a positive integer")
    if not isinstance(source_artifact_digest, str) or not source_artifact_digest:
        raise GoldScreenError("source_artifact_digest is required")

    return {
        "version": "verifier-lora-v0-training-gold-screen",
        "status": "frozen",
        "source_training_manifest": "verifier-lora-v0-train-harvest",
        "source_run_id": source_run_id,
        "source_artifact_id": source_artifact_id,
        "source_artifact_digest": source_artifact_digest,
        "selection_rule": "gold-control resolved=true and test_exit_code=0",
        "clean_instance_ids": clean_ids,
        "confounded_instance_ids": confounded_ids,
        "counts": {
            "requested": expected_count,
            "clean": len(clean_ids),
            "confounded": len(confounded_ids),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sweep", type=Path)
    parser.add_argument(
        "--training-manifest",
        type=Path,
        default=Path("docs/evaluation/verifier-lora-train-subset-v0.json"),
    )
    parser.add_argument("--source-run-id", type=int, required=True)
    parser.add_argument("--source-artifact-id", type=int, required=True)
    parser.add_argument("--source-artifact-digest", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    output = freeze_screen(
        json.loads(args.training_manifest.read_text(encoding="utf-8")),
        json.loads(args.sweep.read_text(encoding="utf-8")),
        args.source_run_id,
        args.source_artifact_id,
        args.source_artifact_digest,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(output, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
