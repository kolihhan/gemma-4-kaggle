"""Verifier-only positive control for the public rich_3278 task.

This runtime never invokes a model or submission agent. It feeds the task's
reference patch directly into the current official swegemma verifier so we can
separate harness failures from agent-quality failures. The reference patch is
never written to an output artifact; only its length and SHA-256 are recorded.
"""

from __future__ import annotations

import asyncio
import glob
import hashlib
import importlib
import json
import shutil
import subprocess
import sys
import time
import traceback
from pathlib import Path


CONTROL_TASK_ID = "rich_3278"
DATA_DIR = Path("/kaggle/input/competitions/gemma-4-developer-agent")
WHEELHOUSE_DIR = Path("/kaggle/input/datasets/metric/gemma-4-developer-agent-wheelhouse")
WORKING_DIR = Path("/kaggle/working")
RESULT_PATH = WORKING_DIR / "gold_control_result.json"


def install_official_wheelhouse() -> None:
    """Install the exact scorer wheelhouse mounted by the official starter."""
    if not WHEELHOUSE_DIR.is_dir():
        raise FileNotFoundError(f"missing official wheelhouse: {WHEELHOUSE_DIR}")

    for pattern in (
        "/usr/local/lib/python*/dist-packages/*cutlass*.pth",
        "/usr/local/lib/python*/site-packages/*cutlass*.pth",
    ):
        for pth in glob.glob(pattern):
            try:
                Path(pth).unlink()
            except OSError:
                pass

    fixed_dir = Path("/tmp/gemma4-scorer-wheelhouse")
    fixed_dir.mkdir(parents=True, exist_ok=True)
    for wheel in WHEELHOUSE_DIR.glob("*.whl"):
        if "cutlass" in wheel.name.lower():
            continue
        target_name = (
            wheel.name.replace("cu128", "+cu128")
            if "cu128" in wheel.name and "+" not in wheel.name
            else wheel.name
        )
        target = fixed_dir / target_name
        if target.exists():
            continue
        try:
            target.symlink_to(wheel)
        except OSError:
            shutil.copyfile(wheel, target)

    wheels = sorted(str(path) for path in fixed_dir.glob("*.whl"))
    if not wheels:
        raise RuntimeError(f"no wheels found under {WHEELHOUSE_DIR}")
    print(f"Installing {len(wheels)} official scorer wheels...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-q", "--no-deps", "--force-reinstall", *wheels],
        check=True,
    )
    importlib.invalidate_caches()
    print("Official scorer wheelhouse installed.")


def write_failure(exc: BaseException) -> None:
    RESULT_PATH.write_text(
        json.dumps(
            {
                "instance_id": CONTROL_TASK_ID,
                "status": "error",
                "error_type": type(exc).__name__,
                "error": str(exc),
                "traceback": traceback.format_exc(),
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


async def run_control() -> dict[str, object]:
    from adk_submission import ModelRegistry
    from swegemma.config import EvalConfig
    from swegemma.deduplication import resolve_task_snapshot_paths
    from swegemma.evaluate import Evaluator
    from swegemma.harness.verification import verify_task
    from swegemma.models import load_tasks

    tasks_path = DATA_DIR / "tasks.jsonl"
    snapshots_dir = DATA_DIR / "snapshots"
    results_dir = WORKING_DIR / "gold-control-results"
    empty_submission_dir = WORKING_DIR / "gold-control-empty-submission"
    results_dir.mkdir(parents=True, exist_ok=True)
    empty_submission_dir.mkdir(parents=True, exist_ok=True)

    tasks = load_tasks(tasks_path)
    task = next((item for item in tasks if item.instance_id == CONTROL_TASK_ID), None)
    if task is None:
        raise RuntimeError(f"public control task not found: {CONTROL_TASK_ID}")

    config = EvalConfig(
        tasks_path=tasks_path,
        snapshots_dir=snapshots_dir,
        results_dir=results_dir,
        submission_dir=empty_submission_dir,
        models=ModelRegistry(),
        sandbox="subprocess",
        wheels_dir=DATA_DIR / "wheels",
        timeout_seconds=300,
        verification_timeout_seconds=300,
        verbose=False,
    )
    evaluator = Evaluator(config)
    task = evaluator._hydrate_task_from_secret(task)

    reference_patch = task.patch
    if not reference_patch or not reference_patch.strip():
        raise RuntimeError("gold reference patch unavailable after current scorer hydration")

    has_test_spec = bool(
        (task.test_patch and task.test_patch.strip())
        or getattr(task, "FAIL_TO_PASS", ())
        or getattr(task, "PASS_TO_PASS", ())
        or getattr(task, "test_files", None)
    )
    if not has_test_spec:
        raise RuntimeError("verification test specification unavailable after current scorer hydration")

    snapshot_path, base_snapshot_path, patch_path = resolve_task_snapshot_paths(
        snapshots_dir,
        task.instance_id,
        task.repo,
    )

    started = time.perf_counter()
    result = await verify_task(
        evaluator.docker,
        evaluator.config,
        task,
        snapshot_path,
        base_snapshot_path=base_snapshot_path,
        patch_path=patch_path,
        agent_patch=reference_patch,
        agent_error=None,
        trace=None,
        start_time=started,
    )

    test_output = result.test_output or ""
    return {
        "instance_id": CONTROL_TASK_ID,
        "status": "completed",
        "control": "gold_reference_patch",
        "resolved": bool(result.resolved),
        "test_exit_code": result.test_exit_code,
        "error": result.error,
        "duration_seconds": result.duration_seconds,
        "reference_patch_chars": len(reference_patch),
        "reference_patch_sha256": hashlib.sha256(reference_patch.encode("utf-8")).hexdigest(),
        "test_patch_present": bool(task.test_patch and task.test_patch.strip()),
        "fail_to_pass_count": len(getattr(task, "FAIL_TO_PASS", ()) or ()),
        "pass_to_pass_count": len(getattr(task, "PASS_TO_PASS", ()) or ()),
        "test_files_count": len(getattr(task, "test_files", None) or ()),
        "test_output_tail": test_output[-4000:],
    }


def main() -> None:
    WORKING_DIR.mkdir(parents=True, exist_ok=True)
    install_official_wheelhouse()
    output = asyncio.run(run_control())
    RESULT_PATH.write_text(json.dumps(output, indent=2, sort_keys=True), encoding="utf-8")
    print("GOLD_CONTROL_RESULT", json.dumps(output, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except BaseException as exc:
        write_failure(exc)
        raise
