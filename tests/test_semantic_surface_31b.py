"""CPU-only synthetic source-impact observations; no private competition data."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "experiments/semantic-surface-v0/skill/scripts/surface.py"
SPEC = importlib.util.spec_from_file_location("surface_v0", SRC)
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def git(directory, *arguments):
    subprocess.run(["git", "-C", str(directory), *arguments], check=True,
                   capture_output=True, timeout=10)


class SemanticSurfaceTests(unittest.TestCase):
    def test_no_diff_and_changed_method_cross_file_reference(self):
        with tempfile.TemporaryDirectory() as dirname:
            root = Path(dirname)
            git(root, "init", "-q")
            git(root, "config", "user.email", "test@example.invalid")
            git(root, "config", "user.name", "Test")
            (root / "api.py").write_text(
                "class Thing:\n    def respond(self):\n        return 1\n")
            (root / "caller.py").write_text(
                "from api import Thing\n\n"
                "def drive():\n    return Thing().respond()\n")
            (root / "tests").mkdir()
            (root / "tests/test_api.py").write_text(
                "def test_respond():\n    assert Thing().respond()\n")
            git(root, "add", ".")
            git(root, "commit", "-qm", "baseline")
            no_change = mod.scan(root)
            self.assertEqual(no_change["status"], "no_python_source_change")
            (root / "api.py").write_text(
                "class Thing:\n    def respond(self):\n        return 2\n")
            data = mod.scan(root)
            self.assertEqual(data["status"], "observational_only")
            self.assertFalse(data["semantic_correctness_verified"])
            self.assertEqual(len(data["symbols"]), 1)
            entry = data["symbols"][0]
            self.assertEqual(entry["symbol"], "Thing.respond")
            paths = {x["path"] for x in entry["other_source_or_test_references"]}
            self.assertEqual(paths, {"caller.py", "tests/test_api.py"})

    def test_no_git_checkout_fails_closed(self):
        with tempfile.TemporaryDirectory() as dirname:
            with self.assertRaisesRegex(ValueError, "requires repository"):
                mod.scan(Path(dirname))


if __name__ == "__main__":
    unittest.main()
