import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "kaggle" / "verifier_gold_teacher_runtime.py"
WORKFLOW = ROOT / ".github" / "workflows" / "run-verifier-gold-teacher.yml"


class VerifierGoldTeacherExecutionContractTests(unittest.TestCase):
    def test_runtime_is_standalone_training_only_teacher(self):
        text = RUNTIME.read_text(encoding="utf-8")
        self.assertIn('SUBMISSION_PAYLOAD_B64 = "__SUBMISSION_PAYLOAD_B64__"', text)
        self.assertIn('TRAINING_MANIFEST_JSON = "__VERIFIER_LORA_TRAINING_MANIFEST_JSON__"', text)
        self.assertIn('TRAINING_GOLD_SCREEN_JSON = "__VERIFIER_LORA_TRAINING_GOLD_SCREEN_JSON__"', text)
        self.assertIn("load_clean_training_ids(", text)
        self.assertIn("build_verifier_only_submission(", text)
        self.assertIn("install_gold_patch_after_baseline_hook()", text)
        self.assertIn("evaluator._hydrate_task_from_secret", text)
        self.assertIn("state[\"patch_path\"]", text)
        self.assertIn("evaluator.evaluate_task(", text)
        self.assertIn('"version": "verifier-lora-v0-gold-teacher"', text)
        self.assertIn("def main()", text)

    def test_workflow_uses_only_frozen_clean_training_screen(self):
        self.assertTrue(WORKFLOW.is_file())
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("docs/evaluation/verifier-lora-training-gold-screen-v0.json", text)
        self.assertIn("docs/evaluation/verifier-lora-train-subset-v0.json", text)
        self.assertIn("kaggle/verifier_gold_teacher_runtime.py", text)
        self.assertIn("expected exactly 12 frozen clean training tasks", text)
        self.assertIn("__VERIFIER_LORA_TRAINING_GOLD_SCREEN_JSON__", text)
        self.assertIn("__VERIFIER_LORA_TRAINING_MANIFEST_JSON__", text)
        self.assertIn("__SUBMISSION_PAYLOAD_B64__", text)

    def test_workflow_is_private_e4b_gpu_and_no_adapter(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn('"enable_gpu": True', text)
        self.assertIn('"enable_internet": False', text)
        self.assertIn('"machine_shape": "NvidiaL4"', text)
        self.assertIn("gemma-4-e4b-it-qat-w4a16-ct", text)
        self.assertIn("training gold teacher must use base submission without adapters", text)
        self.assertIn('python -m pip install --disable-pip-version-check "kaggle==2.2.5" "six==1.17.0"', text)

    def test_workflow_requires_complete_metadata_only_result_and_uploads_traces(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn('result.get("version") == "verifier-lora-v0-gold-teacher"', text)
        self.assertIn('result.get("requested") == 12', text)
        self.assertIn('len(result.get("results", [])) == 12', text)
        self.assertIn('"reference_patch" not in item', text)
        self.assertIn('"agent_patch" not in item', text)
        self.assertIn("gemma4-verifier-gold-teacher-v0-evidence", text)


if __name__ == "__main__":
    unittest.main()
