"""Run one bounded, real pytest witness and compare pre/post-edit evidence.

This script runs inside the *existing per-task offline sandbox*. It does not
edit repository source, read grader gold patches, or claim hidden correctness.
An ADK model has to actually invoke run_skill_script to obtain the result.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

DEFAULT_STATE = Path("/tmp/gemma4-solver-v3r-witness")
VALID_PHASES = {"before", "after"}


def safe_test_node(workspace: Path, target: str) -> str:
    if not isinstance(target, str) or not target or len(target) > 350:
        raise ValueError("invalid test node")
    if any(ch in target for ch in ("\n", "\r", "\x00", "\\", " ")):
        raise ValueError("unsafe test node")
    raw_path = target.split("::", 1)[0]
    path = PurePosixPath(raw_path)
    if (path.is_absolute() or
            any(segment in {"", ".", ".."} for segment in raw_path.split("/")) or
            not path.suffix == ".py"):
        raise ValueError("test target must be a relative Python test file/node")
    root = workspace.resolve(strict=True)
    try:
        full = (root / raw_path).resolve(strict=True)
    except (FileNotFoundError, OSError) as exc:
        raise ValueError("test target outside workspace or missing") from exc
    if not full.is_relative_to(root) or not full.is_file():
        raise ValueError("test target outside workspace or missing")
    return target


def _key(workspace: Path, target: str) -> str:
    return hashlib.sha256(
        (str(workspace.resolve()) + "\n" + target).encode("utf-8")
    ).hexdigest()


def _status(returncode: int, output: str) -> str:
    if returncode == 0 and re.search(r"(?m)(?:\d+ passed|1 passed)\b", output):
        return "pass"
    if returncode == 1 and re.search(
            r"(?im)^\s*FAILED\s|\b\d+ failed\b", output):
        return "fail"
    return "blocked"


def _comparison(before: str | None, after: str) -> str:
    if before is None:
        return "baseline_unavailable"
    if before == "pass" and after == "fail":
        return "regression_introduced"
    if before == "fail" and after == "pass":
        return "repair_demonstrated"
    if before == "fail" and after == "fail":
        return "not_yet_fixed"
    if before == "pass" and after == "pass":
        return "already_passing"
    return "inconclusive"


def run_witness(workspace: Path, target: str, phase: str, *,
                timeout_seconds: int = 20,
                state_dir: Path | None = None) -> dict:
    if phase not in VALID_PHASES:
        raise ValueError("phase must be before or after")
    if (not isinstance(timeout_seconds, int) or
            not 1 <= timeout_seconds <= 45):
        raise ValueError("timeout_seconds out of bounds")
    workspace = Path(workspace).resolve(strict=True)
    target = safe_test_node(workspace, target)
    state = Path(state_dir) if state_dir is not None else DEFAULT_STATE
    if state.is_relative_to(workspace):
        raise ValueError("witness state must remain outside repository")
    key = _key(workspace, target)
    file = state / (key + ".json")
    before: str | None = None
    if phase == "after" and file.is_file():
        saved = json.loads(file.read_text(encoding="utf-8"))
        if saved.get("target") == target and saved.get("workspace") == str(workspace):
            before = saved.get("status")
            if before not in {"pass", "fail", "blocked"}:
                before = None

    command = [sys.executable, "-B", "-m", "pytest", "-q", "-x",
               "--disable-warnings", target]
    try:
        proc = subprocess.run(
            command, cwd=workspace, capture_output=True, text=True,
            timeout=timeout_seconds, check=False,
        )
        output = (proc.stdout + "\n" + proc.stderr).strip()
        returncode = proc.returncode
        status = _status(returncode, output)
    except subprocess.TimeoutExpired:
        output = "targeted pytest timed out; result unknown"
        returncode = None
        status = "blocked"

    if phase == "before":
        state.mkdir(parents=True, exist_ok=True)
        file.write_text(json.dumps({
            "target": target,
            "workspace": str(workspace),
            "status": status,
        }, sort_keys=True), encoding="utf-8")
        comparison = "baseline_recorded"
    else:
        comparison = _comparison(before, status)

    lines = output.splitlines()
    # Emit bounded real output, not a model-composed claim that tests passed.
    evidence = "\n".join(lines[-30:])[-1800:]
    return {
        "phase": phase,
        "target": target,
        "status": status,
        "comparison": comparison,
        "exit_code": returncode,
        "evidence": evidence,
        "verified_test_process": status in {"pass", "fail"},
        "independent_issue_resolved": False,
        "advice": (
            "Inspect assertion/traceback and revise the changed implementation"
            if status == "fail" else
            "Test collection/tool failure or timeout; do not claim verified"
            if status == "blocked" else
            "This specific targeted test passed; hidden issue status unknown"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", required=True, choices=sorted(VALID_PHASES))
    parser.add_argument("--target", required=True)
    parser.add_argument("--workspace", default="/workspace")
    parser.add_argument("--timeout_seconds", type=int, default=20)
    args = parser.parse_args()
    result = run_witness(
        Path(args.workspace), args.target, args.phase,
        timeout_seconds=args.timeout_seconds,
    )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
