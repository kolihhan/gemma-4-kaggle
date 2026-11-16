"""Source-pinned one-mechanism ablation: NO graph tools, native text search.

Both arms keep the SAME Gemma4-31B, sampling, other native tools and 
5min/28 calls/80 turns. Treatment removes only the three code-intelligence
tools and repairs the ONE affected graph rescue sentence in public prompt.
This is a novel *tool affordance* intervention, not an extra instruction.
"""
from __future__ import annotations

import hashlib
import io
import zipfile

from scripts.prepare_public_budgetfit_v2 import (
    EXPECTED_ZIP_SHA256, validate_source_zip
)

GRAPH = ("search_similar_code", "get_code_neighbors", "get_code_subgraph")
OLD_RESCUE = (
    "- Graph retrieval is a rescue lane, not the default. "
    "Only after two specific textual localization attempts fail, "
    "call `search_similar_code` once with the behavior from the issue. "
    "If it returns an exact useful symbol, `get_code_neighbors` may be called once. "
    "Do not use `get_code_subgraph`."
)
NEW_RESCUE = (
    "- If two specific textual localization searches fail, "
    "use one targeted native `run_command` grep/find on a caller, test, "
    "or alternate error/symbol term; do not broaden into unrelated files."
)


def source_payload(source_zip: bytes) -> dict[str, str]:
    if hashlib.sha256(source_zip).hexdigest() != EXPECTED_ZIP_SHA256:
        raise ValueError("not source-pinned V2")
    base = validate_source_zip(source_zip)
    if set(base) != {
        "agent.yaml", "eval_config.yaml", "configs/sampling.yaml", "prompts/system.md"
    }:
        raise ValueError("unexpected baseline components")
    if base["prompts/system.md"].count(OLD_RESCUE) != 1:
        raise ValueError("original graph rescue sentence drifted")
    manifest = base["agent.yaml"]
    for tool in GRAPH:
        line = "  - " + tool + "\n"
        if manifest.count(line) != 1:
            raise ValueError("graph tool declaration drift: " + tool)
        manifest = manifest.replace(line, "", 1)
    for required in ("run_command", "read_file", "edit_file", "get_status", "submit_patch"):
        if ("  - " + required + "\n") not in manifest and not manifest.endswith("  - "+required):
            raise ValueError("important native tool accidentally removed")
    assert not any(("  - "+tool+"\n") in manifest for tool in GRAPH)
    data = dict(base)
    data["agent.yaml"] = manifest
    data["prompts/system.md"] = base["prompts/system.md"].replace(
        OLD_RESCUE, NEW_RESCUE, 1
    )
    budget = base["eval_config.yaml"]
    if budget.count("max_time_minutes: 8") != 1:
        raise ValueError("source budget drift")
    data["eval_config.yaml"] = budget.replace(
        "max_time_minutes: 8", "max_time_minutes: 5", 1
    )
    assert data["configs/sampling.yaml"] == base["configs/sampling.yaml"]
    assert all(t not in data["prompts/system.md"] for t in GRAPH)
    return data


def build(source_zip: bytes) -> bytes:
    components = source_payload(source_zip)
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w") as archive:
        for name, text in sorted(components.items()):
            member = zipfile.ZipInfo(name, date_time=(2026, 11, 16, 0, 0, 0))
            member.compress_type = zipfile.ZIP_DEFLATED
            member.external_attr = 0o100644 << 16
            archive.writestr(member, text.encode("utf-8"))
    result = payload.getvalue()
    assert zipfile.ZipFile(io.BytesIO(result)).testzip() is None
    return result
