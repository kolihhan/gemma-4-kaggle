"""Read existing tests in the solver's checkout and rank exact identifier matches."""

import argparse
import ast
from pathlib import Path
import re


IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z_0-9]*")
ROOT_NAMES = {"tests", "test", "testing"}
IGNORED_PARTS = {".git", ".venv", "node_modules", "site-packages", "vendor", "__pycache__"}


def test_files(root):
    for path in sorted(root.rglob("test*.py")):
        parents = set(path.relative_to(root).parts[:-1])
        if parents & IGNORED_PARTS or not (parents & ROOT_NAMES or path.parent == root):
            continue
        if path.is_symlink() or path.stat().st_size > 200_000:
            continue
        yield path


def collect(root, anchors):
    ranked = []
    for index, path in enumerate(test_files(root)):
        if index >= 400:
            break
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except (OSError, UnicodeError, SyntaxError):
            continue
        lines = source.splitlines()
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or not node.name.startswith("test"):
                continue
            section = lines[node.lineno - 1:node.end_lineno]
            score = len(anchors & set(IDENTIFIER.findall(" ".join(section))))
            if not score:
                continue
            relevant = []
            for line_no, line in enumerate(section, node.lineno):
                if anchors & set(IDENTIFIER.findall(line)) or line.strip().startswith("assert "):
                    relevant.append((line_no, line.strip()[:180]))
            ranked.append((-score, str(path.relative_to(root)), node.lineno, node.name, relevant[:8]))
    return sorted(ranked)[:3]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--anchors", required=True)
    args = parser.parse_args()
    anchors = set(IDENTIFIER.findall(args.anchors))
    if not 1 <= len(anchors) <= 4:
        raise SystemExit("Provide one to four exact identifiers from the issue.")
    matches = collect(Path.cwd(), anchors)
    print(f"EXISTING_TEST_MATCHES={len(matches)}")
    for _, path, line, name, excerpt in matches:
        print(f"{path}:{line} {name}")
        for line_no, text in excerpt:
            print(f"  {line_no}: {text}")


if __name__ == "__main__":
    main()
