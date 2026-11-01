import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPLIT = ROOT / "docs" / "evaluation" / "verifier-lora-split-v0.json"
SCREEN = ROOT / "docs" / "evaluation" / "verifier-lora-gold-screen-v0.json"
WORKFLOW = ROOT / ".github" / "workflows" / "run-verifier-baseline.yml"

EXPECTED_CLEAN_IDS = {
    "rich_3061",
    "rich_3067",
    "rich_3934",
    "rich_3942",
    "fastapi_13920",
    "fastapi_14077",
    "fastapi_14463",
    "fastapi_14851",
    "fastapi_14986",
}
EXPECTED_CONFOUNDED_IDS = {
    "fastapi_14485",
    "requests_7315",
    "requests_7328",
}


class VerifierCleanHoldoutContractTests(unittest.TestCase):
    def test_gold_screen_manifest_freezes_exact_sweep_denominator(self):
        self.assertTrue(SCREEN.is_file(), "gold-screen manifest must be persisted before baseline evaluation")
        screen = json.loads(SCREEN.read_text(encoding="utf-8"))
        split = json.loads(SPLIT.read_text(encoding="utf-8"))

        split_ids = {item["instance_id"] for item in split["holdout"]}
        clean_ids = set(screen["clean_instance_ids"])
        confounded_ids = {item["instance_id"] for item in screen["confounded"]}

        self.assertEqual(screen["version"], "verifier-lora-v0")
        self.assertEqual(screen["source_head_sha"], "3abeb1eee85c9995ec8642178fc160b729e291ed")
        self.assertEqual(screen["gold_sweep_run_id"], 41266798069)
        self.assertEqual(
            screen["artifact_digest"],
            "sha256:c50d25b7a569f831949ccfa844d8067e4e23d88dbe1f252a2933a220b17dee5b",
        )
        self.assertEqual(clean_ids, EXPECTED_CLEAN_IDS)
        self.assertEqual(confounded_ids, EXPECTED_CONFOUNDED_IDS)
        self.assertEqual(clean_ids | confounded_ids, split_ids)
        self.assertFalse(clean_ids & confounded_ids)

    def test_baseline_workflow_filters_frozen_split_to_gold_clean_ids(self):
        text = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("verifier-lora-gold-screen-v0.json", text)
        self.assertIn('screen["clean_instance_ids"]', text)
        self.assertIn('manifest["holdout"] = [', text)
        self.assertIn("clean_ids", text)
        self.assertIn("rendered_clean_holdout_ids", text)


if __name__ == "__main__":
    unittest.main()
