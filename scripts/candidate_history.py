"""Private diagnostic: record source at tool boundaries; grade only after the run."""

import argparse
import base64
import hashlib
import importlib.util
import inspect
import io
import json
from pathlib import Path
import shlex
import subprocess
import tarfile
import tempfile
import time


TAG = "refs/tags/_swegemma_baseline"
ROOT = Path(__file__).resolve().parents[1]


def git(workspace, *arguments):
    return subprocess.check_output(
        ["git", "-C", str(workspace), *arguments], stderr=subprocess.PIPE, timeout=10,
    )


def collect_patch(workspace, baseline):
    patch = git(workspace, "diff", "--binary", "--no-ext-diff", "--no-textconv", baseline, "--")
    for raw in git(workspace, "ls-files", "--others", "--exclude-standard", "-z").split(b"\0"):
        if not raw:
            continue
        process = subprocess.run(
            ["git", "diff", "--no-index", "--binary", "--no-ext-diff", "--no-textconv",
             "--", "/dev/null", raw.decode()], cwd=workspace, capture_output=True, timeout=10,
        )
        if process.returncode not in (0, 1):
            raise ValueError("untracked_diff_failed")
        patch += process.stdout
    if len(patch) > 4 * 1024 * 1024:
        raise ValueError("patch_size_limit")
    return patch


class History:
    def __init__(self, workspace, directory, *, read_patch=None, baseline=None):
        self.workspace = Path(workspace).resolve()
        self.directory = Path(directory).resolve()
        if self.directory.is_relative_to(self.workspace):
            raise ValueError("history_must_be_outside_agent_workspace")
        self.directory.mkdir(parents=True, exist_ok=True)
        self.path = self.directory / "history.json"
        self.baseline = baseline or git(self.workspace, "rev-parse", TAG + "^{commit}").decode().strip()
        self.read_patch = read_patch or (lambda: collect_patch(self.workspace, self.baseline))

    @classmethod
    def for_sandbox(cls, sandbox, directory, workspace="/workspace"):
        result = sandbox.run_command(
            f"git -C {shlex.quote(workspace)} rev-parse '{TAG}^{{commit}}'", timeout=10,
        )
        if result.exit_code != 0:
            raise ValueError("sandbox_baseline_unavailable")
        baseline = result.stdout.strip()
        code = "import base64, subprocess\nfrom pathlib import Path\n"
        code += inspect.getsource(git) + "\n" + inspect.getsource(collect_patch)
        code += f"\nprint(base64.b64encode(collect_patch(Path({workspace!r}), {baseline!r})).decode())\n"
        command = "python3 -c " + shlex.quote(code)
        def read_patch():
            result = sandbox.run_command(command, timeout=15)
            if result.exit_code != 0:
                raise ValueError("sandbox_capture_failed")
            return base64.b64decode(result.stdout.strip(), validate=True)
        return cls(workspace, directory, read_patch=read_patch, baseline=baseline)

    def start(self):
        if self.path.exists():
            raise ValueError("refuse_to_replace_history")
        self.path.write_text(json.dumps({
            "baseline": self.baseline, "complete": True, "finished": False,
            "events": [], "revisions": {}, "capture_seconds": 0.0,
        }))
        self.observe("<start>")
        data = json.loads(self.path.read_text())
        if data["events"] and data["events"][0].get("patch_bytes"):
            data["complete"] = False
            self.path.write_text(json.dumps(data, indent=2))

    def observe(self, tool, tool_failed=False):
        data = json.loads(self.path.read_text())
        event = {"tool": tool, "tool_failed": bool(tool_failed)}
        start = time.monotonic()
        try:
            patch = self.read_patch()
            if patch != self.read_patch():
                raise ValueError("source_changed_during_capture")
            digest = hashlib.sha256(patch).hexdigest()
            (self.directory / (digest + ".patch")).write_bytes(patch)
            data["revisions"][digest] = len(patch)
            event.update(revision=digest, patch_bytes=len(patch))
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            data["complete"] = False
            event["capture_error"] = type(error).__name__
        data["capture_seconds"] += time.monotonic() - start
        data["events"].append(event)
        self.path.write_text(json.dumps(data, indent=2))

    def finish(self):
        self.observe("<final>")
        data = json.loads(self.path.read_text())
        data["finished"] = True
        self.path.write_text(json.dumps(data, indent=2))


def adk_plugin(history):
    """Attach only to a private evaluation App, never the submission agent."""
    from google.adk.plugins.base_plugin import BasePlugin
    class CandidateHistoryPlugin(BasePlugin):
        def __init__(self):
            super().__init__(name="candidate_history_observer")

        async def after_tool_callback(self, *, tool, tool_args, tool_context, result):
            parsed = result
            if isinstance(parsed, str):
                try:
                    parsed = json.loads(parsed)
                except json.JSONDecodeError:
                    parsed = {}
            failed = isinstance(parsed, dict) and parsed.get("status") in {"error", "timeout"}
            history.observe(tool.name, tool_failed=failed)
            return None

        async def on_tool_error_callback(self, *, tool, tool_args, tool_context, error):
            history.observe(tool.name, tool_failed=True)
            return None
    return CandidateHistoryPlugin()


