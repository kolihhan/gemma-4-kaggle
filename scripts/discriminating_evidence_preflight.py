#!/usr/bin/env python3
"""Metadata-only, no-inference preflight for discriminating-evidence v0.

Does not read tasks.jsonl, issue statements, snapshots, reference patches or traces.
No model execution, Kaggle API, GPU, training, or submission.
The resulting selection is PROVISIONAL, never a certified blind denominator.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = Path("docs/evaluation")
SOURCE_FILES = (
    "verifier-lora-split-v0.json",
    "verifier-lora-train-subset-v0.json",
    "verifier-lora-blind-reservation-v0.json",
    "verifier-lora-eval-contract-v1.json",
    "topology-ab-manifest-v1.json",
    "capacity-v0-paired-cohort-2026-11-04.json",
    "capacity-v0-gold-screen-2026-11-04.json",
    "capacity-v0-noop-screen-2026-11-04.json",
    "capacity-v0-replacement-gold-2026-11-04.json",
    "capacity-v0-replacement-noop-2026-11-04.json",
    "public-corpus-summary.md",
)
REPOS = ("Textualize/rich", "fastapi/fastapi")
NAMESPACE = "gemma4-discriminating-evidence-v0-2026-11-05"
PILOT_PER_REPO = 2
CONFIRMATION_PER_REPO = 12
# A feasibility-only gate: unselected candidates must remain for gold/no-op
# ineligibility and historical exposure replacements before ANY model run.
MIN_REPLACEMENTS_PER_REPO = 4


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_metadata(root: Path) -> tuple[dict[str, dict], str, dict[str, str]]:
    sources: dict[str, dict] = {}
    sha: dict[str, str] = {}
    summary = ""
    for name in SOURCE_FILES:
        path = root / SOURCE_DIR / name
        raw = path.read_bytes()  # fails closed if any provenance source is absent
        sha[name] = digest(raw)
        if name.endswith(".md"):
            summary = raw.decode("utf-8")
        else:
            sources[name] = json.loads(raw.decode("utf-8"))
    return sources, summary, sha


def build_preflight(root: Path) -> dict:
    docs, summary, source_sha = load_metadata(root)
    split = docs["verifier-lora-split-v0.json"]
    if split["counts"]["total_input"] != 129 or split["counts"]["train"] != 90:
        raise ValueError("unexpected corpus/split: manually review before selection")
    train = split["train"]
    train_ids = [str(item["instance_id"]) for item in train]
    if len(train_ids) != 90 or len(set(train_ids)) != 90:
        raise ValueError("train metadata does not contain 90 unique IDs")
    if any(item.get("repo") not in REPOS + ("psf/requests",) for item in train):
        raise ValueError("unexpected repository in train metadata")

    used: set[str] = set()
    for key in ("excluded", "holdout"):
        used.update(str(item["instance_id"]) for item in split[key])
    for key in ("verifier-lora-train-subset-v0.json",
                "verifier-lora-blind-reservation-v0.json"):
        used.update(str(item["instance_id"]) for item in docs[key]["tasks"])
    topology = docs["topology-ab-manifest-v1.json"]
    used.update(str(item["instance_id"]) for item in topology["holdout"])
    used.update(str(item) for item in topology["noop_screen"]["excluded_noop_pass"])
    evaluation = docs["verifier-lora-eval-contract-v1.json"]
    for key in ("development_validation", "blind_evaluation"):
        used.update(str(item) for item in evaluation[key]["instance_ids"])
    capacity = docs["capacity-v0-paired-cohort-2026-11-04.json"]
    if capacity.get("certifies_blind") is not False:
        raise ValueError("capacity metadata semantics changed")
    if len(capacity["feasibility"]) != 4 or len(capacity["confirmation"]) != 12:
        raise ValueError("capacity 4+12 reserved denominator changed")
    for key in ("feasibility", "confirmation"):
        used.update(str(item["instance_id"]) for item in capacity[key])
    for key in (
        "capacity-v0-gold-screen-2026-11-04.json",
        "capacity-v0-noop-screen-2026-11-04.json",
        "capacity-v0-replacement-gold-2026-11-04.json",
        "capacity-v0-replacement-noop-2026-11-04.json",
    ):
        used.update(str(item["instance_id"]) for item in docs[key]["results"])
    used.update(re.findall(r"\b(?:rich|fastapi|requests|httpx)_\d+\b", summary))

    pools: dict[str, list[str]] = {}
    for repo in REPOS:
        pool = [
            str(item["instance_id"])
            for item in train
            if item["repo"] == repo and str(item["instance_id"]) not in used
        ]
        pool.sort(key=lambda i: (digest(f"{NAMESPACE}:{i}".encode()), i))
        if len(pool) != len(set(pool)):
            raise ValueError(f"duplicate candidates in {repo}")
        pools[repo] = pool

    requested = PILOT_PER_REPO + CONFIRMATION_PER_REPO
    if any(len(pools[repo]) < requested for repo in REPOS):
        selection_status = "NO_GO_INSUFFICIENT_CANDIDATES"
    elif any(len(pools[repo]) - requested < MIN_REPLACEMENTS_PER_REPO for repo in REPOS):
        selection_status = "NO_GO_INADEQUATE_REPLACEMENT_BUFFER"
    else:
        selection_status = "NO_GO_HISTORY_AND_ELIGIBILITY_UNCHECKED"

    pilot = [i for repo in REPOS for i in pools[repo][:PILOT_PER_REPO]]
    confirmation = [
        i for repo in REPOS
        for i in pools[repo][PILOT_PER_REPO:requested]
    ]
    replacements = [i for repo in REPOS for i in pools[repo][requested:]]
    if set(pilot) & set(confirmation) or set(pilot + confirmation) & used:
        raise ValueError("selected candidate overlaps prior records")
    if len(set(pilot + confirmation + replacements)) != len(pilot + confirmation + replacements):
        raise ValueError("duplicate provisional selection")

    proposal = {
        "version": "discriminating-evidence-v0-preflight",
        "base_ref": "exp/capacity-boundary-v0",
        "selector": NAMESPACE,
        "source_sha256": source_sha,
        "candidate_counts": {repo: len(pools[repo]) for repo in REPOS},
        "replacement_counts": {
            repo: max(0, len(pools[repo]) - requested) for repo in REPOS
        },
        "pilot_ids": pilot,
        "confirmation_ids": confirmation,
        "replacement_ids": replacements,
        "known_exposure_count": len(used),
    }
    fingerprint = digest(json.dumps(proposal, sort_keys=True, separators=(",", ":")).encode())
    return {
        **proposal,
        "selection_fingerprint_sha256": fingerprint,
        "status": selection_status,
        "certifies_blind": False,
        "gold_noop_eligible": False,
        "history_audit_complete": False,
        "model_evaluation_executed": False,
        "GPU_or_Kaggle_submission_authorized": False,
        "limits": (
            "Metadata-only potential candidates; historical source/artifact exposure, "
            "gold-pass/no-op-fail controls, independent holdout cleanliness, "
            "and scorer/runtime support remain unverified."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=ROOT)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--strict", action="store_true",
                        help="return exit code 2 for any NO_GO status")
    args = parser.parse_args()
    result = build_preflight(args.repo.resolve())
    if args.out is not None:
        target = args.out.resolve()
        if target.exists():
            raise ValueError("refusing to overwrite preflight artifact")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                          encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "candidate_counts": result["candidate_counts"],
        "replacement_counts": result["replacement_counts"],
        "pilot_count": len(result["pilot_ids"]),
        "confirmation_count": len(result["confirmation_ids"]),
        "certifies_blind": False,
        "selection_fingerprint_sha256": result["selection_fingerprint_sha256"],
        "no_model_run": True,
    }, sort_keys=True))
    return 2 if args.strict and result["status"].startswith("NO_GO") else 0


if __name__ == "__main__":
    raise SystemExit(main())
