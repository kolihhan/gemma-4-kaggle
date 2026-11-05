#!/usr/bin/env python3
"""Render private Kaggle CPU no-op control from *sanitized* gold eligibility flags.

The model is never loaded. Gold data is never embedded in the kernel; only IDs
of gold-passing tasks. Source gold run ID is pinned to avoid misattribution.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from scripts.discriminating_evidence_exploratory import ROOT, build_exploratory
from scripts.render_discriminating_evidence_gold import D_IMAGE

GOLD_RUN_ID = 42066105011
GOLD_VERSION = "discriminating-evidence-v0-exploratory-gold-screen"
NOOP_VERSION = "discriminating-evidence-v0-noop-screen-v1"


def load_gold_pass_items(root: Path, source: Path) -> list[dict[str, str]]:
    proposal = build_exploratory(root)
    expected_ids = (proposal["pilot_ids"] + proposal["exploratory_ids"]
                    + proposal["replacement_ids"])
    data = json.loads(source.read_text(encoding="utf-8"))
    if (data.get("version") != GOLD_VERSION or
        data.get("source_run_id") != GOLD_RUN_ID or
        data.get("source_selector_sha256") != proposal["selection_digest_sha256"] or
        data.get("contains_raw_patch_or_task_text") is not False or
        data.get("certifies_blind") is not False or
        data.get("model_evaluation_executed") is not False):
        raise ValueError("gold metadata provenance or scope mismatch")
    rows = data.get("results")
    if (not isinstance(rows, list) or len(rows) != 30 or
        data.get("screened") != 30 or
        [x.get("instance_id") for x in rows] != expected_ids):
        raise ValueError("gold records do not match frozen selection")
    passing = []
    for rec in rows:
        iid = rec["instance_id"]
        repo = "Textualize/rich" if iid.startswith("rich_") else "fastapi/fastapi"
        if rec.get("repo") != repo or rec.get("gold_pass") not in (True, False):
            raise ValueError("invalid gold record")
        if rec["gold_pass"]:
            if rec.get("status") != "completed" or rec.get("test_exit_code") != 0:
                raise ValueError("gold_pass flag conflicts with actual exit status")
            passing.append({"instance_id": iid, "repo": repo})
    if len(passing) != data.get("gold_pass_count"):
        raise ValueError("gold pass count mismatch")
    if not passing:
        raise ValueError("no gold-eligible records; no-op not meaningful")
    return passing


def render(root: Path, out: Path, kernel_ref: str, gold_metadata: Path) -> Path:
    if not re.fullmatch(r"kolihhan/[a-z0-9-]+", kernel_ref):
        raise ValueError("invalid private Kaggle kernel owner/slug")
    if out.exists() and any(out.iterdir()):
        raise ValueError("refusing to overwrite no-op kernel")
    items = load_gold_pass_items(root, gold_metadata)
    n = len(items)
    source = (root / "kaggle/topology_noop_screen.py").read_text(encoding="utf-8")
    tasks_regex = re.compile(r"(?s)TASKS = \[\n.*?\n\]\n\n")
    if len(tasks_regex.findall(source)) != 1:
        raise ValueError("official no-op source tasklist shape changed")
    task_lines = ",\n".join(
        f"    ({it['instance_id']!r}, {it['repo']!r})" for it in items
    )
    source = tasks_regex.sub(lambda _: f"TASKS = [\n{task_lines},\n]\n\n",
                             source, count=1)
    substitutions = {
        "topology-ab-noop-screen-v1": NOOP_VERSION,
        "topology_noop_screen.json": "evidence_noop_screen.json",
        "TOPOLOGY_NOOP_SUMMARY": "EVIDENCE_NOOP_SUMMARY",
        "if len(ids) != 19 or len(set(ids)) != 19:": (
            f"if len(ids) != {n} or len(set(ids)) != {n}:"
        ),
        "topology screen must contain exactly 19 unique tasks": (
            f"evidence screen must contain exactly {n} unique tasks"
        ),
        "'requested': 19": f"'requested': {n}",
        "/19] noop": f"/{n}] noop",
    }
    for old, new in substitutions.items():
        if old not in source:
            raise ValueError(f"upstream no-op template changed: {old}")
        source = source.replace(old, new)
    compile(source, "evidence_noop_screen.py", "exec")
    out.mkdir(parents=True, exist_ok=True)
    (out / "evidence_noop_screen.py").write_text(source, encoding="utf-8")
    meta = {
        "id": kernel_ref, "title": kernel_ref.split("/", 1)[1],
        "code_file": "evidence_noop_screen.py",
        "language": "python", "kernel_type": "script",
        "is_private": True, "enable_gpu": False,
        "enable_tpu": False, "enable_internet": False,
        "docker_image": D_IMAGE,
        "dataset_sources": ["metric/gemma-4-developer-agent-wheelhouse"],
        "competition_sources": ["gemma-4-developer-agent"],
        "model_sources": [], "kernel_sources": [],
    }
    (out / "kernel-metadata.json").write_text(
        json.dumps(meta, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return out


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, default=ROOT)
    p.add_argument("--gold-metadata", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--kernel-ref", required=True)
    args = p.parse_args()
    out = render(args.repo.resolve(), args.out.resolve(),
                 args.kernel_ref, args.gold_metadata.resolve())
    print("EVIDENCE_NOOP_CPU_RENDER=PASS")
    print("NOOP_ONLY_MODEL_GPU_TRAINING_SUBMISSION=FALSE")
    print("NOOP_FILES=", sorted(p.name for p in out.iterdir()))


if __name__ == "__main__":
    main()
