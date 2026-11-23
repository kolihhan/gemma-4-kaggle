"""One-variable Gemma 31B edit-argument grammar trial, built from frozen Champion.

Only prompts/system.md differs between arms. This builder is not a grader.
No public-dev issue text or reference solution is used.
"""
from __future__ import annotations
import hashlib
import io
import json
from pathlib import Path
import zipfile

from scripts.build_behavioral_probe_timeout_safe_20261123 import (
    CHAMPION_SHA256, EXPECTED_FILES, MODEL, _source_files, _pack,
    timeout_forecast,
)

# One mechanism only: valid edit_file arguments. No new tools, validation
# stages, extra tests, edit retries or submit timing policy.
EDIT_GRAMMAR = """

## Exact native edit_file argument contract
When using edit_file, supply exactly the required string arguments:
filepath (existing file), old_string (nonempty exact text already read from
that file), and new_string (replacement text). Preserve literal newlines and
quotes in JSON string values. Do not omit old_string, substitute a description
or line number, or send a partial tool-call object. For a new file use the
existing write_file tool instead. Follow the normal patch submission process.
"""


def files_for_pair(source_zip: bytes) -> tuple[dict[str, str], dict[str, str]]:
    source = _source_files(source_zip)
    cfg = source["eval_config.yaml"]
    if cfg.count("max_time_minutes: 5") != 1:
        raise ValueError("Champion budget drift")
    # Keep 5-minute Champion budget; no cap/time variable.
    control = dict(source)
    candidate = dict(control)
    if "Exact native edit_file argument contract" in control["prompts/system.md"]:
        raise ValueError("source contaminated by treatment")
    candidate["prompts/system.md"] = control["prompts/system.md"].rstrip() + "\n" + EDIT_GRAMMAR
    assert all(candidate[k] == control[k] for k in EXPECTED_FILES - {"prompts/system.md"})
    assert candidate["agent.yaml"] == control["agent.yaml"]
    assert candidate["eval_config.yaml"] == control["eval_config.yaml"]
    assert candidate["configs/sampling.yaml"] == control["configs/sampling.yaml"]
    return control, candidate


def build_pair(source_zip: bytes) -> tuple[bytes, bytes]:
    a, b = files_for_pair(source_zip)
    return _pack(a), _pack(b)


def describe(source_zip: bytes) -> dict:
    a, b = build_pair(source_zip)
    return {
        "source_champion_sha256": CHAMPION_SHA256,
        "control_sha256": hashlib.sha256(a).hexdigest(),
        "candidate_sha256": hashlib.sha256(b).hexdigest(),
        "only_difference": "prompts/system.md",
        "single_variable": "native edit_file required argument grammar",
        "model": MODEL, "max_time_minutes": 5, "max_tool_calls": 60,
        "official_submission": False, "gpu_inference": False,
        "proven_improvement": False,
    }


def main() -> None:
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--source-zip", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    if args.out.exists():
        raise FileExistsError("refuse overwrite")
    source = args.source_zip.read_bytes()
    control, candidate = build_pair(source)
    args.out.mkdir(parents=True)
    (args.out / "control.zip").write_bytes(control)
    (args.out / "candidate.zip").write_bytes(candidate)
    (args.out / "manifest.json").write_text(json.dumps(describe(source), indent=2, sort_keys=True) + "\n")
    print("EDIT_GRAMMAR_CPU_BUILD=" + json.dumps(describe(source), sort_keys=True))


if __name__ == "__main__":
    main()
