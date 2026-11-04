#!/usr/bin/env python3
"""Freeze paired model-evaluation IDs from predeclared, model-free eligibility only.

No task/problem/patch text, model output, GPU, or scoreboard information is read.
This does NOT certify blind provenance beyond recorded Git/document sources.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts import build_capacity_replacements_v0 as replacements
from scripts import capacity_preflight_v0 as preflight
from scripts import render_capacity_replacement_noop_v0 as noop_renderer

NOOP_METADATA = "docs/evaluation/capacity-v0-replacement-noop-2026-11-04.json"
NOOP_RUN_ID = 41817822401
EXPECTED_ROWS = 10
QUOTAS = {"feasibility": 2, "confirmation": 6}


def replacement_eligible(root: Path, metadata_path: Path | None = None) -> set[str]:
    data = json.loads((metadata_path or root / NOOP_METADATA).read_text(encoding="utf-8"))
    wanted = noop_renderer.get_gold_pass_items(root)
    if (
        data.get("version") != "capacity-v0-replacement-noop-eligibility"
        or data.get("source_run_id") != NOOP_RUN_ID
        or data.get("source_gold_run_id") != noop_renderer.GOLD_RUN
        or data.get("source_gold_artifact_id") != noop_renderer.GOLD_ARTIFACT
        or data.get("source_gold_artifact_zip_sha256") != noop_renderer.GOLD_ARTIFACT_SHA256
        or data.get("source_selector_sha256") != replacements.FROZEN_SELECTOR
        or data.get("screened") != EXPECTED_ROWS
        or data.get("contains_raw_patch_or_task_text") is not False
    ):
        raise ValueError("untrusted replacement no-op provenance/denominator")
    rows = data.get("results")
    if not isinstance(rows, list) or len(rows) != EXPECTED_ROWS:
        raise ValueError("incomplete no-op screen rows")
    if [(r.get("instance_id"), r.get("repo")) for r in rows] != [
        (w["instance_id"], w["repo"]) for w in wanted
    ]:
        raise ValueError("no-op source order or repository mismatch")
    eligible: set[str] = set()
    counts = {"noop_fail": 0, "noop_pass": 0, "ambiguous": 0}
    for row in rows:
        flags = [row.get(key) for key in counts]
        if any(type(flag) is not bool for flag in flags) or sum(flags) != 1:
            raise ValueError("no-op row status flags ambiguous or invalid")
        count_field = next(key for key in counts if row[key])
        counts[count_field] += 1
        code = row.get("test_exit_code")
        if row["noop_fail"]:
            if row.get("status") != "completed" or type(code) is not int or code == 0:
                raise ValueError("no-op-fail label conflicts with verification status")
            eligible.add(row["instance_id"])
        if row["noop_pass"] and (
            row.get("status") != "completed" or type(code) is not int or code != 0
        ):
            raise ValueError("no-op-pass label conflicts with verification status")
    if any(data.get(f"{key}_count") != val for key, val in counts.items()):
        raise ValueError("no-op aggregate flags mismatch")
    return eligible


def freeze(root: Path, metadata_path: Path | None = None) -> dict:
    plan = replacements.build_plan(root)
    control = preflight.build_feasibility_manifest(root)
    accepted_original = set(
        r["instance_id"]
        for r in json.loads((root / replacements.NOOP_METADATA).read_text(encoding="utf-8"))["results"]
    )
    if len(accepted_original) != plan["original_doubly_eligible"]:
        raise ValueError("original doubly-eligible denominator mismatch")
    fresh = replacement_eligible(root, metadata_path)
    eligible_queue = {
        repo: [item for item in plan["queues"][repo] if item in fresh]
        for repo in preflight.REPOS
    }
    rows_by_cohort = {}
    allocated: set[str] = set()
    cursors = {repo: 0 for repo in preflight.REPOS}
    original_parts = {
        "feasibility": control["feasibility_ids"],
        "confirmation": control["confirmation_reserve_ids"],
    }
    for cohort in ("feasibility", "confirmation"):
        rows = []
        for repo in preflight.REPOS:
            prefix = "rich_" if repo == "Textualize/rich" else "fastapi_"
            kept = [
                issue_id for issue_id in original_parts[cohort]
                if issue_id.startswith(prefix) and issue_id in accepted_original
            ]
            need = QUOTAS[cohort] - len(kept)
            if need != plan["missing_by_cohort"][cohort][repo]:
                raise ValueError("replacement count disagrees with frozen cohort")
            begin, end = cursors[repo], cursors[repo] + need
            taken = eligible_queue[repo][begin:end]
            if len(taken) != need:
                raise ValueError(f"insufficient doubly eligible replacements for {cohort}/{repo}")
            cursors[repo] = end
            rows += [
                {"instance_id": item, "repo": repo, "source": "original"}
                for item in kept
            ] + [
                {"instance_id": item, "repo": repo, "source": "replacement"}
                for item in taken
            ]
        count = 4 if cohort == "feasibility" else 12
        if len(rows) != count:
            raise ValueError(f"wrong {cohort} size")
        if any(row["instance_id"] in allocated for row in rows):
            raise ValueError("paired cohorts overlap")
        allocated.update(row["instance_id"] for row in rows)
        rows_by_cohort[cohort] = rows

    return {
        "version": "capacity-v0-paired-denominator-v1",
        "status": "MODEL_UNTOUCHED_METADATA_ELIGIBLE_NOT_FULLY_BLIND_CERTIFIED",
        "source_selector_sha256": replacements.FROZEN_SELECTOR,
        "replacement_noop_run_id": NOOP_RUN_ID,
        "feasibility": rows_by_cohort["feasibility"],
        "confirmation": rows_by_cohort["confirmation"],
        "totals": {
            "feasibility": 4, "confirmation": 12,
            "replacements_used": sum(
                row["source"] == "replacement"
                for group in rows_by_cohort.values() for row in group
            ),
        },
        "contains_raw_patch_or_task_text": False,
        "model_evaluation_executed": False,
        "certifies_blind": False,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, default=Path("."))
    p.add_argument("--noop", type=Path, default=None)
    p.add_argument("--out", required=True, type=Path)
    args = p.parse_args()
    result = freeze(args.repo.resolve(), args.noop)
    path = args.out.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as f:
        f.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("CAPACITY_FROZEN_METADATA_DENOMINATOR=PASS")
    print("CAPACITY_FROZEN_4_PLUS_12=PASS")
    print("CAPACITY_GPU_TRAINING_SUBMISSION_EXECUTED=NO")


if __name__ == "__main__":
    main()
