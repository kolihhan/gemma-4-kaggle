from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "kaggle" / "gold_control_runtime.py"


class GoldControlRuntimeContractTests(unittest.TestCase):
    def test_gold_control_runtime_exists(self):
        self.assertTrue(RUNTIME.is_file(), "kaggle/gold_control_runtime.py")

    def test_gold_control_uses_current_verifier_without_running_agent(self):
        text = RUNTIME.read_text(encoding="utf-8")
        self.assertIn('CONTROL_TASK_ID = "httpx_3672"', text)
        self.assertIn("verify_task", text)
        self.assertIn("_hydrate_task_from_secret", text)
        self.assertIn("resolve_task_snapshot_paths", text)
        self.assertIn("ModelRegistry()", text)
        self.assertNotIn("evaluate_task(", text)
        self.assertNotIn("VllmServer", text)
        self.assertNotIn("VllmConfig", text)

    def test_gold_patch_stays_verifier_side_and_result_is_structured(self):
        text = RUNTIME.read_text(encoding="utf-8")
        self.assertIn("reference_patch = task.patch", text)
        self.assertIn("agent_patch=reference_patch", text)
        self.assertIn("gold_control_result.json", text)
        self.assertIn("reference_patch_sha256", text)
        self.assertNotIn("reference_patch.diff", text)


if __name__ == "__main__":
    unittest.main()
