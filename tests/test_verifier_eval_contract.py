import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "evaluation" / "verifier-lora-eval-contract-v1.json"
SCREEN = ROOT / "docs" / "evaluation" / "verifier-lora-gold-screen-v0.json"
TRAIN_SUBSET = ROOT / "docs" / "evaluation" / "verifier-lora-train-subset-v0.json"

EXPECTED_DEV_IDS = {
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


class VerifierEvaluationContractTests(unittest.TestCase):
    def setUp(self):
        self.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        self.screen = json.loads(SCREEN.read_text(encoding="utf-8"))
        self.train_subset = json.loads(TRAIN_SUBSET.read_text(encoding="utf-8"))

    def test_inspected_clean_set_is_development_validation_not_blind(self):
        dev_ids = set(self.contract["development_validation"]["instance_ids"])
        self.assertEqual(dev_ids, EXPECTED_DEV_IDS)
        self.assertEqual(dev_ids, set(self.screen["clean_instance_ids"]))
        self.assertFalse(self.contract["development_validation"]["is_blind"])
        self.assertEqual(self.contract["development_validation"]["role"], "development_validation")

    def test_development_coverage_does_not_claim_requests_generalization(self):
        coverage = self.contract["development_validation"]["coverage"]
        self.assertEqual(coverage, {"Textualize/rich": 4, "fastapi/fastapi": 5, "psf/requests": 0})
        self.assertIn("Requests", self.contract["development_validation"]["claim_limit"])

    def test_blind_set_must_be_frozen_before_promotion(self):
        blind = self.contract["blind_evaluation"]
        self.assertIn(blind["status"], {"pending_freeze", "frozen"})
        self.assertTrue(self.contract["promotion"]["requires_frozen_blind_evaluation"])

        blind_ids = set(blind["instance_ids"])
        harvested_ids = {item["instance_id"] for item in self.train_subset["tasks"]}
        self.assertFalse(blind_ids & harvested_ids)

        if blind["status"] == "pending_freeze":
            self.assertEqual(blind_ids, set())
        else:
            self.assertTrue(blind_ids)
            self.assertTrue(blind["automated_gold_control_only"])
            self.assertTrue(blind["base_failure_traces_uninspected_before_adapter_freeze"])

    def test_no_adapter_artifact_is_promotable_while_blind_is_pending(self):
        adapter_dir = ROOT / "submission" / "adapters"
        adapter_files = list(adapter_dir.rglob("*.safetensors")) if adapter_dir.exists() else []
        if adapter_files:
            self.assertEqual(
                self.contract["blind_evaluation"]["status"],
                "frozen",
                "adapter artifacts must not enter the candidate submission before blind evaluation is frozen",
            )


if __name__ == "__main__":
    unittest.main()
