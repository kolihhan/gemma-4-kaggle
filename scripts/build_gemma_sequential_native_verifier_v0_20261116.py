#!/usr/bin/env python3
"""Build an OFFICIAL-SUPPORTED SequentialAgent from SHA-pinned 31B V2 source.

Major mechanism change: mandatory SECOND LlmAgent stage is the only agent with
submit_patch; unlike uninvoked optional Skill, it must run in sequence after
coder, and inspects the persistent sandbox diff/tests using native run_command.

This builder executes no tasks and makes no Kaggle submissions. Frozen first
stage uses unchanged base prompt, same sampling and graph/narrow edit tools.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile

from scripts.prepare_public_budgetfit_v2 import (
    EXPECTED_ZIP_SHA256,
    validate_source_zip,
)

MODEL = "gemma-4-31b-it-qat-w4a16-ct"
VERSION = "gemma-sequential-native-verify-20261116-v0"
CODER_EXTRA = """
STAGED WORKFLOW OVERRIDE — this is stage 1 of 2. You are a coder only.
You have no submit_patch tool. Implement the narrowest patch, inspect the diff,
and do only directly necessary lightweight diagnosis. Do NOT spend all calls:
aim to leave at least 8 tool calls and 90 seconds for mandatory stage 2.
When the code change is ready (even if verification is incomplete), return a
short factual handoff identifying changed files, intended behavior, and the
most relevant exact test candidate. Do not run broad test suites.
The subsequent mandatory verifier stage independently checks the diff and
issues submit_patch. Do not attempt to submit from this stage.
"""
VERIFY_INSTRUCTION = """
You are the mandatory SECOND and FINAL stage of a legal Kaggle coding agent,
after the coder has already edited /workspace. The task: {problem_description}

This is not the hidden grader. You cannot see reference patches/test_patch or
hidden answers. You must use ONLY allowed built-in tools. The coder's changes
are in the persistent /workspace and may be incomplete.

1. FIRST invoke run_command to inspect git diff --name-only and git diff --check.
   If no diff exists, explain and call submit_patch (do not create fake changes).
2. Read the narrow changed hunks / nearby tests; select ONE relevant existing
   targeted test by observed code and actual issue behavior. Execute it with a
   bounded command, not a broad suite or dependency installer. Prefer
   python -m pytest -q -x path/to/test_file.py -k focused_pattern or
   python -m pytest -q -x path/to/test_file.py. Do not invent test paths.
3. If the test FAILS for a clear patch-related reason, make one small,
   evidence-based repair with edit_file. Re-run the same test ONCE if budget
   allows. If no relevant test is runnable, state TEST_UNAVAILABLE; checking
   syntax or git diff --check is not a semantic correctness guarantee.
4. Do not overwrite unrelated code, edit harness scaffolding, or use the
   network. Respect remaining tool/time budget.
5. ALWAYS call submit_patch once as the final action, even if a targeted test
   was unavailable. Make no claim the hidden grader was passed.

