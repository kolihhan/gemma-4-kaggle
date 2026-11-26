"""Summarize the retained frozen-17 patches and traces without exporting their contents."""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

from scripts.audit_gemma31b_semantic_gap_private_20261120 import diff_evidence, overlap_hunks
from scripts.audit_gemma_edit_reliability_20261124 import _observe
from scripts.audit_paired_31b_feedback_v2 import reduce_feedback
from scripts.audit_paired_31b_feedback_v2 import command_class
from scripts.audit_requirements_coverage_private_20261126 import read_selected_tasks
from scripts.render_multisurface_clean17_20261126 import ARMS, RESULT, assess


def package_diff(patch, family):
    return {p: anchors for p, anchors in diff_evidence(patch).items()
            if p.endswith(".py") and p.startswith((family + "/", "src/" + family + "/"))}


def saved_patch(root, row):
    task, arm = row["instance_id"], row["arm"]
    name = root / "paired-multisurface-private-results" / "private-final-patches" / arm / (task + ".patch")
    if type(row.get("has_patch")) is not bool or type(row.get("patch_chars")) is not int:
        raise ValueError("missing scorer patch metadata")
    if not name.is_file():
        if row["has_patch"] or row["patch_chars"]:
            raise ValueError("scored patch artifact missing")
        return ""
    patch = name.read_bytes().decode("utf-8")
    if len(patch) != row["patch_chars"] or bool(patch.strip()) != row["has_patch"]:
        raise ValueError("retained patch disagrees with scorer length or presence")
    return patch


def trace_metrics(trace, expected_calls):
    # Some harness versions emit an action and a response for the same call.
    # Only use exact-call ordinals if the response-only or all-events count reconciles.
    all_calls, with_obs = [], []
    for step in trace["steps"]:
        calls = step.get("tool_calls") or []
        for call in calls:
            name = call.get("function_name")
            if not name:
                continue
            args = call.get("arguments")
            args = args if isinstance(args, dict) else {}
            obs = step.get("observation")
            matched = len(calls) == 1 and obs is not None
            status = _observe(obs)[0] if matched else "unknown"
            category = command_class(args.get("command")) if name == "run_command" else name
            sig = (name, json.dumps(args, sort_keys=True))
            event = (category, status, sig)
            all_calls.append(event)
            if obs is not None:
                with_obs.append(event)
    # Presence of an observed request is still interpretable if callbacks repeat.
    feedback = reduce_feedback(trace)
    result = {"trace_present": 1,
              "explicit_check_after_edit_request_seen": int(feedback["tests_after_first_edit"] > 0),
              "opaque_shell_seen": int(feedback["unclassified_opaque_commands"] > 0)}
    if len(all_calls) == expected_calls:
        events = all_calls
    elif len(with_obs) == expected_calls:
        events = with_obs
    else:
        return result, None
    result["trace_count_matches_scorer"] = 1
    reads = set()
    first_write = None
    post_test = False
    later_write = False
    for index, (category, status, sig) in enumerate(events, 1):
        if category in {"read_file", "source_read", "search_similar_code", "get_code_neighbors", "get_code_subgraph"}:
            result["read_events"] = result.get("read_events", 0) + 1
            if sig in reads:
                result["identical_read_requests"] = result.get("identical_read_requests", 0) + 1
            reads.add(sig)
        if category in {"edit_file", "write_file", "source_mutation"}:
            result["edit_attempt_events"] = result.get("edit_attempt_events", 0) + 1
            if status == "error":
                result["edit_error_events"] = result.get("edit_error_events", 0) + 1
            elif status == "ok":
                if first_write is None:
                    first_write = index
                later_write |= post_test
        if category in {"explicit_test", "inline_assert"} and first_write is not None:
            post_test = True
    result["observed_successful_write"] = int(first_write is not None)
    result["explicit_test_after_successful_write"] = int(post_test)
    result["successful_write_after_such_test"] = int(later_write)
    return result, first_write


def analyze(root, tasks_path):
    data = json.loads((root / RESULT).read_text())
    checked = assess(data)
    if any(checked["error_evaluations"].values()):
        raise ValueError("incomplete grader observations")
    rows = {(r["instance_id"], r["arm"]): r for r in data["results"]}
    ids = {task for task, arm in rows}
    tasks = read_selected_tasks(tasks_path, ids)
    traces = {}
    for p in root.rglob("trace_*.json"):
        task = p.stem.removeprefix("trace_")
        if task not in ids:
            continue
        key = (task, ARMS[int("public-prompt" in p.relative_to(root).parts)])
        if key in traces:
            raise ValueError("ambiguous trace for arm")
        traces[key] = p
    groups = defaultdict(lambda: defaultdict(Counter))
    ordinals = defaultdict(list)
    paired = defaultdict(Counter)
    for task in sorted(ids):
        family = task.split("_")[0]
        original = tasks[task]
        gold = package_diff(original["patch"], family)
        test_paths = set(diff_evidence(original.get("test_patch") or ""))
        left, right = (rows[task, a]["resolved"] for a in ARMS)
        group = {(True, True): "both", (False, True): "rescued",
                 (True, False): "regressed", (False, False): "both_failed"}[left, right]
        patches, locations, regions = [], [], []
        for arm in ARMS:
            row = rows[task, arm]
            stats = groups[group][arm]
            stats["n"] += 1
            patch = saved_patch(root, row)
            patches.append(patch)
            pkg = package_diff(patch, family)
            locations.append(set(pkg) & set(gold))
            regions.append({(p, g) for p in locations[-1] for g in gold[p]
                            if any(abs(g - h) <= 20 for h in pkg[p])})
            stats["retained_nonempty"] += int(bool(patch))
            stats["touches_package"] += int(bool(pkg))
            stats["ref_touches_package"] += int(bool(gold))
            stats["ref_multifile_package"] += int(len(gold) > 1)
            stats["any_ref_package_file"] += int(bool(locations[-1]))
            stats["all_ref_package_files"] += int(bool(gold) and set(gold) <= set(pkg))
            stats["ref_hunk_within_20_lines"] += int(bool(overlap_hunks(gold, pkg)))
            stats["shares_grader_test_file"] += int(bool(set(diff_evidence(patch)) & test_paths))
            trace = traces.get((task, arm))
            if trace:
                trace_stats, first = trace_metrics(json.loads(trace.read_text()), row["tool_calls"])
                stats.update(trace_stats)
                if first is not None:
                    ordinals[group, arm].append(first)
        pairs = paired[group]
        pairs["n"] += 1
        pairs["identical_patch_text"] += int(patches[0] == patches[1])
        pairs["both_nonempty"] += int(all(patches))
        pairs["candidate_gains_ref_files_both_nonempty"] += int(all(patches) and bool(locations[1] - locations[0]))
        pairs["candidate_loses_ref_files_both_nonempty"] += int(all(patches) and bool(locations[0] - locations[1]))
        pairs["candidate_gains_ref_hunks_both_nonempty"] += int(all(patches) and bool(regions[1] - regions[0]))
        pairs["candidate_loses_ref_hunks_both_nonempty"] += int(all(patches) and bool(regions[0] - regions[1]))
    for group, arms in groups.items():
        for arm, stats in arms.items():
            values = ordinals[group, arm]
            stats["first_observed_successful_write_n"] = len(values)
            stats["first_observed_successful_write_call_median"] = median(values) if values else None
    return {"cohort": len(ids), "by_outcome": groups, "paired": paired}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--tasks", required=True, type=Path)
    args = parser.parse_args()
    print("CLEAN17_RETAINED_EVIDENCE=" + json.dumps(analyze(args.root, args.tasks), sort_keys=True))
