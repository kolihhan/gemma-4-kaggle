"""Synthetic mechanism probe only; no inference or competition data."""
import ast
from collections import defaultdict

FILES = {
    'decoy.py': 'def normalize_label(value):\n    return value\n# normalize normalize normalize normalize\n',
    'core.py': 'def normalize(value):\n    if value is None:\n        return ""\n    return value.strip()\n',
    'api.py': 'from core import normalize\ndef render(value):\n    return normalize(value)\n',
    'dynamic.py': 'def broken(:\n    pass\n',
}


def probe(files, anchor, k=2):
    lexical = sorted(files, key=lambda p: (-files[p].count(anchor), p))[:k]
    nodes = defaultdict(list)
    partial = []
    for path, source in sorted(files.items()):
        try:
            tree = ast.parse(source)
        except SyntaxError:
            partial.append(path)
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == anchor:
                nodes['definition'].append((path, node.lineno, node.end_lineno))
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == anchor:
                nodes['caller'].append((path, node.lineno, node.end_lineno))
    definition = nodes['definition'][:k]
    diverse = []
    for kind in ('definition', 'caller'):
        if nodes[kind] and len(diverse) < k:
            path, start, end = nodes[kind][0]
            diverse.append((kind, path, start, end, '\n'.join(files[path].splitlines()[start-1:end])))
    return lexical, definition, diverse, partial


def main():
    lexical, definition, diverse, partial = probe(FILES, 'normalize')
    assert lexical[0] == 'decoy.py'
    assert 'core.py' not in lexical
    assert [x[0] for x in definition] == ['core.py']
    assert {x[1] for x in diverse} == {'core.py', 'api.py'}
    assert 'if value is None:' in diverse[0][4]
    assert partial == ['dynamic.py']
    assert probe(FILES, 'unavailable')[2] == []
    assert len(probe(FILES, 'normalize', 1)[2]) == 1
    print('lexical:', lexical)
    print('definition-only:', [x[0] for x in definition])
    print('role-diverse:', [(x[0], x[1]) for x in diverse])
    print('parse-blocked:', partial)
    print('8 synthetic assertions passed; real-task quality UNKNOWN')


if __name__ == '__main__':
    main()
