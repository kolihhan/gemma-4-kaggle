from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "kaggle" / "smoke_runtime.py"


class SmokeRuntimeContractTests(unittest.TestCase):
    def test_runtime_exists_and_uses_embedded_canonical_submission(self):
        self.assertTrue(RUNTIME.is_file(), "kaggle/smoke_runtime.py")
        text = RUNTIME.read_text(encoding="utf-8")
        self.assertIn('SUBMISSION_PAYLOAD_B64 = "__SUBMISSION_PAYLOAD_B64__"', text)
        self.assertIn("base64.b64decode", text)
        self.assertIn("validate_directory", text)
        self.assertIn("discover_declared_models", text)

    def test_runtime_is_exactly_one_public_smoke_task(self):
        text = RUNTIME.read_text(encoding="utf-8")
        self.assertIn('SMOKE_TASK_ID = "httpx_3672"', text)
        self.assertIn("evaluate_task", text)
        self.assertIn("smoke_result.json", text)
        self.assertNotIn("tasks[:2]", text)

    def test_runtime_uses_current_e4b_and_official_runtime_shape(self):
        text = RUNTIME.read_text(encoding="utf-8")
        self.assertIn('MODEL_NAME = "gemma-4-e4b-it-qat-w4a16-ct"', text)
        self.assertIn("tool_call_parser=\"gemma4\"", text)
        self.assertIn("reasoning_parser=\"gemma4\"", text)
        self.assertIn("max_model_len=32768", text)
        self.assertIn("tensor_parallel_size=tp_size", text)
        self.assertIn("sandbox=\"subprocess\"", text)

    def test_runtime_does_not_read_reference_solution_fields(self):
        text = RUNTIME.read_text(encoding="utf-8")
        self.assertNotIn('["patch"]', text)
        self.assertNotIn("['patch']", text)
        self.assertNotIn('["test_patch"]', text)
        self.assertNotIn("['test_patch']", text)


if __name__ == "__main__":
    unittest.main()
