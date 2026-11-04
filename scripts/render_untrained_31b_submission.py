#!/usr/bin/env python3
"""Render one untrained Gemma 4 31B Kaggle code submission.

Only the root model declaration differs from the pinned scored Reliability-v1
E4B submission. Does not train, inspect task data, or launch model inference.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import re
import zipfile
from pathlib import Path

from scripts import render_reliability_v1_kernel as frozen

BASE_MODEL = "gemma-4-e4b-it-qat-w4a16-ct"
NEW_MODEL = "gemma-4-31b-it-qat-w4a16-ct"
MESSAGE = "untrained-31b-v0:same-policy-as-reliability-v1"
COMPETITION = "gemma-4-developer-agent"
SOURCE_REF = "57921371"
ZIP_FILE = "submission.zip"
KERNEL_FILE = "build_31b_submission.py"


def sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def payload(root: Path) -> tuple[dict[str, str], dict[str, str]]:
    baseline = frozen.load_frozen_submission(root / "submission")
    if len(baseline) != 5 or "agent.yaml" not in baseline:
        raise ValueError("frozen submission structure changed")
    original = baseline["agent.yaml"]
    old_line = f"model: {BASE_MODEL}"
    new_line = f"model: {NEW_MODEL}"
    if original.count(old_line) != 1 or original.count("\nmodel:") != 1:
        raise ValueError("frozen root model declaration count drift")
    if NEW_MODEL in original:
        raise ValueError("unexpected 31B string in control")
    if any("adapter:" in v or ".safetensors" in v for v in baseline.values()):
        raise ValueError("LoRA or adapter unexpectedly present in frozen control")
    treatment = dict(baseline)
    treatment["agent.yaml"] = original.replace(old_line, new_line, 1)
    if treatment["agent.yaml"].replace(new_line, old_line, 1) != original:
        raise ValueError("agent.yaml differs from control beyond model")
    for file in baseline:
        if file != "agent.yaml" and baseline[file] != treatment[file]:
            raise ValueError(f"payload changed frozen non-agent file: {file}")
    return baseline, treatment


def create_zip_bytes(files: dict[str, str]) -> bytes:
    with io.BytesIO() as buffer:
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name in sorted(files):
                # Fixed timestamp and permissions make archive hashes reproducible.
                entry = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
                entry.compress_type = zipfile.ZIP_DEFLATED
                entry.external_attr = 0o100644 << 16
                archive.writestr(entry, files[name].encode("utf-8"))
        data = buffer.getvalue()
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        if sorted(z.namelist()) != sorted(files):
            raise ValueError("zip content list mismatch")
        if any(z.read(k) != v.encode("utf-8") for k, v in files.items()):
            raise ValueError("zip payload mismatch")
    return data


def render(root: Path, out: Path, kernel_ref: str) -> Path:
    if not re.fullmatch(r"kolihhan/[a-z0-9-]+", kernel_ref):
        raise ValueError("invalid owner or Kaggle slug")
    if out.exists() and any(out.iterdir()):
        raise ValueError("refuse overwrite of Kaggle kernel")
    baseline, candidate = payload(root)
    encoded = base64.b64encode(
        json.dumps(candidate, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).decode("ascii")
    expected_zip_sha = sha(create_zip_bytes(candidate))
    code = f'''import base64, hashlib, io, json, zipfile
from pathlib import Path
PAYLOAD = {encoded!r}
EXPECTED_ZIP_SHA = {expected_zip_sha!r}
files = json.loads(base64.b64decode(PAYLOAD).decode("utf-8"))
buf = io.BytesIO()
with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as archive:
    for name in sorted(files):
        entry = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
        entry.compress_type = zipfile.ZIP_DEFLATED
        entry.external_attr = 0o100644 << 16
        archive.writestr(entry, files[name].encode("utf-8"))
data = buf.getvalue()
assert hashlib.sha256(data).hexdigest() == EXPECTED_ZIP_SHA
with zipfile.ZipFile(io.BytesIO(data)) as archive:
    assert sorted(archive.namelist()) == sorted(files)
    assert all(archive.read(name) == files[name].encode("utf-8") for name in files)
out = Path("/kaggle/working/submission.zip")
out.write_bytes(data)
print("UNTRAINED_31B_SUBMISSION_ZIP=PASS")
print("MODEL=gemma-4-31b-it-qat-w4a16-ct")
print("NO_TRAINING=TRUE")
print("SHA256=", EXPECTED_ZIP_SHA)
print("FILE_COUNT=", len(files))
'''
    compile(code, KERNEL_FILE, "exec")
    metadata = {
        "id": kernel_ref,
        "title": kernel_ref.split("/", 1)[1],
        "code_file": KERNEL_FILE,
        "language": "python",
        "kernel_type": "script",
        "is_private": True,
        "enable_gpu": False,
        "enable_tpu": False,
        "enable_internet": False,
        "competition_sources": [COMPETITION],
        "dataset_sources": [],
        "kernel_sources": [],
        "model_sources": [],
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / KERNEL_FILE).write_text(code, encoding="utf-8")
    (out / "kernel-metadata.json").write_text(
        json.dumps(metadata, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    return out


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, default=Path("."))
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--kernel-ref", required=True)
    args = p.parse_args()
    root = args.repo.resolve()
    control, candidate = payload(root)
    render(root, args.out.resolve(), args.kernel_ref)
    print("CONTROL_REF=", SOURCE_REF)
    print("CONTROL_AGENT_SHA256=", sha(control["agent.yaml"].encode("utf-8")))
    print("CANDIDATE_AGENT_SHA256=", sha(candidate["agent.yaml"].encode("utf-8")))
    print("CANDIDATE_ZIP_SHA256=", sha(create_zip_bytes(candidate)))
    print("SINGLE_CHANGED_FIELD=model")
    print("NO_LORA_NO_TRAINING_NO_GPU_BUILDER=TRUE")


if __name__ == "__main__":
    main()