The purpose is to ensure the verifier stage actually happens and calls a
model-visible native executable check before submitting a patch. Truthful
negative test outcomes may be reported; do not hide or relabel failures.
"""


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_payload(source_zip: bytes) -> dict[str, str]:
    if digest(source_zip) != EXPECTED_ZIP_SHA256:
        raise ValueError("pinned Budget-Fit V2 source SHA drift")
    src = validate_source_zip(source_zip)
    if src["agent.yaml"] != (
        "name: swe_agent\n"
        f"model: {MODEL}\n"
        "instruction: !include prompts/system.md\n"
        "tools:\n"
        "  - run_command\n"
        "  - read_file\n"
        "  - edit_file\n"
        "  - write_file\n"
        "  - get_status\n"
        "  - submit_patch\n"
        "  - get_code_neighbors\n"
        "  - search_similar_code\n"
        "  - get_code_subgraph\n"
        "generate_content_config: !include configs/sampling.yaml\n"
    ):
        raise ValueError("exact original agent identity/tools/order drift")

    cfg = src["eval_config.yaml"]
    if cfg.count("max_time_minutes: 8") != 1:
        raise ValueError("original reference budget drift")
    ctrl = dict(src)
    ctrl["eval_config.yaml"] = cfg.replace(
        "max_time_minutes: 8", "max_time_minutes: 5", 1
    )
    ctrl["agent.yaml"] = (
        "agent_class: SequentialAgent\n"
        "name: coder_then_native_verifier\n"
        "description: Coder edits; mandatory independent verifier checks and submits.\n"
        "sub_agents:\n"
        "  - config_path: sub_agents/coder.yaml\n"
        "  - config_path: sub_agents/verifier.yaml\n"
    )
    # All !include paths refer to SAME directory. No ../ or out-of-root paths.
    coder = src["agent.yaml"]
    coder = coder.replace(
        "name: swe_agent\n", "agent_class: LlmAgent\nname: staged_coder\n", 1
    )
    coder = coder.replace(
        "instruction: !include prompts/system.md",
        "instruction: !include coder_prompt.md", 1
    )
    coder = coder.replace(
        "generate_content_config: !include configs/sampling.yaml",
        "generate_content_config: !include sampling.yaml", 1
    )
    if coder.count("  - submit_patch\n") != 1:
        raise ValueError("cannot remove coder's submit tool")
    coder = coder.replace("  - submit_patch\n", "", 1)
    ctrl["sub_agents/coder.yaml"] = coder
    ctrl["sub_agents/coder_prompt.md"] = (
        src["prompts/system.md"].rstrip() + "\n\n" + CODER_EXTRA.strip() + "\n"
    )
    ctrl["sub_agents/sampling.yaml"] = src["configs/sampling.yaml"]
    ctrl["sub_agents/verifier.yaml"] = (
        "agent_class: LlmAgent\n"
        "name: mandatory_native_verifier\n"
        "model: " + MODEL + "\n"
        "description: Must run after coder and use native run_command evidence.\n"
        "instruction: !include verifier_prompt.md\n"
        "tools:\n"
        "  - run_command\n"
        "  - read_file\n"
        "  - edit_file\n"
        "  - get_status\n"
        "  - submit_patch\n"
        "generate_content_config: !include sampling.yaml\n"
    )
    ctrl["sub_agents/verifier_prompt.md"] = VERIFY_INSTRUCTION.strip() + "\n"

    if set(ctrl) != {
        "agent.yaml", "eval_config.yaml", "prompts/system.md",
        "configs/sampling.yaml", "sub_agents/coder.yaml",
        "sub_agents/coder_prompt.md", "sub_agents/sampling.yaml",
        "sub_agents/verifier.yaml", "sub_agents/verifier_prompt.md",
    }:
        raise ValueError("unexpected candidate member list")
    if ctrl["prompts/system.md"] != src["prompts/system.md"]:
        raise ValueError("frozen competitor prompt mutated")
    if ctrl["configs/sampling.yaml"] != src["configs/sampling.yaml"]:
        raise ValueError("frozen competitor sampling mutated")
    if ctrl["sub_agents/sampling.yaml"] != src["configs/sampling.yaml"]:
        raise ValueError("subagent sampling drift")
    if ctrl["sub_agents/coder.yaml"].count("  - submit_patch\n"):
        raise ValueError("coder can preempt reviewer")
    if ctrl["sub_agents/verifier.yaml"].count("  - submit_patch\n") != 1:
        raise ValueError("reviewer cannot submit")
    if ctrl["agent.yaml"].count("config_path:") != 2:
        raise ValueError("mandatory stage count changed")
    if len(re.findall(r"(?m)^model:", "\n".join(ctrl.values()))) != 2:
        raise ValueError("invalid two-subagent single-model contract")
    if not all(re.search(r"(?m)^model: " + MODEL + "$", ctrl[n]) for n in
               ("sub_agents/coder.yaml", "sub_agents/verifier.yaml")):
        raise ValueError("subagents do not share pinned 31B")
    if "max_tool_calls: 28" not in ctrl["eval_config.yaml"]:
        raise ValueError("shared scorer tool budget drift")
    return ctrl


def build_zip(source_zip: bytes) -> bytes:
    files = build_payload(source_zip)
    bio = io.BytesIO()
    with zipfile.ZipFile(bio, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for name, body in sorted(files.items()):
            if name.startswith("/") or ".." in Path(name).parts:
                raise ValueError("unsafe archive path")
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, body.encode("utf-8"))
    return bio.getvalue()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-zip", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    source = args.source_zip.read_bytes()
    candidate = build_zip(source)
    if args.out.exists():
        raise FileExistsError("candidate exists; refuse overwrite")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(candidate)
    print("GEMMA_PRO_SEQUENTIAL_31B_NATIVE_REVIEW_CANDIDATE=" + json.dumps({
        "source_sha256": digest(source),
        "candidate_sha256": digest(candidate),
        "base_model": MODEL,
        "first_stage_has_submit": False,
        "mandatory_second_stage_has_submit": True,
        "stage_count": 2,
        "frozen_original_sampling": True,
        "no_custom_host_tools": True,
        "no_training": True,
        "no_GPU_in_build": True,
        "no_official_submission": True,
        "quality_validated": False,
    }, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
