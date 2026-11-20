#!/usr/bin/env python3
"""Retrospective real 31B patch-vs-reference evidence audit.

Runs only on an isolated CPU runner; reads already-finished private Kaggle outputs.
Reference fixes and raw issues are NEVER passed to an agent, printed, or
exported. Human semantic judgments remain UNKNOWN unless directly supported.
No model/GPU/training/competition submission. No modification to submission/.
"""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import re

from scripts.audit_paired_31b_existing_traces import read_safe_results, trace_for
from scripts.audit_pro_v3r_real31b_uptake_20261115 import (
    validate as validate_v3r, trace_path as v3r_trace_path,
)
from scripts.audit_paired_31b_feedback_v2 import reduce_feedback

EXPECTED_FIRST = {"fastapi_14487", "rich_3782", "requests_7427"}
VALIDITY_FIRST = {
    "fastapi_14487": "GOLD_PASS_NOOP_FAIL",
    "rich_3782": "GOLD_PASS_NOOP_FAIL_SPEC_POINTER_RISK",
    "requests_7427": "GOLD_FAIL_NOOP_FAIL",
}
# Explicitly no grading-validity claim for the different Nov 15 panel.
GOLD_UNKNOWN = "UNTESTED_GOLD_NOOP"
PATH_FLAGS = ("diff --git ", "+++ ", "*** Update File: ", "*** Add File: ")
HUNK = re.compile(r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def diff_evidence(raw: str) -> dict[str, list[int]]:
    """Changed paths and original line anchors, never exported as names."""
    result: dict[str, list[int]] = {}
    current = None
    for line in (raw or "").splitlines():
        p = None
        if line.startswith("diff --git "):
            m = re.match(r"^diff --git a/(.+?) b/(.+?)\s*$", line)
            p = m.group(2) if m else None
        elif line.startswith("+++ "):
            p = line[4:].split("\t", 1)[0].strip()
        elif line.startswith("*** Update File: "):
            p = line[len("*** Update File: "):].strip()
        elif line.startswith("*** Add File: "):
            p = line[len("*** Add File: "):].strip()
        if p is not None:
            p = p.strip('"').strip("'")
            if p in ("/dev/null", ""):
                current = None
                continue
            if p.startswith(("a/", "b/")):
                p = p[2:]
            parts = Path(p).parts
            current = p if not Path(p).is_absolute() and ".." not in parts else None
            if current:
                result.setdefault(current, [])
        m = HUNK.match(line)
        if m and current:
            result[current].append(int(m.group(1)))
    return result


def source(paths: dict[str, list[int]]) -> set[str]:
    return {p for p in paths if p.endswith(".py") and not
            (Path(p).name.startswith("test_") or "/tests/" in "/"+p)}


def overlap_hunks(gold: dict, agent: dict) -> int:
    total = 0
    for path in set(gold) & set(agent):
        total += sum(any(abs(a-g) <= 20 for g in gold[path])
                     for a in agent[path])
    return total


def classify_log(raw: str | None) -> str:
    if raw is None:
        return "UNOBSERVED"
    if re.search(r"ModuleNotFoundError|ImportError|Failed to import", raw):
        return "IMPORT_OR_DEPENDENCY_HINT"
    if re.search(r"SyntaxError|IndentationError", raw):
        return "SYNTAX_HINT"
    if re.search(r"AssertionError|\bFAILED\b|\bfailures?\b", raw, re.I):
        return "TEST_FAILURE_HINT"
    if re.search(r"timed out|timeout|deadline exceeded", raw, re.I):
        return "TIMEOUT_HINT"
    if re.search(r"patch does not apply|corrupt patch|git apply", raw, re.I):
        return "PATCH_APPLICATION_HINT"
    return "UNCLASSIFIED_LOG"


def find_artifacts(trace: Path | None, instance_id: str) -> tuple[str | None, str | None]:
    if trace is None:
        return None, None
    base = trace.parent.parent
    patch = base / "patches" / (instance_id + ".patch")
    log = base / "test_outputs" / (instance_id + ".log")
    return (patch.read_text(errors="replace") if patch.is_file() else None,
            log.read_text(errors="replace") if log.is_file() else None)


def load_gold(path: Path, ids: set[str]) -> dict:
    out = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            entry = json.loads(line)
            tid = entry.get("instance_id")
            if tid in ids:
                if tid in out:
                    raise ValueError("duplicate task label")
                out[tid] = entry
    if set(out) != ids:
        raise ValueError("missing task gold labels: " + str(len(ids-set(out))))
    return out


def audit_cohort(root: Path, flavor: str, gold: dict) -> list[dict]:
    data = json.loads((root / "paired_prompt_v2_31b_results.json").read_text())
    rows = read_safe_results(root / "paired_prompt_v2_31b_results.json") if flavor == "prompt" else validate_v3r(data)
    ids = {r["instance_id"] for r in rows}
    if flavor == "prompt" and ids != EXPECTED_FIRST:
        raise ValueError("wrong original 3-task IDs")
    if len(ids) != 3:
        raise ValueError("wrong cohort size")
    output = []
    for row in rows:
        tid = row["instance_id"]
        arm = row["arm"]
        trace_file = trace_for(root, arm, tid) if flavor == "prompt" else v3r_trace_path(root, arm, tid)
        trace = json.loads(trace_file.read_text()) if trace_file else None
        feedback = reduce_feedback(trace) if trace else None
        patch, testlog = find_artifacts(trace_file, tid)
        gold_patch = gold[tid].get("patch")
        if not isinstance(gold_patch, str) or not gold_patch.strip():
            raise ValueError("missing nonempty gold label")
        gp = diff_evidence(gold_patch)
        mp = diff_evidence(patch) if patch is not None else None
        gs = source(gp)
        ms = source(mp) if mp is not None else None
        validity = VALIDITY_FIRST[tid] if flavor == "prompt" else GOLD_UNKNOWN
        resolved = row["resolved"]
        if type(resolved) is not bool:
            raise ValueError("invalid resolved flag")
        if resolved:
            category = "SUCCESS_DIAGNOSTIC_CONTROL"
        elif validity == "GOLD_FAIL_NOOP_FAIL":
            category = "GRADER_CONFOUNDED_NO_MODEL_ATTRIBUTION"
        elif validity == GOLD_UNKNOWN:
            category = "UNKNOWN_GRADER_VALIDITY"
        elif mp is None:
            category = "UNKNOWN_PATCH_UNAVAILABLE"
        elif gs and ms and not (gs & ms):
            category = "LOCALIZATION_SUSPECT_NOT_PROVEN"
        elif gs and ms and (gs & ms):
            category = "ROOT_CAUSE_VS_PATCH_SEMANTICS_UNRESOLVED"
        else:
            category = "UNKNOWN_PATCH_OR_GOLD_SCOPE"
        statement = gold[tid].get("problem_statement") or ""
        hints = gold[tid].get("hints_text") or ""
        result = {
            "cohort": flavor,
            "instance_id": tid,
            "arm": arm,
            "resolved": resolved,
            "grading_validity": validity,
            "test_exit_code": row.get("test_exit_code"),
            "tool_calls_scorer": row.get("tool_calls"),
            "duration_seconds": round(row.get("duration_seconds"), 2) if
                isinstance(row.get("duration_seconds"), (int, float)) else None,
            "score_record_has_patch": row.get("has_patch"),
            "patch_artifact_recovered": mp is not None,
            "trace_recovered": trace is not None,
            "gold_source_file_count": len(gs),
            "model_source_file_count": len(ms) if ms is not None else None,
            "source_file_overlap_count": len(gs & ms) if ms is not None else None,
            "gold_source_coverage": (len(gs & ms) / len(gs)) if ms is not None and gs else None,
            "model_off_gold_source_count": len(ms - gs) if ms is not None else None,
            "near_reference_hunk_count": overlap_hunks(gp, mp) if mp is not None else None,
            "statement_chars": len(statement),
            "hints_chars": len(hints),
            "statement_contains_url": bool(re.search(r"https?://", statement)),
            "spec_pointer_risk": len(statement) < 120 and bool(re.search(r"https?://", statement)),
            "grader_log_signature": classify_log(testlog),
            "post_edit_explicit_tests_recognized": feedback["tests_after_first_edit"] if feedback else None,
            "unclassified_opaque_commands": feedback["unclassified_opaque_commands"] if feedback else None,
            "nonzero_command_followed_by_edit": feedback["nonzero_commands_followed_by_edit"] if feedback else None,
            "tool_cap_28_reached": row.get("tool_calls") == 28,
            "primary_evidence_class": category,
            "human_semantic_root_cause_verified": False,
            "raw_issue_or_patch_exported": False,
        }
        output.append(result)
    return sorted(output, key=lambda r: (r["instance_id"], r["arm"]))


def self_test() -> None:
    a = diff_evidence("diff --git a/src/a.py b/src/a.py\n@@ -12,2 +12,3 @@\n+++ b/src/a.py\n@@ -17,1 +17,1 @@")
    b = diff_evidence("--- a/src/a.py\n+++ b/src/a.py\n@@ -16 +16 @@")
    assert source(a) == {"src/a.py"}
    assert source(b) == {"src/a.py"}
    assert overlap_hunks(a, b) == 1
    assert diff_evidence("--- a/a.py\n+++ /dev/null\n") == {}
    assert classify_log("ImportError: missing") == "IMPORT_OR_DEPENDENCY_HINT"
    assert classify_log(None) == "UNOBSERVED"
    print("GEMMA_PRIVATE_31B_PATCH_AUDITOR_CPU_SELFTEST=PASS")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--tasks", type=Path)
    p.add_argument("--prompt-root", type=Path)
    p.add_argument("--v3r-root", type=Path)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    if args.self_test:
        self_test()
        return
    if not all((args.tasks, args.prompt_root, args.v3r_root, args.output)):
        p.error("both completed raw outputs, original tasks, and safe output required")
    prompt_data = json.loads((args.prompt_root / "paired_prompt_v2_31b_results.json").read_text())
    v3r_data = json.loads((args.v3r_root / "paired_prompt_v2_31b_results.json").read_text())
    prompt = read_safe_results(args.prompt_root / "paired_prompt_v2_31b_results.json")
    v3r = validate_v3r(v3r_data)
    ids = {r["instance_id"] for r in prompt+v3r}
    gold = load_gold(args.tasks, ids)
    rows = audit_cohort(args.prompt_root, "prompt", gold) + audit_cohort(args.v3r_root, "v3r", gold)
    counts = Counter(x["primary_evidence_class"] for x in rows if not x["resolved"])
    output = {
        "version": "gemma31b-private-raw-patch-gold-retrospective-v1",
        "model": "gemma-4-31b-it-qat-w4a16-ct",
        "source_previous_completed_experiments": [43057377220, 43689217134],
        "new_gpu": False, "new_inference": False,
        "new_kaggle_kernel": False, "competition_submission": False,
        "model_or_submission_modified": False,
        "raw_gold_or_issue_or_model_patch_exported": False,
        "total_evaluations": len(rows),
        "unique_tasks": len(ids),
        "successful_diagnostic_controls": sum(x["resolved"] for x in rows),
        "unsuccessful": sum(not x["resolved"] for x in rows),
        "patch_artifacts_recovered": sum(x["patch_artifact_recovered"] for x in rows),
        "trace_artifacts_recovered": sum(x["trace_recovered"] for x in rows),
        "failure_evidence_class_counts": dict(sorted(counts.items())),
        "caution": ("File and hunk overlap cannot prove semantic correctness or fault location; "
                    "reference edits are not unique ground truth; gold/no-op validity is checked "
                    "for the original Nov12 trio only; source filenames and all patch content "
                    "are deliberately suppressed. UNKNOWN is a legitimate scientific outcome."),
        "rows": rows,
    }
    if len(rows) != 12:
        raise ValueError("incomplete 12-evaluation recovered comparison")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True))
    print("GEMMA_31B_PRIVATE_SAFE_AUDIT=" + json.dumps(output, sort_keys=True))


if __name__ == "__main__":
    main()
