#!/usr/bin/env python3
"""Freeze the smaller, pre-outcome 4+12 exploratory task denominator.

Does NOT inspect task text or raw traces and DOES NOT make the set eligible,
blind-certified, inference-ready or Kaggle-submission-ready.
The existing 4+24 ranking is reused rather than resampled.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from scripts.discriminating_evidence_preflight import (
    ROOT,
    build_preflight,
)

PILOT_PER_REPO = 2
EXPLORATORY_PER_REPO = 6
MIN_REPLACEMENTS_PER_REPO = 4


def build_exploratory(root: Path) -> dict:
    parent = build_preflight(root)
    if parent["version"] != "discriminating-evidence-v0-preflight":
        raise ValueError("parent selector version changed")
    if parent["selector"] != "gemma4-discriminating-evidence-v0-2026-11-05":
        raise ValueError("parent deterministic selector namespace changed")
    if parent["candidate_counts"] != {"Textualize/rich": 14, "fastapi/fastapi": 16}:
        raise ValueError("provenance/pool drift; do not silently resample")
    if len(parent["pilot_ids"]) != 4 or len(parent["confirmation_ids"]) != 24:
        raise ValueError("parent 4+24 planned cohort drift")
    if len(parent["replacement_ids"]) != 2:
        raise ValueError("parent replacement list changed")
    # Parent confirmation is ordered Rich(12), FastAPI(12).
    rich = parent["confirmation_ids"][:12]
    fastapi = parent["confirmation_ids"][12:]
    if len(rich) != 12 or len(fastapi) != 12:
        raise ValueError("parent confirmation per-repo size drift")

    pilot = list(parent["pilot_ids"])
    exploratory = rich[:EXPLORATORY_PER_REPO] + fastapi[:EXPLORATORY_PER_REPO]
    replacements = (
        rich[EXPLORATORY_PER_REPO:]
        + fastapi[EXPLORATORY_PER_REPO:]
        + list(parent["replacement_ids"])
    )
    if len(pilot) != 2 * PILOT_PER_REPO:
        raise ValueError("incorrect pilot size")
    all_ids = pilot + exploratory + replacements
    if len(all_ids) != 30 or len(set(all_ids)) != 30:
        raise ValueError("provisional denominator duplicated/lost candidates")

    replacements_per_repo = {
        "Textualize/rich": len(rich) - EXPLORATORY_PER_REPO,
        "fastapi/fastapi": len(fastapi) - EXPLORATORY_PER_REPO
                           + len(parent["replacement_ids"]),
    }
    if any(n < MIN_REPLACEMENTS_PER_REPO for n in replacements_per_repo.values()):
        status = "NO_GO_INADEQUATE_REPLACEMENT_BUFFER"
    else:
        status = "NO_GO_HISTORY_AND_ELIGIBILITY_UNCHECKED"

    manifest = {
        "version": "discriminating-evidence-v0-exploratory-4plus12",
        "parent_selection_fingerprint_sha256": parent["selection_fingerprint_sha256"],
        "source_sha256": parent["source_sha256"],
        "candidate_counts": parent["candidate_counts"],
        "replacement_counts": replacements_per_repo,
        "pilot_ids": pilot,
        "exploratory_ids": exploratory,
        "replacement_ids": replacements,
    }
    selection_digest = hashlib.sha256(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return {
        **manifest,
        "selection_digest_sha256": selection_digest,
        "status": status,
        "certifies_blind": False,
        "gold_noop_eligible": False,
        "history_audit_complete": False,
        "model_evaluation_executed": False,
        "gpu_or_submission_authorized": False,
        "interpretation": (
            "Only a small exploratory denominator; independent replicated "
            "confirmation is required before any model quality claim."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=ROOT)
    parser.add_argument("--out", type=Path, help="refuse to overwrite any existing artifact")
    args = parser.parse_args()
    r = build_exploratory(args.repo.resolve())
    if args.out:
        dest = args.out.resolve()
        if dest.exists():
            raise ValueError("refuse overwrite of frozen exploratory record")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(r, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(r, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
