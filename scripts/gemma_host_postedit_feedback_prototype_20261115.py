#!/usr/bin/env python3
"""Bounded host-side post-edit test feedback prototype for Gemma 4.

This is an executable tool-side mechanism, NOT a new system prompt,
a deployed Kaggle candidate, a coding-agent success result or a grader score.

The launcher supplies changed paths (not a reference patch). The tool picks a
nearby exact test, executes it without shell expansion under a hard timeout and
returns a small status. Never run broad suites, install deps or expose output.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile


def safe_path(root: Path, path: str) -> Path:
    """Reject escapes, absolute paths, symlinks outside workspace."""
    rel = Path(path)
    if rel.is_absolute() or ".." in rel.parts or not str(rel).strip():
        raise ValueError("invalid_relative_changed_path")
    resolved = (root / rel).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError("changed_path_outside_workspace") from exc
    return resolved


def discover(root: Path, changed_paths: list[str]) -> list[Path]:
    """Exact changed test first; otherwise matching basename tests only.

    Not finding a test is an honest absence of safely discoverable evidence.
    """
    candidates: list[Path] = []
    for changed in changed_paths:
        file = safe_path(root, changed)
        if file.suffix != ".py":
            continue
        if file.name.startswith("test_") and file.is_file():
            candidates.append(file)
            continue
        name = "test_" + file.stem + ".py"
        locations = (
            file.parent / name,
            file.parent / "tests" / name,
            root / "tests" / name,
        )
        for candidate in locations:
            if candidate.is_file() and candidate.resolve().is_relative_to(root.resolve()):
                candidates.append(candidate.resolve())
                break
    unique = sorted(set(candidates))
    return unique[:1]  # Exactly one bounded targeted verification per edit.


def feedback(root: Path, changed_paths: list[str], timeout_seconds: int = 20) -> dict:
    if not 1 <= timeout_seconds <= 30:
        raise ValueError("timeout_out_of_bounds")
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("workspace_not_directory")
    tests = discover(root, changed_paths)
    if not tests:
        return {"status": "NO_TARGETED_TEST_DISCOVERED", "actionable": False,
                "test_count": 0, "repair_signal": False}
    relative = tests[0].relative_to(root)
    try:
        run = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "--maxfail=1",
             "--disable-warnings", str(relative)],
            cwd=root, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, timeout=timeout_seconds, check=False,
        )
    except subprocess.TimeoutExpired:
        return {"status": "TEST_TIMEOUT", "actionable": False,
                "test_count": 1, "repair_signal": False}
    if run.returncode == 0:
        status, actionable, repair = "PASS", True, False
    elif run.returncode == 1:
        status, actionable, repair = "FAIL", True, True
    else:
        # Exit 2..5 signal interrupted/internal/usage/no-collection.
        # Those are NOT evidence of a semantic patch failure.
        status, actionable, repair = "TEST_UNAVAILABLE", False, False
    # No filenames, test output, issue identifiers or patches returned.
    return {"status": status, "actionable": actionable,
            "test_count": 1, "repair_signal": repair}


def smoke() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "pkg").mkdir()
        (root / "tests").mkdir()
        (root / "pkg" / "logic.py").write_text("def answer(): return 42\n")
        test = root / "tests" / "test_logic.py"
        test.write_text("from pkg.logic import answer\ndef test_answer(): assert answer() == 42\n")
        # Namespace package needs not be installed; CWD is on pytest's path.
        ok = feedback(root, ["pkg/logic.py"])
        assert ok["status"] == "PASS", ok
        test.write_text("from pkg.logic import answer\ndef test_answer(): assert answer() == 43\n")
        bad = feedback(root, ["pkg/logic.py"])
        assert bad["status"] == "FAIL" and bad["repair_signal"], bad
        absent = feedback(root, ["pkg/no_test.py"])
        assert absent["status"] == "NO_TARGETED_TEST_DISCOVERED"
        try:
            feedback(root, ["../outside.py"])
        except ValueError:
            pass
        else:
            raise AssertionError("path traversal must be rejected")
        assert discover(root, ["pkg/logic.py"]) == [test.resolve()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--root", type=Path)
    parser.add_argument("--changed", action="append", default=[])
    args = parser.parse_args()
    if args.smoke:
        smoke()
        print("GEMMA_HOST_FEEDBACK_SYNTHETIC_SMOKE=PASS")
    else:
        if args.root is None or not args.changed:
            parser.error("--root and at least one --changed are required")
        print("GEMMA_HOST_FEEDBACK=" + json.dumps(feedback(args.root, args.changed),
                                                  sort_keys=True))


if __name__ == "__main__":
    main()
