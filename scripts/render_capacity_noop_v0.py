#!/usr/bin/env python3
"""Private CPU-only no-op verification on preregistered gold-passing tasks.

No candidate issue text, reference patches, model inference or GPU usage.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
from pathlib import Path


GOLD_METADATA = "docs/evaluation/capacity-v0-gold-screen-2026-11-04.json"
GOLD_SELECTOR = "4abe73d79afcabd64795e7f2eedde5682732a85290f07a09e3f8a181594fd593"
EXPECTED_GOLD_SCREEN = 16
EXPECTED_GOLD_PASS = 10


def import_path(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise FileNotFoundError(path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_gold_metadata(repo: Path, override: Path | None = None) -> dict:
    original_path = repo / GOLD_METADATA
    if not original_path.is_file() and override is None:
        raise FileNotFoundError(original_path)
    data = json.loads((override or original_path).read_text(encoding="utf-8"))
    if data.get("source_selector_sha256") != GOLD_SELECTOR:
        raise ValueError("gold selector SHA drift")
    rows = data.get("results")
    if not isinstance(rows, list) or len(rows) != EXPECTED_GOLD_SCREEN:
        raise ValueError("gold metadata rows incomplete")
    ids = [v.get("instance_id") for v in rows]
    if len(set(ids)) != EXPECTED_GOLD_SCREEN:
        raise ValueError("duplicate gold metadata IDs")
    passing = [v for v in rows if v.get("gold_pass") is True and v.get("test_exit_code") == 0]
    if len(passing) != EXPECTED_GOLD_PASS or data.get("gold_pass_count") != EXPECTED_GOLD_PASS:
        raise ValueError("gold pass count mismatch")
    if any(v.get("gold_pass") is True and v.get("test_exit_code") != 0 for v in rows):
        raise ValueError("gold metadata inconsistent with verification status")
    return data


def get_gold_pass_items(repo: Path) -> list[dict[str, str]]:
    data = load_gold_metadata(repo)
    # The same frozen selector order is retained for all eligibility comparisons.
    preflight = import_path(
        repo / "scripts" / "capacity_preflight_v0.py", "capacity_preflight"
    )
    selector = preflight.build_feasibility_manifest(repo)
    if selector["selection_digest_sha256"] != GOLD_SELECTOR:
        raise ValueError("capacity selector drift")
    ids = selector["feasibility_ids"] + selector["confirmation_reserve_ids"]
    rows = data["results"]
    if ids != [v["instance_id"] for v in rows]:
        raise ValueError("gold metadata does not match frozen selector order")
    return [
        {"instance_id": v["instance_id"], "repo": v["repo"]}
        for v in rows if v["gold_pass"]
    ]


def render(repo: Path, out: Path, kernel_ref: str) -> Path:
    if not kernel_ref.startswith("kolihhan/"):
        raise ValueError("unexpected Kaggle owner")
    items = get_gold_pass_items(repo)
    if out.exists() and any(out.iterdir()):
        raise ValueError("refuse to overwrite no-op kernel output")
    out.mkdir(parents=True, exist_ok=True)
    template = (repo / "kaggle" / "topology_noop_screen.py").read_text(encoding="utf-8")

    target = re.compile(r"(?s)TASKS = \[\n.*?\n\]\n\n")
    if len(target.findall(template)) != 1:
        raise ValueError("upstream no-op template tasklist shape changed")
    task_lines = ",\n".join(
        f"    ({item['instance_id']!r}, {item['repo']!r})" for item in items
    )
    source = target.sub(lambda _: f"TASKS = [\n{task_lines},\n]\n\n", template, count=1)
    replacements = {
        "topology-ab-noop-screen-v1": "capacity-v0-noop-screen-v1",
        "topology_noop_screen.json": "capacity_noop_screen.json",
        "TOPOLOGY_NOOP_SUMMARY": "CAPACITY_NOOP_SUMMARY",
        "if len(ids) != 19 or len(set(ids)) != 19:": (
            f"if len(ids) != {EXPECTED_GOLD_PASS} or len(set(ids)) != {EXPECTED_GOLD_PASS}:"
        ),
        "topology screen must contain exactly 19 unique tasks": (
            "capacity screen must contain exactly 10 gold-passing tasks"
        ),
        "'requested': 19": "'requested': 10",
        "/19] noop": "/10] noop",
        "f'[{index:02d}/19] noop": "f'[{index:02d}/10] noop",
        "[{index:02d}/19] noop": "[{index:02d}/10] noop",
    }
    for old, new in replacements.items():
        if old not in source:
            if old in ("f'[{index:02d}/19] noop",):
                continue
            raise ValueError(f"upstream no-op template drift: {old}")
        source = source.replace(old, new)
    compile(source, "capacity_noop_screen.py", "exec")
    (out / "capacity_noop_screen.py").write_text(source, encoding="utf-8")
    meta = {
        "id": kernel_ref,
        "title": kernel_ref.split("/", 1)[1],
        "code_file": "capacity_noop_screen.py",
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
    parser.add_argument("--kernel-ref", type=str, required=True)
    args = parser.parse_args()
    out = render(args.repo.resolve(), args.out.resolve(), args.kernel_ref)
    print("CAPACITY_NOOP_RENDER=PASS")
    print("CAPACITY_NOOP_TASK_COUNT=", EXPECTED_GOLD_PASS)
    print("CAPACITY_NOOP_GPU=FALSE")
    print("CAPACITY_NOOP_FILES=", sorted(p.name for p in out.iterdir()))


if __name__ == "__main__":
    main()
