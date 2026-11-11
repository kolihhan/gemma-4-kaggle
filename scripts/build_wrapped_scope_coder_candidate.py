"""Isolated LlmAgent-root wrapper for mandatory scope->coder ActionTool.

The root is an LlmAgent, needed for the competition App's default event
compaction. Only its nested workflow AgentTool can edit files. The root may
choose not to call the AgentTool; tool uptake must be measured with real 31B.
This is NOT a quality-proven submission candidate.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path

from scripts import build_two_stage_scope_coder_candidate as staged

ROOT_YAML = """agent_class: LlmAgent
name: repair_orchestrator
model: gemma-4-31b-it-qat-w4a16-ct
description: Delegate one issue repair to the only permitted staged workflow.
instruction: !include prompts/orchestrator.md
tools:
  - agent_tool:
      config_path: workflow.yaml
      skip_summarization: true
generate_content_config:
  temperature: 0.2
  top_p: 0.95
  max_output_tokens: 768
  thinking_config:
    include_thoughts: true
    thinking_budget: 256
"""

ROOT_PROMPT = """You are the top-level coordinator for an offline SWE repair.
You have exactly ONE action tool: mandatory_scope_then_patch. It internally
runs a read-only source/requirement investigator, followed by the only writer.

For every nontrivial issue request, call mandatory_scope_then_patch exactly
once with the user's complete issue request. The nested workflow owns source
edits, focused tests and submit_patch. You CANNOT directly read/write files
or submit. Do not answer as if you made a code change without a tool result.

The nested scope notes are evidence, not a hidden correctness oracle. After
the workflow completes, briefly report whether a materialized patch was
submitted or whether the outcome is unknown. No more tool calls.
"""


def files(source_zip: bytes) -> dict[str, str]:
    entries=staged.files(source_zip)
    # Reuse the identical strong inner stage contract. The sole structural
    # difference is the root LlmAgent and its one AgentTool entrypoint.
    workflow=entries["agent.yaml"]
    if not workflow.startswith("agent_class: SequentialAgent\n"):
        raise ValueError("missing two-stage inner workflow")
    if "sub_agents/scope.yaml" not in workflow or "sub_agents/coder.yaml" not in workflow:
        raise ValueError("inner stage ordering drift")
    entries["workflow.yaml"]=workflow
    entries["agent.yaml"]=ROOT_YAML
    entries["prompts/orchestrator.md"]=ROOT_PROMPT
    return entries


def build(source_zip: bytes) -> bytes:
    return staged.archive(files(source_zip)) if hasattr(staged,"archive") else archive(files(source_zip))


def archive(entries: dict[str, str]) -> bytes:
    import io
    import zipfile
    out=io.BytesIO()
    with zipfile.ZipFile(out,"w") as z:
        for filename,data in sorted(entries.items()):
            info=zipfile.ZipInfo(filename,date_time=staged.STAMP)
            info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=0o100644<<16
            z.writestr(info,data.encode("utf-8"))
    result=out.getvalue()
    with zipfile.ZipFile(io.BytesIO(result)) as z:
        if z.testzip() is not None or set(z.namelist())!=set(entries):
            raise ValueError("wrapped staged ZIP corruption")
    return result


def main() -> None:
    args=argparse.ArgumentParser()
    args.add_argument("--source-zip",type=Path,required=True)
    args.add_argument("--out",type=Path,required=True)
    options=args.parse_args()
    if options.out.exists():
        raise FileExistsError("will not overwrite candidate")
    blob=build(options.source_zip.read_bytes())
    options.out.parent.mkdir(parents=True,exist_ok=True)
    options.out.write_bytes(blob)
    print("WRAPPED_SCOPE_CODER_ZIP_SHA256="+hashlib.sha256(blob).hexdigest())
    print("WRAPPED_SCOPE_CODER_NO_GPU_NO_COMPETITION_SUBMISSION=TRUE")


if __name__=="__main__":
    main()
