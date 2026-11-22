"""Gemma 31B mandatory evidence-channel candidate, sourced from scored 0.18.

Replace unrestricted command/search native tools with the Skill's bounded
locate/test/diff/status. Preserve 31B model, sampling and exact 5-minute,
60-tool-call, 80-turn task cap. No classifier/adapter/training changes.
"""
from __future__ import annotations
import hashlib
import io
from pathlib import Path
import zipfile
from scripts.build_toolcap60_timeout_recovery import (
    build as build_champion,files_for_candidate as control_files,STAMP,
)
SCORER_CHAMPION_SHA="ff08c10240a38e151a2ea1d0478e999ee5d2f437d2dad5571d912cf12859922b"
MODEL="gemma-4-31b-it-qat-w4a16-ct"
ROOT=Path(__file__).resolve().parents[1]
SKILL_DIR=ROOT/"experiments/mandatory-evidence-channel-20261122"
EXPECTED={"agent.yaml","eval_config.yaml","configs/sampling.yaml","prompts/system.md"}
AGENT=f"""agent_class: LlmAgent
name: swe_coder
model: {MODEL}
description: Coder with a bounded mandatory source and test evidence channel.
instruction: !include prompts/system.md
tools:
  - read_file
  - edit_file
  - get_status
  - submit_patch
skills:
  - skills/evidence-channel
generate_content_config: !include configs/sampling.yaml
"""
PROMPT="""You are a coding agent resolving one repository issue in /workspace.
Make the smallest behaviorally correct source change and call submit_patch.

Your tools are intentionally constrained: NO run_command, graph tools,
search_similar_code, or write_file. Use evidence-channel through the native
run_skill_script tool for locate, focused test, diff and status. Call load_skill
if the Skill instructions are not yet in context.

Task:
{problem_description}

Method: From exact issue requirements, choose up to two source-specific
identifiers and use the evidence-channel locate action. Inspect the best
grounded source and caller/test with native read_file before deciding the
cause. A zero-hit result is not evidence the code does not exist. Make a
narrow native edit_file replacement, not a whole-file rewrite. Run one
focused applicable Python test via evidence-channel; interpret nonzero or
timeout as failure. If test execution is unavailable, be explicit about the
missing evidence rather than pretending it passed. Revise on actual feedback
at most once. Use evidence-channel diff and native get_status when needed,
and finish by calling submit_patch to materialize the intended source diff.

Shared budget: 5 minutes / 60 tool calls / 80 turns. No network, pip
installs, long test suites, aimless searches, or empty/text-only patches.
"""

def files_for_candidate(source_zip:bytes)->dict[str,str]:
    champion=build_champion(source_zip)
    if hashlib.sha256(champion).hexdigest()!=SCORER_CHAMPION_SHA:
        raise ValueError("not exact scored 0.18 Champion")
    base=control_files(source_zip)
    if set(base)!=EXPECTED:raise ValueError("base file members changed")
    if base["agent.yaml"].count("model: "+MODEL)!=1:
        raise ValueError("root model changed")
    spec=base["eval_config.yaml"]
    if any(spec.count(x)!=1 for x in
            ("max_time_minutes: 5","max_tool_calls: 60","max_turns: 80")):
        raise ValueError("scored budget changed")
    for tool in ("run_command","read_file","edit_file","search_similar_code",
                 "get_code_subgraph","submit_patch"):
        if tool not in base["agent.yaml"]:
            raise ValueError("unexpected baseline agent tools")
    files=dict(base)
    files["agent.yaml"]=AGENT
    files["prompts/system.md"]=PROMPT
    files["skills/evidence-channel/SKILL.md"]=(SKILL_DIR/"SKILL.md").read_text()
    files["skills/evidence-channel/scripts/evidence.py"]=(SKILL_DIR/"evidence.py").read_text()
    compile(files["skills/evidence-channel/scripts/evidence.py"],
            "skills/evidence-channel/scripts/evidence.py","exec")
    if any(files[k]!=base[k] for k in ("eval_config.yaml","configs/sampling.yaml")):
        raise AssertionError("sampling or budget changed")
    if "run_command" in files["agent.yaml"] or "search_similar_code" in files["agent.yaml"]:
        raise AssertionError("unrestricted shell or graph still accessible")
    if files["agent.yaml"].count("  - submit_patch")!=1:
        raise ValueError("cannot submit patch")
    return files

def build(source_zip:bytes)->bytes:
    files=files_for_candidate(source_zip)
    out=io.BytesIO()
    with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED) as z:
        for name,source in sorted(files.items()):
            if name.startswith("/") or ".." in Path(name).parts:
                raise ValueError("unsafe path")
            item=zipfile.ZipInfo(name,date_time=STAMP)
            item.compress_type=zipfile.ZIP_DEFLATED
            item.external_attr=0o100644<<16
            z.writestr(item,source.encode("utf-8"))
    data=out.getvalue()
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        if z.testzip() is not None or set(z.namelist())!=set(files):
            raise RuntimeError("invalid evidence-channel archive")
    return data
