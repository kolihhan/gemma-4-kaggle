"""Private Kaggle 31B L4x4 startup + tool-call parser diagnostic.

NO issue/task data hydrated, NO agent patch generation, NO leaderboard submission.
This is a deployment feasibility smoke, not a capacity or correctness experiment.
"""
from __future__ import annotations

import glob
import hashlib
import importlib
import json
import os
import shutil
import subprocess
import sys
import time
import traceback
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

MODEL_NAME = "gemma-4-31b-it-qat-w4a16-ct"
MODEL_PATH = Path(f"/kaggle/input/models/google/gemma-4/other/{MODEL_NAME}/2")
WHEELHOUSE = Path("/kaggle/input/datasets/metric/gemma-4-developer-agent-wheelhouse")
RESULT_PATH = Path("/kaggle/working/capacity_31b_startup_result.json")
LOCAL_API = "http://127.0.0.1:8000"
MAX_MODEL_LEN = 32768
GPU_MEMORY_UTILIZATION = 0.90
TP_SIZE = 4
STARTUP_TIMEOUT = 60 * 35


def configure_environment() -> None:
    for k, v in {
        "TRANSFORMERS_NO_TF": "1",
        "TRANSFORMERS_NO_FLAX": "1",
        "TRANSFORMERS_OFFLINE": "1",
        "VLLM_NO_USAGE_STATS": "1",
        "VLLM_WORKER_MULTIPROC_METHOD": "spawn",
        "VLLM_ENGINE_READY_TIMEOUT_S": "2100",
        "VLLM_MEMORY_PROFILER_ESTIMATE_CUDAGRAPHS": "1",
        "NCCL_DEBUG": "WARN",
        "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True",
        "OTEL_SDK_DISABLED": "true",
        "OTEL_PYTHON_DISABLED": "true",
    }.items():
        os.environ[k] = v


def install_official_wheelhouse() -> int:
    if not WHEELHOUSE.is_dir():
        raise FileNotFoundError("official scorer wheelhouse is not mounted")
    for pattern in (
        "/usr/local/lib/python*/dist-packages/*cutlass*.pth",
        "/usr/local/lib/python*/site-packages/*cutlass*.pth",
    ):
        for p in glob.glob(pattern):
            try:
                Path(p).unlink()
            except OSError:
                pass
    clean = Path("/tmp/capacity-v0-31b-official-wheels")
    clean.mkdir(parents=True, exist_ok=True)
    for wheel in WHEELHOUSE.glob("*.whl"):
        if "cutlass" in wheel.name.lower():
            continue
        filename = (
            wheel.name.replace("cu128", "+cu128")
            if "cu128" in wheel.name and "+" not in wheel.name else wheel.name
        )
        dst = clean / filename
        if not dst.exists():
            try:
                dst.symlink_to(wheel)
            except OSError:
                shutil.copyfile(wheel, dst)
    wheels = sorted(str(p) for p in clean.glob("*.whl"))
    if not wheels:
        raise RuntimeError("no official scorer wheels found")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-q",
         "--no-deps", "--force-reinstall", *wheels],
        check=True,
    )
    importlib.invalidate_caches()
    return len(wheels)


def http_json(method: str, endpoint: str, body: dict | None = None) -> dict:
    encoded = json.dumps(body).encode("utf-8") if body is not None else None
    request = Request(
        LOCAL_API + endpoint,
        data=encoded,
        method=method,
        headers={"Content-Type": "application/json", "Authorization": "Bearer EMPTY"},
    )
    with urlopen(request, timeout=120) as response:
        return json.loads(response.read().decode("utf-8"))


def response_summary(data: dict) -> dict:
    choices = data.get("choices") or []
    message = choices[0].get("message", {}) if choices else {}
    usage = data.get("usage") or {}
    return {
        "http_ok": bool(choices),
        "tool_calls": len(message.get("tool_calls") or []),
        "usage_prompt_tokens": usage.get("prompt_tokens"),
        "usage_completion_tokens": usage.get("completion_tokens"),
        "finish_reason": choices[0].get("finish_reason") if choices else None,
    }


def probe_plain(model: str) -> dict:
    start = time.perf_counter()
    try:
        r = http_json("POST", "/v1/chat/completions", {
            "model": model,
            "messages": [
                {"role": "system", "content": "Reply with just READY."},
                {"role": "user", "content": "Say READY."},
            ],
            "max_tokens": 256,
            "temperature": 0.2,
        })
        return {"status": "completed", "elapsed_seconds": round(time.perf_counter()-start, 3),
                **response_summary(r)}
    except Exception as exc:
        return {"status": "error", "elapsed_seconds": round(time.perf_counter()-start, 3),
                "error_type": type(exc).__name__}


def tool_spec(name: str, schema: dict) -> dict:
    return {"type": "function", "function": {
        "name": name,
        "description": "Return the requested synthetic diagnostic arguments.",
        "parameters": schema,
    }}


def probe_scalar_tool(model: str) -> dict:
    return probe_tool(
        model,
        "answer_number",
        {"type": "object", "properties": {"value": {"type": "integer"}},
         "required": ["value"], "additionalProperties": False},
        "Call the answer_number tool with value 42. Do not reply with prose.",
    )


