"""CPU-only action-funnel analysis for an ALREADY RECORDED private 31B history.

Observes tool order and source revision presence; never grades private patches,
executes candidate code, or claims that a nonempty diff fixes an issue.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

CHECKPOINTS = (16, 20)
OBSERVE = frozenset({"read_file", "search_similar_code", "get_code_neighbors",
                      "get_code_subgraph", "load_skill", "run_skill_script"})
EXPLICIT_EDIT = frozenset({"edit_file", "write_file"})
OPAQUE = frozenset({"run_command"})

def analyze(history: dict) -> dict:
    events = history.get("events")
    if not isinstance(events, list):
        raise ValueError("history_events_missing")
    calls = []
    last_rev = None
    for event in events:
        if not isinstance(event, dict):
            raise ValueError("malformed_history_event")
        tool = event.get("tool")
        if tool in ("<start>", "<final>"):
            if event.get("revision"):
                last_rev = event["revision"]
            continue
        # submit_patch is observed both before and after the tool call;
        # a request is counted once even if the callback later reports an error.
        if tool == "submit_patch" and event.get("phase") in {"result", "error"}:
            continue
        if not isinstance(tool, str):
            raise ValueError("missing_tool_name")
        revision = event.get("revision", last_rev)
        if event.get("revision"):
            last_rev = revision
        calls.append({
            "tool": tool,
            "revision": revision,
            "nonempty": event.get("patch_bytes", None),
            "failed": event.get("tool_failed") is True,
        })

    def revision_is_nonempty(revision):
        size = history.get("revisions", {}).get(revision)
        return isinstance(size, int) and size > 0

    def first_idx(test):
        return next((i for i, c in enumerate(calls, 1) if test(c)), None)

    revisions = [c["revision"] for c in calls]
    samples = {}
    for n in CHECKPOINTS:
        if len(calls) < n:
            samples[str(n)] = {"observed": False}
            continue
        rev = revisions[n-1]
        samples[str(n)] = {
            "observed": True,
            "nonempty_patch_observed": revision_is_nonempty(rev),
            "revision_changes_after": sum(
                a != b for a, b in zip(revisions[n-1:-1], revisions[n:])
            ),
            "correctness": "UNKNOWN_without_independent_grader",
        }
    return {
        "history_complete": history.get("complete") is True and history.get("finished") is True,
        "tool_calls_observed": len(calls),
        "first_materialized_patch_call": first_idx(lambda c: revision_is_nonempty(c["revision"])),
        "first_explicit_edit_call": first_idx(lambda c: c["tool"] in EXPLICIT_EDIT),
        "first_submit_request_call": first_idx(lambda c: c["tool"] == "submit_patch"),
        "observation_tool_calls": sum(c["tool"] in OBSERVE for c in calls),
        "opaque_command_calls": sum(c["tool"] in OPAQUE for c in calls),
        "reported_tool_failures": sum(c["failed"] for c in calls),
        "nonempty_final_tree": revision_is_nonempty(
            events[-1].get("revision") if events and events[-1].get("tool") == "<final>" else None
        ),
        "checkpoints": samples,
        "scope": "tool-boundary observation only; no correctness, no causal improvement",
    }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--history", type=Path, required=True)
    args = parser.parse_args()
    report = analyze(json.loads(args.history.read_text()))
    print("GEMMA_ACTION_FUNNEL_SAFE=" + json.dumps(report, sort_keys=True))

if __name__ == "__main__":
    main()
