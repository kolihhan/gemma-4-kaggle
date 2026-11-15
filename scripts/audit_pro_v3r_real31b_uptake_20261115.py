#!/usr/bin/env python3
"""Read only genuine private 31B V3R/V2 paired scoring and Skill uptake.

Never log issue text, tool arguments, tool output, patches, traces, or test
body. Missing evidence is unobserved, never counted as negative uptake.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

VERSION = "v3r-vs-v2-fresh-paired-20261115-v1"
ARMS = ("v2_5min", "v3r_5min")


def validate(data: dict) -> list[dict]:
    if data.get("version") != VERSION:
        raise ValueError("wrong_frozen_protocol")
    rows = data.get("results")
    if not isinstance(rows, list) or len(rows) != 6:
        raise ValueError("require_full_6_evaluations")
    keys = [(r.get("instance_id"), r.get("arm")) for r in rows]
    ids = {k[0] for k in keys}
    if len(ids) != 3 or len(set(keys)) != 6 or any(
        not isinstance(i, str) or not i.startswith(("fastapi_", "rich_", "requests_"))
        for i in ids
    ) or set(keys) != {(id_, arm) for id_ in ids for arm in ARMS}:
        raise ValueError("unpaired_or_invalid_task_ids")
    if any(type(r.get("resolved")) is not bool for r in rows):
        raise ValueError("missing_true_grader_status")
    return rows


def trace_path(root: Path, arm: str, task_id: str) -> Path | None:
    possible = []
    for p in root.rglob("trace_*.json"):
        if p.name != f"trace_{task_id}.json":
            continue
        parts = p.relative_to(root).parts
        is_treat = "v3r-skill" in parts
        # Treatment must be under a dedicated results subtree.
        if is_treat == (arm == "v3r_5min"):
            possible.append(p)
    if len(possible) > 1:
        raise ValueError("ambiguous_trace_path")
    return possible[0] if possible else None


def summarize_trace(trace: dict) -> dict:
    steps = trace.get("steps") if isinstance(trace, dict) else None
    if not isinstance(steps, list):
        raise ValueError("unexpected_trace_structure")
    events = []
    for step in steps:
        calls = step.get("tool_calls") if isinstance(step, dict) else None
        if not isinstance(calls, list):
            continue
        for call in calls:
            if not isinstance(call, dict):
                continue
            name = call.get("function_name")
            args = call.get("arguments", {})
            args = args if isinstance(args, dict) else {}
            phase = None
            if (name == "run_skill_script"
                and args.get("skill_name") == "repair-witness"
                and args.get("file_path") == "scripts/witness.py"):
                subargs = args.get("args", {})
                if isinstance(subargs, dict) and subargs.get("phase") in ("before", "after"):
                    phase = subargs["phase"]
            events.append((name, phase))
    edits = [i for i,(n,_) in enumerate(events) if n in ("edit_file","write_file")]
    before = [i for i,(n,p) in enumerate(events) if n == "run_skill_script" and p == "before"]
    after = [i for i,(n,p) in enumerate(events) if n == "run_skill_script" and p == "after"]
    return {
        "trace_found": True,
        "load_skill_calls": sum(n == "load_skill" for n,p in events),
        "witness_before_calls": len(before),
        "witness_after_calls": len(after),
        "unrecognized_skill_script_calls": sum(n == "run_skill_script" and p is None for n,p in events),
        "edit_calls": len(edits),
        "has_before_edit_after_sequence": any(b < e < a for b in before for e in edits for a in after),
        "observed_reedit_after_after_check": any(e > a for e in edits for a in after),
        "submit_patch_calls": sum(n == "submit_patch" for n,p in events),
        "note": "Tool-call sequence alone does not prove output was consumed or hidden issue was fixed.",
    }


def audit(root: Path) -> dict:
    data = json.loads((root / "paired_prompt_v2_31b_results.json").read_text(encoding="utf-8"))
    rows = validate(data)
    resolved = {a: sum(r["resolved"] for r in rows if r["arm"] == a) for a in ARMS}
    by_id = {
        r["instance_id"]: {
            a: next(x["resolved"] for x in rows if x["instance_id"] == r["instance_id"] and x["arm"] == a)
            for a in ARMS
        }
        for r in rows
    }
    rescues = sum(v["v3r_5min"] and not v["v2_5min"] for v in by_id.values())
    regressions = sum(v["v2_5min"] and not v["v3r_5min"] for v in by_id.values())
    stats = []
    for r in rows:
        p = trace_path(root,r["arm"],r["instance_id"])
        tr = summarize_trace(json.loads(p.read_text(encoding="utf-8"))) if p else {"trace_found": False}
        stats.append({"arm":r["arm"], **tr})
    for_arm = {}
    for arm in ARMS:
        chosen=[t for t in stats if t["arm"]==arm]
        for_arm[arm]={
            "resolved":resolved[arm],
            "traces_found":sum(t["trace_found"] for t in chosen),
            "load_skill_calls":sum(t.get("load_skill_calls",0) for t in chosen),
            "witness_before_calls":sum(t.get("witness_before_calls",0) for t in chosen),
            "witness_after_calls":sum(t.get("witness_after_calls",0) for t in chosen),
            "before_edit_after_sequences":sum(t.get("has_before_edit_after_sequence",False) for t in chosen),
            "reedit_after_after_check":sum(t.get("observed_reedit_after_after_check",False) for t in chosen),
            "unrecognized_skill_script_calls":sum(t.get("unrecognized_skill_script_calls",0) for t in chosen),
        }
    return {
        "version":"v3r-31b-private-mechanism-audit-v1",
        "pairs":3,"evaluations":6,"by_arm":for_arm,
        "rescues":rescues,"regressions":regressions,"net":rescues-regressions,
        "actual_skill_uptake_evidence_complete":for_arm["v3r_5min"]["traces_found"]==3,
        "new_model_inference":False,"new_competition_submission":False,
        "source":"PRIVATE_PUBLIC_DEV_PAIRED_NOT_KAGGLE_HIDDEN",
        "limitation":"A scripted fixture is not counted as 31B uptake; observed tool invocation is not proof that the model interpreted feedback correctly or that test was relevant. Grader resolution is primary.",
    }


def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    a=p.parse_args()
    print("GEMMA_V3R_PRIVATE_REAL_SKILL_AUDIT=" + json.dumps(audit(a.root),sort_keys=True),flush=True)


if __name__=="__main__":
    main()
