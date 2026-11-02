"""Training-only gold-patch verifier teacher runtime for verifier-LoRA v0.

The runtime is rendered into one private Kaggle script. It uses only the frozen
training subset and frozen training gold screen, rewrites an experiment copy of
the canonical submission to a verifier-only root, applies each reference patch
after the official clean baseline commit, and runs the current E4B verifier.
Blind tasks are never accepted here.
"""

from __future__ import annotations

import asyncio
import base64
import glob
import hashlib
import importlib
import inspect
import json
import logging
import os
import shutil
import subprocess
import sys
import traceback
from pathlib import Path
from typing import Any


SUBMISSION_PAYLOAD_B64 = "__SUBMISSION_PAYLOAD_B64__"
TRAINING_MANIFEST_JSON = "__VERIFIER_LORA_TRAINING_MANIFEST_JSON__"
TRAINING_GOLD_SCREEN_JSON = "__VERIFIER_LORA_TRAINING_GOLD_SCREEN_JSON__"
MODEL_NAME = "gemma-4-e4b-it-qat-w4a16-ct"
TRAINING_GOLD_SCREEN_VERSION = "verifier-lora-v0-training-gold-screen"
TRAINING_MANIFEST_VERSION = "verifier-lora-v0-train-harvest"

DATA_DIR = Path("/kaggle/input/competitions/gemma-4-developer-agent")
WHEELHOUSE_DIR = Path("/kaggle/input/datasets/metric/gemma-4-developer-agent-wheelhouse")
WORKING_DIR = Path("/kaggle/working")
AGENT_DIR = WORKING_DIR / "verifier-gold-teacher-submission"
RESULTS_DIR = WORKING_DIR / "verifier-gold-teacher-results"
SUMMARY_PATH = WORKING_DIR / "verifier_gold_teacher_results.json"


