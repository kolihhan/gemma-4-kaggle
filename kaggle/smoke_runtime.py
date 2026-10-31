"""Private Kaggle one-task smoke runtime for the canonical E4B submission.

The GitHub launcher replaces SUBMISSION_PAYLOAD_B64 with a base64-encoded JSON
mapping built from the repository's canonical submission/ directory. This keeps
submission/ as the single source of truth while allowing an internet-disabled
Kaggle kernel to materialize the exact candidate agent at runtime.
"""

from __future__ import annotations

import asyncio
import base64
import glob
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


SUBMISSION_PAYLOAD_B64 = "__SUBMISSION_PAYLOAD_B64__"
MODEL_NAME = "gemma-4-e4b-it-qat-w4a16-ct"
SMOKE_TASK_ID = "rich_3278"

DATA_DIR = Path("/kaggle/input/competitions/gemma-4-developer-agent")
WHEELHOUSE_DIR = Path("/kaggle/input/datasets/metric/gemma-4-developer-agent-wheelhouse")
WORKING_DIR = Path("/kaggle/working")
AGENT_DIR = WORKING_DIR / "submission"
RESULT_PATH = WORKING_DIR / "smoke_result.json"
PATCH_PATH = WORKING_DIR / "smoke_patch.diff"


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

    for name in (
        "LiteLLM",
        "LiteLLM Router",
        "LiteLLM Proxy",
        "litellm",
        "httpx",
        "httpcore",
        "openai",
        "urllib3",
        "opentelemetry",
        "opentelemetry.context",
    ):
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
                os.unlink(pth)
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


def materialize_submission() -> None:
    if not SUBMISSION_PAYLOAD_B64 or SUBMISSION_PAYLOAD_B64.startswith("_"):
        raise RuntimeError("submission payload placeholder was not rendered")

    raw = base64.b64decode(SUBMISSION_PAYLOAD_B64.encode("ascii")).decode("utf-8")
    files = json.loads(raw)
    if not isinstance(files, dict) or "agent.yaml" not in files:
        raise ValueError("embedded submission payload is invalid")

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

    print("Materialized canonical submission files:")
    for path in sorted(AGENT_DIR.rglob("*")):
        if path.is_file():
            print(" -", path.relative_to(AGENT_DIR))


def run_maybe_async(value):
    if inspect.isawaitable(value):
        return asyncio.run(value)
    return value


def write_failure(exc: BaseException) -> None:
    RESULT_PATH.write_text(
        json.dumps(
            {
                "instance_id": SMOKE_TASK_ID,
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
    configure_environment()
    install_official_wheelhouse()
    materialize_submission()

    import litellm
    import torch
    import yaml
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

    model_path = Path(f"/kaggle/input/models/google/gemma-4/other/{MODEL_NAME}/2")
    if not model_path.exists():
        raise FileNotFoundError(f"E4B model weights not found: {model_path}")

    adapters = discover_adapters(str(AGENT_DIR), adapter_extensions=ALLOWED_ADAPTER_EXTENSIONS)
    adapter_map = getattr(adapters, "adapters", None) or {}
    if adapter_map:
        raise RuntimeError(f"baseline v0 must not contain adapters: {sorted(adapter_map)}")

    tasks_path = DATA_DIR / "tasks.jsonl"
    tasks = load_tasks(tasks_path)
    task = next((item for item in tasks if item.instance_id == SMOKE_TASK_ID), None)
    if task is None:
        raise RuntimeError(f"public smoke task not found: {SMOKE_TASK_ID}")

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
        raise RuntimeError("Kaggle smoke kernel has no visible GPU")
    tp_size = 4 if gpu_count >= 4 else (2 if gpu_count >= 2 else 1)

    server = None
    try:
        vllm_config = VllmConfig(
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
        )
        server = VllmServer(vllm_config, adapter_manifest=adapters)
        server.start()
        print(f"vLLM ready at {server.base_url}; visible_gpus={gpu_count}; tp={tp_size}")

        models = server.create_model_registry(
            aliases=[MODEL_NAME],
            model_prefix="openai/",
            api_key=os.environ["LOCAL_API_KEY"],
        )

        eval_config = EvalConfig(
            tasks_path=tasks_path,
            snapshots_dir=DATA_DIR / "snapshots",
            results_dir=WORKING_DIR / "results",
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
                min_tokens=2048,
                ttl_seconds=1800,
                cache_intervals=10,
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
        result = run_maybe_async(
            evaluator.evaluate_task(
                task=task,
                task_index=1,
                total_tasks=1,
            )
        )

        agent_patch = (result.agent_patch or "").strip()
        PATCH_PATH.write_text(agent_patch, encoding="utf-8")
        output = {
            "instance_id": SMOKE_TASK_ID,
            "model": MODEL_NAME,
            "status": "completed",
            "resolved": bool(result.resolved),
            "test_exit_code": result.test_exit_code,
            "patch_chars": len(agent_patch),
            "has_patch": bool(agent_patch),
            "tool_calls": result.tool_calls,
            "duration_seconds": result.duration_seconds,
            "visible_gpus": gpu_count,
            "tensor_parallel_size": tp_size,
        }
        RESULT_PATH.write_text(json.dumps(output, indent=2, sort_keys=True), encoding="utf-8")
        print("SMOKE_RESULT", json.dumps(output, sort_keys=True))
    finally:
        if server is not None:
            server.stop()


if __name__ == "__main__":
    try:
        main()
    except BaseException as exc:
        write_failure(exc)
        raise
