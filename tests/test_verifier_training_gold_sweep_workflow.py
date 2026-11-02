import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "run-verifier-training-gold-sweep.yml"


class VerifierTrainingGoldSweepWorkflowTests(unittest.TestCase):
    def test_workflow_exists_and_uses_frozen_training_subset(self):
        self.assertTrue(WORKFLOW.is_file())
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn('docs/evaluation/verifier-lora-train-subset-v0.json', text)
        self.assertIn('verifier-lora-v0-train-harvest', text)
        self.assertIn('expected 18 training gold-control tasks', text)
        self.assertIn('"version": "verifier-lora-v0"', text)
        self.assertIn('"holdout": tasks', text)

    def test_reuses_gold_control_runtime_without_model_or_agent(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn('root / "kaggle" / "gold_control_sweep.py"', text)
        self.assertIn('"enable_gpu": False', text)
        self.assertIn('"enable_internet": False', text)
        self.assertIn('"model_sources": []', text)
        self.assertNotIn('verifier_training_trace_runtime.py', text)

    def test_asserts_complete_structured_training_result(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn('result.get("requested") == 18', text)
        self.assertIn('len(result.get("results", [])) == 18', text)
        self.assertIn('reference_patch" not in item', text)
        self.assertIn('gemma4-verifier-training-gold-v0-evidence', text)

    def test_pins_kaggle_cli_runtime_dependencies(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn(
            'python -m pip install --disable-pip-version-check "kaggle==2.2.5" "six==1.17.0"',
            text,
        )
        self.assertIn('python -c "import kaggle, six"', text)
        self.assertNotIn('--upgrade kaggle', text)


if __name__ == "__main__":
    unittest.main()
