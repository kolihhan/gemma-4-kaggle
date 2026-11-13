"""Private observer for the frozen 31B champion. The submission has no observer."""
from __future__ import annotations

import inspect
import json
from pathlib import Path
import re
import tempfile
import time
from unittest.mock import patch

from scripts.candidate_history import History, adk_plugin


def earlier_revisions(history, final_patch):
    """Return up to four distinct revisions and the full observed denominator."""
    data = json.loads(history.path.read_text())
    patches = []
    seen = {final_patch.strip()}
    for digest, size in data["revisions"].items():
        if size:
            candidate = (history.directory / (digest + ".patch")).read_text()
            key = candidate.strip()
            if key and key not in seen:
                patches.append(candidate)
                seen.add(key)
    return (patches if len(patches) <= 4 else patches[:2] + patches[-2:]), len(patches), data


def phase_seconds(trace, elapsed):
    """Observed tool time; the remainder includes model, compaction and waits."""
    if not trace or elapsed is None:
        return None
    pending = {}
    intervals = []
    for entry in trace.entries:
        tool = entry.tool_name
        if not tool:
            continue
        if entry.event_type == "tool_call":
            category = {"edit_file": "editing", "write_file": "editing",
                        "submit_patch": "finalizing"}.get(tool, "search_and_other")
            if tool == "run_command":
                command = (entry.tool_args or {}).get("command", "")
                if isinstance(command, str) and re.search(r"\b(pytest|unittest|assert)\b", command):
                    category = "recognized_test"
            pending.setdefault(tool, []).append((entry.elapsed, category))
        elif entry.event_type == "tool_response" and pending.get(tool):
            start, category = pending[tool].pop(0)
            if entry.elapsed > start:
                intervals.append((start, entry.elapsed, category))
    if not intervals:
        return None
    bounds = sorted({x for a, b, _ in intervals for x in (a, b)})
    seconds = {}
    for start, end in zip(bounds, bounds[1:]):
        active = {c for a, b, c in intervals if a <= start < b}
        if active:
            key = active.pop() if len(active) == 1 else "overlapping_tools"
            seconds[key] = seconds.get(key, 0) + end - start
    seconds["outside_observed_tools"] = max(0.0, elapsed - sum(seconds.values()))
    return {key: round(value, 3) for key, value in sorted(seconds.items())}


async def checkpoint_evaluation(evaluator, task, index, total):
    from swegemma.deduplication import resolve_task_snapshot_paths
    from swegemma.harness import agent_runner
    from swegemma.harness.verification import verify_task

    # Hydration and gold/no-op grading happen outside the solver sandbox.
    truth = evaluator._hydrate_task_from_secret(task)
    if not isinstance(truth.patch, str) or not truth.patch.strip():
        raise ValueError("missing gold reference")
    snapshot, base, task_delta = resolve_task_snapshot_paths(
        evaluator.config.snapshots_dir, truth.instance_id, truth.repo
    )

    async def grade(candidate):
        result = await verify_task(
            evaluator.docker, evaluator.config, truth, snapshot,
            base_snapshot_path=base, patch_path=task_delta,
            agent_patch=candidate, start_time=time.perf_counter(),
        )
        return {"resolved": bool(result.resolved), "exit": result.test_exit_code}

    control = {"noop": await grade(""), "gold": await grade(truth.patch)}
    record = {"instance_id": task.instance_id, "integrity": control}
    if (control["noop"]["resolved"] or control["noop"]["exit"] != 1
            or not control["gold"]["resolved"] or control["gold"]["exit"] != 0):
        return {**record, "status": "ineligible_current_verifier"}

    original_app = agent_runner.App
    original_stop = agent_runner.sandbox_stop
    runner = evaluator._run_agent_sandbox
    observed = {}

    with tempfile.TemporaryDirectory(prefix="gemma-patch-history-") as directory:
        def attach_app(**kwargs):
            context = observed["context"]
            history = History.for_sandbox(context.sandbox, Path(directory))
            history.start()
            observed["history"] = history
            observer = adk_plugin(history)
            before = observer.before_tool_callback
            after = observer.after_tool_callback
            on_error = observer.on_tool_error_callback
            change_tools = {"edit_file", "write_file", "run_command", "submit_patch"}

            async def capture(callback, **event):
                if event["tool"].name in change_tools:
                    result = await callback(**event)
                    observed["boundaries"].append(round(context.agent_elapsed_seconds, 3))
                    return result
                return None

            async def before_tool_callback(*, tool, tool_args, tool_context):
                if tool.name == "submit_patch":
                    return await capture(before, tool=tool, tool_args=tool_args, tool_context=tool_context)
                return None

            async def after_tool_callback(*, tool, tool_args, tool_context, result):
                return await capture(after,
                                     tool=tool, tool_args=tool_args, tool_context=tool_context, result=result)

            async def on_tool_error_callback(*, tool, tool_args, tool_context, error):
                return await capture(on_error,
                                     tool=tool, tool_args=tool_args, tool_context=tool_context, error=error)

            observer.before_tool_callback = before_tool_callback
            observer.after_tool_callback = after_tool_callback
            observer.on_tool_error_callback = on_tool_error_callback
            kwargs["plugins"] = [*kwargs["plugins"], observer]
            return original_app(**kwargs)

        async def run_observed(*args, **kwargs):
            observed["context"] = inspect.signature(runner).bind(*args, **kwargs).arguments["context"]
            observed["boundaries"] = []
            async def stop_observed(manager, current):
                try:
                    if current == observed["context"].container_id and "history" in observed:
                        observed["history"].finish()
                finally:
                    await original_stop(manager, current)

            with patch.object(agent_runner, "App", attach_app), patch.object(
                agent_runner, "sandbox_stop", stop_observed
            ):
                return await runner(*args, **kwargs)

        with patch.object(evaluator, "_run_agent_sandbox", run_observed):
            result = await evaluator.evaluate_task(task, index, total)
        final_patch = result.agent_patch or ""
        history = observed.get("history")
        record.update(
            status="completed", resolved=bool(result.resolved),
            test_exit_code=result.test_exit_code, has_patch=bool(final_patch.strip()),
            tool_calls=result.tool_calls, llm_calls=result.total_llm_calls,
            duration_seconds=round(result.duration_seconds or 0, 3),
        )
        if history is None:
            return {**record, "history_complete": False, "earlier_grades": []}
        candidates, count, data = earlier_revisions(history, final_patch)
        event_times = [None, *observed["boundaries"], None]
        first_edit = None
        if len(event_times) == len(data["events"]):
            first_edit = next((t for t, e in zip(event_times, data["events"])
                               if t is not None and e.get("patch_bytes")), None)
        agent_seconds = observed["context"].agent_elapsed_seconds
        return {
            **record,
            "history_complete": bool(data["complete"] and data["finished"]),
            "agent_seconds": round(agent_seconds, 3),
            "phase_seconds": phase_seconds(result.trace, agent_seconds),
            "capture_seconds": round(data["capture_seconds"], 3),
            "first_materialized_edit_seconds": first_edit,
            "earlier_revisions": count,
            "earlier_grades": [] if result.resolved else [await grade(p) for p in candidates],
        }
