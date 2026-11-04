#!/usr/bin/env python3
"""Render private CPU gold eligibility for fresh SHA-ranked capacity replacements.

No model calls. No GPU. Only metadata ID lists embedded into private Kaggle
kernel, with raw hydrated task and patch content never sent to GitHub.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts import build_capacity_replacements_v0 as replacements
from scripts import render_capacity_gold_v0 as original_gold

# The first preregistered queue cushion was historically screened on 467
# preselection Git revisions (run 41803046378), with zero tracked mentions.
# Counts are fixed before any replacement gold/no-op result.
SCREEN_COUNTS = {"Textualize/rich": 4, "fastapi/fastapi": 12}
GOLD_RUNTIME = "kaggle/gold_control_sweep.py"


def create_manifest(root: Path) -> dict:
    plan = replacements.build_plan(root)
    if plan["status"] != "FROZEN_ORDER_UNSCREENED_NOT_BLIND_CERTIFIED":
        raise ValueError("unexpected replacement plan status")
    items = []
    for repo, limit in SCREEN_COUNTS.items():
        ids = plan["queues"][repo][:limit]
        if len(ids) != limit:
            raise ValueError(f"insufficient frozen replacement candidates for {repo}")
        for issue_id in ids:
            items.append({
                "instance_id": issue_id,
                "repo": repo,
                "patch_bucket": "metadata-only",
            })
    original_ids = set(plan["original_ids"])
    selected = [item["instance_id"] for item in items]
    if len(selected) != 16 or len(set(selected)) != 16 or set(selected) & original_ids:
        raise ValueError("replacement candidate selection integrity failed")
    return {
        "version": "verifier-lora-v0",
        "experiment": "capacity-v0-new-replacements-gold-cpu-only",
        "selector_sha256": plan["source_selector_sha256"],
        "holdout": items,
    }


def render(root: Path, out: Path, kernel_ref: str) -> Path:
    if not kernel_ref.startswith("kolihhan/"):
        raise ValueError("private Kaggle kernel owner changed")
    if out.exists() and any(out.iterdir()):
        raise ValueError("refuse to overwrite rendered replacement kernel")
    manifest = create_manifest(root)
    runtime_path = root / GOLD_RUNTIME
    runtime = original_gold.load_module(runtime_path, "gold_sweep_replacement")
    rendered = runtime.render_kernel_source(
        runtime_path.read_text(encoding="utf-8"),
        json.dumps(manifest, sort_keys=True, separators=(",", ":")),
    )
    compile(rendered, "gold_control_sweep.py", "exec")
    out.mkdir(parents=True, exist_ok=True)
    (out / "gold_control_sweep.py").write_text(rendered, encoding="utf-8")
    meta = {
        "id": kernel_ref,
        "title": kernel_ref.split("/", 1)[1],
        "code_file": "gold_control_sweep.py",
        "language": "python",
        "kernel_type": "script",
        "is_private": True,
        "enable_gpu": False,
        "enable_tpu": False,
        "enable_internet": False,
        "docker_image": "gcr.io/kaggle-private-byod/python@sha256:37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461",
        "dataset_sources": ["metric/gemma-4-developer-agent-wheelhouse"],
        "competition_sources": ["gemma-4-developer-agent"],
        "kernel_sources": [],
        "model_sources": [],
    }
    (out / "kernel-metadata.json").write_text(
        json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--kernel-ref", required=True)
    args = parser.parse_args()
    out = render(args.repo.resolve(), args.out.resolve(), args.kernel_ref)
    print("CAPACITY_REPLACEMENT_GOLD_RENDER=PASS")
    print("CAPACITY_REPLACEMENT_GOLD_COUNT=", sum(SCREEN_COUNTS.values()))
    print("CAPACITY_REPLACEMENT_GPU=NONE")
    print("CAPACITY_REPLACEMENT_KERNEL_FILES=", sorted(x.name for x in out.iterdir()))


if __name__ == "__main__":
    main()