def load_clean_training_ids(
    manifest_json: str,
    allowed_training_ids: set[str],
) -> list[str]:
    """Return frozen gold-clean IDs, refusing any non-training contamination."""
    try:
        payload = json.loads(manifest_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid training gold-screen JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("training gold-screen manifest must be an object")
    if payload.get("version") != TRAINING_GOLD_SCREEN_VERSION:
        raise ValueError(
            f"unexpected training gold-screen version: {payload.get('version')!r}"
        )
    if payload.get("status") != "frozen":
        raise ValueError("training gold-screen must be frozen before teacher use")
    if payload.get("source_training_manifest") != TRAINING_MANIFEST_VERSION:
        raise ValueError(
            "training gold-screen source manifest does not match the frozen training subset"
        )

    raw_ids = payload.get("clean_instance_ids")
    if not isinstance(raw_ids, list) or not raw_ids:
        raise ValueError("training gold-screen has no clean_instance_ids")
    ids: list[str] = []
    for raw in raw_ids:
        if not isinstance(raw, str) or not raw:
            raise ValueError("training gold-screen contains an invalid task ID")
        ids.append(raw)
    if len(ids) != len(set(ids)):
        raise ValueError("training gold-screen contains duplicate task IDs")

    contamination = sorted(set(ids) - set(allowed_training_ids))
    if contamination:
        raise ValueError(
            f"training gold-screen contains non-training IDs: {contamination}"
        )
    return ids


def build_verifier_only_submission(files: dict[str, str]) -> dict[str, str]:
    """Build an experiment-only root agent that is exactly the current verifier."""
    if not isinstance(files, dict) or not files:
        raise ValueError("submission payload must be a non-empty file mapping")
    required = ("prompts/verifier.md", "configs/sampling.yaml")
    missing = [path for path in required if not isinstance(files.get(path), str)]
    if missing:
        raise ValueError(f"submission payload is missing verifier assets: {missing}")

    built = dict(files)
    built["agent.yaml"] = (
        "agent_class: LlmAgent\n"
        "name: swe_e4b_verifier\n"
        f"model: {MODEL_NAME}\n"
        "description: Independently verifies the existing patch, performs at most one narrow repair, and owns final submission.\n"
        "instruction: !include prompts/verifier.md\n"
        "tools:\n"
        "  - run_command\n"
        "  - read_file\n"
        "  - edit_file\n"
        "  - get_status\n"
        "  - submit_patch\n"
        "generate_content_config: !include configs/sampling.yaml\n"
    )
    return built


def install_gold_patch_after_baseline_hook():
    """Make the reference patch appear only after the official baseline commit."""
    import swegemma.harness.agent_runner as agent_runner
    from swegemma.harness.container_setup import apply_patch_in_container

    original_setup_baseline_commit = agent_runner.setup_baseline_commit
    state: dict[str, Path | None] = {"patch_path": None}

    def setup_baseline_then_gold_patch(docker, container_id, commit_msg="baseline"):
        original_setup_baseline_commit(docker, container_id, commit_msg)
        patch_path = state.get("patch_path")
        if patch_path is None:
            raise RuntimeError("gold teacher has no active reference patch")
        patch_path = Path(patch_path)
        if not patch_path.is_file() or patch_path.stat().st_size == 0:
            raise RuntimeError(f"gold teacher reference patch is missing/empty: {patch_path}")

        container_patch = "/tmp/verifier_gold_reference.patch"
        docker.copy_to(container_id, patch_path, container_patch)
        exit_code, stdout, stderr = apply_patch_in_container(
            docker, container_id, container_patch
        )
        try:
            if exit_code != 0:
                raise RuntimeError(
                    "failed to apply gold teacher patch: "
                    f"exit={exit_code} stdout={stdout[-1000:]!r} stderr={stderr[-1000:]!r}"
                )
            diff_check = docker.exec(container_id, "cd /workspace && git diff --check")
            if diff_check.exit_code != 0:
                raise RuntimeError(
                    "gold teacher patch failed git diff --check: "
                    f"{(diff_check.stderr or diff_check.stdout)[-1000:]}"
                )
            diff_nonempty = docker.exec(
                container_id, "cd /workspace && git diff --quiet HEAD"
            )
            if diff_nonempty.exit_code != 1:
                raise RuntimeError(
                    "gold teacher patch is not a clean non-empty diff: "
                    f"git diff --quiet HEAD exit={diff_nonempty.exit_code}"
                )
        finally:
            docker.exec(container_id, f"rm -f {container_patch}")

    agent_runner.setup_baseline_commit = setup_baseline_then_gold_patch
    return state, original_setup_baseline_commit


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def build_result_record(
    *,
    instance_id: str,
    repo: str,
    reference_patch: str,
    resolved: bool,
    test_exit_code: int | None,
    agent_patch: str,
    tool_calls: int | None,
    duration_seconds: float | None,
    error: str | None,
) -> dict[str, Any]:
    """Build metadata-only result; never serialize either patch body."""
    if not isinstance(reference_patch, str) or not reference_patch:
        raise ValueError("reference_patch must be non-empty text")
    if not isinstance(agent_patch, str):
        raise ValueError("agent_patch must be text")
    return {
        "instance_id": instance_id,
        "repo": repo,
        "status": "completed" if error is None else "error",
        "resolved": bool(resolved),
        "test_exit_code": test_exit_code,
        "reference_patch_chars": len(reference_patch),
        "reference_patch_sha256": _sha256_text(reference_patch),
        "agent_patch_chars": len(agent_patch),
        "agent_patch_sha256": _sha256_text(agent_patch),
        "has_agent_patch": bool(agent_patch.strip()),
        "tool_calls": tool_calls,
        "duration_seconds": duration_seconds,
        "error": error,
    }


def configure_environment() -> None:
    values = {
        "TRANSFORMERS_NO_TF": "1",
        "TRANSFORMERS_NO_FLAX": "1",
        "TRANSFORMERS_OFFLINE": "1",
        "VLLM_NO_USAGE_STATS": "1",
        "VLLM_WORKER_MULTIPROC_METHOD": "spawn",
        "VLLM_ENGINE_READY_TIMEOUT_S": "1200",
        "VLLM_MEMORY_PROFILER_ESTIMATE_CUDAGRAPHS": "1",
        "NCCL_DEBUG": "WARN",
        "LITELLM_LOCAL_MODEL_COST_MAP": "True",
        "LITELLM_TELEMETRY": "False",
        "LITELLM_LOG": "WARNING",
        "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True",
        "OTEL_SDK_DISABLED": "true",
        "OTEL_PYTHON_DISABLED": "true",
    }
    for key, value in values.items():
        os.environ[key] = value
    os.environ.setdefault("OPENAI_API_KEY", "EMPTY")
    os.environ.setdefault("LOCAL_API_KEY", "EMPTY")
    for name in ("LiteLLM", "LiteLLM Router", "LiteLLM Proxy", "litellm", "httpx", "httpcore", "openai", "urllib3", "opentelemetry", "opentelemetry.context"):
        logger = logging.getLogger(name)
        logger.setLevel(logging.WARNING)
        if "litellm" in name.lower():
            logger.propagate = False
            logger.handlers.clear()


def install_official_wheelhouse() -> None:
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
        if not target.exists():
            try:
                target.symlink_to(wheel)
            except OSError:
                shutil.copyfile(wheel, target)
    wheels = sorted(str(path) for path in fixed_dir.glob("*.whl"))
    if not wheels:
        raise RuntimeError(f"no wheels found under {WHEELHOUSE_DIR}")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-q", "--no-deps", "--force-reinstall", *wheels],
        check=True,
    )
    importlib.invalidate_caches()


