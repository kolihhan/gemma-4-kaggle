#!/usr/bin/env python3
"""Render a private, CPU-only official gold-reference eligibility kernel.

No LLM, no Kaggle GPU, no public task-data mirrors, and no new submission.
Only frozen metadata cohort IDs are embedded; task text/patches hydrate
privately inside the official Kaggle competition mount at runtime.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise FileNotFoundError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def create_gold_manifest(repo: Path) -> dict:
    preflight = load_module(repo / "scripts/capacity_preflight_v0.py", "capacity_preflight")
    cohort = preflight.build_feasibility_manifest(repo)
    preflight.audit_candidate_text_mentions(repo, cohort)
    items = []
    for instance_id in cohort["feasibility_ids"] + cohort["confirmation_reserve_ids"]:
        if instance_id.startswith("rich_"):
            source_repo = "Textualize/rich"
        elif instance_id.startswith("fastapi_"):
            source_repo = "fastapi/fastapi"
        else:
            raise ValueError(f"unsupported prospective repository: {instance_id}")
        items.append({
            "instance_id": instance_id,
            "repo": source_repo,
            "patch_bucket": "metadata-only",
        })
    if len(items) != 16 or len({x["instance_id"] for x in items}) != 16:
        raise ValueError("capacity source candidate manifest is not the frozen 16")
    return {
        "version": "verifier-lora-v0",
        "experiment": "capacity-v0-model-free-eligibility-only",
        "selector_sha256": cohort["selection_digest_sha256"],
        "holdout": items,
    }


def render(repo: Path, out: Path, kernel_ref: str) -> Path:
    if not kernel_ref.startswith("kolihhan/"):
        raise ValueError("private kernel must have the correct Kaggle owner")
    if out.exists() and any(out.iterdir()):
        raise ValueError("refuse to overwrite an existing rendered kernel")
    out.mkdir(parents=True, exist_ok=True)
    manifest = create_gold_manifest(repo)
    source_path = repo / "kaggle" / "gold_control_sweep.py"
    module = load_module(source_path, "gold_control_reuse")
    source = module.render_kernel_source(
        source_path.read_text(encoding="utf-8"),
        json.dumps(manifest, sort_keys=True, separators=(",", ":")),
    )
    compile(source, "gold_control_sweep.py", "exec")
    (out / "gold_control_sweep.py").write_text(source, encoding="utf-8")
    metadata = {
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
        json.dumps(metadata, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--kernel-ref", type=str, required=True)
    args = parser.parse_args()
    out = render(args.repo.resolve(), args.out.resolve(), args.kernel_ref)
    print("CAPACITY_GOLD_RENDER=PASS")
    print("CAPACITY_GOLD_KERNEL_FILES=", sorted(p.name for p in out.iterdir()))
    print("CAPACITY_GOLD_GPU=FALSE")


if __name__ == "__main__":
    main()
