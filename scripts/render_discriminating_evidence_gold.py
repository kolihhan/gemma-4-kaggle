#!/usr/bin/env python3
"""Private, CPU-only gold-control screening for all 30 *preselected* IDs.

Only IDs and repository names go into a private Kaggle kernel. The private
competition mount supplies reference patches at execution time; GitHub sees
only vetted gold-pass/test-exit-code metadata after sanitization. NO model/GPU.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from scripts.discriminating_evidence_exploratory import ROOT, build_exploratory
from scripts.render_capacity_gold_v0 import load_module

FROZEN_SELECTION = (
    "docs/evaluation/discriminating-evidence-v0-exploratory-selection-2026-11-06.json"
)
GOLD_TEMPLATE = "kaggle/gold_control_sweep.py"
D_IMAGE = "gcr.io/kaggle-private-byod/python@sha256:37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461"


def build_gold_manifest(root: Path) -> dict:
    proposed = build_exploratory(root)
    committed = json.loads((root / FROZEN_SELECTION).read_text(encoding="utf-8"))
    for key in ("version", "pilot_ids", "exploratory_ids", "replacement_ids",
                "selection_digest_sha256", "candidate_counts", "replacement_counts"):
        if proposed[key] != committed[key]:
            raise ValueError(f"frozen prospective list changed: {key}")
    if proposed["status"] != "NO_GO_HISTORY_AND_ELIGIBILITY_UNCHECKED":
        raise ValueError("unexpected provisional selection status")
    ids = (committed["pilot_ids"] + committed["exploratory_ids"]
           + committed["replacement_ids"])
    if len(ids) != 30 or len(set(ids)) != 30:
        raise ValueError("bad 30-ID gold prospective list")
    items = []
    for iid in ids:
        if re.fullmatch(r"rich_\d+", iid):
            repo = "Textualize/rich"
        elif re.fullmatch(r"fastapi_\d+", iid):
            repo = "fastapi/fastapi"
        else:
            raise ValueError("unexpected ID prefix")
        items.append({"instance_id": iid, "repo": repo,
                      "patch_bucket": "metadata-only"})
    return {
        "version": "verifier-lora-v0",
        "experiment": "discriminating-evidence-v0-exploratory-gold-cpu-only",
        "selector_sha256": proposed["selection_digest_sha256"],
        "holdout": items,
    }


def render(root: Path, out: Path, kernel_ref: str) -> Path:
    if not re.fullmatch(r"kolihhan/[a-z0-9-]+", kernel_ref):
        raise ValueError("private Kaggle kernel owner/slug invalid")
    if out.exists() and any(out.iterdir()):
        raise ValueError("refuse to overwrite preexisting private kernel")
    manifest = build_gold_manifest(root)
    template_path = root / GOLD_TEMPLATE
    runtime = load_module(template_path, "evidence_gold_runtime")
    code = runtime.render_kernel_source(
        template_path.read_text(encoding="utf-8"),
        json.dumps(manifest, sort_keys=True, separators=(",", ":")),
    )
    compile(code, "gold_control_sweep.py", "exec")
    out.mkdir(parents=True, exist_ok=True)
    (out / "gold_control_sweep.py").write_text(code, encoding="utf-8")
    meta = {
        "id": kernel_ref, "title": kernel_ref.split("/", 1)[1],
        "code_file": "gold_control_sweep.py",
        "language": "python", "kernel_type": "script",
        "is_private": True, "enable_gpu": False, "enable_tpu": False,
        "enable_internet": False, "docker_image": D_IMAGE,
        "dataset_sources": ["metric/gemma-4-developer-agent-wheelhouse"],
        "competition_sources": ["gemma-4-developer-agent"],
        "model_sources": [], "kernel_sources": [],
    }
    (out / "kernel-metadata.json").write_text(
        json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return out


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, default=ROOT)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--kernel-ref", required=True)
    args = p.parse_args()
    render(args.repo.resolve(), args.out.resolve(), args.kernel_ref)
    print("EVIDENCE_GOLD_CPU_RENDER=PASS")
    print("EVIDENCE_GOLD_MODEL_INFERENCE=NO")
    print("EVIDENCE_GOLD_CONTEST_SUBMISSION=NO")


if __name__ == "__main__":
    main()