def probe_array_tool(model: str) -> dict:
    return probe_tool(
        model,
        "get_code_subgraph",
        {"type": "object",
         "properties": {"nodes": {"type": "array", "items": {"type": "string"}}},
         "required": ["nodes"], "additionalProperties": False},
        "Call get_code_subgraph with nodes containing the strings alpha and beta. No prose.",
    )


def probe_tool(model: str, name: str, schema: dict, user_message: str) -> dict:
    start = time.perf_counter()
    try:
        r = http_json("POST", "/v1/chat/completions", {
            "model": model,
            "messages": [
                {"role": "system", "content": "You must invoke the provided tool to satisfy the user."},
                {"role": "user", "content": user_message},
            ],
            "tools": [tool_spec(name, schema)],
            "tool_choice": "auto",
            "max_tokens": 1024,
            "temperature": 0.2,
        })
        summary = response_summary(r)
        calls = (r.get("choices") or [{}])[0].get("message", {}).get("tool_calls") or []
        recognized = False
        argument_valid = False
        for call in calls:
            fn = call.get("function", {}) if isinstance(call, dict) else {}
            if fn.get("name") != name:
                continue
            recognized = True
            try:
                args = json.loads(fn.get("arguments") or "{}")
                if name == "answer_number":
                    argument_valid = (type(args.get("value")) is int and args["value"] == 42)
                else:
                    argument_valid = (args.get("nodes") == ["alpha", "beta"])
            except (ValueError, TypeError, AttributeError):
                pass
        return {
            "status": "completed", "elapsed_seconds": round(time.perf_counter()-start, 3),
            "recognized_tool_call": recognized, "arguments_match_fixture": argument_valid,
            **summary,
        }
    except Exception as exc:
        return {
            "status": "error", "elapsed_seconds": round(time.perf_counter()-start, 3),
            "recognized_tool_call": False, "arguments_match_fixture": False,
            "error_type": type(exc).__name__,
        }


def write_result(result: dict) -> None:
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("CAPACITY_31B_STARTUP_RESULT", json.dumps(result, sort_keys=True), flush=True)


def main() -> None:
    result: dict = {
        "version": "capacity-v0-31b-startup-smoke",
        "experiment_role": "startup_and_synthetic_tool_parser_only",
        "model": MODEL_NAME,
        "max_model_len": MAX_MODEL_LEN,
        "gpu_memory_utilization": GPU_MEMORY_UTILIZATION,
        "lora_enabled": False,
        "tensor_parallel_size": TP_SIZE,
        "status": "started",
        "competition_tasks_used": 0,
        "gpu_count": None,
        "startup_seconds": None,
        "plain": None,
        "scalar": None,
        "array": None,
    }
    start = time.perf_counter()
    server = None
    try:
        configure_environment()
        result["official_wheels"] = install_official_wheelhouse()
        import torch
        from adk_submission import VllmConfig, VllmServer

        count = torch.cuda.device_count() if torch.cuda.is_available() else 0
        result["gpu_count"] = count
        if count != TP_SIZE:
            raise RuntimeError(f"need exactly {TP_SIZE} L4 GPUs, found {count}")
        if not MODEL_PATH.is_dir():
            raise FileNotFoundError(f"official 31B model directory unavailable: {MODEL_PATH}")

        server = VllmServer(VllmConfig(
            model=str(MODEL_PATH),
            host="127.0.0.1",
            port=8000,
            tool_call_parser="gemma4",
            reasoning_parser="gemma4",
            max_model_len=MAX_MODEL_LEN,
            dtype="bfloat16" if torch.cuda.is_bf16_supported() else "auto",
            gpu_memory_utilization=GPU_MEMORY_UTILIZATION,
            enable_auto_tool_choice=True,
            enable_lora=False,
            max_loras=1,
            max_lora_rank=128,
            scheduler_reserve_full_isl=False,
            tensor_parallel_size=TP_SIZE,
            startup_timeout=STARTUP_TIMEOUT,
            extra_args=(),
        ))
        server.start()
        result["startup_seconds"] = round(time.perf_counter()-start, 3)
        models = http_json("GET", "/v1/models").get("data") or []
        if not models:
            raise RuntimeError("vLLM started without an exposed OpenAI-compatible model")
        model = models[0]["id"]
        result["status"] = "server_ready"
        result["plain"] = probe_plain(model)
        result["scalar"] = probe_scalar_tool(model)
        result["array"] = probe_array_tool(model)
        result["status"] = "smoke_completed"
    except Exception as exc:
        result["status"] = "error"
        result["error_type"] = type(exc).__name__
        result["error_digest_sha256"] = hashlib.sha256(
            str(exc).encode("utf-8")).hexdigest()
    finally:
        if server is not None:
            try:
                server.stop()
            except Exception:
                result["server_stop_status"] = "error"
        result["total_seconds"] = round(time.perf_counter()-start, 3)
        write_result(result)


if __name__ == "__main__":
    main()
