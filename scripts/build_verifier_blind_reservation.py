#!/usr/bin/env python3
"""Reserve verifier-LoRA blind candidates from metadata-only training manifests."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


VERSION = "verifier-lora-v0-blind-reservation"
HASH_NAMESPACE = "verifier-lora-v0-blind:<instance_id>"
PATCH_BUCKET_ORDER = ("1-10", "11-30", "31-80", "81+", "0")
DEFAULT_QUOTA = {
    "Textualize/rich": 4,
    "fastapi/fastapi": 6,
    "psf/requests": 0,
}


def _stable_key(instance_id: str) -> tuple[str, str]:
    digest = hashlib.sha256(f"verifier-lora-v0-blind:{instance_id}".encode("utf-8")).hexdigest()
    return digest, instance_id


def _bucket_index(bucket: str) -> int:
    try:
        return PATCH_BUCKET_ORDER.index(bucket)
    except ValueError:
        return len(PATCH_BUCKET_ORDER)


def _manifest_sort_key(item: dict) -> tuple[str, int, str]:
    return (
        str(item.get("repo") or ""),
        _bucket_index(str(item.get("patch_bucket") or "")),
        str(item.get("instance_id") or ""),
    )


def _validate_item(item: dict, *, where: str) -> None:
    if not isinstance(item, dict):
        raise ValueError(f"{where} item must be an object")
    extra = set(item) - {"instance_id", "repo", "patch_bucket"}
    if extra:
        raise ValueError(f"{where} item contains non-metadata fields: {sorted(extra)}")
    for key in ("instance_id", "repo", "patch_bucket"):
        if not str(item.get(key) or ""):
            raise ValueError(f"{where} item missing {key}: {item!r}")


def _choose_repo(candidates: list[dict], quota: int, repo: str) -> list[dict]:
    if quota == 0:
        return []
    if len(candidates) < quota:
        raise ValueError(f"not enough unharvested training tasks for {repo}: need {quota}, have {len(candidates)}")

    buckets: dict[str, list[dict]] = defaultdict(list)
    for item in candidates:
        buckets[str(item["patch_bucket"])].append(item)
    for bucket_items in buckets.values():
        bucket_items.sort(key=lambda item: _stable_key(str(item["instance_id"])))

    selected: list[dict] = []
    while len(selected) < quota:
        progressed = False
        for bucket in PATCH_BUCKET_ORDER:
            bucket_items = buckets.get(bucket)
            if bucket_items and len(selected) < quota:
                selected.append(bucket_items.pop(0))
                progressed = True
        if not progressed:
            raise RuntimeError(f"unable to satisfy blind quota for {repo}")
    return selected


def build_blind_reservation(
    split: dict,
    training_subset: dict,
    quota: dict[str, int] | None = None,
) -> dict:
    """Select blind candidates using only already-materialized metadata.

    The source split's ``train`` entries are metadata-only. Tasks already present
    in the frozen training-trace harvest subset are excluded before selection.
    No task text, reference patch, agent trace, or task outcome is consulted.
    """
    if split.get("version") != "verifier-lora-v0":
        raise ValueError(f"unexpected split version: {split.get('version')!r}")
    if training_subset.get("version") != "verifier-lora-v0-train-harvest":
        raise ValueError(f"unexpected training subset version: {training_subset.get('version')!r}")

    repo_quota = dict(DEFAULT_QUOTA if quota is None else quota)
    train = list(split.get("train") or [])
    harvested = list(training_subset.get("tasks") or [])
    for item in train:
        _validate_item(item, where="split.train")
    for item in harvested:
        _validate_item(item, where="training_subset.tasks")

    harvested_ids = {str(item["instance_id"]) for item in harvested}
    eligible = [item for item in train if str(item["instance_id"]) not in harvested_ids]

    by_repo: dict[str, list[dict]] = defaultdict(list)
    for item in eligible:
        by_repo[str(item["repo"])].append(item)

    selected: list[dict] = []
    for repo, repo_count in repo_quota.items():
        if repo_count < 0:
            raise ValueError(f"negative blind quota for {repo}: {repo_count}")
        selected.extend(_choose_repo(by_repo.get(repo, []), repo_count, repo))

    selected = [
        {
            "instance_id": str(item["instance_id"]),
            "repo": str(item["repo"]),
            "patch_bucket": str(item["patch_bucket"]),
        }
        for item in selected
    ]
    selected.sort(key=_manifest_sort_key)
    selected_ids = [item["instance_id"] for item in selected]
    if len(selected_ids) != len(set(selected_ids)):
        raise ValueError("blind reservation contains duplicate task IDs")

    counts = Counter(item["repo"] for item in selected)
    return {
        "version": VERSION,
        "source_split_version": "verifier-lora-v0",
        "source_training_subset_version": "verifier-lora-v0-train-harvest",
        "selection": {
            "method": "bucket-round-robin-sha256-from-unharvested-training-pool",
            "hash_namespace": HASH_NAMESPACE,
            "patch_bucket_order": list(PATCH_BUCKET_ORDER),
            "quota_by_repo": repo_quota,
            "metadata_only": True,
        },
        "coverage_limit": "No untouched Requests tasks remain in the current training-side pool: both Requests train tasks are already in the frozen trace-harvest subset. Blind v0 therefore supports Rich/FastAPI only and cannot establish Requests generalization.",
        "counts": {
            "tasks": len(selected),
            "by_repo": {repo: counts.get(repo, 0) for repo in repo_quota},
        },
        "tasks": selected,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--split",
        type=Path,
        default=Path("docs/evaluation/verifier-lora-split-v0.json"),
    )
    parser.add_argument(
        "--training-subset",
        type=Path,
        default=Path("docs/evaluation/verifier-lora-train-subset-v0.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/evaluation/verifier-lora-blind-reservation-v0.json"),
    )
    args = parser.parse_args()

    split = json.loads(args.split.read_text(encoding="utf-8"))
    training_subset = json.loads(args.training_subset.read_text(encoding="utf-8"))
    reservation = build_blind_reservation(split, training_subset)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(reservation, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(reservation, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
