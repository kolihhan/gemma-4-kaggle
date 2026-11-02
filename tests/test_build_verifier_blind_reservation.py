import json
import unittest
from pathlib import Path

from scripts.build_verifier_blind_reservation import (
    build_blind_reservation,
    replace_confounded_blind,
)


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

    def test_replacement_prefers_same_repo_and_bucket_and_never_uses_harvested(self):
        split = {
            "version": "verifier-lora-v0",
            "train": [
                {"instance_id": "rich_old", "repo": "Textualize/rich", "patch_bucket": "1-10"},
                {"instance_id": "rich_next", "repo": "Textualize/rich", "patch_bucket": "1-10"},
                {"instance_id": "rich_harvested", "repo": "Textualize/rich", "patch_bucket": "1-10"},
                {"instance_id": "rich_other", "repo": "Textualize/rich", "patch_bucket": "11-30"},
                {"instance_id": "fast_keep", "repo": "fastapi/fastapi", "patch_bucket": "1-10"},
            ],
        }
        harvested = {
            "version": "verifier-lora-v0-train-harvest",
            "tasks": [
                {"instance_id": "rich_harvested", "repo": "Textualize/rich", "patch_bucket": "1-10"}
            ],
        }
        reservation = {
            "version": "verifier-lora-v0-blind-reservation",
            "selection": {"metadata_only": True},
            "coverage_limit": "test",
            "counts": {"tasks": 2, "by_repo": {"Textualize/rich": 1, "fastapi/fastapi": 1}},
            "tasks": [
                {"instance_id": "rich_old", "repo": "Textualize/rich", "patch_bucket": "1-10"},
                {"instance_id": "fast_keep", "repo": "fastapi/fastapi", "patch_bucket": "1-10"},
            ],
        }
        replaced = replace_confounded_blind(
            reservation,
            split,
            harvested,
            {"rich_old"},
        )
        ids = {item["instance_id"] for item in replaced["tasks"]}
        self.assertEqual(ids, {"rich_next", "fast_keep"})
        self.assertNotIn("rich_harvested", ids)
        self.assertEqual(replaced["counts"], reservation["counts"])
        round1 = replaced["selection"]["gold_control_replacement_rounds"][0]
        self.assertEqual(round1["replacements"][0]["selection_scope"], "same_repo_same_bucket")
        self.assertEqual(round1["replacements"][0]["from"], "rich_old")
        self.assertEqual(round1["replacements"][0]["to"], "rich_next")

    def test_replacement_never_reuses_current_or_historical_blind_ids(self):
        split = {
            "version": "verifier-lora-v0",
            "train": [
                {"instance_id": "r1", "repo": "Textualize/rich", "patch_bucket": "1-10"},
                {"instance_id": "r2", "repo": "Textualize/rich", "patch_bucket": "1-10"},
                {"instance_id": "r3", "repo": "Textualize/rich", "patch_bucket": "1-10"},
            ],
        }
        harvested = {"version": "verifier-lora-v0-train-harvest", "tasks": []}
        reservation = {
            "version": "verifier-lora-v0-blind-reservation",
            "selection": {
                "metadata_only": True,
                "gold_control_replacement_rounds": [
                    {
                        "round": 1,
                        "replacements": [
                            {"from": "r1", "to": "r2", "repo": "Textualize/rich", "selection_scope": "same_repo_same_bucket", "from_patch_bucket": "1-10", "to_patch_bucket": "1-10"}
                        ],
                    }
                ],
            },
            "coverage_limit": "test",
            "counts": {"tasks": 1, "by_repo": {"Textualize/rich": 1}},
            "tasks": [
                {"instance_id": "r2", "repo": "Textualize/rich", "patch_bucket": "1-10"}
            ],
        }
        replaced = replace_confounded_blind(reservation, split, harvested, {"r2"})
        self.assertEqual([item["instance_id"] for item in replaced["tasks"]], ["r3"])

    def test_replacement_fails_without_exact_bucket_unless_fallback_explicit(self):
        split = {
            "version": "verifier-lora-v0",
            "train": [
                {"instance_id": "r1", "repo": "Textualize/rich", "patch_bucket": "1-10"},
                {"instance_id": "r2", "repo": "Textualize/rich", "patch_bucket": "11-30"},
            ],
        }
        harvested = {"version": "verifier-lora-v0-train-harvest", "tasks": []}
        reservation = {
            "version": "verifier-lora-v0-blind-reservation",
            "selection": {"metadata_only": True},
            "coverage_limit": "test",
            "counts": {"tasks": 1, "by_repo": {"Textualize/rich": 1}},
            "tasks": [
                {"instance_id": "r1", "repo": "Textualize/rich", "patch_bucket": "1-10"}
            ],
        }
        with self.assertRaisesRegex(ValueError, "same repo/bucket"):
            replace_confounded_blind(reservation, split, harvested, {"r1"})

        replaced = replace_confounded_blind(
            reservation,
            split,
            harvested,
            {"r1"},
            allow_same_repo_fallback=True,
        )
        self.assertEqual(replaced["tasks"][0]["instance_id"], "r2")
        self.assertEqual(
            replaced["selection"]["gold_control_replacement_rounds"][0]["replacements"][0]["selection_scope"],
            "same_repo_fallback",
        )


if __name__ == "__main__":
    unittest.main()
