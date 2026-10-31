"""Gold-reference verifier sweep for the frozen verifier-LoRA v0 holdout.

This runtime never invokes a model or submission agent. It hydrates only the
frozen holdout tasks, feeds each task's reference patch directly into the
current official swegemma verifier, and records metadata needed to decide
whether the task is a clean evaluation target. Raw reference patches are never
written to output artifacts.
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
from typing import Iterable


DATA_DIR = Path("/kaggle/input/competitions/gemma-4-developer-agent")
WHEELHOUSE_DIR = Path("/kaggle/input/datasets/metric/gemma-4-developer-agent-wheelhouse")
WORKING_DIR = Path("/kaggle/working")
RESULT_PATH = WORKING_DIR / "verifier_gold_sweep.json"
_BUNDLED_MANIFEST_PATH = Path(__file__).with_name("verifier-lora-split-v0.json")
_REPO_MANIFEST_PATH = Path(__file__).resolve().parents[1] / "docs" / "evaluation" / "verifier-lora-split-v0.json"
HOLDOUT_MANIFEST_PATH = _BUNDLED_MANIFEST_PATH if _BUNDLED_MANIFEST_PATH.is_file() else _REPO_MANIFEST_PATH


def load_holdout_items(path: Path = HOLDOUT_MANIFEST_PATH) -> list[dict[str, str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("version") != "verifier-lora-v0":
        raise ValueError(f"unexpected split version: {payload.get('version')!r}")

    raw_items = payload.get("holdout")
    if not isinstance(raw_items, list) or not raw_items:
        raise ValueError("holdout manifest is missing a non-empty holdout list")

    items: list[dict[str, str]] = []
    seen: set[str] = set()
    for raw in raw_items:
        if not isinstance(raw, dict):
            raise ValueError("holdout item must be an object")
        item = {
            "instance_id": str(raw.get("instance_id") or ""),
            "repo": str(raw.get("repo") or ""),
            "patch_bucket": str(raw.get("patch_bucket") or ""),
        }
        if not all(item.values()):
            raise ValueError(f"incomplete holdout item: {raw!r}")
        if item["instance_id"] in seen:
            raise ValueError(f"duplicate holdout instance_id: {item['instance_id']}")
        seen.add(item["instance_id"])
        items.append(item)
    return items


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


def build_result_record(
    *,
    instance_id: str,
    repo: str,
    reference_patch: str,
    resolved: bool,
    test_exit_code: int | None,
    error: str | None,
    duration_seconds: float | None,
    test_output: str | None,
    test_patch_present: bool | None = None,
    fail_to_pass_count: int | None = None,
    pass_to_pass_count: int | None = None,
    test_files_count: int | None = None,
) -> dict[str, object]:
    """Return verifier evidence without serializing the raw reference patch."""
    output = test_output or ""
    return {
        "instance_id": instance_id,
        "repo": repo,
        "status": "completed",
        "control": "gold_reference_patch",
        "resolved": bool(resolved),
        "test_exit_code": test_exit_code,
        "error": error,
        "duration_seconds": duration_seconds,
        "reference_patch_chars": len(reference_patch),
        "reference_patch_sha256": hashlib.sha256(reference_patch.encode("utf-8")).hexdigest(),
        "test_patch_present": test_patch_present,
        "fail_to_pass_count": fail_to_pass_count,
        "pass_to_pass_count": pass_to_pass_count,
        "test_files_count": test_files_count,
        "test_output_tail": output[-4000:],
    }


def summarize_results(results: Iterable[dict[str, object]], *, expected_count: int) -> dict[str, object]:
    records = list(results)
    clean_ids = sorted(
        str(item.get("instance_id"))
        for item in records
        if item.get("status") == "completed"
        and item.get("resolved") is True
        and item.get("test_exit_code") == 0
    )
    clean_set = set(clean_ids)
    confounded_ids = sorted(
        str(item.get("instance_id"))
        for item in records
        if str(item.get("instance_id")) not in clean_set
    )
    return {
        "requested": expected_count,
        "completed": sum(item.get("status") == "completed" for item in records),
        "clean": len(clean_ids),
        "confounded": len(confounded_ids),
        "clean_instance_ids": clean_ids,
        "confounded_instance_ids": confounded_ids,
    }


def _error_record(instance_id: str, repo: str, exc: BaseException) -> dict[str, object]:
    return {
        "instance_id": instance_id,
        "repo": repo,
        "status": "error",
        "control": "gold_reference_patch",
        "resolved": False,
        "test_exit_code": None,
        "error_type": type(exc).__name__,
        "error": str(exc),
    }


async def run_sweep() -> dict[str, object]:
    from adk_submission import ModelRegistry
    from swegemma.config import EvalConfig
    from swegemma.deduplication import resolve_task_snapshot_paths
    from swegemma.evaluate import Evaluator
    from swegemma.harness.verification import verify_task
    from swegemma.models import load_tasks

    holdout_items = load_holdout_items()
    holdout_ids = {item["instance_id"] for item in holdout_items}

    tasks_path = DATA_DIR / "tasks.jsonl"
    snapshots_dir = DATA_DIR / "snapshots"
    results_dir = WORKING_DIR / "verifier-gold-sweep-results"
    empty_submission_dir = WORKING_DIR / "verifier-gold-sweep-empty-submission"
    results_dir.mkdir(parents=True, exist_ok=True)
    empty_submission_dir.mkdir(parents=True, exist_ok=True)

    public_tasks = load_tasks(tasks_path)
    tasks_by_id = {task.instance_id: task for task in public_tasks if task.instance_id in holdout_ids}
    missing = sorted(holdout_ids - set(tasks_by_id))
    if missing:
        raise RuntimeError(f"holdout task(s) missing from public corpus: {missing}")

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

    results: list[dict[str, object]] = []
    for index, item in enumerate(holdout_items, 1):
        instance_id = item["instance_id"]
        repo = item["repo"]
        print(f"[{index:02d}/{len(holdout_items):02d}] gold-control {instance_id}", flush=True)
        try:
            task = evaluator._hydrate_task_from_secret(tasks_by_id[instance_id])
            if task.instance_id != instance_id:
                raise RuntimeError(f"hydrated task id mismatch: {task.instance_id!r}")
            if task.repo != repo:
                raise RuntimeError(f"hydrated repo mismatch for {instance_id}: {task.repo!r} != {repo!r}")

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
            verification = await verify_task(
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
            record = build_result_record(
                instance_id=instance_id,
                repo=repo,
                reference_patch=reference_patch,
                resolved=bool(verification.resolved),
                test_exit_code=verification.test_exit_code,
                error=verification.error,
                duration_seconds=verification.duration_seconds,
                test_output=verification.test_output,
                test_patch_present=bool(task.test_patch and task.test_patch.strip()),
                fail_to_pass_count=len(getattr(task, "FAIL_TO_PASS", ()) or ()),
                pass_to_pass_count=len(getattr(task, "PASS_TO_PASS", ()) or ()),
                test_files_count=len(getattr(task, "test_files", None) or ()),
            )
        except BaseException as exc:
            record = _error_record(instance_id, repo, exc)
            print(f"gold-control error for {instance_id}: {type(exc).__name__}: {exc}", flush=True)
        results.append(record)

    summary = summarize_results(results, expected_count=len(holdout_items))
    return {
        "version": "verifier-lora-v0",
        "status": "completed",
        "control": "gold_reference_patch",
        "manifest_path": HOLDOUT_MANIFEST_PATH.name,
        **summary,
        "results": results,
    }


def write_failure(exc: BaseException) -> None:
    RESULT_PATH.write_text(
        json.dumps(
            {
                "version": "verifier-lora-v0",
                "status": "error",
                "control": "gold_reference_patch",
                "error_type": type(exc).__name__,
                "error": str(exc),
                "traceback": traceback.format_exc(),
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def main() -> None:
    WORKING_DIR.mkdir(parents=True, exist_ok=True)
    install_official_wheelhouse()
    output = asyncio.run(run_sweep())
    RESULT_PATH.write_text(json.dumps(output, indent=2, sort_keys=True), encoding="utf-8")
    print("VERIFIER_GOLD_SWEEP", json.dumps({key: value for key, value in output.items() if key != "results"}, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except BaseException as exc:
        write_failure(exc)
        raise
