#!/usr/bin/env python3
"""One-variable 31B source behavior counterexample candidate. No model inference.

The exact hash-pinned 31B Budget-Fit V2 reference is the base. Treatment only
changes instruction text and uses the same 5-minute experimental cap as its
paired control. Neither the base model, sampling, tool set nor call cap changes.
"""
from __future__ import annotations

import hashlib
import io
import zipfile

from scripts.prepare_public_budgetfit_v2 import (
    validate_source_zip, EXPECTED_ZIP_SHA256,
)

MECHANISM = "pre-edit-behavioral-counterexample-v0-20261116"
PROMPT_EXTENSION = """
## Bounded behavioral counterexample check (this experiment's only policy change)

A patch is correct only if it satisfies the *observable behavior* requested by
the issue, not just if it modifies the plausible file. After locating the
relevant code but BEFORE the first edit, identify the most consequential
behavioral edge case the proposed change could get wrong (input, return shape,
exception, backwards compatibility or interacting caller).

Use at most ONE cheap existing-code/test observation to distinguish the patch
from a wrong-but-plausible alternative. Prefer a nearby assertion, call site,
or existing focused test. If no such witness exists or the check would be
expensive, explicitly treat the requirement as unresolved and proceed with
the minimal defensible implementation. Never invent a test or infer hidden
grader expectations.

After editing, execute ONE directly related existing test or inexpensive
executable assertion for that same behavioral contract if available. When it
fails, repair only the observed mismatch once. Do not broaden to unrelated
tests, install dependencies, or sacrifice the remaining submission budget.
The usual narrow edit and submit_patch discipline still applies.
"""


def source_payload(source_zip: bytes) -> dict[str, str]:
    if hashlib.sha256(source_zip).hexdigest() != EXPECTED_ZIP_SHA256:
        raise ValueError("frozen 31B V2 source drift")
    base = validate_source_zip(source_zip)
    if set(base) != {"agent.yaml", "prompts/system.md", "eval_config.yaml",
                     "configs/sampling.yaml"}:
        raise ValueError("unexpected original 31B archive members")
    cfg = base["eval_config.yaml"]
    if cfg.count("max_time_minutes: 8") != 1 or cfg.count("max_tool_calls: 28") != 1:
        raise ValueError("frozen original BudgetFit budget drift")
    data = dict(base)
    data["eval_config.yaml"] = cfg.replace("max_time_minutes: 8",
                                           "max_time_minutes: 5", 1)
    if "submit_patch" not in data["agent.yaml"]:
        raise ValueError("missing allowed native submit tool")
    data["prompts/system.md"] = (
        data["prompts/system.md"].rstrip()
        + "\n\n" + PROMPT_EXTENSION.strip() + "\n"
    )
    assert data["agent.yaml"] == base["agent.yaml"]
    assert data["configs/sampling.yaml"] == base["configs/sampling.yaml"]
    assert data["eval_config.yaml"].replace("max_time_minutes: 5",
                                           "max_time_minutes: 8", 1) == cfg
    return data


def build(source_zip: bytes) -> bytes:
    files = source_payload(source_zip)
    result = io.BytesIO()
    with zipfile.ZipFile(result, "w", compression=zipfile.ZIP_DEFLATED) as output:
        for name, value in sorted(files.items()):
            item = zipfile.ZipInfo(name, date_time=(2026, 11, 16, 0, 0, 0))
            item.compress_type = zipfile.ZIP_DEFLATED
            item.external_attr = 0o100644 << 16
            output.writestr(item, value.encode("utf-8"))
    return result.getvalue()
