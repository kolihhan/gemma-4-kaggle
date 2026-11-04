#!/usr/bin/env python3
"""Freeze a SHA-ranked metadata-only replacement queue for capacity-v0.

Does not run models, inspect issue statements/patches, alter the frozen
4+12 denominator, or pronounce candidate IDs historically blind.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

# Also support `python scripts/build_capacity_replacements_v0.py --out ...`.
import sys
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import capacity_preflight_v0 as preflight


FROZEN_SELECTOR = "4abe73d79afcabd64795e7f2eedde5682732a85290f07a09e3f8a181594fd593"
GOLD_METADATA = "docs/evaluation/capacity-v0-gold-screen-2026-11-04.json"
NOOP_METADATA = "docs/evaluation/capacity-v0-noop-screen-2026-11-04.json"
REPOS = preflight.REPOS
NAMESPACE = preflight.SELECTION_NAMESPACE


def read_noop(root: Path) -> dict:
    return json.loads((root / NOOP_METADATA).read_text(encoding="utf-8"))


def _known_exposures(root: Path, split: dict) -> set[str]:
    """Mirror the original capacity selector's exclusions and cross-check its top 8."""
    other = {
        rel: json.loads((root / rel).read_text(encoding="utf-8"))
        for rel in preflight.EXPOSURE_FILES[1:5]
    }
    exposed = {
        str(row["instance_id"])
        for role in ("excluded", "holdout")
        for row in split[role]
    }
    for rel in preflight.EXPOSURE_FILES[1:3]:
        exposed.update(str(row["instance_id"]) for row in other[rel]["tasks"])
    topology = other[preflight.EXPOSURE_FILES[4]]
    exposed.update(str(row["instance_id"]) for row in topology["holdout"])
    exposed.update(str(value) for value in topology["noop_screen"]["excluded_noop_pass"])
    contract = other[preflight.EXPOSURE_FILES[3]]
    exposed.update(str(value) for value in contract["development_validation"]["instance_ids"])
    exposed.update(str(value) for value in contract["blind_evaluation"]["instance_ids"])
    public_summary = (root / preflight.EXPOSURE_FILES[5]).read_text(encoding="utf-8")
    exposed.update(re.findall(r"(?m)^-\s+`([a-z]+_\d+)`", public_summary))
    if len(exposed) < 35:
        raise ValueError("frozen exposure provenance implausibly incomplete")
    return exposed


def _ranked_candidates(root: Path, original: dict) -> dict[str, list[str]]:
    split = json.loads((root / preflight.EXPOSURE_FILES[0]).read_text(encoding="utf-8"))
    if split["counts"]["train"] != 90 or len(split["train"]) != 90:
        raise ValueError("training-side metadata changed")
    exposed = _known_exposures(root, split)
    ranked = {}
    for repo in REPOS:
        candidates = [
            str(row["instance_id"])
            for row in split["train"]
            if row["repo"] == repo and row["instance_id"] not in exposed
        ]
        candidates.sort(
            key=lambda issue_id: (
                hashlib.sha256(f"{NAMESPACE}:{issue_id}".encode()).hexdigest(), issue_id
            )
        )
        # An exact prefix match proves this independently reconstructed pool
        # preserves the preregistered selector, rather than silently reseeding.
        expected_prefix = [
            x for x in original["feasibility_ids"] if x.startswith("rich_" if repo == REPOS[0] else "fastapi_")
        ] + [
            x for x in original["confirmation_reserve_ids"] if x.startswith("rich_" if repo == REPOS[0] else "fastapi_")
        ]
        if len(expected_prefix) != 8 or candidates[:8] != expected_prefix:
            raise ValueError(f"ranked source metadata disagrees with frozen selector: {repo}")
        if len(candidates) != len(set(candidates)):
            raise ValueError(f"duplicate candidates in {repo}")
        ranked[repo] = candidates[8:]
    return ranked


