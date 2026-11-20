"""Subprocess contract for model-visible first-search evidence via run_command."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "first_search_cli.py"


class DeliveryContract(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "src").mkdir()
        (self.root / "src" / "auth.py").write_text(
            'def refresh_token(token):\n    """Refresh token expiry."""\n    return token\n'
        )
        (self.root / "test_auth.py").write_text(
            'def refresh_token():\n    """GOLD_REFERENCE_SENTINEL"""\n    return 1\n'
        )
        self.issue = self.root / "issue.txt"
        self.issue.write_text("Refresh token expiry fails")

    def run_cli(self, issue_file=None):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--root", str(self.root),
             "--issue-file", str(issue_file or self.issue)],
            capture_output=True, text=True, timeout=10
        )

    def test_stdout_is_bounded_model_visible_json_without_test_leak(self):
        proc = self.run_cli()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertEqual(data["kind"], "first_search_production_evidence_v1")
        self.assertLessEqual(data["count"], 3)
        self.assertEqual(data["spans"][0]["symbol"], "refresh_token")
        self.assertIn("Refresh token expiry", proc.stdout)
        self.assertNotIn("GOLD_REFERENCE_SENTINEL", proc.stdout)
        self.assertNotIn("test_auth.py", proc.stdout)
        self.assertLess(len(proc.stdout), 6000)

    def test_empty_evidence_fallback(self):
        self.issue.write_text("completelyunrelatedword")
        data = json.loads(self.run_cli().stdout)
        self.assertEqual(data["count"], 0)
        self.assertTrue(data["fallback_to_original_search"])

    def test_oversized_issue_fails_closed(self):
        self.issue.write_text("x" * 12001)
        proc = self.run_cli()
        self.assertNotEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout, "")

    def test_symlink_issue_fails_closed(self):
        alias = self.root / "alias.txt"
        alias.symlink_to(self.issue)
        proc = self.run_cli(alias)
        self.assertNotEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout, "")


if __name__ == "__main__":
    unittest.main()
