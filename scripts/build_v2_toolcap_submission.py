"""Candidate: retain pinned V2 31B behavior; relax only the tool-call ceiling.

The full prompt, tools, model, sampling and 8-minute task time are unchanged.
This is an exploratory scored candidate, not a claim of improved correctness.
"""
from __future__ import annotations

import argparse
import hashlib
import io
from pathlib import Path
import zipfile

from scripts.prepare_public_budgetfit_v2 import validate_source_zip

FROM_CALLS = 28
TO_CALLS = 60
SOURCE_MODEL = "gemma-4-31b-it-qat-w4a16-ct"
STABLE_ZIP_TIMESTAMP = (2026, 11, 9, 0, 0, 0)


def files_for_candidate(source_zip: bytes) -> dict[str, str]:
    original = validate_source_zip(source_zip)
    if set(original) != {"agent.yaml", "prompts/system.md", "configs/sampling.yaml", "eval_config.yaml"}:
        raise ValueError("unexpected control file set")
    if "model: " + SOURCE_MODEL not in original["agent.yaml"]:
        raise ValueError("wrong model")
    text = original["eval_config.yaml"]
    marker = "max_tool_calls: 28"
    if text.count(marker) != 1:
        raise ValueError("pinned baseline tool-call contract drift")
    candidate = dict(original)
    candidate["eval_config.yaml"] = text.replace(marker, "max_tool_calls: 60", 1)
    for name in ("agent.yaml", "prompts/system.md", "configs/sampling.yaml"):
        if candidate[name] != original[name]:
            raise AssertionError("base model/prompt/native tools/sampling changed")
    if candidate["eval_config.yaml"].replace("max_tool_calls: 60", marker) != text:
        raise AssertionError("other task time/turn constraints changed")
    return candidate


def build(source_zip: bytes) -> bytes:
    files = files_for_candidate(source_zip)
    target = io.BytesIO()
    with zipfile.ZipFile(target, mode="w") as archive:
        for name, content in sorted(files.items()):
            item = zipfile.ZipInfo(name, date_time=STABLE_ZIP_TIMESTAMP)
            item.compress_type = zipfile.ZIP_DEFLATED
            item.external_attr = 0o100644 << 16
            archive.writestr(item, content.encode("utf-8"))
    payload = target.getvalue()
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        if archive.testzip() is not None or set(archive.namelist()) != set(files):
            raise ValueError("candidate archive invalid")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-zip", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError("refusing overwrite of candidate artifact")
    content = build(args.source_zip.read_bytes())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(content)
    print("TOOLCAP60_ZIP_SHA256=" + hashlib.sha256(content).hexdigest())
    print("COMPETITION_SUBMISSION_PERFORMED=FALSE")


if __name__ == "__main__":
    main()