def _load_training_ids() -> list[str]:
    if not TRAINING_MANIFEST_JSON or TRAINING_MANIFEST_JSON.startswith("_"):
        raise RuntimeError("training manifest placeholder was not rendered")
    payload = json.loads(TRAINING_MANIFEST_JSON)
    if payload.get("version") != TRAINING_MANIFEST_VERSION:
        raise ValueError(f"unexpected training manifest version: {payload.get('version')!r}")
    raw = payload.get("tasks")
    if not isinstance(raw, list) or not raw:
        raise ValueError("training manifest has no tasks")
    ids = [str(item.get("instance_id") or "") for item in raw if isinstance(item, dict)]
    if len(ids) != len(raw) or any(not value for value in ids) or len(ids) != len(set(ids)):
        raise ValueError("training manifest contains invalid or duplicate task IDs")
    return ids


def materialize_submission() -> None:
    if not SUBMISSION_PAYLOAD_B64 or SUBMISSION_PAYLOAD_B64.startswith("_"):
        raise RuntimeError("submission payload placeholder was not rendered")
    raw = base64.b64decode(SUBMISSION_PAYLOAD_B64.encode("ascii")).decode("utf-8")
    canonical = json.loads(raw)
    if not isinstance(canonical, dict) or "agent.yaml" not in canonical:
        raise ValueError("embedded submission payload is invalid")
    if any(str(path).startswith("adapters/") for path in canonical):
        raise RuntimeError("training gold teacher must use base submission without adapters")
    files = build_verifier_only_submission(canonical)

    if AGENT_DIR.exists():
        shutil.rmtree(AGENT_DIR)
    AGENT_DIR.mkdir(parents=True)
    root = AGENT_DIR.resolve()
    for relative, content in sorted(files.items()):
        target = (AGENT_DIR / relative).resolve()
        if root not in target.parents and target != root:
            raise ValueError(f"unsafe submission path: {relative}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")


def run_maybe_async(value):
    if inspect.isawaitable(value):
        return asyncio.run(value)
    return value


def _error_record(instance_id: str, repo: str, exc: BaseException) -> dict[str, Any]:
    return {
        "instance_id": instance_id,
        "repo": repo,
        "status": "error",
        "resolved": False,
        "test_exit_code": None,
        "reference_patch_chars": None,
        "reference_patch_sha256": None,
        "agent_patch_chars": 0,
        "agent_patch_sha256": _sha256_text(""),
        "has_agent_patch": False,
        "tool_calls": None,
        "duration_seconds": None,
        "error_type": type(exc).__name__,
        "error": str(exc),
    }


