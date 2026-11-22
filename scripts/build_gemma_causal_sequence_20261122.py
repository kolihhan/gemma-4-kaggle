"""A REAL declarative two-stage 31B SWE architecture, not a prompt add-on.

The first LlmAgent performs a bounded, tool-backed root-cause *localization*
comparison and places its evidence into session state. The second LlmAgent
alone may edit and submit. SequentialAgent guarantees scout runs before coder.
Its empirical effect on PASS is unknown until native Kaggle scoring.
"""
from __future__ import annotations

import hashlib
import io
import re
from pathlib import Path
import zipfile

from scripts.build_requirements_skill_candidate_20261121 import (
    CHAMPION_SHA256, MODEL, STAMP, EXPECTED,
)
from scripts.build_toolcap60_timeout_recovery import (
    build as build_scored_champion,
    files_for_candidate as scored_champion_files,
)

SCOUT_PROMPT = """You are the EVIDENCE SCOUT, not a code editor.

Task:
{problem_description}

Your ONLY objective is to identify the most likely production-code entry point
and the *closest competing explanation* before a coding agent changes files.

Spend at most 2 search tool calls + 1 targeted read. Use exact names/error
messages from the issue. Prefer run_command with short rg or a targeted
search_similar_code. If no symbol exists, mark the location UNKNOWN.
Do not edit, install packages, run a full test suite, or submit a patch.
Summarize in fewer than 130 words:
1. Observed production file and relevant function (ONLY if inspected).
2. Concrete evidence for hypothesis A and best alternative B.
3. The single smallest next action for the coder to discriminate A vs B.
4. Any missing external issue/spec information. Never invent requirements.
End your response after the summary, even if evidence remains incomplete.
"""

CODER_ADDENDUM = """

## Preceding evidence scout
{scout_evidence}

This scout evidence is non-authoritative, and may be wrong. Do not copy a
guess into a patch. Check actual code and tests, choose the source-based
hypothesis, implement the smallest behaviorally correct change, verify the
relevant behavior, then submit_patch. No repeated investigation if the scout
already found a usable entry point. Preserve remaining time for edit+test.
"""

ROOT = """agent_class: SequentialAgent
name: evidence_and_repair
description: Two-stage candidate: compare root-cause locations, then execute.
sub_agents:
  - config_path: sub_agents/scout.yaml
  - config_path: sub_agents/coder.yaml
"""

SCOUT = f"""agent_class: LlmAgent
name: location_scout
description: Bounded source localization and competing hypotheses.
model: {MODEL}
instruction: !include prompts/scout.md
tools:
  - run_command
  - read_file
  - search_similar_code
  - get_code_neighbors
output_key: scout_evidence
generate_content_config: !include configs/sampling.yaml
"""


def build_files(control: dict[str, str]) -> dict[str, str]:
    if set(control) != EXPECTED:
        raise ValueError("wrong champion source entries")
    old_yaml = control["agent.yaml"]
    if old_yaml.count("model: " + MODEL) != 1:
        raise ValueError("not exact 31B source model")
    if old_yaml.count("tools:") != 1 or "submit_patch" not in old_yaml:
        raise ValueError("unexpected scored coder tools")
    budget = control["eval_config.yaml"]
    for exact in ("max_time_minutes: 5", "max_tool_calls: 60",
                  "max_turns: 80"):
        if budget.count(exact) != 1:
            raise ValueError("champion budget contract drift")
    # Preserve original coder agent byte-for-byte except relocating its
    # instruction to a standalone file that appends scout session evidence.
    old_prompt = control["prompts/system.md"]
    files = dict(control)
    files["agent.yaml"] = ROOT
    files["sub_agents/scout.yaml"] = SCOUT
    files["sub_agents/coder.yaml"] = re.sub(r"(?m)^name:\\s+\\S+\\s*$", "name: swe_coder", old_yaml, count=1)
    files["prompts/scout.md"] = SCOUT_PROMPT
    files["prompts/system.md"] = old_prompt.rstrip() + CODER_ADDENDUM
    if "scout_evidence" not in files["prompts/system.md"]:
        raise AssertionError("scout state not linked to coder")
    # Truly two distinct agents, one base variant.
    if "name: swe_coder" not in files["sub_agents/coder.yaml"]:\n        raise ValueError("scored coder name not recognized")\n    if files["sub_agents/coder.yaml"].count("model: " + MODEL) != 1:
        raise ValueError("coder model mismatch")
    if files["eval_config.yaml"] != budget or files["configs/sampling.yaml"] != control["configs/sampling.yaml"]:
        raise AssertionError("changed budget or sampling")
    return files


def make_zip(source_zip: bytes) -> tuple[bytes, dict]:
    champ = build_scored_champion(source_zip)
    digest = hashlib.sha256(champ).hexdigest()
    if digest != CHAMPION_SHA256:
        raise ValueError("scored 0.18 champion hash mismatch; do not proceed")
    files = build_files(scored_champion_files(source_zip))
    sink = io.BytesIO()
    with zipfile.ZipFile(sink, "w", zipfile.ZIP_DEFLATED) as z:
        for path, body in sorted(files.items()):
            if path.startswith("/") or ".." in Path(path).parts:
                raise ValueError("unsafe archive path")
            info = zipfile.ZipInfo(path, date_time=STAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            z.writestr(info, body.encode("utf-8"))
    output = sink.getvalue()
    with zipfile.ZipFile(io.BytesIO(output)) as z:
        if z.testzip() is not None or set(z.namelist()) != set(files):
            raise ValueError("corrupt candidate")
    return output, {
        "source_scored_champion_sha256": CHAMPION_SHA256,
        "candidate_sha256": hashlib.sha256(output).hexdigest(),
        "model": MODEL,
        "topology": "SequentialAgent(scout, coder)",
        "candidate_files": len(files),
        "max_tool_calls": 60,
        "max_task_minutes": 5,
        "scored_pass": None,
    }
