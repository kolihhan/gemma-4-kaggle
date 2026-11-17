"""Private native 31B patch generation over the frozen solver-only input."""

from dataclasses import replace
from hashlib import sha256
from io import BytesIO
import re
import tempfile
import time
from zipfile import ZipFile


def find_one(pattern):
    paths = list(Path("/kaggle/input").glob(pattern))
    if len(paths) != 1:
        raise RuntimeError("Expected a unique private input: " + pattern)
    return paths[0]


def digest(path):
    h = sha256()
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            h.update(block)
    return h.hexdigest()


def solver_inputs():
    index = find_one("**/gemma31-solver-inputs/gemma31-solver-bundle.json")
    if digest(index) != PLAN["solver_manifest_sha256"]:
        raise ValueError("Solver input bundle mismatch")
    root = index.parent
    manifest = json.loads(index.read_text())
    if manifest["lock_sha256"] != PLAN["membership_sha256"] or manifest["case_count"] != 31:
        raise ValueError("Frozen cohort mismatch")
    expected = {f"{row['instance_id']}.tgz" for row in CASES}
    actual = {path.name for path in (root / "snapshots").iterdir()}
    if expected != actual or set(manifest["files"]) != expected | {"tasks.jsonl"} | {
        f"wheels/{path.name}" for path in (root / "wheels").glob("*.whl")
    }:
        raise ValueError("Unexpected solver input artifacts")
    for name, checksum in manifest["files"].items():
        path = root / ("snapshots/" + name if name in expected else name)
        if digest(path) != checksum:
            raise ValueError("Solver input digest mismatch")
    tasks = [json.loads(line) for line in (root / "tasks.jsonl").read_text().splitlines()]
    for task, case in zip(tasks, CASES, strict=True):
        if set(task) != {"instance_id", "repo", "base_commit", "problem_statement"}:
            raise ValueError("Unexpected task fields")
        if (task["instance_id"], task["repo"]) != (case["instance_id"], case["repo"]):
            raise ValueError("Solver task does not match locked membership")
    return root, tasks


def unpack(content, folder):
    raw = base64.b64decode(content)
    with ZipFile(BytesIO(raw)) as archive:
        if archive.testzip() is not None:
            raise ValueError("Bad experiment submission archive")
        archive.extractall(folder)
    return sha256(raw).hexdigest()


async def solve(config, rows, directory):
    from swegemma.harness.agent_runner import run_agent_sandbox
    from swegemma.models import Task
    from swegemma.sandbox.subprocess import SubprocessManager

    sandbox = SubprocessManager(timeout_seconds=config["control"].harness.command_timeout_seconds or 300)
    results = []
    for index, data in enumerate(rows):
        instance = data["instance_id"]
        task = Task(**data)
        snapshot = config["control"].snapshots_dir / (instance + ".tgz")
        order = tuple(config) if (OFFSET + index) % 2 == 0 else tuple(reversed(config))
        for arm in order:
            start = time.monotonic()
            patch, error, trace = await run_agent_sandbox(sandbox, config[arm], task, snapshot)
            calls = [event for event in trace.entries if event.event_type == "tool_call"]
            retrieval = [
                event.tool_result for event in trace.entries
                if event.event_type == "tool_response" and event.tool_name == "run_skill_script"
            ]
            successes = sum(bool(re.search(r"EXISTING_TEST_MATCHES=[1-3]\b", result or "")) for result in retrieval)
            response = any(event.usage or event.model_version for event in trace.entries) or bool(calls)
            if error and ("exceeded" in error.lower() or "timed out" in error.lower() or "timeout" in error.lower()):
                category = "budget"
            elif error:
                category = "agent_error"
            else:
                category = None
            patch = patch or ""
            if patch:
                (directory / f"{instance}.{arm}.patch").write_text(patch)
            row = {
                "instance_id": instance, "arm": arm, "model_response": response,
                "error": category, "patch_sha256": sha256(patch.encode()).hexdigest(),
                "seconds": round(time.monotonic() - start, 2), "tool_calls": len(calls),
                "retrieval_calls": sum(event.tool_name == "run_skill_script" for event in calls),
                "retrieval_with_matches": successes,
            }
            results.append(row)
            print("GEMMA31_SOLVER_ROW=" + json.dumps(row, sort_keys=True), flush=True)
    return results


