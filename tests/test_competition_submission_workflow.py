from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "submit-baseline.yml"
PREFLIGHT = ROOT / ".github" / "workflows" / "validate-baseline-submission.yml"
VALIDATE_TOOLS = ROOT / ".github" / "workflows" / "validate-tools.yml"


class CompetitionSubmissionWorkflowTests(unittest.TestCase):
    def test_manual_submission_uses_shared_preflight_and_requires_explicit_confirm(self):
        self.assertTrue(WORKFLOW.is_file())
        source = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch", source)
        self.assertIn("confirm", source)
        self.assertIn("uses: ./.github/workflows/validate-baseline-submission.yml", source)
        self.assertIn("secrets: inherit", source)
        self.assertIn("actions/download-artifact@v4", source)
        self.assertIn("submission.zip", source)
        self.assertIn("submission.sha256", source)
        self.assertIn("sha256sum -c submission.sha256", source)
        self.assertIn("kaggle competitions submit", source)
        self.assertIn("gemma-4-developer-agent", source)
        self.assertNotIn("Download current official scorer wheelhouse", source)
        self.assertNotIn("Install current scorer validation packages", source)

    def test_workflow_never_auto_submits_on_push_or_pull_request(self):
        source = WORKFLOW.read_text(encoding="utf-8")
        self.assertNotIn("\n  push:", source)
        self.assertNotIn("\n  pull_request:", source)

    def test_preflight_is_reusable_and_validates_exact_zip_on_private_cpu_kaggle_kernel(self):
        self.assertTrue(PREFLIGHT.is_file())
        source = PREFLIGHT.read_text(encoding="utf-8")
        self.assertIn("workflow_call", source)
        self.assertIn("pull_request", source)
        self.assertIn("submission/agent.yaml", source)
        self.assertIn("submission.zip", source)
        self.assertIn("submission.sha256", source)
        self.assertIn("kaggle kernels push", source)
        self.assertIn("kaggle kernels status", source)
        self.assertIn("kaggle kernels output", source)
        self.assertIn("'enable_gpu': False", source)
        self.assertIn("'is_private': True", source)
        self.assertIn("validate_directory", source)
        self.assertIn("discover_declared_models", source)
        self.assertIn("archive_sha256", source)
        self.assertIn("gemma-4-e4b-it-qat-w4a16-ct", source)
        self.assertIn("actions/upload-artifact@v4", source)
        self.assertNotIn("kaggle competitions submit", source)

    def test_existing_pr_validation_calls_preflight_before_merge(self):
        source = VALIDATE_TOOLS.read_text(encoding="utf-8")
        self.assertIn("baseline-preflight", source)
        self.assertIn("github.head_ref == 'submit/baseline-e4b-v0'", source)
        self.assertIn("uses: ./.github/workflows/validate-baseline-submission.yml", source)
        self.assertIn("secrets: inherit", source)


if __name__ == "__main__":
    unittest.main()
