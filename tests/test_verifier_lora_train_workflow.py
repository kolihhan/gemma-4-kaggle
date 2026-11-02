from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "run-verifier-lora-train.yml"


class VerifierLoraTrainWorkflowContractTests(unittest.TestCase):
    def test_workflow_is_manual_guarded_and_uses_exact_teacher_artifact(self):
        source = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", source)
        self.assertNotIn("\n  push:", source)
        self.assertIn("confirm:", source)
        self.assertIn('if [[ "${{ inputs.confirm }}" != "TRAIN" ]]', source)
        self.assertIn('TEACHER_RUN_ID: "41373086676"', source)
        self.assertIn('TEACHER_ARTIFACT_NAME: "gemma4-verifier-sft-teacher-v0-evidence"', source)
        self.assertIn(
            'EXPECTED_DATASET_SHA256: "188e22d59351ff08e1c3ced0365addaf19ffb9c68ce64df4cafd3e1cce7ecb8c"',
            source,
        )
        self.assertIn("actions/download-artifact@v4", source)
        self.assertIn("run-id: ${{ env.TEACHER_RUN_ID }}", source)

    def test_workflow_pins_e4b_model_and_single_gpu_training_path(self):
        source = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn(
            'MODEL_SOURCE: "google/gemma-4/transformers/gemma-4-e4b-it-qat-q4_0-unquantized/2"',
            source,
        )
        self.assertIn('"enable_gpu": true', source)
        self.assertIn('"model_sources": ["${MODEL_SOURCE}"]', source)
        self.assertIn("kaggle kernels push -p", source)
        self.assertIn("kaggle kernels output", source)
        self.assertNotIn("for rank in", source)
        self.assertNotIn("for lr in", source)
        self.assertNotIn("grid", source.lower())
        self.assertNotIn("sweep", source.lower())

    def test_workflow_verifies_adapter_and_never_submits_competition(self):
        source = WORKFLOW.read_text(encoding="utf-8")
        for required in (
            "training_report.json",
            "adapter_config.json",
            "adapter_model.safetensors",
            "dataset_sha256",
            "verified_submit",
            "safe_stop",
            "sha256sum",
            "actions/upload-artifact@v4",
        ):
            self.assertIn(required, source)
        self.assertNotIn("kaggle competitions submit", source)
        self.assertNotIn("verifier-lora-blind", source)
        self.assertNotIn("solution.parquet", source)
        self.assertNotIn("solution.csv", source)


if __name__ == "__main__":
    unittest.main()