def run(work):
    import litellm
    import torch
    import yaml
    from adk_submission import VllmConfig, VllmServer, discover_adapters, validate_directory
    from adk_submission.discovery import discover_declared_models
    from google.adk.agents.context_cache_config import ContextCacheConfig
    from google.adk.apps._configs import EventsCompactionConfig
    from swegemma.config import ALLOWED_ADAPTER_EXTENSIONS, EvalConfig, build_submission_limits

    litellm.drop_params = True
    root, tasks = solver_inputs()
    control = work / "control"
    treatment = work / "retrieval"
    control_sha = unpack(ARM_ZIPS["control"], control)
    treatment_sha = unpack(ARM_ZIPS["retrieval"], treatment)
    if control_sha != PLAN["control_archive_sha256"]:
        raise ValueError("Control archive drift")
    limits, constraints = build_submission_limits()
    for folder in (control, treatment):
        validate_directory(folder, limits=limits)
        if discover_declared_models(folder) != {MODEL_NAME}:
            raise ValueError("Invalid model declaration")
        spec = yaml.safe_load((folder / "eval_config.yaml").read_text())
        spec = spec.get("evaluation", spec)
        if [spec[key] for key in ("max_time_minutes", "max_tool_calls", "max_turns")] != [5, 60, 80]:
            raise ValueError("Arm budget drift")
    adapters = discover_adapters(str(control), adapter_extensions=ALLOWED_ADAPTER_EXTENSIONS)
    model_path = Path(f"/kaggle/input/models/google/gemma-4/other/{MODEL_NAME}/2")
    count = torch.cuda.device_count()
    if not count or not model_path.is_dir() or adapters.adapters:
        raise ValueError("Pinned unadapted 31B weights and CUDA required")
    tp = 4 if count >= 4 else 2 if count >= 2 else 1
    server = VllmServer(VllmConfig(
        model=str(model_path), port=8000, host="127.0.0.1",
        tool_call_parser="gemma4", reasoning_parser="gemma4", max_model_len=32768,
        dtype="bfloat16" if torch.cuda.is_bf16_supported() else "auto",
        gpu_memory_utilization=0.90, enable_auto_tool_choice=True,
        enable_lora=False, max_loras=1, max_lora_rank=128, scheduler_reserve_full_isl=False,
        tensor_parallel_size=tp, startup_timeout=1200, extra_args=(),
    ), adapter_manifest=adapters)
    start = time.monotonic()
    try:
        server.start()
        startup_seconds = round(time.monotonic() - start, 2)
        print(f"GEMMA31_MODEL_READY={MODEL_NAME};TP={tp}", flush=True)
        config = EvalConfig(
            tasks_path=root / "tasks.jsonl", snapshots_dir=root / "snapshots",
            results_dir=work / "control-traces", submission_dir=control,
            models=server.create_model_registry(aliases=[MODEL_NAME], model_prefix="openai/",
                                                api_key=os.environ["LOCAL_API_KEY"]),
            sandbox="subprocess", timeout_seconds=int(spec.get("timeout_seconds", 300)),
            verification_timeout_seconds=int(spec.get("verification_timeout_seconds", 300)),
            max_time_minutes=5, max_tool_calls=60, max_turns=80,
            limits=limits, generation_constraints=constraints, adapter_manifest=adapters,
            context_cache_config=ContextCacheConfig(min_tokens=2048, ttl_seconds=1800, cache_intervals=10),
            events_compaction_config=EventsCompactionConfig(
                compaction_interval=15, overlap_size=2, token_threshold=14336, event_retention_size=5),
            graph_dir=str(root / "graphs"), embeddings_dir=str(root / "embeddings"),
            wheels_dir=root / "wheels", verbose=False, display_mode="quiet",
        )
        out = WORKING_DIR / f"private-pair-shard-{OFFSET}"
        out.mkdir()
        results = asyncio.run(solve({
            "control": config,
            "retrieval": replace(config, submission_dir=treatment, results_dir=work / "retrieval-traces"),
        }, tasks[OFFSET:STOP], out))
        (out / f"solver-results-{OFFSET}.json").write_text(json.dumps({
            "membership_sha256": PLAN["membership_sha256"], "offset": OFFSET, "stop": STOP,
            "control_archive_sha256": control_sha, "retrieval_archive_sha256": treatment_sha,
            "startup_seconds": startup_seconds, "model": MODEL_NAME, "rows": results,
        }, sort_keys=True))
    finally:
        server.stop()


if __name__ == "__main__":
    configure_environment()
    install_official_wheelhouse()
    with tempfile.TemporaryDirectory(prefix="gemma31-pair-") as temporary:
        run(Path(temporary))
