"""Read-only excerpts of the PUBLIC author's Notebook for source comparison.

Does not execute notebook cells, print code, or inspect private competition data.
"""
from __future__ import annotations
import argparse
import html
import json
import re
from pathlib import Path

HEADING = re.compile(r"^\s*(#{1,6})\s+(.+?)\s*$")
SECTION_MATCH = re.compile(
    r"(reading room|challenge|research assets|agent architecture|"
    r"repair loop|public submission timeline|new milestone|"
    r"most interesting question|agent package|validation|"
    r"controlled comparison|third batch|evidence does|"
    r"prompt lab|why this particular|research roadmap|"
    r"what i want to investigate|three experiments)",
    re.I,
)
def clean(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
    s = re.sub(r"[*_#]{1,3}", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    args = p.parse_args()
    paths = list(args.root.rglob("*.ipynb"))
    if len(paths) != 1:
        raise ValueError("expected exactly one downloaded public notebook")
    doc = json.loads(paths[0].read_text(encoding="utf-8"))
    sections = []
    last = None
    for cell in doc.get("cells", []):
        if cell.get("cell_type") != "markdown":
            continue
        src = cell.get("source", "")
        if isinstance(src, list):
            src = "".join(src)
        for line in src.splitlines():
            found = HEADING.match(line)
            if found:
                title = clean(found.group(2))
                level = len(found.group(1))
                if SECTION_MATCH.search(title):
                    last = {"heading": title[:110], "level": level, "text": []}
                    sections.append(last)
                elif last is not None and level <= last["level"]:
                    last = None
                continue
            if last is not None and line.strip() and not line.lstrip().startswith(("<div", "</div", "<span", "</span", "<a ", "</a")):
                last["text"].append(line)
    summary = []
    for s in sections:
        prose = clean(" ".join(s["text"]))
        summary.append({"heading": s["heading"],"preview": prose[:1550],"section_chars":len(prose)})
    print("EVGEN_SOURCE_SECTION_COMPARISON=" + json.dumps(summary, ensure_ascii=False, sort_keys=True))
    print("PUBLIC_NOTEBOOK_MARKDOWN_ONLY_NO_CODE_EXECUTION=true")

if __name__ == "__main__":
    main()
