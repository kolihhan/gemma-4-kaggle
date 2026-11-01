from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "submit-baseline.yml"


class CompetitionSubmissionWorkflowTests(unittest.TestCase):
    def test_manual_submission_workflow_packages_canonical_submission_and_requires_explicit_confirm(self):
        self.assertTrue(WORKFLOW.is_file())
        source = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("workflow_dispatch", source)
        self.assertIn("confirm", source)
        self.assertIn("submission/agent.yaml", source)
        self.assertIn("submission.zip", source)
        self.assertIn("validate_directory", source)
        self.assertIn("discover_declared_models", source)
        self.assertIn("gemma-4-e4b-it-qat-w4a16-ct", source)
        self.assertIn("kaggle competitions submit", source)
        self.assertIn("gemma-4-developer-agent", source)
        self.assertIn("actions/upload-artifact@v4", source)

    def test_workflow_never_auto_submits_on_push_or_pull_request(self):
        source = WORKFLOW.read_text(encoding="utf-8")
        self.assertNotIn("\n  push:", source)
        self.assertNotIn("\n  pull_request:", source)


if __name__ == "__main__":
    unittest.main()
