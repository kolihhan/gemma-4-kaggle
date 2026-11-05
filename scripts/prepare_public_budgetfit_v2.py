#!/usr/bin/env python3
"""Reproduce, without training, the public scored Budget-Fit V2 submission.

This is an ATTRIBUTED external reference/control, not an original candidate.
The source archive is fetched from Kaggle at runtime, validated byte-for-byte,
then copied unchanged into a private CPU notebook builder. Never store raw
competition task data, patches, or secrets in the public GitHub repository.
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

COMPETITION = "gemma-4-developer-agent"
SOURCE_NOTEBOOK = "lynnsakurai/gemma-4-budget-fit-agent-w-bounded-rescue/2"
SOURCE_CODE_URL = "https://www.kaggle.com/code/lynnsakurai/gemma-4-budget-fit-agent-w-bounded-rescue"
SOURCE_VERSION = 2
SOURCE_REPORTED_PUBLIC_SCORE = "0.18"
SOURCE_LICENSE = "Apache-2.0"
EXPECTED_ZIP_SHA256 = "a4b10f6b8034fd7fffa144a7ee3fbd8faf9a84503ffb1349d1522ba048b534d3"
EXPECTED_MEMBERS = {
    "agent.yaml": "680799291cc7d156d06fb7bfb5577f683ccc0d555b00e8ddb662d577f9bfa5e4",
    "configs/sampling.yaml": "571a934e89911734927533f1d36cbcc7b8d493592febe63b217e911cf7ed4926",
    "eval_config.yaml": "916cf6cb34a6cc3de39837fa72cac681599b9ac2a3ee0b893adadfd36474c531",
    "prompts/system.md": "a42c35081c08f316fc76b02886c82d4073e6c143b63c40a86085b382b8bf113e",
}
MODEL = "gemma-4-31b-it-qat-w4a16-ct"
MESSAGE = "attributed-public-budgetfit-v2-repro:no-train"
BUILD_SCRIPT = "build_public_v2_control.py"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_source_zip(data: bytes) -> dict[str, str]:
    if digest(data) != EXPECTED_ZIP_SHA256:
        raise ValueError("not the pinned, publicly scored Kaggle V2 ZIP")
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        names = z.namelist()
        if len(names) != len(set(names)) or set(names) != set(EXPECTED_MEMBERS):
            raise ValueError("unexpected ZIP members")
        payload = {}
        for name in sorted(EXPECTED_MEMBERS):
            actual = z.read(name)
            if digest(actual) != EXPECTED_MEMBERS[name]:
                raise ValueError("scored V2 member hash mismatch: " + name)
            payload[name] = actual.decode("utf-8")
    if payload["agent.yaml"].count("model: " + MODEL) != 1:
        raise ValueError("expected exactly one allowed 31B model")
    if len(re.findall(r"(?m)^model:", payload["agent.yaml"])) != 1:
        raise ValueError("multi-model or malformed agent config")
    if "adapters/" in " ".join(payload) or any("adapter:" in body for body in payload.values()):
        raise ValueError("no LoRA in V2 control")
    # The SHA-pinned reference declares these settings; do not silently tune them.
    if "max_tool_calls: 28" not in payload["eval_config.yaml"] or "max_time_minutes: 8" not in payload["eval_config.yaml"]:
        raise ValueError("scored V2 budget drift")
    if "thinking_budget: 4096" not in payload["configs/sampling.yaml"]:
        raise ValueError("scored V2 sampling drift")
    return payload


def render(data: bytes, target: Path, kernel_ref: str) -> None:
    validate_source_zip(data)
    if not re.fullmatch(r"kolihhan/[a-z0-9-]+", kernel_ref):
        raise ValueError("invalid owner or Kaggle kernel slug")
    if target.exists() and any(target.iterdir()):
        raise ValueError("refuse to overwrite existing builder")
    target.mkdir(parents=True, exist_ok=True)
    blob = base64.b64encode(data).decode("ascii")
    code = (
        "import base64, hashlib, os\n"
        "from pathlib import Path\n"
        f"BLOB = {blob!r}\n"
        f"EXPECTED_SHA = {EXPECTED_ZIP_SHA256!r}\n"
        "result = base64.b64decode(BLOB)\n"
        "assert hashlib.sha256(result).hexdigest() == EXPECTED_SHA\n"
        'dest = Path(os.environ.get("OUTPUT_DIR", "/kaggle/working"))\n'
        "dest.mkdir(parents=True, exist_ok=True)\n"
        '(dest / "submission.zip").write_bytes(result)\n'
        'print("BUDGETFIT_PUBLIC_V2_EXACT_ZIP=PASS")\n'
        'print("SOURCE_VERSION=2 SOURCE_LICENSE=Apache-2.0 NO_TRAINING=TRUE")\n'
        'print("ZIP_SHA256=", EXPECTED_SHA)\n'
    )
    compile(code, BUILD_SCRIPT, "exec")
    (target / BUILD_SCRIPT).write_text(code, encoding="utf-8")
    metadata = {
        "id": kernel_ref,
        "title": kernel_ref.split("/", 1)[1],
        "code_file": BUILD_SCRIPT,
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
    (target / "kernel-metadata.json").write_text(json.dumps(metadata, sort_keys=True, indent=2) + "\n")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-zip", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--kernel-ref", required=True)
    args = p.parse_args()
    data = args.source_zip.read_bytes()
    payload = validate_source_zip(data)
    render(data, args.out, args.kernel_ref)
    print("ATTRIBUTED_PUBLIC_REFERENCE_VERIFIED=PASS")
    print("ORIGINAL_SOURCE=", SOURCE_NOTEBOOK)
    print("EXACT_ORIGINAL_SHA256=", digest(data))
    print("MEMBERS=", sorted(payload))
    print("NO_MODEL_RUN=TRUE NO_ADAPTERS=TRUE NO_TRAINING=TRUE")


if __name__ == "__main__":
    main()
