import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = (
    ROOT / ".github" / "workflows" / "run-verifier-baseline.yml",
    ROOT / ".github" / "workflows" / "run-verifier-gold-sweep.yml",
    ROOT / ".github" / "workflows" / "run-verifier-blind-gold-sweep.yml",
    ROOT / ".github" / "workflows" / "run-verifier-training-trace-harvest.yml",
)
EXPECTED_INSTALL = (
    'python -m pip install --disable-pip-version-check "kaggle==2.2.5" "six==1.17.0"'
)
EXPECTED_SMOKE = 'python -c "import kaggle, six"'


class KaggleCliWorkflowDependencyTests(unittest.TestCase):
    def test_kaggle_cli_workflows_pin_runtime_dependencies_and_smoke_import(self):
        for workflow in WORKFLOWS:
            with self.subTest(workflow=workflow.name):
                text = workflow.read_text(encoding="utf-8")
                self.assertIn(EXPECTED_INSTALL, text)
                self.assertIn(EXPECTED_SMOKE, text)
                self.assertNotIn("--upgrade kaggle", text)


if __name__ == "__main__":
    unittest.main()
