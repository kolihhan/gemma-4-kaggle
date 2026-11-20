"""Opt-in CPU evidence via the existing run_command tool; no new ADK tool required."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from scripts.first_search_function_retriever import retrieve


def evidence(issue: str, root: Path) -> dict:
    if not issue.strip() or len(issue) > 12000:
        raise ValueError("issue length outside 1..12000")
    snippets = retrieve(issue, root, limit=3, max_files=250, max_bytes=120000)
    return {
        "kind": "first_search_production_evidence_v1",
        "spans": [{"path": s["path"], "line": s["line"],
                   "symbol": s["symbol"], "snippet": s["snippet"][:1600]}
                  for s in snippets],
        "count": len(snippets),
        "fallback_to_original_search": not bool(snippets),
    }


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--root", required=True, type=Path)
    p.add_argument("--issue-file", required=True, type=Path)
    args = p.parse_args(argv)
    issue_file = args.issue_file
    if issue_file.is_symlink() or not issue_file.is_file() or issue_file.stat().st_size > 12000:
        p.error("invalid issue file")
    try:
        result = evidence(issue_file.read_text(encoding="utf-8"), args.root)
    except (ValueError, OSError, UnicodeError) as exc:
        p.error(str(exc))
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))


if __name__ == "__main__":
    main()
