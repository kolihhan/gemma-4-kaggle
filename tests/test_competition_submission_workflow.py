from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "submit-baseline.yml"
PREFLIGHT = ROOT / ".github" / "workflows" / "validate-baseline-submission.yml"


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

    def test_pr_preflight_validates_exact_zip_on_private_cpu_kaggle_kernel(self):
        self.assertTrue(PREFLIGHT.is_file())
        source = PREFLIGHT.read_text(encoding="utf-8")
        self.assertIn("pull_request", source)
        self.assertIn("submission/agent.yaml", source)
        self.assertIn("submission.zip", source)
        self.assertIn("submission.sha256", source)
        self.assertIn("kaggle kernels push", source)
        self.assertIn("kaggle kernels status", source)
        self.assertIn("kaggle kernels output", source)
        self.assertIn('"enable_gpu": False', source)
        self.assertIn('"is_private": True', source)
        self.assertIn("validate_directory", source)
        self.assertIn("discover_declared_models", source)
        self.assertIn("archive_sha256", source)
        self.assertIn("gemma-4-e4b-it-qat-w4a16-ct", source)
        self.assertIn("actions/upload-artifact@v4", source)
        self.assertNotIn("kaggle competitions submit", source)
        self.assertNotIn("Resolve runtime dependencies for vanilla GitHub runner", source)


if __name__ == "__main__":
    unittest.main()
