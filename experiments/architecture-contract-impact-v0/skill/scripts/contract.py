"""Read-only contract/impact analyzer for an optional SWE agent Skill.

This is structural evidence, not an oracle for issue correctness. No tests or
model calls are run, no source tree modifications are made.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
import subprocess


SOURCES = {"issue", "repository", "hypothesis"}
CHECKS = {"not_run", "reported_pass", "reported_fail", "blocked", "unknown"}


def relative_path(raw):
    if not isinstance(raw, str) or not raw or "\\" in raw:
        raise ValueError("invalid repository path")
    path = PurePosixPath(raw)
    if path.is_absolute() or any(x in {".", ".."} for x in raw.split("/")):
        raise ValueError("unsafe repository path")
    return path.as_posix()


def changed_files(workspace):
    workspace = Path(workspace).resolve()
    if not (workspace / ".git").exists():
        raise ValueError("workspace is not a git checkout")
    def git(*args):
        result = subprocess.run(
            ["git", "-C", str(workspace), *args], check=True, capture_output=True,
            text=True, timeout=10,
        )
        return result.stdout.splitlines()
    # Diff against HEAD includes tracked staged and unstaged modifications.
    tracked = git("diff", "--name-only", "--no-ext-diff", "HEAD", "--")
    untracked = git("ls-files", "--others", "--exclude-standard")
    deleted = git("diff", "--name-only", "--diff-filter=D", "HEAD", "--")
    return sorted({relative_path(x) for x in tracked + untracked}), sorted(set(deleted))


def analyze(request, workspace):
    if not isinstance(request, dict):
        raise ValueError("request must be an object")
    if set(request) - {"requirements", "unknowns"}:
        raise ValueError("unknown request fields")
    requirements = request.get("requirements", [])
    unknowns = request.get("unknowns", [])
    if not isinstance(requirements, list) or not isinstance(unknowns, list):
        raise ValueError("requirements and unknowns must be lists")
    if len(requirements) > 30 or len(unknowns) > 30:
        raise ValueError("oversized contract")
    if any(not isinstance(x, str) or not x.strip() for x in unknowns):
        raise ValueError("invalid unknown")
    changed, deleted = changed_files(workspace)
    ids = set()
    results = []
    for req in requirements:
        if not isinstance(req, dict) or set(req) != {
                "id", "statement", "source", "evidence", "edit_targets", "check"}:
            raise ValueError("invalid requirement schema")
        ident, statement, source, evidence = (
            req[x] for x in ("id", "statement", "source", "evidence"))
        if (not isinstance(ident, str) or not ident.strip() or ident in ids
                or not isinstance(statement, str) or not statement.strip()
                or not isinstance(evidence, str) or not evidence.strip()
                or source not in SOURCES):
            raise ValueError("missing/duplicate requirement evidence")
        ids.add(ident)
        if not isinstance(req["edit_targets"], list):
            raise ValueError("edit_targets must be a list")
        targets = sorted({relative_path(p) for p in req["edit_targets"]})
        check = req["check"]
        if not isinstance(check, dict) or set(check) != {"status", "evidence"}:
            raise ValueError("invalid check schema")
        if check["status"] not in CHECKS or not isinstance(check["evidence"], str):
            raise ValueError("invalid check")
        # Claimed pass/fail never becomes a trusted observation without proof.
        if check["status"] in {"reported_pass", "reported_fail"} and not check["evidence"].strip():
            raise ValueError("reported check needs evidence")
        missing = sorted(set(targets) - set(changed))
        materialized = sorted(set(targets) & set(changed))
        issues = []
        if source == "hypothesis":
            issues.append("unverified_requirement")
        if not targets:
            issues.append("unmapped_impact")
        elif missing and materialized:
            issues.append("partial_impact")
        elif missing:
            issues.append("no_targeted_change")
        if check["status"] in {"not_run", "unknown", "blocked"}:
            issues.append("verification_not_established")
        elif check["status"] == "reported_fail":
            issues.append("agent_reported_verification_failure")
        results.append({
            "id": ident, "source": source, "expected_edit_targets": targets,
            "changed_targets": materialized, "missing_targets": missing,
            "agent_reported_check": check["status"], "issues": issues,
        })
    if not requirements:
        decision = "insufficient_specification"
    elif any("partial_impact" in x["issues"] for x in results):
        decision = "investigate_missing_impact"
    elif any("unverified_requirement" in x["issues"] for x in results) or unknowns:
        decision = "investigate_contract"
    elif any("unmapped_impact" in x["issues"] for x in results):
        decision = "localize"
    elif any("no_targeted_change" in x["issues"] for x in results):
        decision = "implement"
    elif any(x["agent_reported_check"] != "reported_pass" for x in results):
        decision = "verify_or_repair"
    else:
        decision = "review_final_not_certified"
    return {
        "decision": decision,
        "warning": "Tool checks structure and git changes, not semantic correctness; test results are agent-reported.",
        "changed_files": changed,
        "deleted_files": deleted,
        "unknowns": unknowns,
        "requirements": results,
        "independent_correctness_verified": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", required=True, help="JSON contract object")
    parser.add_argument("--workspace", default="/workspace")
    args = parser.parse_args()
    request = json.loads(args.request)
    print(json.dumps(analyze(request, args.workspace), sort_keys=True))


if __name__ == "__main__":
    main()
