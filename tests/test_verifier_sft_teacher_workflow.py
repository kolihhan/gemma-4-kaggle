from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "kaggle" / "verifier_sft_teacher_runtime.py"
WORKFLOW = ROOT / ".github" / "workflows" / "run-verifier-sft-teacher.yml"
PLAN = ROOT / "docs" / "evaluation" / "verifier-lora-targeted-tests-v0.json"


class VerifierSftTeacherRuntimeContractTests(unittest.TestCase):
    def test_runtime_collects_deterministic_gold_workspace_evidence(self):
        self.assertTrue(RUNTIME.is_file())
        source = RUNTIME.read_text(encoding="utf-8")
        self.assertIn('TARGETED_TEST_PLAN_JSON = "__VERIFIER_LORA_TARGETED_TEST_PLAN_JSON__"', source)
        self.assertIn("load_targeted_test_plan", source)
        self.assertIn("build_teacher_supervision_record", source)
        self.assertIn("apply_patch_in_container", source)
        self.assertIn("original_setup_baseline_commit", source)
        self.assertIn("git diff --check && git diff", source)
        self.assertIn('SUPERVISION_PATH = WORKING_DIR / "verifier_gold_teacher_supervision.json"', source)
        self.assertNotIn("blind_evaluation", source)
        self.assertNotIn("test_patch", source)

    def test_workflow_embeds_frozen_targets_and_builds_sft_artifact(self):
        self.assertTrue(WORKFLOW.is_file())
        source = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("verifier-lora-targeted-tests-v0.json", source)
        self.assertIn("verifier_sft_teacher_runtime.py", source)
        self.assertIn("verifier_gold_teacher_supervision.py", source)
        self.assertIn("machine_shape", source)
        self.assertIn("NvidiaL4", source)
        self.assertIn("is_private", source)
        self.assertIn("scripts/build_verifier_sft.py", source)
        self.assertIn("verifier-sft-v0.jsonl", source)
        self.assertIn("gemma4-verifier-sft-teacher-v0-evidence", source)

    def test_frozen_plan_has_exact_six_training_targets(self):
        import json

        payload = json.loads(PLAN.read_text(encoding="utf-8"))
        self.assertEqual(payload["version"], "verifier-lora-v0-targeted-tests")
        self.assertEqual(payload["status"], "frozen")
        ids = [item["instance_id"] for item in payload["targets"]]
        self.assertEqual(
            ids,
            [
                "fastapi_14479",
                "requests_6644",
                "rich_3718",
                "rich_3882",
                "rich_3953",
                "rich_4006",
            ],
        )
        self.assertEqual(len(ids), len(set(ids)))


if __name__ == "__main__":
    unittest.main()
