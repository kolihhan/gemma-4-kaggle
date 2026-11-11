"""Render a private CPU-only contemporary verifier integrity screen of four prequalified issues.

The four issues were chosen based on independent public PR specification quality
and 2026-11-04 gold-pass/noop-fail metadata, BEFORE model outcome inspection.
This tool does not read task text, reference solutions, private data, or use GPU.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
BASE = "kaggle/paired_three_task_integrity_cpu.py"
OLD = '''TASKS = (
    ("fastapi_14487", "fastapi/fastapi"),
    ("rich_3782", "Textualize/rich"),
    ("requests_7427", "psf/requests"),
)'''
NEW = '''TASKS = (
    ("fastapi_14458", "fastapi/fastapi"),
    ("fastapi_15589", "fastapi/fastapi"),
    ("rich_3894", "Textualize/rich"),
    ("rich_3905", "Textualize/rich"),
)'''
OUTPUT_NAME = "clean_four_integrity_cpu.json"
VERSION = "gemma4-clean-four-integrity-v1"
CONTAINER = "gcr.io/kaggle-private-byod/python@sha256:37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461"


def render(repo: Path, out: Path, kernel_ref: str) -> dict:
    if not re.fullmatch(r"kolihhan/[a-z0-9-]{15,90}", kernel_ref):
        raise ValueError("unexpected private kernel ref")
    if out.exists() and any(out.iterdir()):
        raise FileExistsError("refuse to overwrite kernel")
    import json
    gold = json.loads((repo / "docs/evaluation/capacity-v0-gold-screen-2026-11-04.json").read_text())
    noop = json.loads((repo / "docs/evaluation/capacity-v0-noop-screen-2026-11-04.json").read_text())
    frozen = ["fastapi_14458", "fastapi_15589", "rich_3894", "rich_3905"]
    gold_good = {r["instance_id"] for r in gold["results"] if r.get("gold_pass") is True and r.get("test_exit_code") == 0}
    noop_fail = {r["instance_id"] for r in noop["results"] if r.get("noop_fail") is True and r.get("test_exit_code") != 0}
    if not set(frozen).issubset(gold_good & noop_fail):
        raise ValueError("historical gold/noop eligibility mismatch")
    text = (repo / BASE).read_text(encoding="utf-8")
    if text.count(OLD) != 1:
        raise ValueError("3-task base changed; refuse render")
    text = text.replace(OLD, NEW)
    for old, new in (
        ("paired_three_task_integrity_cpu.json", OUTPUT_NAME),
        ("gemma4-paired-31b-three-task-integrity-v1", VERSION),
        ("original_31b_paired_run", "prequalification_gold_noop_run"),
        ("43057377220", "41782992381"),
    ):
        if text.count(old) != 1:
            raise ValueError("runtime anchor mismatch " + old)
        text = text.replace(old, new)
    compile(text, "clean_four_integrity_cpu.py", "exec")
    out.mkdir(parents=True, exist_ok=True)
    (out/"clean_four_integrity_cpu.py").write_text(text, encoding="utf-8")
    metadata = {
        "id": kernel_ref,
        "title": kernel_ref.rsplit("/", 1)[-1],
        "code_file": "clean_four_integrity_cpu.py",
        "language": "python", "kernel_type": "script",
        "is_private": True, "enable_gpu": False, "enable_tpu": False, "enable_internet": False,
        "docker_image": CONTAINER,
        "competition_sources": ["gemma-4-developer-agent"],
        "dataset_sources": ["metric/gemma-4-developer-agent-wheelhouse"],
        "model_sources": [], "kernel_sources": [],
    }
    (out/"kernel-metadata.json").write_text(json.dumps(metadata, sort_keys=True, indent=2)+"\n")
    return {"private": True, "cpu_only": True, "tasks": frozen,
            "sha256":hashlib.sha256(text.encode("utf-8")).hexdigest()}


def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--repo", type=Path, default=ROOT)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--kernel-ref", required=True)
    a=p.parse_args()
    print("CLEAN_FOUR_CPU_RENDER="+json.dumps(
        render(a.repo.resolve(), a.out.resolve(), a.kernel_ref), sort_keys=True))


if __name__=="__main__":
    main()
