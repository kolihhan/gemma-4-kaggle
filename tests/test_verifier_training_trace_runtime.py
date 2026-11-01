import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "kaggle" / "verifier_training_trace_runtime.py"
WORKFLOW = ROOT / ".github" / "workflows" / "run-verifier-training-trace-harvest.yml"
EXPECTED_KERNEL_REF = "kolihhan/gemma-4-verifier-training-trace-harvest-v0"


class VerifierTrainingTraceRuntimeTests(unittest.TestCase):
    def require_runtime(self) -> str:
        if not RUNTIME.is_file():
            self.skipTest("training trace runtime not implemented yet")
        return RUNTIME.read_text(encoding="utf-8")

    def require_workflow(self) -> str:
        if not WORKFLOW.is_file():
            self.skipTest("training trace workflow not implemented yet")
        return WORKFLOW.read_text(encoding="utf-8")

    def test_runtime_exists(self):
        self.assertTrue(RUNTIME.is_file())

    def test_runtime_uses_embedded_submission_and_training_subset(self):
        text = self.require_runtime()

        self.assertIn('SUBMISSION_PAYLOAD_B64 = "__SUBMISSION_PAYLOAD_B64__"', text)
        self.assertIn(
            'TRAINING_MANIFEST_JSON = "__VERIFIER_LORA_TRAINING_MANIFEST_JSON__"',
            text,
        )
        self.assertIn("materialize_submission", text)
        self.assertIn("load_training_ids", text)
        self.assertIn('"verifier-lora-v0-train-harvest"', text)

    def test_runtime_keeps_base_e4b_and_rejects_adapters(self):
        text = self.require_runtime()

        self.assertIn('MODEL_NAME = "gemma-4-e4b-it-qat-w4a16-ct"', text)
        self.assertIn("discover_adapters", text)
        self.assertIn("training trace v0 must not contain adapters", text)
        self.assertIn("enable_lora=False", text)

    def test_runtime_reuses_one_server_for_all_training_tasks(self):
        text = self.require_runtime()
        tree = ast.parse(text)
        starts = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "start"
        ]
        evaluations = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "evaluate_task"
        ]

        self.assertEqual(len(starts), 1)
        self.assertEqual(len(evaluations), 1)
        self.assertIn("for index, task_id in enumerate(training_ids, 1):", text)

    def test_runtime_writes_structured_summary_and_keeps_full_evaluator_artifacts(self):
        text = self.require_runtime()

        self.assertIn('RESULTS_DIR = WORKING_DIR / "verifier-training-trace-results"', text)
        self.assertIn('SUMMARY_PATH = WORKING_DIR / "verifier_training_trace_results.json"', text)
        for token in (
            '"instance_id"',
            '"resolved"',
            '"test_exit_code"',
            '"patch_chars"',
            '"has_patch"',
            '"tool_calls"',
            '"duration_seconds"',
            '"resolved_instance_ids"',
        ):
            self.assertIn(token, text)
        self.assertIn("TRAINING_TRACE_RESULT", text)
        self.assertIn("TRAINING_TRACE_SUMMARY", text)

    def test_runtime_does_not_read_reference_solution_fields(self):
        text = self.require_runtime()

        self.assertNotIn(".patch", text)
        self.assertNotIn("test_patch", text)
        self.assertNotIn("FAIL_TO_PASS", text)
        self.assertNotIn("PASS_TO_PASS", text)
        self.assertNotIn('"agent_patch":', text)

    def test_training_trace_workflow_exists(self):
        self.assertTrue(WORKFLOW.is_file())

    def test_workflow_locks_kernel_identity_gpu_and_timeouts(self):
        text = self.require_workflow()

        self.assertIn("timeout-minutes: 150", text)
        self.assertIn(f"KERNEL_REF: {EXPECTED_KERNEL_REF}", text)
        self.assertIn(f'"id": "{EXPECTED_KERNEL_REF}"', text)
        self.assertIn('"machine_shape": "NvidiaL4"', text)
        self.assertIn("--accelerator NvidiaL4 -t 7200", text)
        self.assertIn(
            '"google/gemma-4/Other/gemma-4-e4b-it-qat-w4a16-ct/2"',
            text,
        )

    def test_workflow_embeds_frozen_training_manifest_and_asserts_all_ids_in_order(self):
        text = self.require_workflow()

        self.assertIn("verifier-lora-train-subset-v0.json", text)
        self.assertIn("__VERIFIER_LORA_TRAINING_MANIFEST_JSON__", text)
        self.assertIn('expected_ids = [item["instance_id"] for item in manifest["tasks"]]', text)
        self.assertIn('result.get("requested") == len(expected_ids)', text)
        self.assertIn(
            '[item.get("instance_id") for item in result.get("results", [])] == expected_ids',
            text,
        )

    def test_workflow_always_uploads_full_training_trace_evidence(self):
        text = self.require_workflow()

        self.assertIn("name: gemma4-verifier-training-trace-harvest-v0-evidence", text)
        self.assertIn("if: always()", text)
        self.assertIn("verifier_training_trace_results.json", text)
        self.assertIn("verifier-training-trace-results", text)


if __name__ == "__main__":
    unittest.main()
