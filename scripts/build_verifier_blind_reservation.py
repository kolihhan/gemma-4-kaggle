#!/usr/bin/env python3
"""Reserve and replace verifier-LoRA blind candidates from metadata only."""

from __future__ import annotations

import argparse
import copy
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


def _clean_item(item: dict) -> dict[str, str]:
    return {
        "instance_id": str(item["instance_id"]),
        "repo": str(item["repo"]),
        "patch_bucket": str(item["patch_bucket"]),
    }


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

    selected = [_clean_item(item) for item in selected]
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


def _historical_blind_ids(reservation: dict) -> set[str]:
    ids = {
        str(item.get("instance_id") or "")
        for item in reservation.get("tasks") or []
        if isinstance(item, dict) and str(item.get("instance_id") or "")
    }
    selection = reservation.get("selection") or {}
    rounds = selection.get("gold_control_replacement_rounds") or []
    if not isinstance(rounds, list):
        raise ValueError("blind replacement history must be a list")
    for round_item in rounds:
        if not isinstance(round_item, dict):
            raise ValueError("blind replacement round must be an object")
        replacements = round_item.get("replacements") or []
        if not isinstance(replacements, list):
            raise ValueError("blind replacement entries must be a list")
        for replacement in replacements:
            if not isinstance(replacement, dict):
                raise ValueError("blind replacement entry must be an object")
            for key in ("from", "to"):
                value = str(replacement.get(key) or "")
                if value:
                    ids.add(value)
    return ids


def replace_confounded_blind(
    reservation: dict,
    split: dict,
    training_subset: dict,
    confounded_ids: set[str],
    *,
    allow_same_repo_fallback: bool = False,
) -> dict:
    """Replace gold-confounded blind slots without consulting task content.

    By default a replacement must come from the same repository and patch-size
    bucket. If that exact bucket is exhausted, callers may *explicitly* enable a
    deterministic same-repository fallback. Harvested tasks, current blind IDs,
    and every historical blind ID are permanently ineligible.
    """
    if reservation.get("version") != VERSION:
        raise ValueError(f"unexpected blind reservation version: {reservation.get('version')!r}")
    if split.get("version") != "verifier-lora-v0":
        raise ValueError(f"unexpected split version: {split.get('version')!r}")
    if training_subset.get("version") != "verifier-lora-v0-train-harvest":
        raise ValueError(f"unexpected training subset version: {training_subset.get('version')!r}")

    current = list(reservation.get("tasks") or [])
    train = list(split.get("train") or [])
    harvested = list(training_subset.get("tasks") or [])
    for item in current:
        _validate_item(item, where="reservation.tasks")
    for item in train:
        _validate_item(item, where="split.train")
    for item in harvested:
        _validate_item(item, where="training_subset.tasks")

    confounded = {str(value) for value in confounded_ids if str(value)}
    if not confounded:
        return copy.deepcopy(reservation)
    current_by_id = {str(item["instance_id"]): item for item in current}
    missing = sorted(confounded - set(current_by_id))
    if missing:
        raise ValueError(f"confounded id(s) are not in current blind reservation: {missing}")

    harvested_ids = {str(item["instance_id"]) for item in harvested}
    blocked_ids = _historical_blind_ids(reservation) | harvested_ids
    pool = [
        item
        for item in train
        if str(item["instance_id"]) not in blocked_ids
    ]

    result = copy.deepcopy(reservation)
    tasks = list(result.get("tasks") or [])
    replacement_log: list[dict[str, str]] = []

    for failed_id in sorted(confounded, key=lambda value: _manifest_sort_key(current_by_id[value])):
        failed = current_by_id[failed_id]
        repo = str(failed["repo"])
        bucket = str(failed["patch_bucket"])
        candidates = [
            item
            for item in pool
            if str(item["repo"]) == repo and str(item["patch_bucket"]) == bucket
        ]
        selection_scope = "same_repo_same_bucket"
        if not candidates and allow_same_repo_fallback:
            candidates = [item for item in pool if str(item["repo"]) == repo]
            selection_scope = "same_repo_fallback"
        if not candidates:
            raise ValueError(
                f"no same repo/bucket blind replacement candidate for {failed_id}: {repo} / {bucket}"
            )

        replacement = min(candidates, key=lambda item: _stable_key(str(item["instance_id"])))
        replacement = _clean_item(replacement)
        replacement_id = replacement["instance_id"]
        pool = [item for item in pool if str(item["instance_id"]) != replacement_id]
        blocked_ids.add(replacement_id)
        tasks = [item for item in tasks if str(item["instance_id"]) != failed_id]
        tasks.append(replacement)
        replacement_log.append(
            {
                "from": failed_id,
                "to": replacement_id,
                "repo": repo,
                "selection_scope": selection_scope,
                "from_patch_bucket": bucket,
                "to_patch_bucket": replacement["patch_bucket"],
            }
        )

    tasks.sort(key=_manifest_sort_key)
    task_ids = [str(item["instance_id"]) for item in tasks]
    if len(task_ids) != len(set(task_ids)):
        raise ValueError("replacement produced duplicate blind task IDs")

    original_counts = copy.deepcopy(reservation.get("counts") or {})
    expected_tasks = int(original_counts.get("tasks") or len(current))
    if len(tasks) != expected_tasks:
        raise ValueError(
            f"replacement changed blind denominator size: {len(tasks)} != {expected_tasks}"
        )
    original_repo_counts = Counter(str(item["repo"]) for item in current)
    new_repo_counts = Counter(str(item["repo"]) for item in tasks)
    if original_repo_counts != new_repo_counts:
        raise ValueError("replacement changed blind repository quotas")

    selection = copy.deepcopy(result.get("selection") or {})
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
    result["selection"] = selection
    result["tasks"] = tasks
    result["counts"] = original_counts
    return result


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
        "--input-reservation",
        type=Path,
        help="existing blind reservation to update after automated gold-control screening",
    )
    parser.add_argument("--replace-confounded", nargs="*", default=[])
    parser.add_argument(
        "--allow-same-repo-fallback",
        action="store_true",
        help="when the exact patch bucket is exhausted, allow a deterministic same-repo replacement",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/evaluation/verifier-lora-blind-reservation-v0.json"),
    )
    args = parser.parse_args()

    split = json.loads(args.split.read_text(encoding="utf-8"))
    training_subset = json.loads(args.training_subset.read_text(encoding="utf-8"))
    if args.input_reservation is not None:
        if not args.replace_confounded:
            parser.error("--input-reservation requires one or more --replace-confounded IDs")
        reservation = json.loads(args.input_reservation.read_text(encoding="utf-8"))
        reservation = replace_confounded_blind(
            reservation,
            split,
            training_subset,
            set(args.replace_confounded),
            allow_same_repo_fallback=args.allow_same_repo_fallback,
        )
    else:
        if args.replace_confounded:
            parser.error("--replace-confounded requires --input-reservation")
        if args.allow_same_repo_fallback:
            parser.error("--allow-same-repo-fallback requires --input-reservation")
        reservation = build_blind_reservation(split, training_subset)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(reservation, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(reservation, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
