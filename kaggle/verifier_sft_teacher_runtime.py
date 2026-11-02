"""Model-free deterministic training supervision collector for verifier-LoRA v0.

For each frozen training-only target, this runtime creates the same prepared
workspace used by the official harness, then records two public-regression
states without running an LLM or submission agent:

1. clean baseline + failing public behavior assertion -> safe-stop candidate;
2. reference-patched workspace + passing same assertion -> submit candidate.

Only frozen training IDs are accepted. Blind evaluation data is never read.
"""

from __future__ import annotations

import asyncio
import json
import tempfile
import traceback
from pathlib import Path
from typing import Any

import verifier_gold_teacher_runtime as gold
from verifier_gold_teacher_supervision import (
    DIFF_COMMAND,
    build_teacher_safe_stop_record,
    build_teacher_supervision_record,
    load_targeted_test_plan,
)


SUBMISSION_PAYLOAD_B64 = "__SUBMISSION_PAYLOAD_B64__"
TRAINING_MANIFEST_JSON = "__VERIFIER_LORA_TRAINING_MANIFEST_JSON__"
TRAINING_GOLD_SCREEN_JSON = "__VERIFIER_LORA_TRAINING_GOLD_SCREEN_JSON__"
TARGETED_TEST_PLAN_JSON = "__VERIFIER_LORA_TARGETED_TEST_PLAN_JSON__"
TEACHER_BUILD_ID = "__VERIFIER_SFT_TEACHER_BUILD_ID__"
MODEL_NAME = gold.MODEL_NAME

WORKING_DIR = gold.WORKING_DIR
RESULTS_DIR = WORKING_DIR / "verifier-sft-teacher-results"
EMPTY_SUBMISSION_DIR = WORKING_DIR / "verifier-sft-teacher-empty-submission"
SUPERVISION_PATH = WORKING_DIR / "verifier_gold_teacher_supervision.json"


def _exec_evidence(result: Any) -> dict[str, Any]:
    exit_code = getattr(result, "exit_code", None)
    if not isinstance(exit_code, int) or isinstance(exit_code, bool):
        raise RuntimeError(f"sandbox command returned invalid exit code: {exit_code!r}")
    stdout = getattr(result, "stdout", "") or ""
    stderr = getattr(result, "stderr", "") or ""
    if not isinstance(stdout, str) or not isinstance(stderr, str):
        raise RuntimeError("sandbox command output is not text")
    output = stdout
    if stderr:
        output = f"{output}\n[stderr]\n{stderr}" if output else f"[stderr]\n{stderr}"
    return {"exit_code": exit_code, "output": output}


def _run_gate(docker: Any, container_id: str, command: str) -> dict[str, Any]:
    return _exec_evidence(docker.exec(container_id, f"cd /workspace && {command}"))


def _unapproved_error_record(
    instance_id: str,
    problem_description: str,
    exc: BaseException,
    phase: str,
) -> dict[str, Any]:
    source = "base_targeted_failure" if phase == "base-fail" else "gold_patch_targeted_test"
    return {
        "instance_id": instance_id,
        "example_id": f"{instance_id}:{phase}",
        "approved": False,
        "label": None,
        "source": source,
        "problem_description": problem_description.strip(),
        "steps": [],
        "audit_flags": ["collector_error"],
        "collector_error_type": type(exc).__name__,
        "collector_error": str(exc),
    }


