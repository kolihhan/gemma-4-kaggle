"""Paired Gemma 31B behavioral-probe candidates, timeout-safe and CPU-build-only.

CONTROL and CANDIDATE derive from exact scored 0.18 Champion.
Both arms: four minutes, 60 calls, 80 turns; only candidate prompt differs.
No Kaggle submission, model inference, tools or training are performed here.
"""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import zipfile
from scripts.build_toolcap60_timeout_recovery import (
    STAMP, build as build_scored_champion,
    files_for_candidate as champion_files,
)

CHAMPION_SHA256 = "ff08c10240a38e151a2ea1d0478e999ee5d2f437d2dad5571d912cf12859922b"
MODEL = "gemma-4-31b-it-qat-w4a16-ct"
TASK_MINUTES = 4
TOOL_CALLS = 60
TURNS = 80
TOTAL_LIMIT_SECONDS = 12 * 3600
RESERVE_SECONDS = 3600
EXPECTED_FILES = {"agent.yaml", "eval_config.yaml", "configs/sampling.yaml", "prompts/system.md"}

BEHAVIORAL_PROBE = """

## Conditional behavioral counterexample check (one bounded experiment)
After identifying the issue's expected behavior, state one concrete input and
observable expected outcome for the changed code. Do not invent requirements.
Make the smallest plausible fix first. Only run a test when an existing
relevant test or a safe, minimal local reproduction genuinely distinguishes
correct from incorrect behavior. Use native run_command (no new tools).

The probe MUST be narrow, offline and bounded: prefer an existing test node;
for an eligible shell test command use an operating-system timeout of 20 seconds
(e.g. timeout 20s python -m pytest path/to/test.py -q --maxfail=1).
Never run a full suite, install dependencies, or create complex test scaffolding.
A test timeout, nonzero exit or missing output is NOT a pass. If informative
feedback contradicts the patch, make at most one evidence-based correction.

Use get_status when available. If under 70 seconds of the task budget remain,
skip further probes, inspect the diff quickly and call submit_patch before the
hard stop. Do not keep exploring or testing at the cost of losing a plausible
patch. If no meaningful probe is available quickly, skip it and proceed with
the best evidence-supported source change. Avoid extra calls for ceremony.
"""


def _source_files(source_zip: bytes) -> dict[str, str]:
    scored = build_scored_champion(source_zip)
    if hashlib.sha256(scored).hexdigest() != CHAMPION_SHA256:
        raise ValueError("source does not reconstruct exact scored 0.18 Champion")
    original = champion_files(source_zip)
    if set(original) != EXPECTED_FILES:
        raise ValueError("unexpected Champion archive membership")
    if original["agent.yaml"].count("model: " + MODEL) != 1:
        raise ValueError("wrong model")
    for tool in ("run_command", "read_file", "edit_file", "submit_patch", "get_status"):
        if "  - " + tool not in original["agent.yaml"]:
            raise ValueError("missing native tool " + tool)
    cfg = original["eval_config.yaml"]
    for expected in ("max_time_minutes: 5", "max_tool_calls: 60", "max_turns: 80"):
        if cfg.count(expected) != 1:
            raise ValueError("Champion budget mismatch: " + expected)
    if not original["prompts/system.md"].strip():
        raise ValueError("empty original prompt")
    return original


def files_for_pair(source_zip: bytes) -> tuple[dict[str, str], dict[str, str]]:
    source = _source_files(source_zip)
    cfg = source["eval_config.yaml"].replace("max_time_minutes: 5", "max_time_minutes: 4", 1)
    control = dict(source, **{"eval_config.yaml": cfg})
    candidate = dict(control)
    original_prompt = control["prompts/system.md"]
    if "Conditional behavioral counterexample check" in original_prompt:
        raise ValueError("probe already present in source")
    candidate["prompts/system.md"] = original_prompt.rstrip() + "\n" + BEHAVIORAL_PROBE
    assert all(candidate[k] == control[k] for k in EXPECTED_FILES - {"prompts/system.md"})
    return control, candidate


def _pack(files: dict[str, str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for path in sorted(files):
            if Path(path).is_absolute() or ".." in Path(path).parts:
                raise ValueError("unsafe path")
            entry = zipfile.ZipInfo(path, date_time=STAMP)
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            z.writestr(entry, files[path].encode("utf-8"))
    payload = buf.getvalue()
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        if z.testzip() is not None or set(z.namelist()) != EXPECTED_FILES:
            raise ValueError("invalid bundle")
    return payload


def build_pair(source_zip: bytes) -> tuple[bytes, bytes]:
    a, b = files_for_pair(source_zip)
    return _pack(a), _pack(b)


def timeout_forecast(*, tasks: int, mean_setup_seconds: float,
                     startup_seconds: float = 1800,
                     reserve_seconds: float = RESERVE_SECONDS) -> dict:
    """Planning estimate only, not a guarantee for unknown hidden tasks."""
    if tasks <= 0 or min(mean_setup_seconds, startup_seconds, reserve_seconds) < 0:
        raise ValueError("invalid forecast inputs")
    projected = tasks * (TASK_MINUTES * 60 + mean_setup_seconds) + startup_seconds
    available = TOTAL_LIMIT_SECONDS - reserve_seconds
    return {"tasks": tasks, "projected_seconds": projected,
            "limit_seconds": TOTAL_LIMIT_SECONDS, "reserved_seconds": reserve_seconds,
            "safe_under_assumptions": projected <= available,
            "estimated_headroom_seconds": available - projected,
            "note": "Estimate only; hidden task count and setup time may differ"}


def describe(source_zip: bytes) -> dict:
    control, candidate = build_pair(source_zip)
    return {"source_champion_sha256": CHAMPION_SHA256,
            "control_sha256": hashlib.sha256(control).hexdigest(),
            "candidate_sha256": hashlib.sha256(candidate).hexdigest(),
            "model": MODEL, "per_task_minutes": TASK_MINUTES,
            "max_tool_calls": TOOL_CALLS, "max_turns": TURNS,
            "only_difference_between_arms": "prompts/system.md",
            "method": "conditional bounded behavioral probe, prompt-level trial",
            "gpu": False, "official_submission": False,
            "proven_resolved_task_gain": False}


def main() -> None:
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-zip", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--tasks", type=int, default=120)
    p.add_argument("--setup-seconds", type=float, default=45)
    args = p.parse_args()
    if args.out.exists():
        raise FileExistsError("refuse overwrite")
    source = args.source_zip.read_bytes()
    a, b = build_pair(source)
    args.out.mkdir(parents=True)
    (args.out / "control.zip").write_bytes(a)
    (args.out / "candidate.zip").write_bytes(b)
    result = {"experiment": describe(source),
              "timeout_forecast": timeout_forecast(tasks=args.tasks,
                                                  mean_setup_seconds=args.setup_seconds)}
    (args.out / "manifest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
