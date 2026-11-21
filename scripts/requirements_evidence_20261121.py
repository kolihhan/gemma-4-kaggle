"""Bounded, read-only sandbox-local behavioral evidence for coding issues.

This does NOT fetch external issue bodies, inspect gold patches, or verify that
an inferred behavior is correct. It retrieves existing tests and docstrings.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
from pathlib import Path
import re
import time

EXCLUDE = frozenset({
    '.git', '.venv', 'venv', 'site-packages', '__pycache__', '.tox',
    'private', 'hidden', 'grader', 'evaluation', 'fixtures', 'fixture',
    'benchmarks', 'examples', 'node_modules', 'dist', 'build',
})
STOP = frozenset({'the','and','for','that','with','should','when','from','this',
                  'there','what','which','issue','code','file','error',
                  'return','fix','function','bug','not','its','but'})


def tokens(value: str) -> set[str]:
    return {x.lower() for x in re.findall(r'[A-Za-z]{3,}', value.replace('_', ' ')) if x.lower() not in STOP}


def _excerpt(lines: list[str], node: ast.AST, query: set[str], is_test: bool) -> str:
    start = node.lineno - 1
    end = min(len(lines), node.end_lineno or node.lineno)
    body = lines[start:end]
    # When available, a concrete assertion or exception is more informative
    # than an abstract function name or a long docstring.
    focus = next((i for i, line in enumerate(body) if is_test and re.search(r'\b(assert|raises|pytest\.raises)\b', line)), None)
    if focus is None:
        focus = max(range(min(len(body), 40)), key=lambda i: len(query & tokens(body[i])), default=0)
    lo = max(0, focus-1)
    return '\n'.join(body[lo:lo+4]).strip()[:450]


def find_evidence(issue: str, root: Path, max_files: int = 240,
                  seconds: float = 2.5, limit: int = 4) -> dict:
    """Returns evidence candidates; TRUNCATED never implies no matching test.

    All content is from preexisting sandbox-local files. No execution/imports.
    """
    if max_files < 1 or seconds <= 0 or not 1 <= limit <= 4:
        raise ValueError('invalid evidence search budget')
    root = Path(root).resolve(strict=True)
    query = tokens(issue)
    if not query:
        return {'status':'NO_QUERY','scanned':0,'matches':[]}
    scanned, truncated, candidates = 0, False, []
    start = time.monotonic()
    for directory, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if not d.startswith('.') and d.lower() not in EXCLUDE
                         and not (Path(directory)/d).is_symlink())
        for name in sorted(files):
            if not name.endswith('.py') or name.startswith('.'):
                continue
            path = Path(directory)/name
            if path.is_symlink():
                continue
            if scanned >= max_files or time.monotonic()-start > seconds:
                truncated = True
                break
            try:
                if path.stat().st_size > 120_000:
                    continue
                body = path.read_text(encoding='utf-8')
                tree = ast.parse(body)
            except (OSError, UnicodeError, SyntaxError):
                continue
            scanned += 1
            rel = path.relative_to(root).as_posix()
            parts = rel.split('/')
            is_test = ('tests' in parts or 'test' in parts or name.startswith('test_') or name.endswith('_test.py'))
            lines = body.splitlines()
            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                name_score = len(query & tokens(node.name))
                path_score = len(query & tokens(rel))
                doc_score = len(query & tokens(ast.get_docstring(node) or ''))
                statement = _excerpt(lines, node, query, is_test)
                body_score = len(query & tokens(statement))
                score = 6*name_score + 2*path_score + doc_score + body_score
                if score <= 0:
                    continue
                candidates.append((score, int(is_test), rel, node.lineno, {
                    'kind':'existing_test' if is_test else 'production_definition',
                    'path':rel, 'line':node.lineno, 'symbol':node.name,
                    'excerpt':statement, 'score':score,
                }))
        if truncated:
            break
    candidates.sort(key=lambda x:(-x[0],-x[1],x[2],x[3]))
    return {'status':'TRUNCATED' if truncated else 'EVIDENCE' if candidates else 'NO_MATCH',
            'scanned':scanned, 'matches':[c[-1] for c in candidates[:limit]]}


def main() -> None:
    parser = argparse.ArgumentParser(description='Read only existing local tests and code')
    parser.add_argument('--query', required=True, help='short issue title/API/expected behavior')
    parser.add_argument('--root', type=Path, default=Path('/workspace'))
    args = parser.parse_args()
    print(json.dumps(find_evidence(args.query, args.root), ensure_ascii=True, sort_keys=True))


if __name__ == '__main__':
    main()
