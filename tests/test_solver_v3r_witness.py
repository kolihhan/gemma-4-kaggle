"""Focused behavioral tests of Solver V3-R's actual sandbox witness script."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "experiments/solver-v3/skill/scripts/witness.py"


def witness_module():
    spec = importlib.util.spec_from_file_location("v3r_witness", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class WitnessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.workspace = Path(self.tmp.name) / "workspace"
        self.workspace.mkdir()
        self.state = Path(self.tmp.name) / "state"
        subprocess.run(["git", "init", "-q", str(self.workspace)], check=True)
        (self.workspace / "fixme.py").write_text(
            "def answer():\n    return 2\n", encoding="utf-8")
        (self.workspace / "test_fixme.py").write_text(
            "from fixme import answer\n\n"
            "def test_answer():\n    assert answer() == 3\n", encoding="utf-8")

    def test_genuine_fail_then_pass_produces_repair_evidence(self):
        w = witness_module()
        before = w.run_witness(self.workspace, "test_fixme.py::test_answer",
                               "before", state_dir=self.state)
        self.assertEqual(before["status"], "fail")
        self.assertEqual(before["comparison"], "baseline_recorded")
        self.assertIn("AssertionError", before["evidence"])
        (self.workspace / "fixme.py").write_text(
            "def answer():\n    return 3\n", encoding="utf-8")
        after = w.run_witness(self.workspace, "test_fixme.py::test_answer",
                              "after", state_dir=self.state)
        self.assertEqual(after["status"], "pass")
        self.assertEqual(after["comparison"], "repair_demonstrated")
        self.assertEqual(after["target"], before["target"])
        self.assertTrue(after["verified_test_process"])
        self.assertFalse(after["independent_issue_resolved"])

    def test_pass_to_fail_marks_regression(self):
        w = witness_module()
        (self.workspace / "fixme.py").write_text(
            "def answer():\n    return 3\n", encoding="utf-8")
        w.run_witness(self.workspace, "test_fixme.py", "before",
                      state_dir=self.state)
        (self.workspace / "fixme.py").write_text(
            "def answer():\n    return 4\n", encoding="utf-8")
        result = w.run_witness(self.workspace, "test_fixme.py", "after",
                               state_dir=self.state)
        self.assertEqual(result["comparison"], "regression_introduced")

    def test_missing_baseline_is_reported_not_invented(self):
        w = witness_module()
        r = w.run_witness(self.workspace, "test_fixme.py", "after",
                          state_dir=self.state)
        self.assertEqual(r["status"], "fail")
        self.assertEqual(r["comparison"], "baseline_unavailable")

    def test_rejects_path_escape_and_symlink(self):
        w = witness_module()
        with self.assertRaises(ValueError):
            w.run_witness(self.workspace, "../secret_test.py", "after",
                          state_dir=self.state)
        with self.assertRaises(ValueError):
            w.run_witness(self.workspace, "/tmp/test_fixme.py", "after",
                          state_dir=self.state)
        (self.workspace / "escape.py").symlink_to(Path(self.tmp.name) / "outside.py")
        with self.assertRaises(ValueError):
            w.run_witness(self.workspace, "escape.py", "after",
                          state_dir=self.state)

    def test_no_tests_does_not_count_as_pass(self):
        w = witness_module()
        (self.workspace / "test_none.py").write_text("x = 1\n", encoding="utf-8")
        output = w.run_witness(self.workspace, "test_none.py", "after",
                               state_dir=self.state)
        self.assertEqual(output["status"], "blocked")
        self.assertFalse(output["verified_test_process"])
        self.assertNotEqual(output["comparison"], "repair_demonstrated")

    def test_state_is_per_target_not_shared(self):
        w = witness_module()
        w.run_witness(self.workspace, "test_fixme.py::test_answer", "before",
                      state_dir=self.state)
        after = w.run_witness(self.workspace, "test_fixme.py", "after",
                              state_dir=self.state)
        self.assertEqual(after["comparison"], "baseline_unavailable")


if __name__ == "__main__":
    unittest.main()
