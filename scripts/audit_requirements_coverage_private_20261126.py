#!/usr/bin/env python3
"""Conservative CPU-only audit of existing 31B patches vs public-dev references.

No model calls or grading. No issue text, reference patch, candidate patch,
private filename or task ID leaves the runner. All claims are structural.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
from typing import Any

from scripts.audit_gemma31b_semantic_gap_private_20261120 import (
    diff_evidence, overlap_hunks, source,
)

ARMS = ("fastpath_4min", "single_edit_4min")
RESULT_FILENAME = "paired_single_edit_channel31b_4min_results.json"


def patch_evidence(reference_patch: str, candidate_patch: str | None) -> dict[str, Any]:
    """A reference source file/hunk overlap is NOT a correctness finding."""
    reference = diff_evidence(reference_patch)
    gold_sources = source(reference)
    base = {
        "reference_source_file_count": len(gold_sources),
        "candidate_source_file_count": None,
        "source_overlap_count": None,
        "near_reference_hunk": None,
        "explicit_requirement_omitted": None,
    }
    if candidate_patch is None:
        return dict(base, scope_label="patch_artifact_unavailable")
    if not candidate_patch.strip():
        return dict(base, candidate_source_file_count=0,
                    scope_label="empty_patch")
    candidate = diff_evidence(candidate_patch)
    model_sources = source(candidate)
    count = len(gold_sources & model_sources)
    if not gold_sources:
        label = "reference_source_scope_unavailable"
    elif not model_sources:
        label = "no_candidate_source_paths_parsed"
    elif not count:
        label = "no_reference_source_overlap"
    elif gold_sources - model_sources:
        label = "partial_reference_source_overlap"
    else:
        label = "all_reference_source_paths_overlap"
    return dict(base, scope_label=label,
                candidate_source_file_count=len(model_sources),
                source_overlap_count=count,
                near_reference_hunk=bool(overlap_hunks(reference, candidate)))


def spec_evidence(statement: str) -> dict[str, Any]:
    """Syntactic indicators only: an issue's real requirements remain unknown."""
    if not isinstance(statement, str):
        statement = ""
    external = bool(re.search(r"https?://", statement))
    return {
        "short_external_reference_risk": external and len(statement.strip()) < 160,
        "has_external_url": external,
        "has_code_fence": chr(96) * 3 in statement,
        "has_reproduction_marker": bool(re.search(
            r"\b(reproduc|expected|actual|steps to|test case|example)\b",
            statement, re.I)),
        "specification_sufficient": None,
    }


