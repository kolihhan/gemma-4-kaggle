"""Bounded, read-only first-search production function evidence; CPU-only prototype."""
from __future__ import annotations
import ast
import os
from pathlib import Path
import re

TOKENS = re.compile(r'[A-Za-z_][A-Za-z_0-9]*')
SKIP = {'the','and','for','with','from','this','that','should','when','error','function','issue','code','file','return','python'}

def words(s: str) -> set[str]:
    return {w.lower() for w in TOKENS.findall(s) if len(w)>2 and w.lower() not in SKIP}

def retrieve(issue: str, root: Path, limit: int = 3, max_files: int = 250, max_bytes: int = 120_000) -> list[dict]:
    """Rank bounded Python function snippets by issue-token overlap, stable ties.

    No reference patch, external network, dynamic imports or code execution.
    Symlinks and tests are excluded; no wrapper traversal in this conservative v0.
    """
    if limit < 1 or limit > 3: raise ValueError('limit must be 1..3')
    root = root.resolve(strict=True)
    query = words(issue)
    results = []
    # Two bounded stages: inspect only allowlisted production paths and short
    # function headers, then spend the AST budget on the strongest candidates.
    # Avoid rglob: it enumerates hidden/test trees before applying any cap.
    excluded = {'tests', 'test', 'testing', 'fixtures', 'fixture', 'benchmarks',
                '.git', '.venv', 'venv', 'site-packages', '__pycache__',
                'private', 'hidden', 'secrets', 'grader', 'evaluation'}
    candidates = []
    visited = 0
    max_candidates = 2000
    max_dirs = 300
    dirs_seen = 0
    for directory, dirs, files in os.walk(root, followlinks=False):
        dirs_seen += 1
        if dirs_seen > max_dirs or visited >= max_candidates:
            break
        dirs[:] = sorted(d for d in dirs if not d.startswith('.')
                         and d.lower() not in excluded
                         and not (Path(directory) / d).is_symlink())
        for filename in sorted(files):
            if visited >= max_candidates:
                break
            if (not filename.endswith('.py') or filename.startswith('.')
                or filename.startswith('test_') or filename.endswith('_test.py')):
                continue
            path = Path(directory) / filename
            if path.is_symlink() or not path.is_file():
                continue
            try:
                if path.stat().st_size > max_bytes:
                    continue
                rel = str(path.relative_to(root))
                # A capped header scan permits exact symbol matches to outrank
                # unrelated alphabetically earlier files.
                with path.open(encoding='utf-8') as stream:
                    headers = ''.join(stream.readline() for _ in range(160))
            except (OSError, UnicodeError):
                continue
            visited += 1
            path_score = len(query & words(rel.replace('_', ' ').replace('/', ' ')))
            header_score = 0
            for name in re.findall(r'^\\s*(?:async\\s+)?def\\s+([A-Za-z_][A-Za-z_0-9]*)\\s*\\(', headers, re.M):
                header_score = max(header_score, len(query & words(name.replace('_', ' '))))
            candidates.append((-(10 * header_score + 4 * path_score), rel, path))
    candidates.sort(key=lambda item: (item[0], item[1]))
    for _, rel, path in candidates[:max_files]:
        try:
            content = path.read_text(encoding='utf-8')
            tree = ast.parse(content)
        except (UnicodeError, OSError, SyntaxError):
            continue
        lines = content.splitlines()
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            start, end = node.lineno, min(node.end_lineno or node.lineno + 23)
            snippet = '\\n'.join(lines[start-1:end])[:1600]
            name_words = words(node.name.replace('_', ' '))
            path_words = words(rel.replace('/', ' ').replace('_', ' '))
            doc_words = words(ast.get_docstring(node) or '')
            score = 5 * len(query & name_words) + 2 * len(query & path_words) + len(query & doc_words) + len(query & words(snippet))
            if score > 0:
                results.append((score, rel, start, {'path': rel, 'line': start, 'symbol': node.name, 'score': score, 'snippet': snippet}))
    results.sort(key=lambda x:(-x[0],x[1],x[2]))
    return [x[3] for x in results[:limit]]
