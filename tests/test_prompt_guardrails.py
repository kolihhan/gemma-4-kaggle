import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROMPT = ROOT / "submission" / "prompts" / "system.md"


class PromptGuardrailTests(unittest.TestCase):
    def test_edit_failure_stops_destructive_fallbacks(self):
        text = PROMPT.read_text(encoding="utf-8")
        self.assertIn("If the same edit fails twice", text)
        self.assertIn("do not replace an existing source file with `write_file`", text)

    def test_diff_is_checked_for_unexpected_scope(self):
        text = PROMPT.read_text(encoding="utf-8")
        self.assertIn("unexpectedly large", text)
        self.assertIn("repair or revert it before testing or submitting", text)

    def test_failing_targeted_test_blocks_submission(self):
        text = PROMPT.read_text(encoding="utf-8")
        self.assertIn("Do not submit while the targeted verification is failing", text)
        self.assertIn("Never reinterpret a non-zero test result as success", text)


if __name__ == "__main__":
    unittest.main()
