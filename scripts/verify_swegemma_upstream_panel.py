#!/usr/bin/env python3
"""Run official SWE-Gemma verifier code on locally prequalified upstream repairs."""
from __future__ import annotations

import argparse
import asyncio
import gzip
from hashlib import sha256
from importlib.metadata import version
import json
import logging
from pathlib import Path
import tempfile
import time

from qualify_upstream_repair_panel import SOURCES, git


def diff(source: Path, row: dict, field: str) -> str:
    return git(source, "diff", "--binary", "--no-renames", row["base"], row["fix"], "--", *row[field]).decode()


def instance_id(row: dict) -> str:
    return f"upstream_{row['repo']}_{row['pr']}"


async def evaluate(source: Path, row: dict) -> dict:
    from adk_submission import ModelRegistry
    from swegemma.config import EvalConfig
    from swegemma.harness.verification import verify_task
    from swegemma.models import Task
    from swegemma.sandbox.subprocess import SubprocessManager

    instance = instance_id(row)
    with tempfile.TemporaryDirectory(prefix="upstream-control-") as workspace:
        folder = Path(workspace)
        snapshot = folder / f"{instance}.tar.gz"
        snapshot.write_bytes(gzip.compress(git(source, "archive", row["base"]), mtime=0))
        task = Task(instance_id=instance, repo=row["upstream"], base_commit=row["base"],
                    problem_statement="", test_patch=diff(source, row, "tests"))
        config = EvalConfig(tasks_path=folder / "tasks.jsonl", snapshots_dir=folder,
                            results_dir=folder / "results", submission_dir=folder / "submission",
                            models=ModelRegistry(), sandbox="subprocess", timeout_seconds=300,
                            verification_timeout_seconds=160, display_mode="quiet")
        sandbox = SubprocessManager(timeout_seconds=160)
        outcome: dict = {"instance": instance}
        for control, patch in (("noop", ""), ("gold", diff(source, row, "production"))):
            try:
                result = await verify_task(sandbox, config, task, snapshot, agent_patch=patch,
                                           start_time=time.perf_counter())
                outcome[control] = {"resolved": bool(result.resolved), "exit": result.test_exit_code}
            except Exception as error:
                outcome[control] = {"error_type": type(error).__name__}
    return outcome


async def run(args: argparse.Namespace) -> None:
    payload = args.manifest.read_bytes()
    if sha256(payload).hexdigest() != args.sha256 or version("swegemma") != "0.2.11":
        raise SystemExit("Frozen manifest or verifier version mismatch")
    key = lambda x: (x["repo"], x["pr"], x["fix"])
    frozen = json.loads(payload)["tasks"]
    local = [json.loads(line) for line in args.local_results.read_text().splitlines()]
    if len(local) != len(frozen) or {key(x) for x in local} != {key(x) for x in frozen}:
        raise SystemExit("Local controls do not match the frozen manifest")
    passed = {key(x) for x in local if x.get("eligible_local") is True}
    admitted = frozen if args.all_frozen else [x for x in frozen if key(x) in passed]
    previous = json.loads(args.reuse.read_text()) if args.reuse else []
    completed = {out["instance"] for out in previous}
    if len(previous) != len(completed) or completed - {instance_id(x) for x in admitted}:
        raise SystemExit("Reused outcomes do not match the admitted cohort")
    source = {name: getattr(args, name).resolve() for name in SOURCES}
    slots = asyncio.Semaphore(args.parallel)

    async def bounded(row: dict) -> dict:
        async with slots:
            return await evaluate(source[row["repo"]], row)

    pending = [bounded(row) for row in admitted if instance_id(row) not in completed]
    with args.output.open("x", encoding="utf-8") as log:
        for out in previous:
            print(json.dumps(out, sort_keys=True), file=log, flush=True)
        for next_result in asyncio.as_completed(pending):
            out = await next_result
            print(json.dumps(out, sort_keys=True), file=log, flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--local-results", required=True, type=Path)
    parser.add_argument("--reuse", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--parallel", type=int, default=4, choices=range(1, 7))
    parser.add_argument("--all-frozen", action="store_true", help="Also verify the cases rejected by local pytest.")
    for repo in SOURCES:
        parser.add_argument(f"--{repo}", type=Path, default=Path(f"gemma-upstream-{repo}"))
    logging.disable(logging.CRITICAL)
    asyncio.run(run(parser.parse_args()))


if __name__ == "__main__":
    main()
