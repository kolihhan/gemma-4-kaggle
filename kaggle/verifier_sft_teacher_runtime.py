"""Deterministic training-only verifier supervision collector for LoRA v0.

The collector reuses the frozen training gold screen, applies each training
reference patch only after the official baseline commit, and executes one
frozen targeted pytest gate between two diff-integrity checks. It records the
result before the model can mutate the workspace. Blind tasks and hidden test
patches are never read here.
"""

from __future__ import annotations

import asyncio
import json
import os
import traceback
from pathlib import Path
from typing import Any

import verifier_gold_teacher_runtime as gold
from verifier_gold_teacher_supervision import (
    DIFF_COMMAND,
    build_teacher_supervision_record,
    load_targeted_test_plan,
)


SUBMISSION_PAYLOAD_B64 = "__SUBMISSION_PAYLOAD_B64__"
TRAINING_MANIFEST_JSON = "__VERIFIER_LORA_TRAINING_MANIFEST_JSON__"
TRAINING_GOLD_SCREEN_JSON = "__VERIFIER_LORA_TRAINING_GOLD_SCREEN_JSON__"
TARGETED_TEST_PLAN_JSON = "__VERIFIER_LORA_TARGETED_TEST_PLAN_JSON__"
MODEL_NAME = gold.MODEL_NAME

WORKING_DIR = gold.WORKING_DIR
AGENT_DIR = gold.AGENT_DIR
RESULTS_DIR = WORKING_DIR / "verifier-sft-teacher-results"
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


def install_deterministic_teacher_hook(targeted_commands: dict[str, str]):
    """Capture deterministic evidence immediately after applying the gold patch."""
    import swegemma.harness.agent_runner as agent_runner
    from swegemma.harness.container_setup import apply_patch_in_container

    original_setup_baseline_commit = agent_runner.setup_baseline_commit
    state: dict[str, Any] = {
        "patch_path": None,
        "task_id": None,
        "problem_description": None,
        "records": {},
    }

    def setup_baseline_then_collect(docker, container_id, commit_msg="baseline"):
        original_setup_baseline_commit(docker, container_id, commit_msg)
        patch_path = state.get("patch_path")
        task_id = state.get("task_id")
        problem_description = state.get("problem_description")
        if not isinstance(task_id, str) or task_id not in targeted_commands:
            raise RuntimeError(f"deterministic teacher has no active targeted task: {task_id!r}")
        if not isinstance(problem_description, str) or not problem_description.strip():
            raise RuntimeError(f"deterministic teacher has no problem description for {task_id}")
        if patch_path is None:
            raise RuntimeError(f"deterministic teacher has no active reference patch for {task_id}")
        patch_path = Path(patch_path)
        if not patch_path.is_file() or patch_path.stat().st_size == 0:
            raise RuntimeError(f"deterministic teacher reference patch is missing/empty: {patch_path}")

        container_patch = "/tmp/verifier_sft_teacher_reference.patch"
        docker.copy_to(container_id, patch_path, container_patch)
        try:
            exit_code, stdout, stderr = apply_patch_in_container(
                docker, container_id, container_patch
            )
            if exit_code != 0:
                raise RuntimeError(
                    "failed to apply deterministic teacher patch: "
                    f"exit={exit_code} stdout={stdout[-1000:]!r} stderr={stderr[-1000:]!r}"
                )

            pre_diff = _exec_evidence(
                docker.exec(container_id, f"cd /workspace && {DIFF_COMMAND}")
            )
            targeted_command = targeted_commands[task_id]
            targeted_test = _exec_evidence(
                docker.exec(container_id, f"cd /workspace && {targeted_command}")
            )
            final_diff = _exec_evidence(
                docker.exec(container_id, f"cd /workspace && {DIFF_COMMAND}")
            )
            state["records"][task_id] = build_teacher_supervision_record(
                instance_id=task_id,
                problem_description=problem_description,
                targeted_command=targeted_command,
                pre_diff=pre_diff,
                targeted_test=targeted_test,
                final_diff=final_diff,
            )
        finally:
            docker.exec(container_id, f"rm -f {container_patch}")

    agent_runner.setup_baseline_commit = setup_baseline_then_collect
    return state, original_setup_baseline_commit


