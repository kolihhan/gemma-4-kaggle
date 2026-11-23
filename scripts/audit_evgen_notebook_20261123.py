"""Read-only provenance audit of a downloaded PUBLIC Kaggle notebook.

Never executes notebook cells. Reports only derived counts/flags and short headings,
not its source, code, outputs or any competition/private task material.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

HEADING = re.compile(r"^\s*(#{1,6})\s+(.+?)\s*$")
SECTION11 = re.compile(r"\b11\s*[.)-]?\s*what\s+i\s+want\s+to\s+investigate\s+next\b", re.I)
TERMS = {
    "read_file": r"\bread_file\b",
    "150_line_limit": r"(?:(?:150|one\s+hundred\s+fifty)\s*(?:lines?|line\s+limit))|(?:lines?\s*(?:limit|maximum|cap)[^\n]{0,30}150)",
    "second_attempt": r"(?:second\s+(?:attempt|try|repair)|2nd\s+(?:attempt|try))",
    "zero_of_ten": r"(?:0\s*/\s*10|zero\s+(?:out\s+of\s+)?ten)",
    "context": r"\b(?:context|truncate|truncation|coverage)\b",
    "verification": r"\b(?:verify|verification|test|pytest)\b",
    "retry": r"\b(?:retry|retries|repair|second\s+pass)\b",
    "budget": r"\b(?:budget|time\s+limit|tool\s+calls?|wall\s+time)\b",
    "localization": r"\b(?:localization|locate|navigation|search)\b",
}
def to_text(source):
    if isinstance(source, list):
        return "".join(source)
    return source if isinstance(source, str) else ""

def read_notebook(root: Path):
    paths = sorted(root.rglob("*.ipynb"))
    if len(paths) == 1:
        doc = json.loads(paths[0].read_text(encoding="utf-8"))
        cells = doc.get("cells", [])
        if not isinstance(cells, list):
            raise ValueError("invalid_cells")
        return [(c.get("cell_type", "unknown"), to_text(c.get("source", ""))) for c in cells], paths[0].name
    if len(paths) > 1:
        raise ValueError("ambiguous_notebook_sources")
    py = [p for p in root.rglob("*.py") if p.name != "__init__.py"]
    if len(py) != 1:
        raise ValueError("expected_one_downloaded_notebook_source")
    return [("script", py[0].read_text(encoding="utf-8"))], py[0].name

def analyze(cells, filename):
    headings = []
    section_parts = []
    inside = False
    section_level = None
    all_parts = []
    for kind, source in cells:
        all_parts.append(source)
        # Python cells are retained for term counts but are not interpreted as
        # markdown headings, so code comments cannot spoof the Section 11 title.
        if kind not in {"markdown", "raw", "script"}:
            if inside:
                section_parts.append(source)
            continue
        for line in source.splitlines():
            match = HEADING.match(line)
            if match:
                level, title = len(match.group(1)), match.group(2).strip()
                headings.append({"level": level, "title": title[:130]})
                if SECTION11.search(title):
                    inside, section_level = True, level
                elif inside and level <= section_level:
                    inside = False
            elif SECTION11.search(line) and not inside:
                # Tolerate a numbered plain-text heading in Kaggle's export.
                inside, section_level = True, 2
            if inside:
                section_parts.append(line)
    full_text = "\n".join(all_parts)
    section_text = "\n".join(section_parts)
    def hits(text):
        return {key: len(re.findall(pattern, text, re.I)) for key, pattern in TERMS.items()}
    return {
        "source": "public Kaggle notebook code pull, latest version only",
        "filename": filename,
        "cell_count": len(cells),
        "section11_found": bool(section_text),
        "section11_chars": len(section_text),
        "section11_line_previews": [
            re.sub(r"\\s+", " ", line).strip()[:180]
            for line in section_text.splitlines() if line.strip()
        ][:40],
        "heading_titles": [h["title"] for h in headings[:35]],
        "all_topic_hits": hits(full_text),
        "section11_topic_hits": hits(section_text),
        "no_notebook_execution": True,
        "is_notebook_v41_proven": False,
        "warning": "Latest source cannot be asserted identical to historical V41 without pinned version retrieval.",
    }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cells, name = read_notebook(args.input)
    summary = analyze(cells, name)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print("EVGEN_PUBLIC_NOTEBOOK_READONLY_AUDIT=" + json.dumps(summary, ensure_ascii=False, sort_keys=True))

if __name__ == "__main__":
    main()
