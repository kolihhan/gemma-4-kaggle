#!/usr/bin/env python3
"""Assemble a preregistered 4+12 exploratory cohort from sanitized CPU flags.

NO model execution. Uses only pinned gold-pass/no-op-fail metadata. A candidate
never replaces another based on issue text, patch size, model output or score.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from scripts.discriminating_evidence_exploratory import ROOT, build_exploratory

GOLD_RUN = 42066105011
NOOP_RUN = 42067120930
GOLD_VERSION = "discriminating-evidence-v0-exploratory-gold-screen"
NOOP_VERSION = "discriminating-evidence-v0-exploratory-noop-screen"
REPOS = ("Textualize/rich", "fastapi/fastapi")


def read_flags(source: Path, expected_version: str, expected_count: int | None) -> dict:
    raw = source.read_bytes()
    result = json.loads(raw)
    if result.get("version") != expected_version:
        raise ValueError("incorrect gold/no-op provenance version")
    if (result.get("contains_raw_patch_or_task_text") is not False or
        result.get("certifies_blind") is not False or
        result.get("model_evaluation_executed") is not False):
        raise ValueError("unsafe/unrecognized sanitized source")
    rows = result.get("results")
    if not isinstance(rows, list) or result.get("screened") != len(rows):
        raise ValueError("missing or uncounted source records")
    if expected_count is not None and len(rows) != expected_count:
        raise ValueError("source size differs from frozen cohort")
    ids = [r.get("instance_id") for r in rows]
    if any(not isinstance(x, str) for x in ids) or len(set(ids)) != len(ids):
        raise ValueError("missing or duplicated source task IDs")
    result["_safe_input_sha256"] = hashlib.sha256(raw).hexdigest()
    return result


def build_ready(root: Path, gold_path: Path, noop_path: Path) -> dict:
    original = build_exploratory(root)
    source_sha = original["selection_digest_sha256"]
    gold = read_flags(gold_path, GOLD_VERSION, 30)
    if (gold.get("source_run_id") != GOLD_RUN or
        gold.get("source_selector_sha256") != source_sha):
        raise ValueError("gold metadata source run/selector mismatch")
    frozen = (original["pilot_ids"] + original["exploratory_ids"]
              + original["replacement_ids"])
    if [x["instance_id"] for x in gold["results"]] != frozen:
        raise ValueError("gold IDs/order drift")
    gold_ids = []
    for row in gold["results"]:
        iid = row["instance_id"]
        repo = "Textualize/rich" if iid.startswith("rich_") else "fastapi/fastapi"
        if row.get("repo") != repo or row.get("gold_pass") not in (True, False):
            raise ValueError("malformed gold safe flags")
        if row["gold_pass"]:
            if row.get("test_exit_code") != 0 or row.get("status") != "completed":
                raise ValueError("gold_pass inconsistent with exit code")
            gold_ids.append(iid)
    if len(gold_ids) != gold.get("gold_pass_count"):
        raise ValueError("gold pass count mismatch")

    noop = read_flags(noop_path, NOOP_VERSION, len(gold_ids))
    if (noop.get("source_gold_action_run_id") != GOLD_RUN or
        noop.get("source_noop_action_run_id") != NOOP_RUN or
        noop.get("source_selector_sha256") != source_sha):
        raise ValueError("no-op source run/selector mismatch")
    if [row["instance_id"] for row in noop["results"]] != gold_ids:
        raise ValueError("no-op must cover every gold-passing task in source order")

    eligible: set[str] = set()
    for row in noop["results"]:
        iid = row["instance_id"]
        repo = "Textualize/rich" if iid.startswith("rich_") else "fastapi/fastapi"
        if row.get("repo") != repo or row.get("noop_fail") not in (True, False):
            raise ValueError("malformed no-op safe flags")
        if row["noop_fail"]:
            code = row.get("test_exit_code")
            if row.get("status") != "completed" or type(code) is not int or code == 0:
                raise ValueError("no-op-fail inconsistent with exit code")
            eligible.add(iid)
    if len(eligible) != noop.get("noop_fail_count"):
        raise ValueError("no-op pass/fail count mismatch")

    chosen_pilot: list[str] = []
    chosen_exploratory: list[str] = []
    unused: list[str] = []
    eligible_by_repo: dict[str, int] = {}
    for repo in REPOS:
        prefix = "rich_" if repo == "Textualize/rich" else "fastapi_"
        pilot = [i for i in original["pilot_ids"] if i.startswith(prefix)]
        exploratory = [i for i in original["exploratory_ids"] if i.startswith(prefix)]
        replacements = [i for i in original["replacement_ids"] if i.startswith(prefix)]
        if len(pilot) != 2 or len(exploratory) != 6:
            raise ValueError("frozen per-repo 2+6 composition drift")
        eligible_by_repo[repo] = sum(i in eligible for i in pilot + exploratory + replacements)
        available_replacements = [i for i in replacements if i in eligible]
        kept_pilot = [i for i in pilot if i in eligible]
        while len(kept_pilot) < 2 and available_replacements:
            kept_pilot.append(available_replacements.pop(0))
        kept_exploratory = [i for i in exploratory if i in eligible]
        while len(kept_exploratory) < 6 and available_replacements:
            kept_exploratory.append(available_replacements.pop(0))
        chosen_pilot.extend(kept_pilot)
        chosen_exploratory.extend(kept_exploratory)
        unused.extend(available_replacements)
    selected = chosen_pilot + chosen_exploratory
    if len(selected) != len(set(selected)) or not set(selected).issubset(eligible):
        raise ValueError("assembled task cohort includes ineligible or duplicate IDs")
    ready = (len(chosen_pilot) == 4 and len(chosen_exploratory) == 12)
    result = {
        "version": "discriminating-evidence-v0-exploratory-qualified-v1",
        "status": ("ELIGIBILITY_READY_NOT_BLIND_CERTIFIED"
                   if ready else "NO_GO_INSUFFICIENT_ELIGIBLE_TASKS"),
        "source_selector_sha256": source_sha,
        "source_gold_run_id": GOLD_RUN,
        "source_noop_run_id": NOOP_RUN,
        "source_gold_metadata_sha256": gold["_safe_input_sha256"],
        "source_noop_metadata_sha256": noop["_safe_input_sha256"],
        "gold_pass_count": len(gold_ids),
        "noop_fail_count": len(eligible),
        "eligible_by_repo": eligible_by_repo,
        "pilot_ids": chosen_pilot,
        "exploratory_ids": chosen_exploratory,
        "unused_replacement_ids": unused,
        "certifies_blind": False,
        "model_evaluation_executed": False,
        "gpu_or_submission_authorized": False,
        "limits": (
            "Metadata-eligible only, not full historical blind certification. "
            "No new 31B model evaluation, inference, training, or Kaggle "
            "competition submission has occurred."
        ),
    }
    result["qualified_manifest_sha256"] = hashlib.sha256(
        json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return result


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, default=ROOT)
    p.add_argument("--gold-metadata", type=Path, required=True)
    p.add_argument("--noop-metadata", type=Path, required=True)
    p.add_argument("--out", type=Path)
    args = p.parse_args()
    result = build_ready(args.repo.resolve(), args.gold_metadata.resolve(),
                         args.noop_metadata.resolve())
    if args.out:
        path = args.out.resolve()
        if path.exists():
            raise ValueError("refusing to overwrite qualified manifest")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "gold_pass_count": result["gold_pass_count"],
        "noop_fail_count": result["noop_fail_count"],
        "eligible_by_repo": result["eligible_by_repo"],
        "pilot_count": len(result["pilot_ids"]),
        "exploratory_count": len(result["exploratory_ids"]),
        "qualified_manifest_sha256": result["qualified_manifest_sha256"],
        "certifies_blind": False, "model_evaluation_executed": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
