"""Private diagnostic adapter for the OFFICIAL 31B runner; never ship in an agent zip.

Attaches the already-tested Candidate History ADK plugin to the official
swegemma App. Reference fixes and grading labels never enter agent context.
Run sequentially: official App/SwegemmaContext globals are temporarily wrapped.
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import json
import re
import time

# This source is embedded AFTER scripts/candidate_history.py when rendered for
# the private Kaggle Notebook; History and adk_plugin are then available.

class ContextSandboxAdapter:
    """Expose the official SwegemmaContext.exec as the recorder's sandbox interface."""
    def __init__(self, context):
        self.context = context

    def run_command(self, command, timeout=15):
        result = self.context.exec(command, timeout=timeout)
        code = getattr(result, "exit_code", None)
        if code is None:
            code = getattr(result, "returncode", None)
        if code is None:
            code = getattr(result, "return_code", None)
        stdout = getattr(result, "stdout", None)
        if type(code) is not int or not isinstance(stdout, (str, bytes)):
            raise TypeError("official_sandbox_result_contract_unknown")
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8")
        return SimpleNamespace(exit_code=code, stdout=stdout)


async def run_with_history(docker, config, task, snapshot_path, *, history_directory):
    """Run unmodified 31B; capture full patch snapshots privately at tool boundaries."""
    import swegemma.harness.agent_runner as runner
    from scripts.candidate_history import History, adk_plugin

    if not re.fullmatch(r"[A-Za-z0-9_.-]+", task.instance_id):
        raise ValueError("unsafe_task_identifier")
    target = Path(history_directory)
    if target.exists():
        raise FileExistsError("history_directory_reuse_forbidden")
    target.mkdir(parents=True)
    if not callable(getattr(runner, "sandbox_stop", None)):
        raise RuntimeError("official_runner_stop_hook_missing")
    original_context = runner.SwegemmaContext
    original_app = runner.App
    original_stop = runner.sandbox_stop
    state = {"context": None, "history": None, "hook_error": None, "stopped": False}
    started = time.monotonic()

    def context_factory(*args, **kwargs):
        instance = original_context(*args, **kwargs)
        state["context"] = instance
        return instance

    def app_factory(**kwargs):
        if state["context"] is None or state["history"] is not None:
            raise RuntimeError("official_app_context_not_unique")
        hist = History.for_sandbox(ContextSandboxAdapter(state["context"]), target / "snapshots")
        hist.start()
        kwargs["plugins"] = [*kwargs.get("plugins", []), adk_plugin(hist)]
        state["history"] = hist
        return original_app(**kwargs)

    async def stop_factory(*args, **kwargs):
        try:
            hist = state["history"]
            if hist is not None and not state["stopped"]:
                try:
                    hist.finish()  # Before the sandbox is torn down.
                except Exception as exc:
                    state["hook_error"] = type(exc).__name__
                state["stopped"] = True
        finally:
            return await original_stop(*args, **kwargs)

    runner.SwegemmaContext = context_factory
    runner.App = app_factory
    runner.sandbox_stop = stop_factory
    failure = None
    try:
        return await runner.run_agent_sandbox(docker, config, task, snapshot_path)
    except Exception as exc:
        failure = type(exc).__name__
        raise
    finally:
        runner.SwegemmaContext = original_context
        runner.App = original_app
        runner.sandbox_stop = original_stop
        hist = state["history"]
        report = {
            "version": "gemma31-history-v1",
            "task": task.instance_id,
            "observer_installed": hist is not None,
            "finalized_before_sandbox_stop": state["stopped"],
            "hook_error_type": state["hook_error"],
            "model_error_type": failure,
            "elapsed_observer_wrapper_s": round(time.monotonic() - started, 3),
        }
        if hist is not None and hist.path.exists():
            data = json.loads(hist.path.read_text())
            report.update({
                "history_complete": bool(data.get("complete") and data.get("finished")),
                "unique_revisions": len(data.get("revisions", {})),
                "nonempty_revisions": sum(bool(v) for v in data.get("revisions", {}).values()),
                "boundary_events": len(data.get("events", [])),
                "capture_seconds": round(float(data.get("capture_seconds", 0)), 3),
                "submit_attempts": sum(e.get("tool") == "submit_patch" and e.get("phase") == "attempt" for e in data.get("events", [])),
            })
        (target / "status.json").write_text(json.dumps(report, sort_keys=True, indent=2))
