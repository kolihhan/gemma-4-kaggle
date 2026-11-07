"""CPU cases with an independent behavioral grader and real Git revisions."""

from pathlib import Path
import subprocess
import tempfile
import unittest

from scripts.candidate_history import History, grade_history


CHECK = "import samplepkg; assert samplepkg.twice(2) == 4; assert samplepkg.twice(-2) == -4"
BAD = "def twice(x):\n    return x + 1\n"
GOOD = "def twice(x):\n    return 2 * x\n"
PARTIAL = "def twice(x):\n    return 2 * abs(x)\n"


class CandidateHistoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.git("init", "-q")
        self.git("config", "user.name", "CPU fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        (self.repo / "samplepkg.py").write_text(BAD)
        self.git("add", ".")
        self.git("commit", "-qm", "base")
        self.git("tag", "_swegemma_baseline")
        (self.repo / "samplepkg.py").write_text(GOOD)
        self.gold = self.git("diff", "--binary", "_swegemma_baseline").encode()
        (self.repo / "samplepkg.py").write_text(BAD)
        self.history = History(self.repo, self.root / "history")
        self.history.start()

    def git(self, *arguments):
        return subprocess.check_output(["git", "-C", str(self.repo), *arguments], text=True)

    def change(self, code, error=False):
        (self.repo / "samplepkg.py").write_text(code)
        self.history.observe("edit_file", tool_failed=error)

    def grade(self):
        self.history.finish()
        return grade_history(self.repo, self.root / "history", CHECK, self.gold)

    def test_independently_passing_candidate_is_detected_after_it_is_overwritten(self):
        self.change(GOOD)
        self.change(PARTIAL)
        report = self.grade()
        self.assertEqual(report["diagnosis"], "discarded_passing_candidate")
        self.assertEqual(report["passing_candidates"], 1)
        self.assertEqual(report["final_grade"], "fail")

    def test_final_passing_patch_is_retained(self):
        self.change(GOOD)
        self.assertEqual(self.grade()["diagnosis"], "retained_passing_candidate")

    def test_partial_repair_is_not_a_passing_candidate(self):
        self.change(PARTIAL)
        self.assertEqual(self.grade()["diagnosis"], "no_passing_candidate_observed")

    def test_failed_edit_without_source_change_is_separate_from_patch_generation(self):
        self.history.observe("edit_file", tool_failed=True)
        report = self.grade()
        self.assertEqual(report["diagnosis"], "no_materialized_source_patch")
        self.assertEqual(report["failed_edit_calls"], 1)

    def test_tool_error_does_not_hide_a_real_passing_source_change(self):
        self.change(GOOD, error=True)
        self.assertEqual(self.grade()["diagnosis"], "retained_passing_candidate")

    def test_invalid_positive_control_prevents_a_bottleneck_claim(self):
        self.change(PARTIAL)
        self.history.finish()
        report = grade_history(self.repo, self.root / "history", CHECK, b"")
        self.assertEqual(report["diagnosis"], "ineligible_controls")

    def test_staged_committed_and_untracked_source_can_be_replayed(self):
        self.change(GOOD)
        self.git("add", ".")
        self.git("commit", "-qm", "agent edit")
        (self.repo / "extra.py").write_text("value = 7\n")
        self.history.observe("run_command")
        before = self.git("status", "--porcelain")
        self.history.observe("read_file")
        self.assertEqual(self.git("status", "--porcelain"), before)
        self.assertEqual(self.grade()["diagnosis"], "retained_passing_candidate")

    def test_missing_initial_history_cannot_claim_that_no_correct_patch_ever_existed(self):
        import json
        path = self.root / "history/history.json"
        data = json.loads(path.read_text())
        data["complete"] = False
        path.write_text(json.dumps(data))
        self.change(PARTIAL)
        self.assertEqual(self.grade()["diagnosis"], "inconclusive_history")

    def test_grader_that_does_not_import_copied_source_is_inconclusive(self):
        self.change(GOOD)
        self.history.finish()
        report = grade_history(self.repo, self.root / "history", "print('fine')", self.gold)
        self.assertEqual(report["diagnosis"], "ineligible_controls")

    def test_unfinished_history_cannot_label_the_last_seen_candidate_as_final(self):
        self.change(GOOD)
        report = grade_history(self.repo, self.root / "history", CHECK, self.gold)
        self.assertEqual(report["diagnosis"], "inconclusive_history")

    def test_changed_candidate_bytes_are_not_graded_under_the_old_identity(self):
        import json
        self.change(GOOD)
        self.history.finish()
        data = json.loads((self.root / "history/history.json").read_text())
        digest = next(k for k, n in data["revisions"].items() if n)
        (self.root / "history" / (digest + ".patch")).write_text("tampered")
        with self.assertRaisesRegex(ValueError, "hash_mismatch"):
            grade_history(self.repo, self.root / "history", CHECK, self.gold)


if __name__ == "__main__":
    unittest.main()
