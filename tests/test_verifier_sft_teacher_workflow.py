from pathlib import Path
import unittest

from kaggle.verifier_gold_teacher_supervision import DIFF_COMMAND


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "kaggle" / "verifier_sft_teacher_runtime.py"
WORKFLOW = ROOT / ".github" / "workflows" / "run-verifier-sft-teacher.yml"
BUNDLER = ROOT / "scripts" / "render_verifier_sft_teacher.py"
PLAN = ROOT / "docs" / "evaluation" / "verifier-lora-targeted-tests-v0.json"


class VerifierSftTeacherRuntimeContractTests(unittest.TestCase):
    def test_runtime_collects_paired_base_and_gold_deterministic_evidence(self):
        self.assertTrue(RUNTIME.is_file())
        source = RUNTIME.read_text(encoding="utf-8")
        self.assertIn('TARGETED_TEST_PLAN_JSON = "__VERIFIER_LORA_TARGETED_TEST_PLAN_JSON__"', source)
        self.assertIn('TEACHER_BUILD_ID = "__VERIFIER_SFT_TEACHER_BUILD_ID__"', source)
        self.assertIn("load_targeted_test_plan", source)
        self.assertIn("build_teacher_safe_stop_record", source)
        self.assertIn("build_teacher_supervision_record", source)
        self.assertIn("base_targeted_test", source)
        self.assertIn("gold_targeted_test", source)
        self.assertIn("apply_patch_in_container", source)
        self.assertIn("setup_baseline_commit", source)
        self.assertNotIn("original_setup_baseline_commit", source)
        self.assertEqual(DIFF_COMMAND, "git diff --check && git diff")
        self.assertIn("DIFF_COMMAND", source)
        self.assertIn('"teacher_build_id": TEACHER_BUILD_ID', source)
        self.assertIn('SUPERVISION_PATH = WORKING_DIR / "verifier_gold_teacher_supervision.json"', source)
        self.assertNotIn("blind_evaluation", source)
        self.assertNotIn("test_patch", source)

    def test_renderer_bundles_sibling_modules_into_one_code_file(self):
        self.assertTrue(BUNDLER.is_file())
        from scripts.render_verifier_sft_teacher import bundle_runtime

        bundled = bundle_runtime(
            RUNTIME.read_text(encoding="utf-8"),
            "MODEL_NAME = 'dummy'\nWORKING_DIR = None\nAGENT_DIR = None\n",
            "DIFF_COMMAND = 'git diff --check && git diff'\n"
            "def build_teacher_safe_stop_record(**kwargs): return kwargs\n"
            "def build_teacher_supervision_record(**kwargs): return kwargs\n"
            "def load_targeted_test_plan(*args): return {}\n",
        )
        self.assertNotIn("import verifier_gold_teacher_runtime as gold", bundled)
        self.assertNotIn("from verifier_gold_teacher_supervision import (", bundled)
        self.assertIn("build_teacher_safe_stop_record = _supervision_helper.build_teacher_safe_stop_record", bundled)
        self.assertIn("_load_embedded_module", bundled)
        compile(bundled, "bundled_verifier_sft_teacher.py", "exec")

    def test_workflow_uses_single_file_renderer_instead_of_sibling_copies(self):
        self.assertTrue(WORKFLOW.is_file())
        source = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("render_verifier_sft_teacher", source)
        self.assertIn("bundle_runtime", source)
        self.assertIn("verifier_gold_teacher_runtime.py", source)
        self.assertIn("verifier_gold_teacher_supervision.py", source)
        self.assertNotIn("shutil.copy2(helper", source)
        self.assertNotIn("shutil.copy2(gold_runtime", source)

    def test_workflow_fails_closed_on_push_error_and_stale_kernel_output(self):
        source = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn('TEACHER_BUILD_ID: ${{ github.sha }}', source)
        self.assertIn('KERNEL_REF: kolihhan/gemma-4-verifier-sft-teacher-v0-${{ github.run_id }}', source)
        self.assertIn('KERNEL_TITLE: Gemma 4 Verifier SFT Teacher v0 ${{ github.run_id }}', source)
        self.assertIn('"id": kernel_ref', source)
        self.assertIn('"title": kernel_title', source)
        self.assertIn("push_output=", source)
        self.assertIn("push_status=", source)
        self.assertIn("Kernel push error", source)
        self.assertIn('result.get("teacher_build_id") == os.environ["TEACHER_BUILD_ID"]', source)
        self.assertIn('__VERIFIER_SFT_TEACHER_BUILD_ID__', source)

    def test_workflow_embeds_frozen_targets_and_builds_balanced_sft_artifact(self):
        self.assertTrue(WORKFLOW.is_file())
        source = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("verifier-lora-targeted-tests-v0.json", source)
        self.assertIn("verifier_sft_teacher_runtime.py", source)
        self.assertIn('"enable_gpu": False', source)
        self.assertIn('"model_sources": []', source)
        self.assertIn("is_private", source)
        self.assertIn("scripts/build_verifier_sft.py", source)
        self.assertIn("verifier-sft-v0.jsonl", source)
        self.assertIn("example_id", source)
        self.assertIn("safe_stop", source)
        self.assertIn("verified_submit", source)
        self.assertIn("gemma4-verifier-sft-teacher-v0-evidence", source)

    def test_frozen_plan_has_exact_six_training_targets_and_requests_uses_inline_assertion(self):
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
        commands = {item["instance_id"]: item["command"] for item in payload["targets"]}
        self.assertIn("python -c", commands["requests_6644"])
        self.assertIn("assert", commands["requests_6644"])
        self.assertNotIn("tests/test_adapters.py", commands["requests_6644"])


if __name__ == "__main__":
    unittest.main()
