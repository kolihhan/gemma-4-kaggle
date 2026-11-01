import json
import unittest
from pathlib import Path

from scripts.build_verifier_blind_reservation import build_blind_reservation


ROOT = Path(__file__).resolve().parents[1]
SPLIT = ROOT / "docs" / "evaluation" / "verifier-lora-split-v0.json"
TRAIN_SUBSET = ROOT / "docs" / "evaluation" / "verifier-lora-train-subset-v0.json"


class VerifierBlindReservationTests(unittest.TestCase):
    def setUp(self):
        self.split = json.loads(SPLIT.read_text(encoding="utf-8"))
        self.harvest = json.loads(TRAIN_SUBSET.read_text(encoding="utf-8"))

    def test_real_reservation_is_reproducible_and_disjoint(self):
        first = build_blind_reservation(self.split, self.harvest)
        second = build_blind_reservation(self.split, self.harvest)
        self.assertEqual(first, second)

        blind_ids = {item["instance_id"] for item in first["tasks"]}
        train_ids = {item["instance_id"] for item in self.split["train"]}
        harvested_ids = {item["instance_id"] for item in self.harvest["tasks"]}
        old_holdout_ids = {item["instance_id"] for item in self.split["holdout"]}

        self.assertEqual(len(blind_ids), 10)
        self.assertTrue(blind_ids <= train_ids)
        self.assertFalse(blind_ids & harvested_ids)
        self.assertFalse(blind_ids & old_holdout_ids)
        self.assertEqual(
            first["counts"]["by_repo"],
            {"Textualize/rich": 4, "fastapi/fastapi": 6, "psf/requests": 0},
        )
        print("blind_reservation_instance_ids=", sorted(blind_ids))

    def test_requests_has_no_unharvested_blind_candidate(self):
        harvested_ids = {item["instance_id"] for item in self.harvest["tasks"]}
        requests_train = [
            item for item in self.split["train"] if item["repo"] == "psf/requests"
        ]
        self.assertEqual(len(requests_train), 2)
        self.assertTrue(all(item["instance_id"] in harvested_ids for item in requests_train))

    def test_reservation_records_metadata_only(self):
        reservation = build_blind_reservation(self.split, self.harvest)
        self.assertEqual(reservation["version"], "verifier-lora-v0-blind-reservation")
        self.assertEqual(
            reservation["selection"]["method"],
            "bucket-round-robin-sha256-from-unharvested-training-pool",
        )
        self.assertEqual(
            set().union(*(item.keys() for item in reservation["tasks"])),
            {"instance_id", "repo", "patch_bucket"},
        )
        self.assertIn("Requests", reservation["coverage_limit"])


if __name__ == "__main__":
    unittest.main()