def summarize_cohort(data: dict, tasks_by_id: dict,
                     patches: dict[tuple[str, str], str | None]) -> dict:
    """Fail-closed pair integrity and anonymous aggregates, never causal claims."""
    if data.get("status") != "completed":
        raise ValueError("not a completed scorer run")
    rows = data.get("results")
    if not isinstance(rows, list) or len(rows) != 12:
        raise ValueError("expected twelve scorer evaluation rows")
    keys = [(r.get("instance_id"), r.get("arm")) for r in rows]
    ids = {i for i, _ in keys}
    if (len(ids) != 6 or len(set(keys)) != 12 or
            set(keys) != {(tid, arm) for tid in ids for arm in ARMS} or
            not all(isinstance(tid, str) and
                    re.fullmatch(r"(fastapi|rich|requests)_[0-9]+", tid)
                    for tid in ids)):
        raise ValueError("frozen paired cohort identity mismatch")
    if set(tasks_by_id) != ids:
        raise ValueError("missing or unexpected task metadata")
    stats = {arm: Counter() for arm in ARMS}
    for row in rows:
        tid, arm = row["instance_id"], row["arm"]
        if type(row.get("resolved")) is not bool or type(row.get("has_patch")) is not bool:
            raise ValueError("unknown result flag")
        task = tasks_by_id[tid]
        gold = task.get("patch")
        if not isinstance(gold, str) or not gold.strip():
            raise ValueError("missing reference patch")
        spec = spec_evidence(task.get("problem_statement", ""))
        candidate = patches.get((tid, arm))
        if candidate is not None and not row["has_patch"]:
            raise ValueError("patch artifact contradicts scorer patch flag")
        scope = patch_evidence(gold, candidate)
        counter = stats[arm]
        counter["evaluated"] += 1
        counter["resolved"] += int(row["resolved"])
        counter["scorer_reported_patch"] += int(row["has_patch"])
        counter["recovered_patch"] += int(candidate is not None)
        counter["short_external_reference_risk"] += int(
            spec["short_external_reference_risk"])
        counter["has_external_url"] += int(spec["has_external_url"])
        counter["has_reproduction_marker"] += int(spec["has_reproduction_marker"])
        counter["reference_multi_source"] += int(
            scope["reference_source_file_count"] > 1)
        counter["scope_" + scope["scope_label"]] += 1
        counter["near_reference_hunk"] += int(scope["near_reference_hunk"] is True)
    idx = {(r["instance_id"], r["arm"]): r for r in rows}
    pair = Counter()
    for tid in ids:
        a, b = (idx[(tid, arm)]["resolved"] for arm in ARMS)
        key = "both" if a and b else "fastpath_only" if a else (
            "single_edit_only" if b else "neither")
        pair[key] += 1
    names = (
        "evaluated", "resolved", "scorer_reported_patch", "recovered_patch",
        "short_external_reference_risk", "has_external_url",
        "has_reproduction_marker", "reference_multi_source",
        "scope_patch_artifact_unavailable", "scope_empty_patch",
        "scope_reference_source_scope_unavailable",
        "scope_no_candidate_source_paths_parsed",
        "scope_no_reference_source_overlap",
        "scope_partial_reference_source_overlap",
        "scope_all_reference_source_paths_overlap", "near_reference_hunk",
    )
    return {
        "version": "gemma-31b-existing-real-final-patches-requirement-evidence-v1",
        "unique_tasks": len(ids),
        "scored_evaluations": len(rows),
        "arms": {arm: {key: stats[arm][key] for key in names} for arm in ARMS},
        "paired_outcomes": {
            key: pair[key] for key in
            ("both", "fastpath_only", "single_edit_only", "neither")
        },
        "gold_noop_controls": "UNVERIFIED",
        "confirmed_explicit_requirement_omissions": None,
        "agent_improvement_demonstrated": False,
        "changed_agent": False,
        "new_model_inference": False,
        "new_gpu": False,
        "new_official_submission": False,
        "raw_private_content_exported": False,
        "research_gate": "NEEDS_GOLD_NOOP_AND_ACTUAL_SEMANTIC_ISSUE_REVIEW",
        "interpretation": (
            "Source-path and hunk overlap against one reference patch are "
            "only proxies: cannot certify semantic correctness, coverage of "
            "requirements, wrong-source errors, or test validity. A short "
            "external-link issue is only a specification risk. No automatic "
            "labeling of explicit requirement omissions. Private original "
            "task IDs, paths, raw issues, patches, traces remain unexported."
        ),
    }


def read_selected_tasks(path: Path, ids: set[str]) -> dict:
    selected = {}
    with path.open(encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            tid = row.get("instance_id")
            if tid in ids:
                if tid in selected:
                    raise ValueError("duplicate task metadata")
                selected[tid] = row
    if set(selected) != ids:
        raise ValueError("incomplete task metadata")
    return selected


def recover_private_patches(root: Path, rows: list[dict]) -> dict:
    found = {}
    for row in rows:
        tid, arm = row["instance_id"], row["arm"]
        p = (root / "paired-single-edit-private-results" /
             "private-final-patches" / arm / (tid + ".patch"))
        if p.is_file():
            found[(tid, arm)] = p.read_text(encoding="utf-8", errors="replace")
    if not found:
        for row in rows:
            tid, arm = row["instance_id"], row["arm"]
            matches = [p for p in root.rglob(tid + ".patch")
                       if p.parent.name == arm and "private-final-patches" in p.parts]
            if len(matches) > 1:
                raise ValueError("ambiguous private patch artifact")
            if matches:
                found[(tid, arm)] = matches[0].read_text(
                    encoding="utf-8", errors="replace")
    return found


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    obj = json.loads((args.root / RESULT_FILENAME).read_text(encoding="utf-8"))
    rows = obj.get("results", [])
    ids = {r["instance_id"] for r in rows}
    tasks = read_selected_tasks(args.tasks, ids)
    patches = recover_private_patches(args.root, rows)
    result = summarize_cohort(obj, tasks, patches)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    print("REAL_31B_REQUIREMENT_EVIDENCE_SAFE=" +
          json.dumps(result, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
