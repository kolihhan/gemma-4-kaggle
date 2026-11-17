#!/usr/bin/env python3
"""Screen upstream regression pairs locally before considering them for an official-harness study."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import tempfile
import xml.etree.ElementTree as ET


AFTER = datetime.fromisoformat("2026-06-20T00:20:49+00:00")
SOURCES = {"fastapi": "fastapi/fastapi", "starlette": "encode/starlette"}
FIX = re.compile(r"(?:🐛|\b(?:fix(?:es|ed)?|regression)\b)", re.I)
PR = re.compile(r"(?:\(#|^Merge pull request #)(\d+)", re.M)
CONFLICT = re.compile(r"(?<!\w)#(\d+)")


def git(repo: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(repo), *args])


def select(source: Path, repo: str, blocked: set[int]) -> list[dict]:
    entries = []
    commits = git(source, "log", "--first-parent", f"--since={AFTER.isoformat()}",
                  "--format=%H %P").decode().splitlines()
    for entry in commits:
        sha, *parents = entry.split()
        if not parents:
            continue
        parent = parents[0]
        date, subject, message = git(source, "show", "-s", "--format=%cI%n%s%n%b", sha).decode().split("\n", 2)
        match = PR.search(subject)
        if datetime.fromisoformat(date) <= AFTER or not match:
            continue
        if repo == "fastapi" and not FIX.search(subject + message):
            continue
        references = {int(x) for x in CONFLICT.findall(subject + "\n" + message)}
        if references & blocked:
            continue
        paths = git(source, "diff", "--name-only", "--no-renames", parent, sha).decode().splitlines()
        production = [path for path in paths if path.startswith(repo + "/") and path.endswith(".py")]
        tests = [path for path in paths if path.startswith("tests/") and Path(path).name.startswith("test_")
                 and path.endswith(".py")]
        if not production or not tests or len(production) + len(tests) > 12:
            continue
        if any(path.startswith("tests/") and path.endswith(".py") and path not in tests for path in paths):
            continue
        entries.append({"repo": repo, "upstream": SOURCES[repo], "pr": int(match[1]),
                        "fix": sha, "base": parent, "production": production, "tests": tests})
    return sorted(entries, key=lambda row: row["pr"])


def snapshot(source: Path, ref: str, directory: Path) -> None:
    archive = git(source, "archive", ref)
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as tar:
        tar.extractall(directory, filter="data")


def apply(source: Path, row: dict, paths: list[str], directory: Path) -> None:
    patch = git(source, "diff", "--binary", "--no-renames", row["base"], row["fix"], "--", *paths)
    subprocess.run(["git", "apply", "-"], input=patch, cwd=directory, capture_output=True, check=True)


def pytest_control(directory: Path, paths: list[str]) -> dict:
    report = directory / "control.xml"
    environment = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "HOME": str(directory),
                   "TMPDIR": str(directory), "PYTHONPATH": str(directory),
                   "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"}
    command = [sys.executable, "-m", "pytest", "-q", "-o", "addopts=", "--maxfail=1",
               "-p", "anyio.pytest_plugin", "-p", "pytest_mock", "-p", "pytest_timeout",
               "-p", "inline_snapshot.pytest_plugin", f"--junitxml={report}", *paths]
    try:
        result = subprocess.run(command, cwd=directory, env=environment, capture_output=True, timeout=90)
    except subprocess.TimeoutExpired:
        return {"exit": None, "passed": set(), "failed": set(), "error": "timeout"}
    passed, failed = set(), set()
    if report.is_file():
        for test in ET.parse(report).iter("testcase"):
            name = (test.get("classname"), test.get("name"))
            if test.find("failure") is not None:
                failed.add(name)
            if len(test) == 0:
                passed.add(name)
    error = None
    if not passed and not failed:
        match = re.search(rb"(?:ModuleNotFoundError|ImportError): ([^\n]+)", result.stdout + result.stderr)
        error = match[1].decode(errors="replace")[:120] if match else "no_test_outcomes"
    return {"exit": result.returncode, "passed": passed, "failed": failed, "error": error}


def qualify(source: Path, row: dict) -> dict:
    with tempfile.TemporaryDirectory(prefix="repair-pair-") as work:
        directory = Path(work)
        snapshot(source, row["base"], directory)
        apply(source, row, row["tests"], directory)
        noop = pytest_control(directory, row["tests"])
        # Gold runs in a new checkout so artifacts produced by no-op cannot influence it.
        with tempfile.TemporaryDirectory(prefix="repair-gold-") as gold_work:
            gold_dir = Path(gold_work)
            snapshot(source, row["base"], gold_dir)
            apply(source, row, row["tests"], gold_dir)
            apply(source, row, row["production"], gold_dir)
            gold = pytest_control(gold_dir, row["tests"])
    witnessed = noop["failed"] & gold["passed"]
    return {"repo": row["repo"], "pr": row["pr"], "fix": row["fix"],
            "noop_exit": noop["exit"], "gold_exit": gold["exit"],
            "noop_error": noop["error"], "gold_error": gold["error"],
            "witnessed_regressions": len(witnessed),
            "eligible_local": noop["exit"] == 1 and gold["exit"] == 0 and bool(witnessed)}


def run_pair(source: Path, row: dict) -> dict:
    try:
        return qualify(source, row)
    except (OSError, subprocess.CalledProcessError, tarfile.TarError, ET.ParseError) as error:
        return {"repo": row["repo"], "pr": row["pr"], "fix": row["fix"],
                "eligible_local": False, "setup_error": type(error).__name__}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    preflight = subcommands.add_parser("freeze")
    preflight.add_argument("--official-id-json", required=True, type=Path)
    for repo in SOURCES:
        preflight.add_argument(f"--{repo}", required=True, type=Path)
    execute = subcommands.add_parser("verify")
    execute.add_argument("--manifest", required=True, type=Path)
    execute.add_argument("--sha256", required=True)
    execute.add_argument("--workers", default=4, type=int, choices=range(1, 5))
    for repo in SOURCES:
        execute.add_argument(f"--{repo}", type=Path, default=Path(f"gemma-upstream-{repo}"))
    args = parser.parse_args()
    if args.command == "freeze":
        ids = json.loads(args.official_id_json.read_text())
        sources = {repo: getattr(args, repo).resolve() for repo in SOURCES}
        rows = []
        for repo, source in sources.items():
            blocked = {int(task.rsplit("_", 1)[1]) for task in ids if task.startswith(repo + "_")}
            rows.extend(select(source, repo, blocked))
        print(json.dumps({"source_cutoff": AFTER.isoformat(), "tasks": rows}, indent=2))
        return
    frozen = args.manifest.read_bytes()
    if hashlib.sha256(frozen).hexdigest() != args.sha256:
        raise SystemExit("Frozen manifest SHA-256 mismatch")
    rows = json.loads(frozen)["tasks"]
    sources = {repo: getattr(args, repo).resolve() for repo in SOURCES}
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        runs = [executor.submit(run_pair, sources[row["repo"]], row) for row in rows]
        for finished in as_completed(runs):
            print(json.dumps(finished.result(), sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
