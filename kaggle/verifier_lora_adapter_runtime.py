"""Private Kaggle verifier-only LoRA frozen-adapter loading smoke.

The launcher renders two placeholders before pushing this single-file Kaggle
script:

1. ``SUBMISSION_PAYLOAD_B64``: the exact repository ``submission/`` tree.
2. ``HOLDOUT_MANIFEST_JSON``: the finalized, gold-screened verifier-LoRA v0
   holdout manifest.

This runtime intentionally starts one E4B vLLM server and reuses it across all
held-out tasks. It records agent-quality metadata but does not serialize raw
agent patches or reference-solution fields into the summary artifact.
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


SUBMISSION_PAYLOAD_B64 = "__SUBMISSION_PAYLOAD_B64__"
HOLDOUT_MANIFEST_JSON = "__VERIFIER_LORA_HOLDOUT_MANIFEST_JSON__"
MODEL_NAME = "gemma-4-e4b-it-qat-w4a16-ct"

DATA_DIR = Path("/kaggle/input/competitions/gemma-4-developer-agent")
WHEELHOUSE_DIR = Path("/kaggle/input/datasets/metric/gemma-4-developer-agent-wheelhouse")
WORKING_DIR = Path("/kaggle/working")
AGENT_DIR = WORKING_DIR / "submission"
RESULTS_DIR = WORKING_DIR / "verifier-adapter-smoke-results"
SUMMARY_PATH = WORKING_DIR / "verifier_adapter_smoke_results.json"


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



# Training artifact provenance: GitHub Actions 41398395423, frozen adapter.
# Kaggle mounts the output of this private kernel as a private kernel source.
FROZEN_ADAPTER_SOURCE = (
    Path("/kaggle/input/gemma4-verifier-lora-v0-41398395423")
    / "verifier-lora-v0" / "adapter"
)
EXPECTED_ADAPTER_SHA256 = {
    "adapter_config.json": "40a58557e443898efb125f0ed1b47b3691932f45d5f16826d98679c2593c3b9d",
    "adapter_model.safetensors": "3b8e4a90cb3eb718a07ec3c8d53705e0bcc21fa84aeae819ad12ad5ff8bcc199",
}
ADAPTER_NAME = "verifier_lora_v0"


def install_frozen_verifier_adapter() -> None:
    """Copy only the hashed private adapter; leave root coder unchanged."""
    dest = AGENT_DIR / "adapters" / ADAPTER_NAME
    if dest.exists():
        raise RuntimeError("submission unexpectedly already contains verifier adapter")
    if not (AGENT_DIR / "agent.yaml").is_file():
        raise RuntimeError("root coder configuration is missing")
    for filename, expected in EXPECTED_ADAPTER_SHA256.items():
        candidate = FROZEN_ADAPTER_SOURCE / filename
        if not candidate.is_file():
            raise FileNotFoundError(f"frozen private Kaggle adapter input not found: {candidate}")
        digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
        if digest != expected:
            raise RuntimeError(f"frozen adapter hash mismatch for {filename}")
    dest.mkdir(parents=True)
    for filename in EXPECTED_ADAPTER_SHA256:
        shutil.copyfile(FROZEN_ADAPTER_SOURCE / filename, dest / filename)

    verifier_path = AGENT_DIR / "sub_agents" / "verifier.yaml"
    verifier_config = verifier_path.read_text(encoding="utf-8")
    if "adapter:" in verifier_config:
        raise RuntimeError("verifier config already specifies an adapter")
    anchor = "model: gemma-4-e4b-it-qat-w4a16-ct\\n"
    if verifier_config.count(anchor) != 1:
        raise RuntimeError("unexpected verifier base model declaration")
    verifier_config = verifier_config.replace(anchor, anchor + f"adapter: {ADAPTER_NAME}\\n", 1)
    verifier_path.write_text(verifier_config, encoding="utf-8")
    print("FROZEN_ADAPTER_ATTACHED", ADAPTER_NAME, sorted(EXPECTED_ADAPTER_SHA256), flush=True)


def load_holdout_ids() -> list[str]:
    if not HOLDOUT_MANIFEST_JSON or HOLDOUT_MANIFEST_JSON.startswith("_"):
        raise RuntimeError("holdout manifest placeholder was not rendered")
    payload = json.loads(HOLDOUT_MANIFEST_JSON)
    if payload.get("version") != "verifier-lora-v0":
        raise ValueError(f"unexpected holdout version: {payload.get('version')!r}")

    raw = payload.get("holdout")
    if not isinstance(raw, list) or not raw:
        raise ValueError("holdout manifest has no tasks")
    ids = [str(item.get("instance_id") or "") for item in raw if isinstance(item, dict)]
    if len(ids) != len(raw) or any(not value for value in ids):
        raise ValueError("holdout manifest contains an invalid task entry")
    if len(ids) != len(set(ids)):
        raise ValueError("holdout manifest contains duplicate task IDs")
    return ids


def run_maybe_async(value):
    if inspect.isawaitable(value):
        return asyncio.run(value)
    return value


def _error_record(task_id: str, exc: BaseException) -> dict[str, object]:
    return {
        "instance_id": task_id,
        "status": "error",
        "resolved": False,
        "test_exit_code": None,
        "patch_chars": 0,
        "has_patch": False,
        "tool_calls": None,
        "duration_seconds": None,
        "error_type": type(exc).__name__,
        "error": str(exc),
    }


def write_failure(exc: BaseException) -> None:
    SUMMARY_PATH.write_text(
        json.dumps(
            {
                "version": "verifier-lora-v0",
                "model": MODEL_NAME,
                "variant": ADAPTER_NAME,
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
    install_frozen_verifier_adapter()
    holdout_ids = load_holdout_ids()

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

    adapters = discover_adapters(str(AGENT_DIR), adapter_extensions=ALLOWED_ADAPTER_EXTENSIONS)
    adapter_map = getattr(adapters, "adapters", None) or {}
    if set(adapter_map) != {ADAPTER_NAME}:
        raise RuntimeError(f"expected only frozen verifier adapter, found: {sorted(adapter_map)}")

    model_path = Path(f"/kaggle/input/models/google/gemma-4/other/{MODEL_NAME}/2")
    if not model_path.exists():
        raise FileNotFoundError(f"E4B model weights not found: {model_path}")

    tasks_path = DATA_DIR / "tasks.jsonl"
    public_tasks = load_tasks(tasks_path)
    tasks_by_id = {task.instance_id: task for task in public_tasks if task.instance_id in set(holdout_ids)}
    missing = [task_id for task_id in holdout_ids if task_id not in tasks_by_id]
    if missing:
        raise RuntimeError(f"holdout task(s) missing from public corpus: {missing}")

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
        raise RuntimeError("Kaggle baseline kernel has no visible GPU")
    tp_size = 4 if gpu_count >= 4 else (2 if gpu_count >= 2 else 1)

    server = None
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
                enable_lora=True,
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
        print(f"vLLM ready at {server.base_url}; visible_gpus={gpu_count}; tp={tp_size}")

        models = server.create_model_registry(
            aliases=[MODEL_NAME],
            model_prefix="openai/",
            api_key=os.environ["LOCAL_API_KEY"],
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

        records: list[dict[str, object]] = []
        for index, task_id in enumerate(holdout_ids, 1):
            print(f"[{index:02d}/{len(holdout_ids):02d}] adapter-smoke {task_id}", flush=True)
            try:
                result = run_maybe_async(
                    evaluator.evaluate_task(
                        task=tasks_by_id[task_id],
                        task_index=index,
                        total_tasks=len(holdout_ids),
                    )
                )
                candidate = (result.agent_patch or "").strip()
                record = {
                    "instance_id": task_id,
                    "status": "completed",
                    "resolved": bool(result.resolved),
                    "test_exit_code": result.test_exit_code,
                    "patch_chars": len(candidate),
                    "has_patch": bool(candidate),
                    "tool_calls": result.tool_calls,
                    "duration_seconds": result.duration_seconds,
                }
            except BaseException as exc:
                record = _error_record(task_id, exc)
                print(f"baseline error for {task_id}: {type(exc).__name__}: {exc}", flush=True)
            records.append(record)
            print("BASELINE_RESULT", json.dumps(record, sort_keys=True), flush=True)

        resolved_ids = sorted(
            str(record["instance_id"])
            for record in records
            if record.get("status") == "completed" and record.get("resolved") is True
        )
        output = {
            "version": "verifier-lora-v0",
            "model": MODEL_NAME,
            "variant": ADAPTER_NAME,
            "adapter_weights_sha256": EXPECTED_ADAPTER_SHA256["adapter_model.safetensors"],
            "status": "completed",
            "requested": len(holdout_ids),
            "completed": sum(record.get("status") == "completed" for record in records),
            "resolved": len(resolved_ids),
            "resolved_instance_ids": resolved_ids,
            "visible_gpus": gpu_count,
            "tensor_parallel_size": tp_size,
            "results": records,
        }
        SUMMARY_PATH.write_text(json.dumps(output, indent=2, sort_keys=True), encoding="utf-8")
        print(
            "BASELINE_SUMMARY",
            json.dumps({key: value for key, value in output.items() if key != "results"}, sort_keys=True),
            flush=True,
        )
    finally:
        if server is not None:
            server.stop()


if __name__ == "__main__":
    try:
        main()
    except BaseException as exc:
        write_failure(exc)
        raise