def _unapproved_error_record(
    instance_id: str,
    problem_description: str,
    exc: BaseException,
) -> dict[str, Any]:
    return {
        "instance_id": instance_id,
        "approved": False,
        "label": None,
        "source": "gold_patch_targeted_test",
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


def main() -> None:
    WORKING_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Reuse the already-tested gold-teacher environment/materialization path.
    gold.SUBMISSION_PAYLOAD_B64 = SUBMISSION_PAYLOAD_B64
    gold.TRAINING_MANIFEST_JSON = TRAINING_MANIFEST_JSON
    gold.TRAINING_GOLD_SCREEN_JSON = TRAINING_GOLD_SCREEN_JSON
    gold.configure_environment()
    gold.install_official_wheelhouse()
    gold.materialize_submission()

    training_ids = gold._load_training_ids()
    clean_ids = gold.load_clean_training_ids(TRAINING_GOLD_SCREEN_JSON, set(training_ids))
    targeted_commands = load_targeted_test_plan(TARGETED_TEST_PLAN_JSON, set(clean_ids))
    target_ids = list(targeted_commands)

    import litellm
    import torch
    import yaml
    import swegemma.harness.agent_runner as agent_runner
    from adk_submission import VllmConfig, VllmServer, discover_adapters, validate_directory
    from adk_submission.discovery import discover_declared_models
    from google.adk.agents.context_cache_config import ContextCacheConfig
    from google.adk.apps._configs import EventsCompactionConfig
    from swegemma.config import ALLOWED_ADAPTER_EXTENSIONS, EvalConfig, build_submission_limits
    from swegemma.evaluate import Evaluator
    from swegemma.models import load_tasks

    litellm.drop_params = True
    limits, generation_constraints = build_submission_limits()
    validate_directory(AGENT_DIR, limits=limits)
    declared_models = discover_declared_models(AGENT_DIR)
    if declared_models != {MODEL_NAME}:
        raise RuntimeError(f"expected only {MODEL_NAME}, got {sorted(declared_models)}")
    adapters = discover_adapters(str(AGENT_DIR), adapter_extensions=ALLOWED_ADAPTER_EXTENSIONS)
    adapter_map = getattr(adapters, "adapters", None) or {}
    if adapter_map:
        raise RuntimeError(f"deterministic teacher must not contain adapters: {sorted(adapter_map)}")

    model_path = Path(f"/kaggle/input/models/google/gemma-4/other/{MODEL_NAME}/2")
    if not model_path.exists():
        raise FileNotFoundError(f"E4B model weights not found: {model_path}")

    tasks_path = gold.DATA_DIR / "tasks.jsonl"
    public_tasks = load_tasks(tasks_path)
    selected = set(target_ids)
    tasks_by_id = {task.instance_id: task for task in public_tasks if task.instance_id in selected}
    missing = [task_id for task_id in target_ids if task_id not in tasks_by_id]
    if missing:
        raise RuntimeError(f"deterministic-teacher task(s) missing from public corpus: {missing}")

    raw_eval = yaml.safe_load((AGENT_DIR / "eval_config.yaml").read_text(encoding="utf-8")) or {}
    eval_section = raw_eval.get("evaluation", raw_eval)
    timeout_seconds = int(eval_section.get("timeout_seconds", 300))
    verification_timeout_seconds = int(eval_section.get("verification_timeout_seconds", 300))

    # The deterministic evidence is captured before the model runs. Keep the
    # post-capture agent phase tightly bounded so this collector is not another
    # behavioral teacher run.
    max_tool_calls = 1
    max_time_minutes = 3.0
    max_turns = 1

    gpu_count = torch.cuda.device_count() if torch.cuda.is_available() else 0
    if gpu_count < 1:
        raise RuntimeError("Kaggle deterministic-teacher kernel has no visible GPU")
    tp_size = 4 if gpu_count >= 4 else (2 if gpu_count >= 2 else 1)

    server = None
    hook_state = None
    original_setup_baseline_commit = None
    records: list[dict[str, Any]] = []
    try:
        server = VllmServer(
            VllmConfig(
                model=str(model_path),
                port=8000,
                host="127.0.0.1",
                tool_call_parser="gemma4",
                reasoning_parser="gemma4",
                max_model_len=32768,
                dtype="bfloat16" if torch.cuda.is_bf16_supported() else "auto",
                gpu_memory_utilization=0.90,
                enable_auto_tool_choice=True,
                enable_lora=False,
                max_loras=1,
                max_lora_rank=128,
                scheduler_reserve_full_isl=False,
                tensor_parallel_size=tp_size,
                startup_timeout=60 * 20,
                extra_args=(),
            ),
            adapter_manifest=adapters,
        )
        server.start()
        models = server.create_model_registry(
            aliases=[MODEL_NAME], model_prefix="openai/", api_key=os.environ["LOCAL_API_KEY"]
        )
        eval_config = EvalConfig(
            tasks_path=tasks_path,
            snapshots_dir=gold.DATA_DIR / "snapshots",
            results_dir=RESULTS_DIR,
            submission_dir=AGENT_DIR,
            models=models,
            sandbox="subprocess",
            timeout_seconds=timeout_seconds,
            verification_timeout_seconds=verification_timeout_seconds,
            max_time_minutes=max_time_minutes,
            max_tool_calls=max_tool_calls,
            max_turns=max_turns,
            limits=limits,
            generation_constraints=generation_constraints,
            adapter_manifest=adapters,
            context_cache_config=ContextCacheConfig(
                min_tokens=2048, ttl_seconds=1800, cache_intervals=10
            ),
            events_compaction_config=EventsCompactionConfig(
                compaction_interval=15,
                overlap_size=2,
                token_threshold=14336,
                event_retention_size=5,
            ),
            graph_dir=str(gold.DATA_DIR / "graphs"),
            embeddings_dir=str(gold.DATA_DIR / "embeddings"),
            wheels_dir=gold.DATA_DIR / "wheels",
            verbose=False,
        )
        evaluator = Evaluator(eval_config)
        hook_state, original_setup_baseline_commit = install_deterministic_teacher_hook(
            targeted_commands
        )

        for index, task_id in enumerate(target_ids, 1):
            public_task = tasks_by_id[task_id]
            problem_description = public_task.problem_statement or ""
            patch_path = Path(f"/tmp/verifier-sft-teacher-{task_id}.patch")
            eval_error: BaseException | None = None
            try:
                task = evaluator._hydrate_task_from_secret(public_task)
                reference_patch = task.patch or ""
                if not reference_patch.strip():
                    raise RuntimeError("deterministic teacher reference patch unavailable after hydration")
                patch_path.write_text(reference_patch, encoding="utf-8")
                hook_state["patch_path"] = patch_path
                hook_state["task_id"] = task_id
                hook_state["problem_description"] = problem_description
                try:
                    gold.run_maybe_async(
                        evaluator.evaluate_task(
                            task=task,
                            task_index=index,
                            total_tasks=len(target_ids),
                        )
                    )
                except BaseException as exc:
                    # The model phase is deliberately bounded and is not a label.
                    # Keep the error for audit, but deterministic hook evidence may
                    # already be complete and valid.
                    eval_error = exc
            except BaseException as exc:
                eval_error = exc
            finally:
                if hook_state is not None:
                    hook_state["patch_path"] = None
                    hook_state["task_id"] = None
                    hook_state["problem_description"] = None
                try:
                    patch_path.unlink()
                except OSError:
                    pass

            record = None if hook_state is None else hook_state["records"].get(task_id)
            if record is None:
                if eval_error is None:
                    eval_error = RuntimeError("deterministic evidence hook produced no record")
                record = _unapproved_error_record(task_id, problem_description, eval_error)
            elif eval_error is not None:
                record = dict(record)
                record["collector_post_capture_error_type"] = type(eval_error).__name__
                record["collector_post_capture_error"] = str(eval_error)
            records.append(record)
            print(
                "SFT_TEACHER_RECORD",
                json.dumps(
                    {
                        "instance_id": task_id,
                        "approved": record.get("approved"),
                        "audit_flags": record.get("audit_flags"),
                    },
                    sort_keys=True,
                ),
                flush=True,
            )

        approved_ids = [
            str(record["instance_id"])
            for record in records
            if record.get("approved") is True
        ]
        output = {
            "version": "verifier-lora-v0-deterministic-teacher",
            "status": "completed",
            "model": MODEL_NAME,
            "requested": len(target_ids),
            "approved": len(approved_ids),
            "approved_instance_ids": approved_ids,
            "visible_gpus": gpu_count,
            "tensor_parallel_size": tp_size,
            "records": records,
        }
        SUPERVISION_PATH.write_text(
            json.dumps(output, indent=2, sort_keys=True), encoding="utf-8"
        )
        print(
            "SFT_TEACHER_SUMMARY",
            json.dumps({k: v for k, v in output.items() if k != "records"}, sort_keys=True),
            flush=True,
        )
    finally:
        if original_setup_baseline_commit is not None:
            agent_runner.setup_baseline_commit = original_setup_baseline_commit
        if server is not None:
            server.stop()


if __name__ == "__main__":
    try:
        main()
    except BaseException as exc:
        write_failure(exc)
        raise
