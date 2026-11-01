#!/usr/bin/env python3
"""Freeze a deterministic, leakage-safe verifier LoRA training trace subset."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


SOURCE_VERSION = "verifier-lora-v0"
VERSION = "verifier-lora-v0-train-harvest"
HASH_NAMESPACE = "verifier-lora-v0-train-harvest"
PATCH_BUCKET_ORDER = ("1-10", "11-30", "31-80", "81+", "0")
DEFAULT_TRAIN_QUOTA = {
    "Textualize/rich": 8,
    "fastapi/fastapi": 8,
    "psf/requests": 2,
}


def _stable_key(instance_id: str) -> tuple[str, str]:
    digest = hashlib.sha256(f"{HASH_NAMESPACE}:{instance_id}".encode("utf-8")).hexdigest()
    return digest, instance_id


def _validate_item(item: dict, *, where: str) -> None:
    if not isinstance(item, dict):
        raise ValueError(f"{where} item must be an object")
    for key in ("instance_id", "repo", "patch_bucket"):
        if not str(item.get(key) or ""):
            raise ValueError(f"{where} item missing {key}: {item!r}")


def _choose_repo_tasks(candidates: list[dict], quota: int, repo: str) -> list[dict]:
    if quota < 0:
        raise ValueError(f"negative training quota for {repo}: {quota}")
    if len(candidates) < quota:
        raise ValueError(f"not enough training tasks for {repo}: need {quota}, have {len(candidates)}")
    if quota == 0:
        return []

    buckets: dict[str, list[dict]] = defaultdict(list)
    for item in candidates:
        bucket = str(item["patch_bucket"])
        buckets[bucket].append(item)
    for items in buckets.values():
        items.sort(key=lambda item: _stable_key(str(item["instance_id"])))

    selected: list[dict] = []
    while len(selected) < quota:
        progressed = False
        for bucket in PATCH_BUCKET_ORDER:
            items = buckets.get(bucket)
            if items and len(selected) < quota:
                selected.append(dict(items.pop(0)))
                progressed = True
        if not progressed:
            raise RuntimeError(f"unable to satisfy training quota for {repo}")
    return selected


def build_training_subset(
    split: dict,
    quota: dict[str, int] | None = None,
) -> dict:
    if split.get("version") != SOURCE_VERSION:
        raise ValueError(f"unexpected split version: {split.get('version')!r}")

    quotas = dict(DEFAULT_TRAIN_QUOTA if quota is None else quota)
    train = list(split.get("train") or [])
    holdout = list(split.get("holdout") or [])
    excluded = list(split.get("excluded") or [])

    for item in train:
        _validate_item(item, where="train")
    for item in holdout:
        _validate_item(item, where="holdout")
    for item in excluded:
        _validate_item(item, where="excluded")

    train_ids = [str(item["instance_id"]) for item in train]
    if len(train_ids) != len(set(train_ids)):
        raise ValueError("train partition contains duplicate instance_id values")

    holdout_ids = {str(item["instance_id"]) for item in holdout}
    excluded_ids = {str(item["instance_id"]) for item in excluded}
    overlap = set(train_ids) & (holdout_ids | excluded_ids)
    if overlap:
        raise ValueError(f"training partition overlaps non-training partitions: {sorted(overlap)}")

    by_repo: dict[str, list[dict]] = defaultdict(list)
    for item in train:
        by_repo[str(item["repo"])].append(item)

    selected: list[dict] = []
    for repo, repo_quota in quotas.items():
        selected.extend(_choose_repo_tasks(by_repo.get(repo, []), int(repo_quota), repo))

    selected_ids = [str(item["instance_id"]) for item in selected]
    if len(selected_ids) != len(set(selected_ids)):
        raise RuntimeError("training subset selection produced duplicate instance_id values")
    if not set(selected_ids) <= set(train_ids):
        raise RuntimeError("training subset selection escaped train partition")
    if set(selected_ids) & (holdout_ids | excluded_ids):
        raise RuntimeError("training subset selection leaked holdout/excluded tasks")

    counts = Counter(str(item["repo"]) for item in selected)
    return {
        "version": VERSION,
        "source_split_version": SOURCE_VERSION,
        "selection": {
            "method": "bucket-round-robin-sha256",
            "hash_namespace": f"{HASH_NAMESPACE}:<instance_id>",
            "patch_bucket_order": list(PATCH_BUCKET_ORDER),
            "quota_by_repo": quotas,
        },
        "tasks": selected,
        "counts": {
            "tasks": len(selected),
            "by_repo": {repo: counts.get(repo, 0) for repo in quotas},
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("docs/evaluation/verifier-lora-split-v0.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/evaluation/verifier-lora-train-subset-v0.json"),
    )
    args = parser.parse_args()

    split = json.loads(args.input.read_text(encoding="utf-8"))
    subset = build_training_subset(split)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(subset, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "version": subset["version"],
                "counts": subset["counts"],
                "instance_ids": [item["instance_id"] for item in subset["tasks"]],
                "output": str(args.output),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
