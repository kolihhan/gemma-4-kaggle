#!/usr/bin/env python3
"""Build a deterministic leakage-safe train/holdout split for verifier LoRA v0."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

try:
    from scripts.analyze_tasks import diff_stats
except ModuleNotFoundError:
    from analyze_tasks import diff_stats


VERSION = "verifier-lora-v0"
HTTPX_REPO = "encode/httpx"
PATCH_BUCKET_ORDER = ("1-10", "11-30", "31-80", "81+", "0")

DEFAULT_HOLDOUT_QUOTA = {
    "fastapi/fastapi": 6,
    "Textualize/rich": 4,
    "psf/requests": 2,
}

DEFAULT_EXCLUDED_IDS = {
    "rich_3278",
    "rich_2725",
    "rich_3930",
    "httpx_3672",
    "fastapi_14361",
    "fastapi_14266",
    "fastapi_14609",
    "requests_6592",
    "requests_7502",
    "requests_6757",
}


def load_jsonl(path: Path) -> list[dict]:
    tasks: list[dict] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, 1):
            line = raw.strip()
            if not line:
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"line {line_number} is not a JSON object")
            tasks.append(value)
    return tasks


def patch_bucket(task: dict) -> str:
    lines = diff_stats(task.get("patch"))["lines"]
    if lines == 0:
        return "0"
    if lines <= 10:
        return "1-10"
    if lines <= 30:
        return "11-30"
    if lines <= 80:
        return "31-80"
    return "81+"


def _stable_key(instance_id: str) -> tuple[str, str]:
    digest = hashlib.sha256(f"{VERSION}:{instance_id}".encode("utf-8")).hexdigest()
    return digest, instance_id


def _manifest_item(task: dict) -> dict[str, str]:
    return {
        "instance_id": str(task.get("instance_id") or ""),
        "repo": str(task.get("repo") or "UNKNOWN"),
        "patch_bucket": patch_bucket(task),
    }


def _choose_holdout(candidates: list[dict], quota: int, repo: str) -> list[dict]:
    if quota < 0:
        raise ValueError(f"negative holdout quota for {repo}: {quota}")
    if len(candidates) < quota:
        raise ValueError(f"not enough eligible tasks for {repo}: need {quota}, have {len(candidates)}")
    if quota == 0:
        return []

    buckets: dict[str, list[dict]] = defaultdict(list)
    for task in candidates:
        buckets[patch_bucket(task)].append(task)
    for bucket_tasks in buckets.values():
        bucket_tasks.sort(key=lambda task: _stable_key(str(task.get("instance_id") or "")))

    selected: list[dict] = []
    while len(selected) < quota:
        progressed = False
        for bucket in PATCH_BUCKET_ORDER:
            bucket_tasks = buckets.get(bucket)
            if bucket_tasks and len(selected) < quota:
                selected.append(bucket_tasks.pop(0))
                progressed = True
        if not progressed:
            raise RuntimeError(f"unable to satisfy holdout quota for {repo}")
    return selected


def build_split(
    tasks: Iterable[dict],
    holdout_quota: dict[str, int] | None = None,
    excluded_ids: set[str] | None = None,
) -> dict:
    quota = dict(DEFAULT_HOLDOUT_QUOTA if holdout_quota is None else holdout_quota)
    excluded = set(DEFAULT_EXCLUDED_IDS if excluded_ids is None else excluded_ids)
    items = list(tasks)

    eligible_by_repo: dict[str, list[dict]] = defaultdict(list)
    excluded_items: list[dict[str, str]] = []

    for task in items:
        instance_id = str(task.get("instance_id") or "")
        repo = str(task.get("repo") or "UNKNOWN")
        if not instance_id:
            raise ValueError("task missing instance_id")
        if instance_id in excluded or repo == HTTPX_REPO:
            reason_parts = []
            if instance_id in excluded:
                reason_parts.append("development_seen")
            if repo == HTTPX_REPO:
                reason_parts.append("harness_confounded")
            excluded_items.append({**_manifest_item(task), "reason": "+".join(reason_parts)})
            continue
        eligible_by_repo[repo].append(task)

    holdout_tasks: list[dict] = []
    for repo, repo_quota in quota.items():
        holdout_tasks.extend(_choose_holdout(eligible_by_repo.get(repo, []), repo_quota, repo))

    holdout_ids = {str(task["instance_id"]) for task in holdout_tasks}
    train_tasks = [
        task
        for repo_tasks in eligible_by_repo.values()
        for task in repo_tasks
        if str(task.get("instance_id")) not in holdout_ids
    ]

    holdout_manifest = [_manifest_item(task) for task in holdout_tasks]
    holdout_manifest.sort(key=lambda item: (item["repo"], PATCH_BUCKET_ORDER.index(item["patch_bucket"]), item["instance_id"]))
    train_manifest = [_manifest_item(task) for task in train_tasks]
    train_manifest.sort(key=lambda item: (item["repo"], item["instance_id"]))
    excluded_items.sort(key=lambda item: (item["repo"], item["instance_id"]))

    holdout_by_repo = Counter(item["repo"] for item in holdout_manifest)
    return {
        "version": VERSION,
        "selection": {
            "method": "bucket-round-robin-sha256",
            "hash_namespace": f"{VERSION}:<instance_id>",
            "patch_bucket_order": list(PATCH_BUCKET_ORDER),
        },
        "holdout": holdout_manifest,
        "train": train_manifest,
        "excluded": excluded_items,
        "counts": {
            "total_input": len(items),
            "train": len(train_manifest),
            "holdout": len(holdout_manifest),
            "excluded": len(excluded_items),
            "holdout_by_repo": {repo: holdout_by_repo.get(repo, 0) for repo in quota},
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tasks", nargs="?", type=Path, default=Path("tasks.jsonl"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/evaluation/verifier-lora-split-v0.json"),
    )
    args = parser.parse_args()

    split = build_split(load_jsonl(args.tasks))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(split, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    summary = {
        "version": split["version"],
        "counts": split["counts"],
        "holdout_instance_ids": [item["instance_id"] for item in split["holdout"]],
        "output": str(args.output),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
