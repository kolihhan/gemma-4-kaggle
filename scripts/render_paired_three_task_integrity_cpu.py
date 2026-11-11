"""Build exactly one private CPU-only Kaggle kernel for the frozen 3-task integrity screen."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path("kaggle/paired_three_task_integrity_cpu.py")
CONTAINER = "gcr.io/kaggle-private-byod/python@sha256:37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461"


def render(repo: Path, out: Path, kernel_ref: str) -> dict:
    if not re.fullmatch(r"kolihhan/[a-z0-9-]{15,100}", kernel_ref):
        raise ValueError("unexpected private Kaggle kernel id")
    if out.exists() and any(out.iterdir()):
        raise FileExistsError("refuse overwrite")
    content = (repo / SOURCE).read_text(encoding="utf-8")
    compile(content, str(SOURCE), "exec")
    if content.count('("fastapi_14487", "fastapi/fastapi")') != 1:
        raise ValueError("task cohort drift")
    if content.count('("rich_3782", "Textualize/rich")') != 1:
        raise ValueError("task cohort drift")
    if content.count('("requests_7427", "psf/requests")') != 1:
        raise ValueError("task cohort drift")
    if "def install_wheelhouse()" not in content or "agent_patch=patch" not in content:
        raise ValueError("official verifier path missing")
    out.mkdir(parents=True, exist_ok=True)
    (out / SOURCE.name).write_text(content, encoding="utf-8")
    meta = {
        "id": kernel_ref,
        "title": kernel_ref.rsplit("/", 1)[-1],
        "code_file": SOURCE.name,
        "language": "python", "kernel_type": "script",
        "is_private": True, "enable_gpu": False, "enable_tpu": False,
        "enable_internet": False, "docker_image": CONTAINER,
        "competition_sources": ["gemma-4-developer-agent"],
        "dataset_sources": ["metric/gemma-4-developer-agent-wheelhouse"],
        "model_sources": [], "kernel_sources": [],
    }
    (out / "kernel-metadata.json").write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n")
    return {"code_sha256": hashlib.sha256(content.encode()).hexdigest(),
            "kernel_ref": kernel_ref, "cpu_only": True, "task_count": 3}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--repo", type=Path, default=ROOT)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--kernel-ref", required=True)
    a = p.parse_args()
    print("INTEGRITY_CPU_RENDER=" + json.dumps(
        render(a.repo.resolve(), a.out.resolve(), a.kernel_ref), sort_keys=True))


if __name__ == "__main__":
    main()
