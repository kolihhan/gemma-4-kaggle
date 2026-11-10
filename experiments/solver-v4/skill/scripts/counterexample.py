"""V4 counterexample-guided repair: lock a model-authored issue-specific test.

This is a *self-generated* witness, never an independent hidden oracle.
The initial source must actually fail with an assertion on the untouched
checkout, and the exact same locked source must pass after a real edit.
No repo tests, source, or config are written by this script.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

BASE = Path(tempfile.gettempdir()) / "gemma4-v4-counterexample"
IDENTIFIER = re.compile(r"^[0-9a-f]{24}$")


def workspace_path(explicit: str | None = None) -> Path:
    if explicit:
        path = Path(explicit).resolve(strict=True)
        if not path.is_dir() or not (path / ".git").exists():
            raise ValueError("explicit workspace is not a git checkout")
        return path
    for candidate in (os.environ.get("SWE_WORKSPACE"), os.environ.get("PWD"),
                      "/workspace", str(Path.cwd())):
        if not candidate:
            continue
        try:
            path = Path(candidate).resolve(strict=True)
        except (OSError, ValueError):
            continue
        if path.is_dir() and (path / ".git").exists():
            return path
    raise ValueError("no active git workspace found")


def check_source(source: str) -> str:
    if not isinstance(source, str) or not 30 <= len(source) <= 6000:
        raise ValueError("test source must be 30..6000 characters")
    try:
        program = ast.parse(source, filename="test_issue_contract.py")
    except SyntaxError as exc:
        raise ValueError("test source cannot parse") from exc
    tests = [node for node in program.body if isinstance(node,
             (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_")]
    if not tests or not any(isinstance(n, ast.Assert)
                            for test in tests for n in ast.walk(test)):
        raise ValueError("need a real test_* function with an assert")
    return source


def _case_dir(workspace: Path) -> Path:
    digest = hashlib.sha256(str(workspace).encode()).hexdigest()[:24]
    return BASE / digest


def _assess(returncode: int | None, output: str) -> str:
    if returncode == 0 and re.search(r"\b\d+ passed\b", output):
        return "pass"
    # Only a real pytest assertion failure counts as a counterexample.
    if (returncode == 1 and "AssertionError" in output and
            re.search(r"\b\d+ failed\b", output)):
        return "fail"
    return "blocked"


def _test(workspace: Path, path: Path, seconds: int) -> dict:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(workspace) + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    command = [sys.executable, "-B", "-m", "pytest", "-q", "-x",
               "-p", "no:cacheprovider", "--disable-warnings", str(path)]
    try:
        p = subprocess.run(command, cwd=workspace, env=env, text=True,
                           capture_output=True, timeout=seconds, check=False)
        combined = (p.stdout + "\n" + p.stderr).strip()
        status = _assess(p.returncode, combined)
        code = p.returncode
    except subprocess.TimeoutExpired:
        combined, status, code = "targeted contract timed out", "blocked", None
    return {"status": status, "exit_code": code,
            "evidence": "\n".join(combined.splitlines()[-22:])[-1500:]}


def compare(before: str, after: str) -> str:
    if before == "fail" and after == "pass":
        return "counterexample_repaired"
    if before == "pass" and after == "fail":
        return "regression"
    if before == "fail" and after == "fail":
        return "still_broken"
    if before == "pass" and after == "pass":
        return "no_baseline_failure"
    return "inconclusive"


def run(workspace: Path, phase: str, *, source: str | None = None,
        case_id: str | None = None, timeout_seconds: int = 20) -> dict:
    workspace = workspace.resolve(strict=True)
    if not (workspace / ".git").exists():
        raise ValueError("workspace is not a git checkout")
    if not isinstance(timeout_seconds, int) or not 1 <= timeout_seconds <= 40:
        raise ValueError("timeout_seconds out of range")
    cases = _case_dir(workspace)

    if phase == "before":
        if case_id is not None or source is None:
            raise ValueError("before needs source and no case-id")
        source = check_source(source)
        case_id = hashlib.sha256((str(workspace) + "\n" + source).encode()).hexdigest()[:24]
        location = cases / case_id
        location.mkdir(parents=True, exist_ok=True)
        test_file = location / "test_issue_contract.py"
        record_file = location / "state.json"
        if test_file.exists() and test_file.read_text(encoding="utf-8") != source:
            raise ValueError("existing case ID source mismatch")
        test_file.write_text(source, encoding="utf-8")
        evidence = _test(workspace, test_file, timeout_seconds)
        record = {"workspace": str(workspace),
                  "test_sha256": hashlib.sha256(source.encode()).hexdigest(),
                  "baseline_status": evidence["status"]}
        record_file.write_text(json.dumps(record, sort_keys=True), encoding="utf-8")
        return {"phase": "before", "case_id": case_id, **evidence,
                "baseline_discriminating": evidence["status"] == "fail",
                "comparison": "baseline_recorded",
                "independent_issue_resolved": False,
                "test_relevance_verified": False,
                "advice": "Only a relevant before-fail justifies editing; use source+issue evidence."}

    if phase != "after" or source is not None or not case_id or not IDENTIFIER.fullmatch(case_id):
        raise ValueError("after needs locked case-id only")
    location = cases / case_id
    state = json.loads((location / "state.json").read_text(encoding="utf-8"))
    test_file = location / "test_issue_contract.py"
    raw = test_file.read_bytes()
    if (state.get("workspace") != str(workspace) or
            hashlib.sha256(raw).hexdigest() != state.get("test_sha256")):
        raise ValueError("test source or workspace changed after baseline")
    result = _test(workspace, test_file, timeout_seconds)
    comparison = compare(state["baseline_status"], result["status"])
    return {"phase": "after", "case_id": case_id, **result,
            "baseline_status": state["baseline_status"],
            "baseline_discriminating": state["baseline_status"] == "fail",
            "comparison": comparison,
            "independent_issue_resolved": False,
            "test_relevance_verified": False,
            "advice": (
                "Self-authored counterexample now passes; check unrelated existing tests and diff."
                if comparison == "counterexample_repaired" else
                "Do not claim the issue fixed; reconsider hypothesis or blocked test."
            )}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", required=True, choices=("before", "after"))
    parser.add_argument("--source")
    parser.add_argument("--case-id")
    parser.add_argument("--workspace")
    parser.add_argument("--timeout-seconds", type=int, default=20)
    args = parser.parse_args()
    result = run(
        workspace_path(args.workspace), args.phase,
        source=args.source, case_id=args.case_id,
        timeout_seconds=args.timeout_seconds,
    )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
