"""Single-variable multi-entrypoint repair treatment, derived from scored Champion.

The only submission-bundle delta is prompts/system.md.
No train/inference, no tools/config/model changes, no Kaggle submit here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

from scripts.build_behavioral_probe_timeout_safe_20261123 import (
    CHAMPION_SHA256, EXPECTED_FILES, MODEL, _source_files, _pack,
)

SCOPE_GUIDANCE = """
## Explicitly named code-surface coverage (conditional)
Only when the issue explicitly names two or more affected entry points,
callers, interfaces or code paths, check whether the proposed fix addresses
each named behavior. During normal code reading, locate the shared source
of the behavior first; do not assume that changing one visible caller is
sufficient for another caller, or that all callers need separate patches.
Make at most one additional focused source read when it resolves which
path implements an explicitly stated requirement. Do not infer requirements
from inaccessible links, invent missing behavior or run a broad test suite.
For one-path issues, do not add planning, tools or tests for this instruction.
Before submit_patch, briefly check that each explicitly named behavior is
covered by the actual diff. Prefer a correct minimal patch over extensive
exploration, and preserve the existing time/tool/submission limits.
"""

def eligible_source_paths(ids: list[str]) -> list[str]:
    if not isinstance(ids, list) or len(ids) != 17 or len(set(ids)) != 17:
        raise ValueError("expected exactly 17 frozen distinct public-dev IDs")
    if any(not isinstance(i,str) or not re.fullmatch(r"(fastapi|rich)_[0-9]+",i)
           for i in ids):
        raise ValueError("unexpected public-dev task identifier")
    return sorted(ids)

def files_for_pair(source_zip: bytes):
    control=_source_files(source_zip)  # SHA checked against scored 0.18 champion
    if set(control) != EXPECTED_FILES:
        raise ValueError("Champion file membership drift")
    for phrase in ("run_command","read_file","edit_file","submit_patch"):
        if "  - "+phrase not in control["agent.yaml"]:
            raise ValueError("Champion native tool missing: "+phrase)
    prompt=control["prompts/system.md"]
    if "Explicitly named code-surface coverage (conditional)" in prompt:
        raise ValueError("treatment already present in Champion")
    if any(term not in control["eval_config.yaml"] for term in
           ("max_time_minutes: 5","max_tool_calls: 60","max_turns: 80")):
        raise ValueError("Scored Champion budget drift")
    candidate=dict(control)
    candidate["prompts/system.md"]=prompt.rstrip()+"\n\n"+SCOPE_GUIDANCE.strip()+"\n"
    if {k for k in control if candidate[k]!=control[k]} != {"prompts/system.md"}:
        raise AssertionError("unexpected prompt-only intervention drift")
    return control,candidate

def build_pair(source_zip: bytes):
    control,candidate=files_for_pair(source_zip)
    control_zip=_pack(control)
    treatment_zip=_pack(candidate)
    if hashlib.sha256(control_zip).hexdigest() != CHAMPION_SHA256:
        raise RuntimeError("reconstructed Champion byte mismatch")
    return control_zip,treatment_zip

def summary(source_zip: bytes):
    c,t=build_pair(source_zip)
    return {
        "frozen_control_sha256":hashlib.sha256(c).hexdigest(),
        "candidate_sha256":hashlib.sha256(t).hexdigest(),
        "only_changed":"prompts/system.md",
        "model":MODEL,
        "minutes_per_issue":5,"max_tool_calls":60,"max_turns":80,
        "new_training":False,"submission":False,
        "accuracy_unproven":True
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--source",required=True,type=Path)
    parser.add_argument("--output",required=True,type=Path)
    args=parser.parse_args()
    source=args.source.read_bytes()
    control,candidate=build_pair(source)
    if args.output.exists():raise FileExistsError("no overwriting")
    args.output.mkdir(parents=True)
    (args.output/"control.zip").write_bytes(control)
    (args.output/"candidate.zip").write_bytes(candidate)
    (args.output/"candidate-manifest.json").write_text(
        json.dumps(summary(source),indent=2,sort_keys=True)+"\n")
    print("MULTISURFACE_CHAMPION_CPU_BUILD="+json.dumps(summary(source),sort_keys=True))
if __name__=="__main__":
    main()
