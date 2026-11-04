#!/usr/bin/env python3
"""Render the frozen, private CPU-only no-op screen for capacity replacements.

Uses only metadata IDs from the already completed private gold-control run.
Competition task text and patches hydrate inside private Kaggle CPU runtime.
No LLM, adapter, GPU, leaderboard run, or task text in the public repository.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import render_capacity_replacement_gold_v0 as gold_renderer

GOLD_FILE = "docs/evaluation/capacity-v0-replacement-gold-2026-11-04.json"
GOLD_RUN = 41803516800
GOLD_ARTIFACT = 13308702997
GOLD_ARTIFACT_SHA256 = "944b8acaac1e5f349f81bb0c941348dbc7c5694a57a48ce0ea843023a416711b"
EXPECTED_GOLD_ROWS = 16
EXPECTED_GOLD_PASS = 10
VERSION = "capacity-v0-replacement-noop-screen-v1"
RESULT_FILENAME = "capacity_replacement_noop_screen.json"
SOURCE_FILENAME = "capacity_replacement_noop_screen.py"


def get_gold_pass_items(root: Path, override: Path | None = None) -> list[dict[str, str]]:
    manifest = gold_renderer.create_manifest(root)
    expected = manifest["holdout"]
    if len(expected) != EXPECTED_GOLD_ROWS:
        raise ValueError("replacement manifest count drift")
    data = json.loads((override or (root / GOLD_FILE)).read_text(encoding="utf-8"))
    if (
        data.get("version") != "capacity-v0-replacement-gold-eligibility"
        or data.get("source_run_id") != GOLD_RUN
        or data.get("artifact_id") != GOLD_ARTIFACT
        or data.get("artifact_zip_sha256") != GOLD_ARTIFACT_SHA256
        or data.get("source_selector_sha256") != manifest["selector_sha256"]
        or data.get("screened") != EXPECTED_GOLD_ROWS
        or data.get("gold_pass_count") != EXPECTED_GOLD_PASS
        or data.get("contains_raw_patch_or_task_text") is not False
    ):
        raise ValueError("gold-screen provenance/status mismatch")

    rows = data.get("results")
    if not isinstance(rows, list) or len(rows) != EXPECTED_GOLD_ROWS:
        raise ValueError("gold-screen results count mismatch")
    if [(r.get("instance_id"), r.get("repo")) for r in rows] != [
        (x["instance_id"], x["repo"]) for x in expected
    ]:
        raise ValueError("gold-screen ordered candidate metadata drift")
    for row in rows:
        code = row.get("test_exit_code")
        passed = (
            row.get("status") == "completed"
            and type(code) is int and code == 0
            and row.get("error_type") is None
        )
        if row.get("gold_pass") is not passed:
            raise ValueError("inconsistent gold verification row")
    chosen = [
        {"instance_id": row["instance_id"], "repo": row["repo"]}
        for row in rows if row["gold_pass"] is True
    ]
    if len(chosen) != EXPECTED_GOLD_PASS or len({x["instance_id"] for x in chosen}) != EXPECTED_GOLD_PASS:
        raise ValueError("gold-pass selection count/uniqueness mismatch")
    return chosen


def render(root: Path, out: Path, kernel_ref: str) -> Path:
    if not kernel_ref.startswith("kolihhan/"):
        raise ValueError("private Kaggle kernel owner changed")
    if out.exists() and any(out.iterdir()):
        raise ValueError("refuse to overwrite prior kernel output")
    items = get_gold_pass_items(root)
    template = (root / "kaggle" / "topology_noop_screen.py").read_text(encoding="utf-8")
    tasks_expr = re.compile(r"(?s)TASKS = \[\n.*?\n\]\n\n")
    if len(tasks_expr.findall(template)) != 1:
        raise ValueError("no-op upstream task list template drift")
    task_text = ",\n".join(
        f"    ({item['instance_id']!r}, {item['repo']!r})" for item in items
    )
    source = tasks_expr.sub(lambda _: f"TASKS = [\n{task_text},\n]\n\n", template, count=1)
    changes = (
        ("topology-ab-noop-screen-v1", VERSION),
        ("topology_noop_screen.json", RESULT_FILENAME),
        ("TOPOLOGY_NOOP_SUMMARY", "CAPACITY_REPLACEMENT_NOOP_SUMMARY"),
        ("if len(ids) != 19 or len(set(ids)) != 19:",
         f"if len(ids) != {EXPECTED_GOLD_PASS} or len(set(ids)) != {EXPECTED_GOLD_PASS}:"),
        ("topology screen must contain exactly 19 unique tasks",
         f"capacity replacement screen must contain exactly {EXPECTED_GOLD_PASS} unique tasks"),
        ("'requested': 19", f"'requested': {EXPECTED_GOLD_PASS}"),
        ("/19] noop", f"/{EXPECTED_GOLD_PASS}] noop"),
    )
    for before, after in changes:
        if source.count(before) != 1:
            raise ValueError(f"no-op upstream token count drift: {before!r}")
        source = source.replace(before, after)
    compile(source, SOURCE_FILENAME, "exec")
    out.mkdir(parents=True, exist_ok=True)
    (out / SOURCE_FILENAME).write_text(source, encoding="utf-8")
    meta = {
        "id": kernel_ref,
        "title": kernel_ref.split("/", 1)[1],
        "code_file": SOURCE_FILENAME,
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--kernel-ref", required=True)
    args = parser.parse_args()
    out = render(args.repo.resolve(), args.out.resolve(), args.kernel_ref)
    print("CAPACITY_REPLACEMENT_NOOP_RENDER=PASS")
    print("CAPACITY_REPLACEMENT_NOOP_TASKS=", EXPECTED_GOLD_PASS)
    print("CAPACITY_REPLACEMENT_NOOP_GPU=NONE")
    print("CAPACITY_REPLACEMENT_NOOP_FILES=", sorted(x.name for x in out.iterdir()))


if __name__ == "__main__":
    main()
