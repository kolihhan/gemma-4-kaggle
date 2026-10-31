#!/usr/bin/env python3
"""Build and maintain a deterministic leakage-safe verifier LoRA v0 split."""

from __future__ import annotations

import argparse
import copy
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


def _bucket_sort_key(bucket: str) -> int:
    try:
        return PATCH_BUCKET_ORDER.index(bucket)
    except ValueError:
        return len(PATCH_BUCKET_ORDER)


def _manifest_sort_key(item: dict) -> tuple[str, int, str]:
    return (
        str(item.get("repo") or ""),
        _bucket_sort_key(str(item.get("patch_bucket") or "")),
        str(item.get("instance_id") or ""),
    )


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


def _validate_manifest_item(item: dict, *, where: str) -> None:
    if not isinstance(item, dict):
        raise ValueError(f"{where} item must be an object")
    for key in ("instance_id", "repo", "patch_bucket"):
        if not str(item.get(key) or ""):
            raise ValueError(f"{where} item missing {key}: {item!r}")


def replace_confounded_holdout(
    split: dict,
    confounded_ids: set[str],
    *,
    allow_same_repo_fallback: bool = False,
) -> dict:
    """Replace failed gold-control holdout slots from the current train pool.

    The default remains strict: each replacement must match the failed task's
    repository and patch-size bucket. When ``allow_same_repo_fallback`` is
    explicitly enabled, an exhausted exact bucket may fall back to the stable
    SHA-256 minimum from the same repository only. Failed holdout tasks move
    permanently to ``excluded`` and never re-enter training.
    """
    if split.get("version") != VERSION:
        raise ValueError(f"unexpected split version: {split.get('version')!r}")
    confounded = {str(value) for value in confounded_ids if str(value)}
    if not confounded:
        return copy.deepcopy(split)

    result = copy.deepcopy(split)
    holdout = list(result.get("holdout") or [])
    train = list(result.get("train") or [])
    excluded = list(result.get("excluded") or [])
    for item in holdout:
        _validate_manifest_item(item, where="holdout")
    for item in train:
        _validate_manifest_item(item, where="train")
    for item in excluded:
        _validate_manifest_item(item, where="excluded")

    holdout_by_id = {str(item["instance_id"]): item for item in holdout}
    missing = sorted(confounded - set(holdout_by_id))
    if missing:
        raise ValueError(f"confounded id(s) are not in current holdout: {missing}")

    replacement_log: list[dict[str, str]] = []
    for failed_id in sorted(confounded, key=lambda value: _manifest_sort_key(holdout_by_id[value])):
        failed = holdout_by_id[failed_id]
        repo = str(failed["repo"])
        bucket = str(failed["patch_bucket"])
        candidates = [
            item
            for item in train
            if str(item.get("repo")) == repo and str(item.get("patch_bucket")) == bucket
        ]
        selection_scope = "same_repo_same_bucket"
        if not candidates and allow_same_repo_fallback:
            candidates = [item for item in train if str(item.get("repo")) == repo]
            selection_scope = "same_repo_fallback"
        if not candidates:
            raise ValueError(
                f"no same repo/bucket replacement candidate for {failed_id}: {repo} / {bucket}"
            )
        replacement = min(candidates, key=lambda item: _stable_key(str(item["instance_id"])))
        replacement_id = str(replacement["instance_id"])
        replacement_bucket = str(replacement["patch_bucket"])

        train = [item for item in train if str(item.get("instance_id")) != replacement_id]
        holdout = [item for item in holdout if str(item.get("instance_id")) != failed_id]
        holdout.append(copy.deepcopy(replacement))
        excluded.append({**copy.deepcopy(failed), "reason": "gold_control_confounded"})
        replacement_log.append(
            {
                "from": failed_id,
                "to": replacement_id,
                "repo": repo,
                "selection_scope": selection_scope,
                "from_patch_bucket": bucket,
                "to_patch_bucket": replacement_bucket,
            }
        )

    holdout.sort(key=_manifest_sort_key)
    train.sort(key=_manifest_sort_key)
    excluded.sort(key=_manifest_sort_key)

    holdout_repo_counts = Counter(str(item["repo"]) for item in holdout)
    total_input = int((result.get("counts") or {}).get("total_input") or (len(holdout) + len(train) + len(excluded)))
    selection = dict(result.get("selection") or {})
    rounds = list(selection.get("gold_control_replacement_rounds") or [])
    rounds.append(
        {
            "round": len(rounds) + 1,
            "reason": "gold_control_confounded",
            "same_repo_fallback_allowed": bool(allow_same_repo_fallback),
            "replacements": replacement_log,
        }
    )
    selection["gold_control_replacement_rounds"] = rounds

    result.update(
        {
            "selection": selection,
            "holdout": holdout,
            "train": train,
            "excluded": excluded,
            "counts": {
                "total_input": total_input,
                "train": len(train),
                "holdout": len(holdout),
                "excluded": len(excluded),
                "holdout_by_repo": dict(sorted(holdout_repo_counts.items())),
            },
        }
    )
    return result


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
    holdout_manifest.sort(key=_manifest_sort_key)
    train_manifest = [_manifest_item(task) for task in train_tasks]
    train_manifest.sort(key=_manifest_sort_key)
    excluded_items.sort(key=_manifest_sort_key)

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
    parser.add_argument("--input-manifest", type=Path)
    parser.add_argument("--replace-confounded", nargs="*", default=[])
    parser.add_argument(
        "--allow-same-repo-fallback",
        action="store_true",
        help="allow exhausted exact buckets to fall back to a deterministic candidate from the same repo",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/evaluation/verifier-lora-split-v0.json"),
    )
    args = parser.parse_args()

    if args.input_manifest is not None:
        if not args.replace_confounded:
            parser.error("--input-manifest requires one or more --replace-confounded IDs")
        split = json.loads(args.input_manifest.read_text(encoding="utf-8"))
        split = replace_confounded_holdout(
            split,
            set(args.replace_confounded),
            allow_same_repo_fallback=args.allow_same_repo_fallback,
        )
    else:
        if args.replace_confounded:
            parser.error("--replace-confounded requires --input-manifest")
        if args.allow_same_repo_fallback:
            parser.error("--allow-same-repo-fallback requires --input-manifest and --replace-confounded")
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
