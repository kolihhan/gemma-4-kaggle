#!/usr/bin/env python3
"""Analyze the public Gemma 4 development task corpus.

This tool intentionally uses only the Python standard library so it can run in
CI and on a fresh clone without extra dependencies.
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable


def diff_stats(patch: str | None) -> dict[str, int]:
    """Return changed-file and +/- line counts for a unified git diff."""
    text = patch or ""
    files = 0
    additions = 0
    deletions = 0

    for line in text.splitlines():
        if line.startswith("diff --git "):
            files += 1
        elif line.startswith("+") and not line.startswith("+++"):
            additions += 1
        elif line.startswith("-") and not line.startswith("---"):
            deletions += 1

    return {
        "files": files,
        "additions": additions,
        "deletions": deletions,
        "lines": additions + deletions,
    }


def _line_bucket(lines: int) -> str:
    if lines == 0:
        return "0"
    if lines <= 10:
        return "1-10"
    if lines <= 30:
        return "11-30"
    if lines <= 80:
        return "31-80"
    return "81+"


def summarize_tasks(tasks: Iterable[dict]) -> dict:
    """Summarize repository mix, hints, reference-patch size, and date range."""
    items = list(tasks)
    repos = Counter(item.get("repo") or "UNKNOWN" for item in items)
    patch_buckets = Counter()
    problem_lengths: list[int] = []
    dates: list[str] = []
    hints = 0

    for item in items:
        if (item.get("hints_text") or "").strip():
            hints += 1
        patch_buckets[_line_bucket(diff_stats(item.get("patch"))["lines"])] += 1
        problem_lengths.append(len(item.get("problem_statement") or ""))
        if item.get("created_at"):
            dates.append(str(item["created_at"]))

    bucket_order = ("0", "1-10", "11-30", "31-80", "81+")
    return {
        "task_count": len(items),
        "repos": dict(sorted(repos.items())),
        "tasks_with_hints": hints,
        "solution_patch_lines": {key: patch_buckets.get(key, 0) for key in bucket_order},
        "problem_statement_chars": {
            "median": int(statistics.median(problem_lengths)) if problem_lengths else 0,
            "max": max(problem_lengths, default=0),
        },
        "created_at": {
            "min": min(dates) if dates else None,
            "max": max(dates) if dates else None,
        },
    }


def choose_sample(tasks: Iterable[dict], per_repo: int = 3) -> list[dict]:
    """Choose a deterministic low/medium/high patch-size sample per repository."""
    if per_repo <= 0:
        return []

    grouped: dict[str, list[dict]] = defaultdict(list)
    for item in tasks:
        grouped[item.get("repo") or "UNKNOWN"].append(item)

    selected: list[dict] = []
    for repo in sorted(grouped):
        ordered = sorted(
            grouped[repo],
            key=lambda item: (
                diff_stats(item.get("patch"))["lines"],
                item.get("instance_id") or "",
            ),
        )
        if len(ordered) <= per_repo:
            chosen = ordered
        elif per_repo == 1:
            chosen = [ordered[len(ordered) // 2]]
        else:
            indexes = [round(i * (len(ordered) - 1) / (per_repo - 1)) for i in range(per_repo)]
            chosen = []
            seen: set[int] = set()
            for index in indexes:
                if index not in seen:
                    chosen.append(ordered[index])
                    seen.add(index)
            if len(chosen) < per_repo:
                for index, item in enumerate(ordered):
                    if index not in seen:
                        chosen.append(item)
                        seen.add(index)
                    if len(chosen) == per_repo:
                        break
        selected.extend(chosen)

    return selected


def load_jsonl(path: Path) -> list[dict]:
    tasks: list[dict] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, 1):
            line = raw.strip()
            if not line:
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON on line {line_number}: {exc}") from exc
            if not isinstance(value, dict):
                raise ValueError(f"line {line_number} is not a JSON object")
            tasks.append(value)
    return tasks


def _summary_markdown(summary: dict, sample: list[dict]) -> str:
    lines = [
        "# Public task corpus summary",
        "",
        f"- Tasks: **{summary['task_count']}**",
        f"- Tasks with hints: **{summary['tasks_with_hints']}**",
        f"- Median problem-statement chars: **{summary['problem_statement_chars']['median']}**",
        "",
        "## Repository mix",
        "",
    ]
    lines.extend(f"- `{repo}`: {count}" for repo, count in summary["repos"].items())
    lines.extend(["", "## Reference patch changed-line buckets", ""])
    lines.extend(f"- `{bucket}`: {count}" for bucket, count in summary["solution_patch_lines"].items())
    lines.extend(["", "## Deterministic baseline sample", ""])
    for item in sample:
        stats = diff_stats(item.get("patch"))
        lines.append(
            f"- `{item.get('instance_id')}` — `{item.get('repo')}` — reference patch {stats['lines']} changed lines"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tasks", nargs="?", type=Path, default=Path("tasks.jsonl"))
    parser.add_argument("--per-repo", type=int, default=3)
    parser.add_argument("--summary-json", type=Path)
    parser.add_argument("--summary-md", type=Path)
    parser.add_argument("--sample-json", type=Path)
    args = parser.parse_args()

    tasks = load_jsonl(args.tasks)
    summary = summarize_tasks(tasks)
    sample = choose_sample(tasks, per_repo=args.per_repo)
    payload = {"summary": summary, "sample_instance_ids": [item.get("instance_id") for item in sample]}

    if args.summary_json:
        args.summary_json.parent.mkdir(parents=True, exist_ok=True)
        args.summary_json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    if args.summary_md:
        args.summary_md.parent.mkdir(parents=True, exist_ok=True)
        args.summary_md.write_text(_summary_markdown(summary, sample), encoding="utf-8")
    if args.sample_json:
        args.sample_json.parent.mkdir(parents=True, exist_ok=True)
        args.sample_json.write_text(json.dumps(sample, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
