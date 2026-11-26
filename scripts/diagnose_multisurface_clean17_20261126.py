"""Private-scorer retrospective: aggregate-only matched Gemma 31B outcome audit.

Reads exact frozen 17-pair result. Emits no issue IDs, prompts, source snippets,
patch contents, paths, model traces, or private competition resources.
This is observational error triage, NOT independent causal identification.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean, median

from scripts.render_multisurface_clean17_20261126 import assess, ARMS

def as_number(value):
    return round(float(value), 2)

def analyze(data: dict) -> dict:
    reference = assess(data)  # Strict 17 IDs / 34 real outcomes / membership check
    rows = data["results"]
    by = defaultdict(dict)
    for r in rows:
        by[r["instance_id"]][r["arm"]] = r
    groups = defaultdict(list)
    repo_outcomes = defaultdict(lambda: defaultdict(int))
    for task_id, pair in by.items():
        c, t = (pair[a] for a in ARMS)
        label = ("both" if c["resolved"] and t["resolved"]
                 else "control_only" if c["resolved"]
                 else "candidate_only" if t["resolved"]
                 else "neither")
        groups[label].append((c, t))
        prefix = task_id.split("_", 1)[0]  # Aggregated repo family only
        if prefix not in ("fastapi", "rich"):
            raise ValueError("unexpected repo in frozen cohort")
        repo_outcomes[prefix][label] += 1

    stats = {}
    for label in ("both", "candidate_only", "control_only", "neither"):
        pairs = groups[label]
        n = len(pairs)
        if n == 0:
            continue
        ctools = [x["tool_calls"] for x, _ in pairs]
        ttools = [y["tool_calls"] for _, y in pairs]
        sec_c = [x["duration_seconds"] for x, _ in pairs]
        sec_t = [y["duration_seconds"] for _, y in pairs]
        delta = [b - a for a, b in zip(ctools, ttools)]
        stats[label] = {
            "n": n,
            "control_calls_total": sum(ctools),
            "candidate_calls_total": sum(ttools),
            "calls_delta_total": sum(delta),
            "calls_delta_mean": as_number(mean(delta)),
            "calls_delta_median": as_number(median(delta)),
            "candidate_more_calls": sum(x > 0 for x in delta),
            "candidate_fewer_calls": sum(x < 0 for x in delta),
            "time_delta_seconds_total": as_number(sum(sec_t) - sum(sec_c)),
            "control_patched": sum(bool(x.get("has_patch")) for x, _ in pairs),
            "candidate_patched": sum(bool(y.get("has_patch")) for _, y in pairs),
            "control_patch_chars_mean": as_number(mean(x.get("patch_chars", 0) for x, _ in pairs)),
            "candidate_patch_chars_mean": as_number(mean(y.get("patch_chars", 0) for _, y in pairs)),
            "control_tool_cap_near_55": sum(x >= 55 for x in ctools),
            "candidate_tool_cap_near_55": sum(x >= 55 for x in ttools),
        }

    # Paired discordant outcomes 2 rescues vs 1 regression (n=3),
    # exact two-sided McNemar/binomial sign test p=1.0 (not significant).
    b = len(groups["candidate_only"])
    c = len(groups["control_only"])
    if (b, c) != (2, 1):
        raise ValueError("unexpected frozen research result")
    if sum(v["calls_delta_total"] for v in stats.values()) != 73:
        raise ValueError("expected 73 extra treatment calls; scorer drift")

    return {
        "analysis_version": "retrospective-outcome-cost-v1",
        "scorer_verified": True,
        "sample_n": 17,
        "discordant_rescues": b,
        "discordant_regressions": c,
        "exact_mcnemar_two_sided_p": 1.0,
        "observed_tool_calls_delta_total": 73,
        "by_outcome": stats,
        "repo_family_counts": {
            family: {label: counts.get(label, 0)
                     for label in ("both", "candidate_only", "control_only", "neither")}
            for family, counts in sorted(repo_outcomes.items())
        },
        "limitations": [
            "Existing public-development cohort, not independent hidden set",
            "Patch size and tool count do not establish semantic correctness",
            "No raw model trajectories/timeline in this metric file",
            "No causal attribution from paired outcome counts alone"
        ],
    }

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--private-result", required=True, type=Path)
    args = p.parse_args()
    report = analyze(json.loads(args.private_result.read_text()))
    print("MULTISURFACE17_PRIVATE_AGGREGATE_RESEARCH=" +
          json.dumps(report, sort_keys=True), flush=True)

if __name__ == "__main__":
    main()
