from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "kaggle" / "gold_sample_runtime.py"

EXPECTED_IDS = (
    "rich_3278",
    "rich_2725",
    "rich_3930",
    "httpx_3672",
    "fastapi_14361",
    "fastapi_14266",
    "fastapi_14609",
    "requests_6592",
    "requests_7502",
    "requests_6757",
)


class GoldSampleRuntimeContractTests(unittest.TestCase):
    def test_runtime_exists_and_freezes_diagnostic_holdout(self):
        self.assertTrue(RUNTIME.is_file(), "kaggle/gold_sample_runtime.py")
        text = RUNTIME.read_text(encoding="utf-8")
        for instance_id in EXPECTED_IDS:
            self.assertIn(f'"{instance_id}"', text)
        self.assertIn("DIAGNOSTIC_TASK_IDS", text)

    def test_runtime_uses_reference_patch_only_inside_verifier_control(self):
        text = RUNTIME.read_text(encoding="utf-8")
        self.assertIn("verify_task", text)
        self.assertIn("reference_patch = task.patch", text)
        self.assertIn("reference_patch_sha256", text)
        self.assertNotIn('"reference_patch": reference_patch', text)
        self.assertNotIn("'reference_patch': reference_patch", text)

    def test_runtime_records_each_task_without_aborting_whole_sample(self):
        text = RUNTIME.read_text(encoding="utf-8")
        self.assertIn("results.append", text)
        self.assertIn("except BaseException as exc", text)
        self.assertIn('"status": "error"', text)
        self.assertIn("gold_sample_results.json", text)

    def test_holdout_is_not_a_training_export(self):
        text = RUNTIME.read_text(encoding="utf-8")
        self.assertNotIn("training_examples", text)
        self.assertNotIn("sft", text.lower())


if __name__ == "__main__":
    unittest.main()