def write_failure(exc: BaseException) -> None:
    SUMMARY_PATH.write_text(
        json.dumps(
            {
                "version": "verifier-lora-v0-gold-teacher",
                "model": MODEL_NAME,
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


def main() -> None:
    WORKING_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    configure_environment()
    install_official_wheelhouse()
    materialize_submission()

    training_ids = _load_training_ids()
    clean_ids = load_clean_training_ids(TRAINING_GOLD_SCREEN_JSON, set(training_ids))

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
        raise RuntimeError(f"gold teacher must not contain adapters: {sorted(adapter_map)}")

    model_path = Path(f"/kaggle/input/models/google/gemma-4/other/{MODEL_NAME}/2")
    if not model_path.exists():
        raise FileNotFoundError(f"E4B model weights not found: {model_path}")

    tasks_path = DATA_DIR / "tasks.jsonl"
    public_tasks = load_tasks(tasks_path)
    selected = set(clean_ids)
    tasks_by_id = {task.instance_id: task for task in public_tasks if task.instance_id in selected}
    missing = [task_id for task_id in clean_ids if task_id not in tasks_by_id]
    if missing:
        raise RuntimeError(f"gold-teacher task(s) missing from public corpus: {missing}")

    raw_eval = yaml.safe_load((AGENT_DIR / "eval_config.yaml").read_text(encoding="utf-8")) or {}
    eval_section = raw_eval.get("evaluation", raw_eval)
    timeout_seconds = int(eval_section.get("timeout_seconds", 300))
    verification_timeout_seconds = int(eval_section.get("verification_timeout_seconds", 300))
    max_tool_calls = int(eval_section.get("max_tool_calls", 100))
    max_time_minutes = float(eval_section.get("max_time_minutes", 60.0))
    turns_raw = eval_section.get("max_turns", eval_section.get("max_llm_calls"))
    max_turns = int(turns_raw) if turns_raw is not None else None

    gpu_count = torch.cuda.device_count() if torch.cuda.is_available() else 0
    if gpu_count < 1:
        raise RuntimeError("Kaggle gold-teacher kernel has no visible GPU")
    tp_size = 4 if gpu_count >= 4 else (2 if gpu_count >= 2 else 1)

    server = None
    hook_state = None
    original_setup_baseline_commit = None
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
            snapshots_dir=DATA_DIR / "snapshots",
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
            graph_dir=str(DATA_DIR / "graphs"),
            embeddings_dir=str(DATA_DIR / "embeddings"),
            wheels_dir=DATA_DIR / "wheels",
            verbose=False,
        )
        evaluator = Evaluator(eval_config)
        hook_state, original_setup_baseline_commit = install_gold_patch_after_baseline_hook()

        records: list[dict[str, Any]] = []
        for index, task_id in enumerate(clean_ids, 1):
            public_task = tasks_by_id[task_id]
            repo = public_task.repo
            patch_path = Path(f"/tmp/verifier-gold-teacher-{task_id}.patch")
            try:
                task = evaluator._hydrate_task_from_secret(public_task)
                reference_patch = task.patch or ""
                if not reference_patch.strip():
                    raise RuntimeError("gold teacher reference patch unavailable after hydration")
                patch_path.write_text(reference_patch, encoding="utf-8")
                hook_state["patch_path"] = patch_path
                result = run_maybe_async(
                    evaluator.evaluate_task(
                        task=task,
                        task_index=index,
                        total_tasks=len(clean_ids),
                    )
                )
                agent_patch = result.agent_patch or ""
                record = build_result_record(
                    instance_id=task_id,
                    repo=repo,
                    reference_patch=reference_patch,
                    resolved=bool(result.resolved),
                    test_exit_code=result.test_exit_code,
                    agent_patch=agent_patch,
                    tool_calls=result.tool_calls,
                    duration_seconds=result.duration_seconds,
                    error=result.error,
                )
            except BaseException as exc:
                record = _error_record(task_id, repo, exc)
                print(f"GOLD_TEACHER_ERROR {task_id}: {type(exc).__name__}: {exc}", flush=True)
            finally:
                if hook_state is not None:
                    hook_state["patch_path"] = None
                try:
                    patch_path.unlink()
                except OSError:
                    pass
            records.append(record)
            print("GOLD_TEACHER_RESULT", json.dumps(record, sort_keys=True), flush=True)

        resolved_ids = sorted(
            str(record["instance_id"])
            for record in records
            if record.get("status") == "completed" and record.get("resolved") is True
        )
        output = {
            "version": "verifier-lora-v0-gold-teacher",
            "model": MODEL_NAME,
            "status": "completed",
            "requested": len(clean_ids),
            "completed": sum(record.get("status") == "completed" for record in records),
            "resolved": len(resolved_ids),
            "resolved_instance_ids": resolved_ids,
            "visible_gpus": gpu_count,
            "tensor_parallel_size": tp_size,
            "results": records,
        }
        SUMMARY_PATH.write_text(json.dumps(output, indent=2, sort_keys=True), encoding="utf-8")
        print(
            "GOLD_TEACHER_SUMMARY",
            json.dumps({k: v for k, v in output.items() if k != "results"}, sort_keys=True),
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
