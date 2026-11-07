"""Inspect archived final outcomes without inventing missing candidate histories."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import zipfile

from scripts.analyze_root_trace_mechanics import _decode_observation


def inventory(archive):
    archive = Path(archive)
    counts, tasks = Counter(), []
    with zipfile.ZipFile(archive) as zipped:
        summary = json.loads(zipped.read("verifier_baseline_results.json"))
        traces = {Path(name).stem.removeprefix("trace_"): json.loads(zipped.read(name))
                  for name in zipped.namelist() if "/traces/trace_" in name and name.endswith(".json")}
        results = summary["results"]
        if len(results) != len({r["instance_id"] for r in results}) or set(traces) != {r["instance_id"] for r in results}:
            raise ValueError("archive_result_trace_mismatch")
        for row in results:
            if type(row.get("has_patch")) is not bool or type(row.get("resolved")) is not bool:
                raise ValueError("missing_final_patch_or_verdict")
            edit_errors, partial_diffs = 0, 0
            for step in traces[row["instance_id"]]["steps"]:
                calls = step.get("tool_calls") or []
                result = _decode_observation(step.get("observation"))
                if len(calls) == 1:
                    if calls[0].get("function_name") in {"edit_file", "write_file"} and result.get("status") in {"error", "timeout"}:
                        edit_errors += 1
                    if calls[0].get("function_name") == "run_command" and "diff --git " in str(result.get("stdout", "")):
                        partial_diffs += 1
            if row["resolved"]:
                category = "reported_resolved_final"
            elif row["has_patch"]:
                category = "unresolved_nonempty_patch"
            elif edit_errors:
                category = "no_patch_with_edit_error"
            else:
                category = "no_patch_other"
            counts[category] += 1
            tasks.append({
                "task": row["instance_id"], "final_category": category,
                "recorded_test_exit_code": row.get("test_exit_code"),
                "failed_edit_calls": edit_errors,
                "partial_diff_observations": partial_diffs,
                "candidate_history_verdict": ("reported_final_pass_history_unmeasured" if row["resolved"]
                                              else "unknown_missing_boundary_history_and_grades"),
            })
    return {
        "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "model": summary.get("model"), "task_count": len(tasks), "counts": dict(counts),
        "full_boundary_histories_missing": len(tasks),
        "generation_vs_selection_unknown": sum(not r["resolved"] for r in results), "tasks": tasks,
        "new_model_runs": 0, "new_patch_grading_runs": 0,
        "scope": "descriptive inventory of archived final outcomes; not a causal bottleneck diagnosis",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    options = parser.parse_args()
    result = inventory(options.archive)
    options.output.parent.mkdir(parents=True, exist_ok=True)
    options.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("model", "task_count", "counts", "generation_vs_selection_unknown")}))


if __name__ == "__main__":
    main()
