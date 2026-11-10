"""CPU official-compiler and packaged-script execution check for Solver V3-R.

No model calls, GPU, competition tasks, reference solutions or submissions.
The skill's *actual 31B call uptake* is NOT established by this check.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import zipfile

MODEL = "gemma-4-31b-it-qat-w4a16-ct"
NATIVE = (
    "run_command", "read_file", "edit_file", "write_file", "get_status",
    "submit_patch", "get_code_neighbors", "search_similar_code",
    "get_code_subgraph",
)


def verify(data: bytes) -> dict:
    from adk_submission import (
        validate_directory, compile_submission, ModelRegistry, ToolRegistry,
    )
    from google.adk.models.base_llm import BaseLlm
    from swegemma.config import build_submission_limits

    class NoInference(BaseLlm):
        async def generate_content_async(self, *args, **kwargs):
            raise AssertionError("GPU_MODEL_INFERENCE_FORBIDDEN")
            yield

    with TemporaryDirectory(prefix="solver-v3r-official-cpu-") as tmp:
        root = Path(tmp) / "submission"
        root.mkdir()
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            if archive.testzip() is not None:
                raise ValueError("bad candidate ZIP CRC")
            names = archive.namelist()
            if len(names) != len(set(names)) or set(names) != {
                "agent.yaml", "configs/sampling.yaml", "eval_config.yaml",
                "prompts/system.md", "skills/repair-witness/SKILL.md",
                "skills/repair-witness/scripts/witness.py",
            }:
                raise ValueError("unexpected ZIP structure")
            archive.extractall(root)

        limits, _ = build_submission_limits()
        validate_directory(root, limits=limits)
        models = ModelRegistry()
        models.register(MODEL, NoInference(model=MODEL))
        tools = ToolRegistry()
        for name in NATIVE:
            def unused(*args, **kwargs):
                raise AssertionError("NATIVE_TOOL_CALLED_DURING_COMPILE")
            tools.register(name, unused)
        agent = compile_submission(
            submission_dir=root, model_registry=models, tool_registry=tools,
        )
        if agent.model.model != MODEL:
            raise RuntimeError("unexpected compiled model")
        descriptions = [
            str(getattr(t, "name", None) or type(t).__name__)
            for t in agent.tools
        ]
        print("SOLVER_V3R_COMPILED_TOOLS="+json.dumps(
            descriptions, sort_keys=True), flush=True)
        print("SOLVER_V3R_ADK_COMPILER=PASS", flush=True)
        print("SOLVER_V3R_ADK_LIMITS=PASS", flush=True)

        # Execute exact code from the ZIP on a synthetic, exposure-free
        # workspace. A real process returning pass is not an LLM tool call.
        workspace = Path(tmp) / "fixture"
        workspace.mkdir()
        (workspace / "witness_target.py").write_text(
            "def test_synthetic():\n    assert 2 + 2 == 4\n",
            encoding="utf-8",
        )
        script = root / "skills/repair-witness/scripts/witness.py"
        process = subprocess.run(
            [
                sys.executable, str(script), "--workspace", str(workspace),
                "--phase", "after", "--target", "witness_target.py",
            ],
            capture_output=True, text=True, timeout=35,
        )
        if process.returncode:
            raise RuntimeError("packaged skill script failure: "
                               + process.stderr[-450:])
        output = json.loads(process.stdout.strip())
        if (output.get("status") != "pass" or
                output.get("comparison") != "baseline_unavailable" or
                output.get("independent_issue_resolved") is not False):
            raise RuntimeError("bad packaged skill real test evidence")
        print("SOLVER_V3R_PACKAGED_SCRIPT_REAL_PROCESS=PASS", flush=True)
        return {
            "zip_sha256": hashlib.sha256(data).hexdigest(),
            "model": MODEL,
            "compiled_tool_descriptions": descriptions,
            "sandbox_test_process": "pass",
            "actual_31b_tool_invocation": "NOT_TESTED_CPU_ONLY",
            "correctness_gain": "NOT_MEASURED",
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.zip.read_bytes())
    print("SOLVER_V3R_VERIFICATION_SUMMARY="+json.dumps(
        result, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