def build_plan(root: Path) -> dict:
    original = preflight.build_feasibility_manifest(root)
    if original["selection_digest_sha256"] != FROZEN_SELECTOR:
        raise ValueError("frozen initial capacity selection drift")
    original_ids = original["feasibility_ids"] + original["confirmation_reserve_ids"]
    if len(original_ids) != 16 or len(set(original_ids)) != 16:
        raise ValueError("frozen capacity task count/uniqueness drift")

    gold = json.loads((root / GOLD_METADATA).read_text(encoding="utf-8"))
    if (
        gold.get("source_selector_sha256") != FROZEN_SELECTOR
        or gold.get("source_run_id") != 41782992381
        or gold.get("gold_pass_count") != 10
        or gold.get("screened") != 16
    ):
        raise ValueError("unrecognized gold-screen provenance/denominator")
    g_rows = gold.get("results", [])
    if [r.get("instance_id") for r in g_rows] != original_ids:
        raise ValueError("gold metadata changed frozen selection/order")
    g_by_id = {row["instance_id"]: row for row in g_rows}
    if any(
        row.get("gold_pass") is not (row.get("test_exit_code") == 0)
        for row in g_rows
    ):
        raise ValueError("inconsistent gold control records")
    positive_ids = [row["instance_id"] for row in g_rows if row["gold_pass"]]
    if len(positive_ids) != 10:
        raise ValueError("unexpected number of gold-clean candidates")

    noop = read_noop(root)
    if (
        noop.get("version") != "capacity-v0-noop-eligibility"
        or noop.get("source_artifact_id") != 13300818683
        or noop.get("source_gold_action") != 41782992381
        or noop.get("selector_sha256") != FROZEN_SELECTOR
        or noop.get("screened") != 10
        or noop.get("noop_fail_count") != 10
    ):
        raise ValueError("unrecognized no-op provenance/denominator")
    n_rows = noop.get("results", [])
    if [row.get("instance_id") for row in n_rows] != positive_ids:
        raise ValueError("no-op ID list differs from gold-pass subset")
    if any(
        row.get("noop_fail") is not True
        or row.get("status") != "completed"
        or not isinstance(row.get("test_exit_code"), int)
        or isinstance(row.get("test_exit_code"), bool)
        or row["test_exit_code"] == 0
        or row.get("repo") != g_by_id[row["instance_id"]]["repo"]
        for row in n_rows
    ):
        raise ValueError("inconsistent no-op failure control")

    known_eligible = set(positive_ids)
    split = json.loads((root / preflight.EXPOSURE_FILES[0]).read_text(encoding="utf-8"))
    id_repo = {str(row["instance_id"]): str(row["repo"]) for row in split["train"]}
    if any(x not in id_repo for x in original_ids):
        raise ValueError("original ID missing in source train metadata")

    missing = {}
    for cohort, ids, per_repo_quota in (
        ("feasibility", original["feasibility_ids"], 2),
        ("confirmation", original["confirmation_reserve_ids"], 6),
    ):
        missing[cohort] = {}
        for repo in REPOS:
            cohort_ids = [x for x in ids if id_repo[x] == repo]
            if len(cohort_ids) != per_repo_quota:
                raise ValueError(f"frozen cohort allocation changed: {cohort}/{repo}")
            missing[cohort][repo] = per_repo_quota - sum(x in known_eligible for x in cohort_ids)
    total_slots = sum(sum(d.values()) for d in missing.values())
    if total_slots != 6:
        raise ValueError(f"unexpected capacity replacement slot count: {total_slots}")

    queues = _ranked_candidates(root, original)
    for repo in REPOS:
        needed = missing["feasibility"][repo] + missing["confirmation"][repo]
        if len(queues[repo]) < needed:
            raise ValueError(f"insufficient replacement candidate metadata for {repo}")
        if set(queues[repo]) & set(original_ids):
            raise ValueError("replacement queue intersects original sixteen")
    queue_ids = [x for queue in queues.values() for x in queue]
    if len(queue_ids) != len(set(queue_ids)):
        raise ValueError("replacement queue has overlapping candidates")

    return {
        "version": "capacity-v0-replacement-queue-v1",
        "status": "FROZEN_ORDER_UNSCREENED_NOT_BLIND_CERTIFIED",
        "source_selector_sha256": FROZEN_SELECTOR,
        "source_gold_run_id": 41782992381,
        "source_noop_run_id": 41786342489,
        "source_noop_artifact_id": 13300818683,
        "original_ids": original_ids,
        "original_screened": 16,
        "original_doubly_eligible": len(known_eligible),
        "missing_by_cohort": missing,
        "replacement_slots_total": total_slots,
        "queues": queues,
        "contains_task_text": False,
        "eligibility_gate": "Before model inference, historical-source provenance and private CPU gold-pass + no-op-fail screening; queue entries are NOT yet eligible.",
        "quota_gate": "31B Kaggle GPU quota blocked; do not schedule GPU automatically.",
    }


def write_plan(plan: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(plan, indent=2, sort_keys=True) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = build_plan(args.repo.resolve())
    write_plan(result, args.out)
    print("CAPACITY_REPLACEMENTS_STATUS=", result["status"])
    print("CAPACITY_REPLACEMENTS_SLOTS=", result["replacement_slots_total"])
    print("CAPACITY_REPLACEMENTS_QUEUE_SIZES=", {k: len(v) for k, v in result["queues"].items()})
    print("CAPACITY_REPLACEMENTS_GPU=NONE")


if __name__ == "__main__":
    main()
