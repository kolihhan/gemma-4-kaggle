"""Read-only AST + git diff semantic-impact navigator for a coding agent.

Surfaces are *lexical clues*, not a specification, test or correctness oracle.
No model calls, dependencies, file writes, or reference patch access.
"""
from __future__ import annotations

import argparse
import ast
from collections import defaultdict
import json
from pathlib import Path
import re
import subprocess

MAX_FILES = 350
MAX_BYTES = 350_000
MAX_SYMBOLS = 8
MAX_REFERENCES = 8


def command(root: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(root), *args],
                            capture_output=True, text=True, timeout=7, check=True)
    if len(result.stdout) > 450_000:
        raise ValueError("diff too large")
    return result.stdout


def diff_spans(root: Path) -> dict[str, set[int]]:
    diff = command(root, "diff", "--no-ext-diff", "--unified=0", "HEAD", "--", "*.py")
    out = defaultdict(set)
    file = None
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            file = line[6:]
        elif line.startswith("@@ ") and file and file.endswith(".py"):
            match = re.match(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", line)
            if match:
                start = int(match.group(1))
                count = int(match.group(2)) if match.group(2) is not None else 1
                out[file].update(range(start, start + max(1, min(count, 150))))
    return out


def scan(root: Path) -> dict:
    root = root.resolve()
    if not (root / ".git").exists():
        raise ValueError("requires repository checkout")
    spans = diff_spans(root)
    if not spans:
        return {"status": "no_python_source_change", "symbols": [],
                "semantic_correctness_verified": False}
    paths = []
    for path in root.rglob("*.py"):
        rel = path.relative_to(root).as_posix()
        if (any(p in {".git", ".venv", "venv", "node_modules", "__pycache__"}
                for p in path.relative_to(root).parts)
                or not path.is_file() or path.stat().st_size > MAX_BYTES):
            continue
        paths.append((rel, path))
        if len(paths) >= MAX_FILES:
            break
    if len(paths) >= MAX_FILES:
        # A partial tree may miss a related entrypoint: fail closed.
        return {"status": "repository_scan_limit", "symbols": [],
                "semantic_correctness_verified": False}
    source = {}
    for rel, path in paths:
        try:
            source[rel] = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
    symbols = []
    for rel, lines in sorted(spans.items()):
        if rel not in source:
            continue
        try:
            tree = ast.parse(source[rel])
        except SyntaxError:
            continue
        nodes = []
        def visit(node, parents):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = ".".join(parents + [node.name])
                nodes.append((node, name, len(parents)))
                parents = parents + [node.name]
            for child in ast.iter_child_nodes(node):
                visit(child, parents)
        visit(tree, [])
        for line in sorted(lines):
            hits = [(n, name, depth) for n, name, depth in nodes
                    if n.lineno <= line <= n.end_lineno]
            if not hits:
                continue
            node, qualified, _ = max(hits, key=lambda x: x[2])
            name = qualified.split(".")[-1]
            if not re.match(r"^[A-Za-z_]\w*$", name):
                continue
            key = (rel, qualified)
            if key not in {(s["path"], s["symbol"]) for s in symbols}:
                symbols.append({"path": rel, "symbol": qualified,
                                "kind": "class" if isinstance(node, ast.ClassDef) else "function"})
            if len(symbols) >= MAX_SYMBOLS:
                break
        if len(symbols) >= MAX_SYMBOLS:
            break
    findings = []
    for item in symbols:
        name = item["symbol"].split(".")[-1]
        pattern = re.compile(r"\b" + re.escape(name) + r"\b")
        refs = []
        for rel, body in sorted(source.items()):
            if rel == item["path"]:
                continue
            hits = [i for i, line in enumerate(body.splitlines(), 1)
                    if pattern.search(line) and not line.lstrip().startswith("#")]
            if hits:
                refs.append({"path": rel, "lines": hits[:3]})
            if len(refs) >= MAX_REFERENCES:
                break
        findings.append({**item, "other_source_or_test_references": refs,
                         "reference_limit_reached": len(refs) == MAX_REFERENCES})
    return {"status": "observational_only", "symbols": findings,
            "changed_py_files": len(spans), "files_scanned": len(source),
            "semantic_correctness_verified": False,
            "warning": "Lexical symbol references are not behavioral obligations. Inspect source and task contract."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", default="/workspace")
    args = parser.parse_args()
    print(json.dumps(scan(Path(args.workspace)), sort_keys=True))


if __name__ == "__main__":
    main()