def write_failure(exc: BaseException) -> None:
    SUPERVISION_PATH.write_text(
        json.dumps(
            {
                "version": "verifier-lora-v0-deterministic-teacher",
                "status": "error",
                "teacher_build_id": TEACHER_BUILD_ID,
                "execution_mode": "deterministic_model_free",
                "error_type": type(exc).__name__,
                "error": str(exc),
                "traceback": traceback.format_exc(),
                "records": [],
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


async def _collect_task_records(
    *,
    evaluator: Any,
    task: Any,
    snapshots_dir: Path,
    targeted_command: str,
    problem_description: str,
) -> list[dict[str, Any]]:
    from swegemma.deduplication import resolve_task_snapshot_paths
    from swegemma.harness.container_setup import (
        apply_patch_in_container,
        extract_snapshot,
        install_editable_package,
        install_test_dependencies,
        setup_baseline_commit,
        setup_container_wheels,
        setup_git_exclude,
        setup_synthetic_hardware,
        setup_workspace_test_config,
    )
    from swegemma.sandbox import sandbox_start, sandbox_stop

    reference_patch = task.patch or ""
    if not reference_patch.strip():
        raise RuntimeError("deterministic teacher reference patch is unavailable")

    snapshot_path, base_snapshot_path, patch_path = resolve_task_snapshot_paths(
        snapshots_dir,
        task.instance_id,
        task.repo,
    )

    docker = evaluator.docker
    sandbox_id = await sandbox_start(docker)
    records: list[dict[str, Any]] = []
    host_patch_path: Path | None = None
    container_patch = "/tmp/verifier_sft_teacher_reference.patch"
    try:
        await asyncio.to_thread(setup_container_wheels, docker, sandbox_id, evaluator.config)
        await asyncio.to_thread(
            extract_snapshot,
            docker,
            sandbox_id,
            snapshot_path,
            patch_path=patch_path,
            base_snapshot_path=base_snapshot_path,
        )
        await asyncio.to_thread(setup_synthetic_hardware, docker, sandbox_id)
        await asyncio.to_thread(setup_git_exclude, docker, sandbox_id)
        await asyncio.to_thread(install_editable_package, docker, sandbox_id)
        await asyncio.to_thread(
            install_test_dependencies,
            docker,
            sandbox_id,
            task.repo,
            fast_path=True,
            config=evaluator.config,
        )
        await asyncio.to_thread(
            setup_workspace_test_config,
            docker,
            sandbox_id,
            repo=task.repo,
        )
        await asyncio.to_thread(
            setup_baseline_commit,
            docker,
            sandbox_id,
            "verifier_sft_teacher_baseline",
        )

        base_pre_diff = _run_gate(docker, sandbox_id, DIFF_COMMAND)
        base_targeted_test = _run_gate(docker, sandbox_id, targeted_command)
        base_final_diff = _run_gate(docker, sandbox_id, DIFF_COMMAND)
        records.append(
            build_teacher_safe_stop_record(
                instance_id=task.instance_id,
                problem_description=problem_description,
                targeted_command=targeted_command,
                pre_diff=base_pre_diff,
                targeted_test=base_targeted_test,
                final_diff=base_final_diff,
            )
        )

        with tempfile.NamedTemporaryFile("w", suffix=".patch", delete=False) as handle:
            handle.write(reference_patch if reference_patch.endswith("\n") else reference_patch + "\n")
            host_patch_path = Path(handle.name)
        await asyncio.to_thread(docker.copy_to, sandbox_id, host_patch_path, container_patch)
        exit_code, stdout, stderr = await asyncio.to_thread(
            apply_patch_in_container,
            docker,
            sandbox_id,
            container_patch,
        )
        if exit_code != 0:
            raise RuntimeError(
                "failed to apply deterministic teacher patch: "
                f"exit={exit_code} stdout={stdout[-1000:]!r} stderr={stderr[-1000:]!r}"
            )

        gold_pre_diff = _run_gate(docker, sandbox_id, DIFF_COMMAND)
        gold_targeted_test = _run_gate(docker, sandbox_id, targeted_command)
        gold_final_diff = _run_gate(docker, sandbox_id, DIFF_COMMAND)
        records.append(
            build_teacher_supervision_record(
                instance_id=task.instance_id,
                problem_description=problem_description,
                targeted_command=targeted_command,
                pre_diff=gold_pre_diff,
                targeted_test=gold_targeted_test,
                final_diff=gold_final_diff,
            )
        )
        return records
    except BaseException as exc:
        if not records:
            return [
                _unapproved_error_record(task.instance_id, problem_description, exc, "base-fail"),
                _unapproved_error_record(task.instance_id, problem_description, exc, "gold-pass"),
            ]
        if len(records) == 1:
            return records + [
                _unapproved_error_record(task.instance_id, problem_description, exc, "gold-pass")
            ]
        raise
    finally:
        try:
            docker.exec(sandbox_id, f"rm -f {container_patch}")
        except BaseException:
            pass
        if host_patch_path is not None:
            host_patch_path.unlink(missing_ok=True)
        await sandbox_stop(docker, sandbox_id)


async def run_teacher() -> dict[str, Any]:
    gold.install_official_wheelhouse()

    from adk_submission import ModelRegistry
    from swegemma.config import EvalConfig
    from swegemma.evaluate import Evaluator
    from swegemma.models import load_tasks

    if not TEACHER_BUILD_ID or TEACHER_BUILD_ID.startswith("__"):
        raise RuntimeError("deterministic teacher build ID placeholder was not rendered")

    WORKING_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    EMPTY_SUBMISSION_DIR.mkdir(parents=True, exist_ok=True)

    gold.TRAINING_MANIFEST_JSON = TRAINING_MANIFEST_JSON
    training_ids = gold._load_training_ids()
    clean_ids = gold.load_clean_training_ids(TRAINING_GOLD_SCREEN_JSON, set(training_ids))
    targeted_commands = load_targeted_test_plan(TARGETED_TEST_PLAN_JSON, set(clean_ids))
    target_ids = list(targeted_commands)

    tasks_path = gold.DATA_DIR / "tasks.jsonl"
    snapshots_dir = gold.DATA_DIR / "snapshots"
    public_tasks = load_tasks(tasks_path)
    selected = set(target_ids)
    tasks_by_id = {task.instance_id: task for task in public_tasks if task.instance_id in selected}
    missing = [task_id for task_id in target_ids if task_id not in tasks_by_id]
    if missing:
        raise RuntimeError(f"deterministic-teacher task(s) missing from public corpus: {missing}")
    missing_reference_patches = [
        task_id
        for task_id in target_ids
        if not (tasks_by_id[task_id].patch or "").strip()
    ]
    if missing_reference_patches:
        raise RuntimeError(
            f"deterministic-teacher reference patch(es) missing from training task corpus: "
            f"{missing_reference_patches}"
        )

    config = EvalConfig(
        tasks_path=tasks_path,
        snapshots_dir=snapshots_dir,
        results_dir=RESULTS_DIR,
        submission_dir=EMPTY_SUBMISSION_DIR,
        models=ModelRegistry(),
        sandbox="subprocess",
        wheels_dir=gold.DATA_DIR / "wheels",
        timeout_seconds=300,
        verification_timeout_seconds=300,
        verbose=False,
    )
    evaluator = Evaluator(config)

    records: list[dict[str, Any]] = []
    for index, task_id in enumerate(target_ids, 1):
        task = tasks_by_id[task_id]
        problem_description = task.problem_statement or ""
        print(f"[{index:02d}/{len(target_ids):02d}] deterministic-teacher {task_id}", flush=True)
        try:
            task_records = await _collect_task_records(
                evaluator=evaluator,
                task=task,
                snapshots_dir=snapshots_dir,
                targeted_command=targeted_commands[task_id],
                problem_description=problem_description,
            )
        except BaseException as exc:
            task_records = [
                _unapproved_error_record(task_id, problem_description, exc, "base-fail"),
                _unapproved_error_record(task_id, problem_description, exc, "gold-pass"),
            ]

        records.extend(task_records)
        for record in task_records:
            print(
                "SFT_TEACHER_RECORD",
                json.dumps(
                    {
                        "instance_id": task_id,
                        "example_id": record.get("example_id"),
                        "approved": record.get("approved"),
                        "label": record.get("label"),
                        "audit_flags": record.get("audit_flags"),
                    },
                    sort_keys=True,
                ),
                flush=True,
            )

    approved_example_ids = [
        str(record["example_id"])
        for record in records
        if record.get("approved") is True
    ]
    return {
        "version": "verifier-lora-v0-deterministic-teacher",
        "status": "completed",
        "teacher_build_id": TEACHER_BUILD_ID,
        "execution_mode": "deterministic_model_free",
        "model": MODEL_NAME,
        "requested": len(target_ids),
        "record_count": len(records),
        "approved": len(approved_example_ids),
        "approved_example_ids": approved_example_ids,
        "records": records,
    }


def main() -> None:
    output = asyncio.run(run_teacher())
    SUPERVISION_PATH.write_text(
        json.dumps(output, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(
        "SFT_TEACHER_SUMMARY",
        json.dumps({key: value for key, value in output.items() if key != "records"}, sort_keys=True),
        flush=True,
    )


if __name__ == "__main__":
    try:
        main()
    except BaseException as exc:
        write_failure(exc)
        raise