def grade_history(workspace, directory, check, gold_patch, timeout=10):
    workspace, directory = Path(workspace).resolve(), Path(directory).resolve()
    data = json.loads((directory / "history.json").read_text())
    path = ROOT / "experiments/paired-check-v0/skill/scripts/compare.py"
    spec = importlib.util.spec_from_file_location("source_check_runner", path)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    archive = git(workspace, "archive", data["baseline"])
    report = {
        "scope": "independent check at recorded tool boundaries, not all possible repairs",
        "grader_sha256": hashlib.sha256(check.encode()).hexdigest(),
        "history_complete": data["complete"] and data["finished"],
        "capture_seconds": round(data["capture_seconds"], 4),
        "failed_edit_calls": sum(e["tool_failed"] and e["tool"] in {"edit_file", "write_file"}
                                 for e in data["events"]),
        "grades": {},
    }
    with tempfile.TemporaryDirectory(prefix="candidate-grading-") as temporary:
        temporary = Path(temporary)
        code = temporary / "independent-check.txt"
        code.write_text(check)
        def grade(patch, label):
            snapshot = temporary / label
            snapshot.mkdir()
            with tarfile.open(fileobj=io.BytesIO(archive)) as tree:
                tree.extractall(snapshot, filter="data")
            if patch:
                process = subprocess.run(["git", "apply", "--binary", "--"], input=patch,
                                         cwd=snapshot, capture_output=True, timeout=10)
                if process.returncode:
                    return {"grade": "blocked", "reason": "patch_apply_failed"}
            result = runner.run_check(code, snapshot, workspace, timeout, label, temporary)
            verified = result["source_imports"] and not result["origin_conflicts"] and not result["timed_out"]
            dependency_error = any(s in result["stderr"] for s in ("ModuleNotFoundError", "ImportError"))
            label = ("pass" if result["return_code"] == 0 else "fail") if verified and not dependency_error else "blocked"
            return {"grade": label, "return_code": result["return_code"],
                    "source_imports": result["source_imports"], "timed_out": result["timed_out"]}
        report["controls"] = {"base": grade(b"", "base"), "reference": grade(gold_patch, "reference")}
        if (report["controls"]["base"]["grade"], report["controls"]["reference"]["grade"]) != ("fail", "pass"):
            return {**report, "diagnosis": "ineligible_controls"}
        for digest in data["revisions"]:
            patch = (directory / (digest + ".patch")).read_bytes()
            if hashlib.sha256(patch).hexdigest() != digest:
                raise ValueError("candidate_patch_hash_mismatch")
            report["grades"][digest] = grade(patch, "revision_" + digest[:16])
    final_event = data["events"][-1] if data["events"] else {}
    final = final_event.get("revision") if data["finished"] and final_event.get("tool") == "<final>" else None
    grades = report["grades"]
    passing = [k for k, v in grades.items() if v["grade"] == "pass"]
    final_grade = grades.get(final, {}).get("grade", "blocked")
    report.update(passing_candidates=len(passing), final_grade=final_grade,
                  nonempty_candidates=sum(bool(n) for n in data["revisions"].values()))
    if final_grade == "pass":
        diagnosis = "retained_passing_candidate"
    elif passing and final_grade == "fail":
        diagnosis = "discarded_passing_candidate"
    elif not report["history_complete"]:
        diagnosis = "inconclusive_history"
    elif any(v["grade"] == "blocked" for v in grades.values()):
        diagnosis = "inconclusive_grades"
    elif not report["nonempty_candidates"]:
        diagnosis = "no_materialized_source_patch"
    else:
        diagnosis = "no_passing_candidate_observed"
    return {**report, "diagnosis": diagnosis}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--history", type=Path, required=True)
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("start")
    observe = sub.add_parser("observe")
    observe.add_argument("--tool", required=True)
    observe.add_argument("--tool-failed", action="store_true")
    sub.add_parser("finish")
    grade = sub.add_parser("grade")
    grade.add_argument("--check", type=Path, required=True)
    grade.add_argument("--reference-patch", type=Path, required=True)
    options = parser.parse_args()
    if options.action == "grade":
        print(json.dumps(grade_history(options.workspace, options.history,
                                       options.check.read_text(), options.reference_patch.read_bytes())))
    else:
        history = History(options.workspace, options.history)
        if options.action == "observe":
            history.observe(options.tool, options.tool_failed)
        else:
            getattr(history, options.action)()


if __name__ == "__main__":
    main()
