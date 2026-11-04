#!/usr/bin/env python3
"""Render standalone private Kaggle L4x4 31B startup and tool-parser smoke."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

MODEL_NAME = "gemma-4-31b-it-qat-w4a16-ct"
MODEL_SOURCE = f"google/gemma-4/Other/{MODEL_NAME}/2"
RUNTIME_FILE = "kaggle/capacity_31b_startup_v0.py"


def render(repo: Path, out: Path, kernel_ref: str) -> Path:
    if not re.fullmatch(r"kolihhan/[a-z0-9-]+", kernel_ref):
        raise ValueError("unexpected Kaggle owner or kernel slug")
    source = (repo / RUNTIME_FILE).read_text(encoding="utf-8")
    if source.count(f'MODEL_NAME = "{MODEL_NAME}"') != 1:
        raise ValueError("31B runtime model declaration drift")
    for bad in ("tasks.jsonl", "reference_patch", "agent_patch", "evaluate_task"):
        if bad in source:
            raise ValueError(f"startup smoke unexpectedly includes task/evaluation code: {bad}")
    required = ("VllmServer", "probe_plain", "probe_scalar_tool", "probe_array_tool")
    if not all(w in source for w in required):
        raise ValueError("runtime lacks required startup/parser checks")
    compile(source, "capacity_31b_startup_v0.py", "exec")

    if out.exists() and any(out.iterdir()):
        raise ValueError("refuse to overwrite existing kernel")
    out.mkdir(parents=True, exist_ok=True)
    (out / "capacity_31b_startup_v0.py").write_text(source, encoding="utf-8")
    meta = {
        "id": kernel_ref,
        "title": kernel_ref.split("/", 1)[1],
        "code_file": "capacity_31b_startup_v0.py",
        "language": "python",
        "kernel_type": "script",
        "is_private": True,
        "enable_gpu": True,
        "enable_tpu": False,
        "enable_internet": False,
        "machine_shape": "NvidiaL4",
        "docker_image": "gcr.io/kaggle-private-byod/python@sha256:37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461",
        "dataset_sources": ["metric/gemma-4-developer-agent-wheelhouse"],
        "competition_sources": ["gemma-4-developer-agent"],
        "kernel_sources": [],
        "model_sources": [MODEL_SOURCE],
    }
    (out / "kernel-metadata.json").write_text(
        json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return out


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, default=Path("."))
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--kernel-ref", type=str, required=True)
    args = p.parse_args()
    out = render(args.repo.resolve(), args.out.resolve(), args.kernel_ref)
    print("CAPACITY_31B_RENDER=PASS")
    print("CAPACITY_31B_PRIVATE=TRUE")
    print("CAPACITY_31B_COMPETITION_TASKS=ZERO")
    print("CAPACITY_31B_FILES=", sorted(p.name for p in out.iterdir()))


if __name__ == "__main__":
    main()
