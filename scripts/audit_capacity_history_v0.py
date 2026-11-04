#!/usr/bin/env python3
"""Audit candidate task-ID mentions in pre-capacity Git history without reading task data.

This verifies only tracked source/document history reachable in local git refs.
Not a guarantee about old workflow artifacts, unrecorded views, old Releases,
outside conversations, or task semantic overlap.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
from pathlib import Path

# Earlier than the first capacity-v0 selection, not simply "before today".
PRESELECTION_CUTOFF = "2026-11-04T05:48:00Z"
SOURCE_PATHS = ("docs", "scripts", "tests", "kaggle", ".github/workflows", "NOW.md", "README.md", "AGENTS.md")
METADATA_ONLY_ALLOWLIST = frozenset((
    "docs/evaluation/verifier-lora-split-v0.json",
    "docs/evaluation/verifier-lora-train-subset-v0.json",
    "docs/evaluation/verifier-lora-blind-reservation-v0.json",
    "docs/evaluation/verifier-lora-eval-contract-v1.json",
    "docs/evaluation/topology-ab-manifest-v1.json",
    "docs/evaluation/public-corpus-summary.md",
))


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True, text=True, check=False,
    )
    if check and result.returncode != 0:
        raise ValueError(
            f"git command failed ({result.returncode}): {args[0]}: {result.stderr[:300]}"
        )
    return result


def scan_history(repo: Path, candidate_ids: list[str]) -> dict:
    if not candidate_ids or len(candidate_ids) != len(set(candidate_ids)):
        raise ValueError("invalid/duplicate candidate IDs")
    if any(not re.fullmatch(r"(rich|fastapi)_\d+", i) for i in candidate_ids):
        raise ValueError("task ID outside supported capacity slice")
    shallow = git(repo, "rev-parse", "--is-shallow-repository").stdout.strip()
    if shallow != "false":
        raise ValueError("shallow or unverifiable history; fail closed")
    refs = git(repo, "for-each-ref", "--format=%(refname)", "refs/heads", "refs/remotes").stdout.splitlines()
    if not refs:
        raise ValueError("no readable Git branches in historical audit")
    revisions = git(
        repo, "rev-list", "--all", "--before=" + PRESELECTION_CUTOFF,
        "--", *SOURCE_PATHS
    ).stdout.splitlines()
    if not revisions:
        raise ValueError("no historical source revisions; fail closed")
    expr = "(^|[^[:alnum:]_])(" + "|".join(re.escape(i) for i in candidate_ids) + ")([^[:alnum:]_]|$)"
    findings = []
    excluded_metadata_paths = 0
    for sha in revisions:
        result = git(
            repo, "grep", "-I", "-l", "-E", "-e", expr, sha, "--", *SOURCE_PATHS,
            check=False,
        )
        if result.returncode == 1:
            continue
        if result.returncode != 0:
            raise ValueError(f"git grep failure on {sha}: {result.stderr[:250]}")
        for found in result.stdout.splitlines():
            path = found[len(sha) + 1 :] if found.startswith(sha + ":") else None
            if not path:
                raise ValueError(f"unexpected git-grep entry shape on {sha}")
            if path in METADATA_ONLY_ALLOWLIST:
                excluded_metadata_paths += 1
                continue
            # Avoid publishing the underlying source line (and any task data).
            # Extract IDs only by a second, non-printing match at the same ref/path.
            for issue_id in candidate_ids:
                exists = git(
                    repo, "grep", "-I", "-q", "-E",
                    "-e", r"(^|[^[:alnum:]_])" + re.escape(issue_id) + r"([^[:alnum:]_]|$)",
                    sha, "--", path, check=False,
                )
                if exists.returncode == 0:
                    findings.append({
                        "instance_id": issue_id,
                        "historical_path": path,
                        "revision": sha,
                    })
                elif exists.returncode != 1:
                    raise ValueError("historical match verification failed")
    # Deduplicate repeated adjacent-version findings, retain representative origin.
    unique = {}
    for f in findings:
        unique.setdefault((f["instance_id"], f["historical_path"]), f)
    compact = sorted(unique.values(), key=lambda x: (x["instance_id"], x["historical_path"]))
    return {
        "version": "capacity-v0-preselection-git-history-audit",
        "cutoff_utc": PRESELECTION_CUTOFF,
        "source_paths": list(SOURCE_PATHS),
        "scope": "tracked source/document Git history only; unrecorded/artifact exposure unknown",
        "checked_revisions": len(revisions),
        "checked_branch_refs": len(refs),
        "candidate_count": len(candidate_ids),
        "allowlisted_metadata_hits": excluded_metadata_paths,
        "historical_exposed_ids": sorted({f["instance_id"] for f in compact}),
        "historical_mentions": compact,
        "certifies_blind": False,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--repo", type=Path, default=Path("."))
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    root = args.repo.resolve()
    selector_path = root / "scripts" / "capacity_preflight_v0.py"
    spec = importlib.util.spec_from_file_location("capacity_preflight", selector_path)
    if not spec or not spec.loader:
        raise FileNotFoundError(selector_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    s = module.build_feasibility_manifest(root)
    ids = s["feasibility_ids"] + s["confirmation_reserve_ids"]
    data = scan_history(root, ids)
    data["source_selector_sha256"] = s["selection_digest_sha256"]
    if args.out.exists():
        raise ValueError("refuse overwrite of historical audit output")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("CAPACITY_HISTORY_CANDIDATES=", data["candidate_count"])
    print("CAPACITY_HISTORY_REVISIONS=", data["checked_revisions"])
    print("CAPACITY_HISTORY_PREEXPOSED=", ",".join(data["historical_exposed_ids"]))
    print("CAPACITY_HISTORY_IS_CERTIFIED_BLIND=NO")
    return 0 if not data["historical_exposed_ids"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
