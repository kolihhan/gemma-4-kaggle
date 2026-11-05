#!/usr/bin/env python3
"""CPU-only generation of untrained, matched B/C evidence-handoff schema candidates.

Generates temporary *unsubmitted* YAML directories only. No model loading,
Kaggle API, private task data, GPU, inference, training or benchmark evaluation.
Does not modify canonical submission/ or any frozen task reservation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from scripts.discriminating_evidence_preflight import ROOT
from scripts.render_untrained_31b_submission import payload, create_zip_bytes

MODEL = "gemma-4-31b-it-qat-w4a16-ct"
FROZEN_31B_ZIP_SHA256 = "42ac2e15e42118b51a2e8835ad5fc5e51cbbdfb472e65e3b8720b38b69738820"

ROOT_YAML = """agent_class: LlmAgent
name: evidence_experiment_root
model: gemma-4-31b-it-qat-w4a16-ct
description: Invoke the evidence_then_coder workflow exactly once.
instruction: !include prompts/wrapper.md
tools:
  - agent_tool:
      config_path: sub_agents/sequence.yaml
      skip_summarization: true
generate_content_config: !include configs/sampling.yaml
"""
SEQUENCE_YAML = """agent_class: SequentialAgent
name: evidence_then_coder
description: First inspect competing hypotheses, then make and verify a patch.
sub_agents:
  - config_path: sub_agents/evidence.yaml
  - config_path: sub_agents/coder.yaml
"""
EVIDENCE_YAML = """agent_class: LlmAgent
name: pre_edit_evidence
model: gemma-4-31b-it-qat-w4a16-ct
description: Read-only pre-edit discrimination between plausible causes.
instruction: !include prompts/evidence.md
output_key: evidence_packet
include_contents: none
tools:
  - read_file
  - run_command
  - get_status
  - get_code_neighbors
  - search_similar_code
generate_content_config: !include configs/sampling.yaml
"""
CODER_YAML = """agent_class: LlmAgent
name: evidence_conditioned_coder
model: gemma-4-31b-it-qat-w4a16-ct
description: Edit, verify and submit a narrow issue fix.
instruction: !include prompts/coder_stage.md
include_contents: none
tools:
  - run_command
  - read_file
  - edit_file
  - get_status
  - get_code_neighbors
  - search_similar_code
  - get_code_subgraph
  - submit_patch
generate_content_config: !include configs/sampling.yaml
"""
WRAPPER_PROMPT = """You are an orchestration controller, not the repair agent.
The issue is:
{problem_description}

Invoke the evidence_then_coder tool exactly once to run the pre-edit
evidence and patching workflow. Never edit, test, or submit directly.
Do not invent findings. Once the workflow returns, finish.
"""
EVIDENCE_PROMPT = """You are a bounded, pre-edit diagnostic investigator.
Task:
{problem_description}

Do not edit or write files. Do not call network or install packages.
Use small, targeted reads/commands under /workspace; any temporary scratch
file must be under /tmp. Do not inspect reference patches or gold tests.
If a command is used, it must be only read-only relative to /workspace.
Before ending, execute a clean working-tree check with a command equivalent to
'git -C /workspace diff --quiet && git -C /workspace diff --cached --quiet'.
If there is an unexpected diff, report it and do not hide that result.

Your final response, max 350 words, will be transferred as evidence_packet.
Report precisely:
1. Two competing possible root causes; label both hypotheses.
2. A small code/test location that supports each, or UNKNOWN.
3. One discriminating local command/assertion whose expected observations differ;
   write UNAVAILABLE when there is no valid safe test.
4. Actual observation, command exit status and which hypothesis it weakens.
5. What remains uncertain and how the leading hypothesis could be disproved.
Never fabricate test output or assert that merely running a test proves a fix.
"""
CODER_INSERTION = "Task:\n{problem_description}"
PACKET_BLIND = "[diagnostic packet withheld]"
PACKET_TRANSFER = "{evidence_packet}"


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_arm_pair(root: Path) -> tuple[dict[str, str], dict[str, str]]:
    _, frozen_31b = payload(root)
    frozen_hash = sha_bytes(create_zip_bytes(frozen_31b))
    if frozen_hash != FROZEN_31B_ZIP_SHA256:
        raise ValueError("frozen official 31B source bytes changed; refuse re-render")
    old_prompt = frozen_31b["prompts/coder.md"]
    if old_prompt.count(CODER_INSERTION) != 1:
        raise ValueError("frozen coder prompt task interpolation changed")
    candidates: list[dict[str, str]] = []
    for evidence_text in (PACKET_BLIND, PACKET_TRANSFER):
        candidate = dict(frozen_31b)
        candidate["agent.yaml"] = ROOT_YAML
        candidate["sub_agents/sequence.yaml"] = SEQUENCE_YAML
        candidate["sub_agents/evidence.yaml"] = EVIDENCE_YAML
        candidate["sub_agents/coder.yaml"] = CODER_YAML
        candidate["prompts/wrapper.md"] = WRAPPER_PROMPT
        candidate["prompts/evidence.md"] = EVIDENCE_PROMPT
        candidate["prompts/coder_stage.md"] = old_prompt.replace(
            CODER_INSERTION,
            CODER_INSERTION + "\n\nPre-edit observations (treat as fallible):\n"
            + evidence_text,
            1,
        )
        if set(candidate) != set(frozen_31b) | {
            "sub_agents/sequence.yaml",
            "sub_agents/evidence.yaml",
            "sub_agents/coder.yaml",
            "prompts/wrapper.md",
            "prompts/evidence.md",
            "prompts/coder_stage.md",
        }:
            raise ValueError("B/C file set drift")
        if any("adapter:" in contents for contents in candidate.values()):
            raise ValueError("LoRA/adapter disallowed")
        if any(MODEL not in candidate[path] for path in (
            "agent.yaml", "sub_agents/evidence.yaml", "sub_agents/coder.yaml",
        )):
            raise ValueError("31B declaration drift")
        candidates.append(candidate)
    b, c = candidates
    if sorted(k for k in b if b[k] != c[k]) != ["prompts/coder_stage.md"]:
        raise ValueError("B/C confounded: file difference exceeds packet interpolation")
    return b, c


def render_pair(root: Path, output: Path) -> dict:
    if output.exists() and any(output.iterdir()):
        raise ValueError("refuse overwriting nonempty rendered candidate directory")
    b, c = build_arm_pair(root)
    result: dict[str, dict] = {}
    for label, artifact in (("b", b), ("c", c)):
        for name, contents in artifact.items():
            path = output / label / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(contents.encode("utf-8"))
        result[label] = {
            "file_count": len(artifact),
            "candidate_sha256": sha_bytes(create_zip_bytes(artifact)),
            "root_model": MODEL,
        }
    return {
        "status": "SCHEMA_ONLY_NOT_EXECUTED",
        "scored_baseline_31b_zip_sha256": FROZEN_31B_ZIP_SHA256,
        "b": result["b"], "c": result["c"],
        "model_inference_executed": False,
        "training_or_submission": False,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, default=ROOT)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(render_pair(a.repo.resolve(), a.out.resolve()), sort_keys=True))


if __name__ == "__main__":
    main()
