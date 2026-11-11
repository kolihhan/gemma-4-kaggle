"""Isolated CPU-only two-stage SWE architecture, not a submission.

Unlike the failed optional Contract & Impact Skill, this is a root
SequentialAgent: the read-only investigator runs before the only patch writer.
No new tools/weights/training, no hidden patch access. Source V2 must be pinned.
Root SequentialAgent has a historical compaction/continuation concern:
the official harness probe must verify lifecycle before ANY GPU run.
"""
from __future__ import annotations
import argparse
import hashlib
import io
from pathlib import Path
import zipfile

from scripts.prepare_public_budgetfit_v2 import validate_source_zip

MODEL = "gemma-4-31b-it-qat-w4a16-ct"
STAMP = (2026, 11, 11, 0, 0, 0)
BASE = {"agent.yaml", "prompts/system.md", "configs/sampling.yaml", "eval_config.yaml"}
READ_ONLY_TOOLS = (
    "read_file", "get_status", "get_code_neighbors",
    "search_similar_code", "get_code_subgraph",
)
WRITER_TOOLS = (
    "run_command", "read_file", "edit_file", "write_file", "get_status",
    "submit_patch", "get_code_neighbors", "search_similar_code",
    "get_code_subgraph",
)

ROOT_YAML = """agent_class: SequentialAgent
name: mandatory_scope_then_patch
description: Always inspect available evidence before letting the coder change files.
sub_agents:
  - config_path: sub_agents/scope.yaml
  - config_path: sub_agents/coder.yaml
"""

SCOPE_PROMPT = """You are the READ-ONLY investigation phase of a SWE repair.
This phase always runs BEFORE the only source writer. You cannot edit or submit.

Use the issue in the user message, read at most the relevant code/tests,
and state only what you could observe. An issue title is not full requirements.
Avoid broad searches and do not run shell commands.

Finish with a concise factual packet, using these labels:
EXPLICIT_BEHAVIOR: verbatim or close paraphrase of requirements actually present
REPOSITORY_FACTS: file/symbol evidence observed via read-only tools, if any
CANDIDATE_AFFECTED_SURFACES: evidence-backed likely edit/caller paths (UNKNOWN is fine)
UNRESOLVED_AMBIGUITIES: missing specs, competing interpretations, inaccessible evidence
FIRST_DISCRIMINATING_ACTION: most useful next read/patch/test for the coder

Do not claim tests ran, edits happened, hidden rules, or a valid solution.
Do not spend the full time budget investigating. Stop promptly after enough evidence.
"""

CODER_PROMPT = """You are the ONLY writer and submitter for the SWE task.
The preceding scope phase is guaranteed to have executed, but its conclusions
can be incomplete or wrong; recheck critical observations before using them.

Read this UNVERIFIED earlier investigation packet:
{scope_packet}

Treat it as a starting hypothesis, not an oracle. Recover missing requirements
from actual callers/tests when available. Implement the smallest complete
behavioral fix, inspect actual git diff, run one or two focused relevant tests
as time permits, and call submit_patch on the useful materialized change.

You own all editing, shell commands and submission. Avoid endlessly browsing,
fabricating test results, editing reference test patches, or trusting a
self-generated passing test as proof of hidden issue correctness. If the scope
packet lacks relevant evidence, correct it using native repository tools.
The entire investigation+coding sequence shares a 5 minute task cap.
"""


def yaml_agent(name: str, prompt: str, tools: tuple[str, ...], *,
               output_key: str | None = None, scope: bool = False) -> str:
    result = (
        "agent_class: LlmAgent\n"
        f"name: {name}\n"
        f"model: {MODEL}\n"
        "description: A stage in a sequential SWE repair workflow.\n"
        f"instruction: !include ../prompts/{prompt}\n"
        "tools:\n" +
        "".join(f"  - {tool}\n" for tool in tools)
    )
    if output_key:
        result += f"output_key: {output_key}\n"
    if scope:
        result += (
            "generate_content_config:\n"
            "  temperature: 0.2\n"
            "  top_p: 0.95\n"
            "  max_output_tokens: 1024\n"
            "  thinking_config:\n"
            "    include_thoughts: true\n"
            "    thinking_budget: 768\n"
        )
    else:
        result += "generate_content_config: !include ../configs/sampling.yaml\n"
    return result


def files(source: bytes) -> dict[str, str]:
    baseline = validate_source_zip(source)
    if set(baseline) != BASE:
        raise ValueError("unexpected V2 base payload")
    original = baseline["agent.yaml"]
    # The official ADK config defaults to LlmAgent when agent_class is absent.
    # The external V2 root uses that default; explicit declarations are optional.
    classes = [line.strip() for line in original.splitlines()
               if line.strip().startswith("agent_class:")]
    if (original.count("model: "+MODEL) != 1 or
        classes not in ([], ["agent_class: LlmAgent"]) or
        "skills:" in original or "agent_tool:" in original or
        "sub_agents:" in original):
        raise ValueError("unexpected V2 root agent")
    for tool in WRITER_TOOLS:
        if original.count(f"  - {tool}\n") != 1:
            raise ValueError("missing native writer tool: "+tool)
    config = baseline["eval_config.yaml"]
    if (config.count("max_time_minutes: 8") != 1 or
        config.count("max_tool_calls: 28") != 1 or
        config.count("max_turns: 80") != 1):
        raise ValueError("unrecognized V2 budget")
    packed = dict(baseline)
    packed["agent.yaml"] = ROOT_YAML
    packed["sub_agents/scope.yaml"] = yaml_agent(
        "read_only_scope", "scope.md", READ_ONLY_TOOLS,
        output_key="scope_packet", scope=True)
    packed["sub_agents/coder.yaml"] = yaml_agent(
        "sole_patch_writer", "coder.md", WRITER_TOOLS)
    packed["prompts/scope.md"] = SCOPE_PROMPT
    packed["prompts/coder.md"] = CODER_PROMPT
    # Explicit single shared limit; no extra tool/LLM budget added.
    packed["eval_config.yaml"] = config.replace(
        "max_time_minutes: 8", "max_time_minutes: 5", 1)
    del packed["prompts/system.md"]
    return packed


def build(source: bytes) -> bytes:
    entries = files(source)
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as z:
        for path, data in sorted(entries.items()):
            info = zipfile.ZipInfo(path, date_time=STAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            z.writestr(info, data.encode("utf-8"))
    result = out.getvalue()
    with zipfile.ZipFile(io.BytesIO(result)) as z:
        if z.testzip() is not None or set(z.namelist()) != set(entries):
            raise ValueError("invalid staged solver ZIP")
    return result


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--source-zip",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    if args.out.exists():
        raise FileExistsError("refuse to overwrite staged candidate")
    result=build(args.source_zip.read_bytes())
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_bytes(result)
    print("TWO_STAGE_SCOPE_CODER_ZIP_SHA256="+hashlib.sha256(result).hexdigest())
    print("TWO_STAGE_SCOPE_CODER_NO_INFERENCE_NO_KAGGLE_SUBMISSION=TRUE")


if __name__ == "__main__":
    main()
