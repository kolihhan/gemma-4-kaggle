import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "kaggle" / "verifier_baseline_runtime.py"


class VerifierBaselineRuntimeContractTests(unittest.TestCase):
    def test_runtime_exists_and_uses_embedded_submission_and_holdout(self):
        self.assertTrue(RUNTIME.is_file())
        text = RUNTIME.read_text(encoding="utf-8")

        self.assertIn('SUBMISSION_PAYLOAD_B64 = "__SUBMISSION_PAYLOAD_B64__"', text)
        self.assertIn('HOLDOUT_MANIFEST_JSON = "__VERIFIER_LORA_HOLDOUT_MANIFEST_JSON__"', text)
        self.assertIn("materialize_submission", text)
        self.assertIn("load_holdout_ids", text)
        self.assertIn('"verifier-lora-v0"', text)

    def test_runtime_keeps_base_e4b_and_rejects_adapters(self):
        text = RUNTIME.read_text(encoding="utf-8")

        self.assertIn('MODEL_NAME = "gemma-4-e4b-it-qat-w4a16-ct"', text)
        self.assertIn("discover_adapters", text)
        self.assertIn("baseline v0 must not contain adapters", text)
        self.assertIn("enable_lora=False", text)

    def test_runtime_reuses_one_server_for_all_holdout_tasks(self):
        tree = ast.parse(RUNTIME.read_text(encoding="utf-8"))
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
        text = RUNTIME.read_text(encoding="utf-8")
        self.assertIn("for index, task_id in enumerate(holdout_ids, 1):", text)

    def test_runtime_does_not_read_reference_solution_fields(self):
        text = RUNTIME.read_text(encoding="utf-8")

        self.assertNotIn(".patch", text)
        self.assertNotIn("test_patch", text)
        self.assertNotIn("FAIL_TO_PASS", text)
        self.assertNotIn("PASS_TO_PASS", text)

    def test_result_schema_records_agent_quality_without_raw_patch(self):
        text = RUNTIME.read_text(encoding="utf-8")

        for token in (
            '"instance_id"',
            '"resolved"',
            '"test_exit_code"',
            '"patch_chars"',
            '"has_patch"',
            '"tool_calls"',
            '"duration_seconds"',
        ):
            self.assertIn(token, text)
        self.assertNotIn('"agent_patch":', text)
        self.assertIn("BASELINE_RESULT", text)


if __name__ == "__main__":
    unittest.main()
