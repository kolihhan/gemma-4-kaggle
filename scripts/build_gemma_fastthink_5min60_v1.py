"""Falsifiable Gemma 31B inference-throughput candidate, NOT a scored gain.

Mechanism: the 5-minute / 60-tool-call scored 0.18 control may spend too
much of its wall budget in a 4096-token reasoning step. One-variable
intervention: cap model thinking to 2048 tokens; preserve ALL other
model, prompt, tool, sampling, task/total-budget and zip files.
Candidate requires real matched heldout evaluation before promotion.
"""
from __future__ import annotations

import hashlib
import io
import zipfile

from scripts.build_toolcap60_timeout_recovery import files_for_candidate as incumbent

BASE = "thinking_budget: 4096"
TREATMENT = "thinking_budget: 2048"
STAMP = (2026, 11, 13, 0, 0, 0)


def files_for_candidate(source_zip: bytes) -> dict[str, str]:
    control = incumbent(source_zip)
    if set(control) != {"agent.yaml", "prompts/system.md",
                        "configs/sampling.yaml", "eval_config.yaml"}:
        raise ValueError("unexpected scored control files")
    cfg = control["configs/sampling.yaml"]
    if cfg.count(BASE) != 1 or TREATMENT in cfg:
        raise ValueError("frozen thinking-budget control drift")
    if (control["eval_config.yaml"].count("max_time_minutes: 5") != 1 or
        control["eval_config.yaml"].count("max_tool_calls: 60") != 1 or
        control["eval_config.yaml"].count("max_turns: 80") != 1):
        raise ValueError("scored 5min60 operating budget drift")
    if "model: gemma-4-31b-it-qat-w4a16-ct" not in control["agent.yaml"]:
        raise ValueError("not original 31B")
    candidate = dict(control)
    candidate["configs/sampling.yaml"] = cfg.replace(BASE, TREATMENT, 1)
    for key in control:
        expected = cfg.replace(BASE, TREATMENT, 1) if key == "configs/sampling.yaml" else control[key]
        if candidate[key] != expected:
            raise ValueError("uncontrolled change " + key)
    return candidate


def build(source_zip: bytes) -> bytes:
    files = files_for_candidate(source_zip)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, text in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=STAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            z.writestr(info, text.encode("utf-8"))
    raw = buf.getvalue()
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if z.testzip() or set(z.namelist()) != set(files):
            raise ValueError("damaged candidate archive")
    return raw


def report(source_zip: bytes) -> dict:
    control = incumbent(source_zip)
    cand = files_for_candidate(source_zip)
    changed = [key for key in control if control[key] != cand[key]]
    if changed != ["configs/sampling.yaml"]:
        raise AssertionError("not exactly one changed source member")
    return {"candidate_sha256": hashlib.sha256(build(source_zip)).hexdigest(),
            "changed_files": changed,
            "thinking_budget_before": 4096, "thinking_budget_after": 2048,
            "task_minutes": 5, "tool_calls": 60, "model": "gemma-4-31b-it-qat-w4a16-ct",
            "training": False, "official_submission": False,
            "independent_model_quality_gain": None}
