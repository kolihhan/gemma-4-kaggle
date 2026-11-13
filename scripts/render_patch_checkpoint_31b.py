"""Render one private inference run with the scored Gemma 31B champion."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path
import re

from scripts.build_toolcap60_timeout_recovery import build, files_for_candidate
from scripts.render_earlyedit_v2_paired_31b import IMAGE
from scripts.render_v2_toolcap_31b_pilot import MODEL, MODEL_SOURCE, replace_one, replace_section

ROOT = Path(__file__).resolve().parents[1]
CHAMPION_SHA = "ff08c10240a38e151a2ea1d0478e999ee5d2f437d2dad5571d912cf12859922b"
TASKS = ("fastapi_11194", "rich_3935", "fastapi_14419", "rich_3470")
VERSION = "gemma-31b-patch-checkpoint-20261114"


def render(repo, source_zip, out, kernel_ref):
    if not re.fullmatch(r"kolihhan/gemma4-patch-checkpoint-[0-9]+", kernel_ref):
        raise ValueError("invalid kernel identity")
    if hashlib.sha256(build(source_zip)).hexdigest() != CHAMPION_SHA:
        raise ValueError("champion archive drift")
    files = files_for_candidate(source_zip)
    payload = base64.b64encode(json.dumps(files).encode()).decode()
    history_source = (repo / "scripts/candidate_history.py").read_text()
    observer_source = (repo / "kaggle/patch_checkpoint_runtime.py").read_text()
    runtime = (repo / "kaggle/verifier_baseline_runtime.py").read_text()
    runtime = replace_one(runtime, '"__SUBMISSION_PAYLOAD_B64__"', repr(payload), "champion")
    runtime = replace_one(
        runtime, 'MODEL_NAME = "gemma-4-e4b-it-qat-w4a16-ct"',
        f"MODEL_NAME = {MODEL!r}", "31B model",
    )
    runtime = replace_one(runtime, '"verifier_baseline_results.json"',
                          '"patch_checkpoint_summary.json"', "safe output")
    runtime = replace_section(runtime, "def load_holdout_ids() -> list[str]:",
                              "def run_maybe_async(", f"def load_holdout_ids():\n    return {TASKS!r}",
                              "frozen tasks")
    runtime = replace_one(runtime, "    import litellm",
                          "    from patch_checkpoint_runtime import checkpoint_evaluation\n    import litellm",
                          "observer")
    runtime = replace_one(runtime, "    if gpu_count < 1:",
                          "    if gpu_count != 4:", "expected L4x4")
    runtime = replace_one(runtime, "Kaggle baseline kernel has no visible GPU",
                          "checkpoint requires the official four-GPU shape", "GPU shape error")
    runtime = replace_section(
        runtime, "            try:\n                result = run_maybe_async(",
        "            records.append(record)",
        "            try:\n"
        "                record = run_maybe_async(checkpoint_evaluation(\n"
        "                    evaluator, tasks_by_id[task_id], index, len(holdout_ids)))\n"
        "            except Exception as exc:\n"
        "                record = {'instance_id': task_id, 'status': 'error',\n"
        "                          'error_type': type(exc).__name__}",
        "private checkpoint evaluation",
    )
    runtime = replace_one(runtime, 'output = {\n            "version": "verifier-lora-v0",',
                          f'output = {{\n            "version": {VERSION!r},\n            "champion_zip_sha256": {CHAMPION_SHA!r},',
                          "runtime identity")
    runtime = replace_one(runtime, '                "traceback": traceback.format_exc(),\n', "",
                          "remove raw traceback from result")
    runtime = replace_one(runtime, '                "error": str(exc),\n', "",
                          "remove raw error message from result")
    runtime = replace_one(runtime, "        write_failure(exc)\n        raise",
                          "        write_failure(exc)\n        raise RuntimeError(type(exc).__name__) from None",
                          "failure status")
    setup = (
        "import sys\n"
        "from pathlib import Path\n"
        "runtime_dir = Path('/kaggle/temp/gemma-patch-checkpoint-code')\n"
        "(runtime_dir / 'scripts').mkdir(parents=True, exist_ok=True)\n"
        "(runtime_dir / 'scripts/__init__.py').touch()\n"
        f"(runtime_dir / 'scripts/candidate_history.py').write_text({history_source!r})\n"
        f"(runtime_dir / 'patch_checkpoint_runtime.py').write_text({observer_source!r})\n"
        "sys.path.insert(0, str(runtime_dir))\n"
    )
    runtime = replace_one(runtime, "from __future__ import annotations\n",
                          "from __future__ import annotations\n" + setup, "inline private modules")
    for name, code in (("checkpoint.py", runtime), ("observer", observer_source), ("history", history_source)):
        compile(code, name, "exec")
    out.mkdir(parents=True, exist_ok=False)
    (out / "checkpoint.py").write_text(runtime)
    (out / "kernel-metadata.json").write_text(json.dumps({
        "id": kernel_ref, "title": kernel_ref.split("/", 1)[1], "code_file": "checkpoint.py",
        "language": "python", "kernel_type": "script", "is_private": True, "enable_gpu": True,
        "enable_tpu": False, "enable_internet": False, "machine_shape": "NvidiaL4", "docker_image": IMAGE,
        "competition_sources": ["gemma-4-developer-agent"],
        "dataset_sources": ["metric/gemma-4-developer-agent-wheelhouse"],
        "model_sources": [MODEL_SOURCE], "kernel_sources": [],
    }, indent=2) + "\n")
    print("GEMMA_PATCH_CHECKPOINT_RENDER=" + json.dumps({
        "version": VERSION, "tasks": TASKS, "champion_zip_sha256": CHAMPION_SHA,
        "runtime_sha256": hashlib.sha256(runtime.encode()).hexdigest(),
    }), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-zip", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--kernel-ref", required=True)
    args = parser.parse_args()
    render(ROOT, args.source_zip.read_bytes(), args.out, args.kernel_ref)
