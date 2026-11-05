#!/usr/bin/env python3
"""Metadata-ID-only historical exposure audit for frozen 4+12 exploratory cohort.

This walks preselection source Git history; it does not open raw competition
tasks, patches, test logs, model traces or private Kaggle resources.
Historical Git scan CANNOT certify fully blind evaluation.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts import audit_capacity_history_v0 as previous
from scripts.discriminating_evidence_exploratory import ROOT, build_exploratory

# Before first 4+24 selection script commit: 2026-11-05 15:59:39Z.
# Do NOT use current time: that would incorrectly flag our own frozen IDs.
CUTOFF_UTC = "2026-11-05T15:59:38Z"


def audit(root: Path) -> dict:
    cohort = build_exploratory(root)
    ids = cohort["pilot_ids"] + cohort["exploratory_ids"] + cohort["replacement_ids"]
    if len(ids) != 30 or len(set(ids)) != 30:
        raise ValueError("bad frozen cohort")
    previous.PRESELECTION_CUTOFF = CUTOFF_UTC
    history = previous.scan_history(root, ids)
    if history["candidate_count"] != 30 or history["cutoff_utc"] != CUTOFF_UTC:
        raise ValueError("historical audit contract drift")
    return {
        **history,
        "version": "discriminating-evidence-v0-preselection-git-history-audit",
        "source_selector_sha256": cohort["selection_digest_sha256"],
        "status": (
            "NO_GO_TRACKED_HISTORICAL_EXPOSURE"
            if history["historical_exposed_ids"]
            else "HISTORY_ONLY_CLEAR_OTHER_EXPOSURE_UNKNOWN"
        ),
        "certifies_blind": False,
        "gold_noop_eligible": False,
        "model_evaluation_executed": False,
        "notes": (
            "Tracked source Git history only, not prior GitHub artifacts, "
            "unrecorded viewing, Kaggle kernels/results or task semantic overlap."
        ),
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, default=ROOT)
    p.add_argument("--out", type=Path)
    args = p.parse_args()
    result = audit(args.repo.resolve())
    if args.out:
        path = args.out.resolve()
        if path.exists():
            raise ValueError("refusing to overwrite historical audit")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "candidate_count": result["candidate_count"],
        "history_checked_revisions": result["checked_revisions"],
        "checked_branch_refs": result["checked_branch_refs"],
        "historical_exposed_ids": result["historical_exposed_ids"],
        "certifies_blind": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
