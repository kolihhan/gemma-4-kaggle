"""Bounded, read-only first-search production function evidence; CPU-only prototype."""
from __future__ import annotations
import ast
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
    paths = sorted(root.rglob('*.py'))
    scanned = 0
    for path in paths:
        if scanned >= max_files: break
        if (path.is_symlink() or path.name.startswith('test_') or path.name.endswith('_test.py')
            or any(x.lower() in {'tests','test','venv','.venv','site-packages'} for x in path.relative_to(root).parts)): continue
        if path.stat().st_size > max_bytes: continue
        scanned += 1
        try:
            content = path.read_text(encoding='utf-8')
            tree = ast.parse(content)
        except (UnicodeError, OSError, SyntaxError): continue
        lines = content.splitlines()
        for node in ast.walk(tree):
            if not isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)): continue
            start, end = node.lineno, min(node.end_lineno or node.lineno+23)
            snippet = '\n'.join(lines[start-1:end])[:1600]
            name_words = words(node.name.replace('_',' '))
            path_words = words(str(path.relative_to(root)).replace('/',' ').replace('_',' '))
            doc_words = words(ast.get_docstring(node) or '')
            score = 5*len(query & name_words)+2*len(query & path_words)+len(query & doc_words)+len(query & words(snippet))
            if score > 0:
                results.append((score,str(path.relative_to(root)),start,{'path':str(path.relative_to(root)),'line':start,'symbol':node.name,'score':score,'snippet':snippet}))
    results.sort(key=lambda x:(-x[0],x[1],x[2]))
    return [x[3] for x in results[:limit]]
