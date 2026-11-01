import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_verifier_training_subset.py"
SPLIT = ROOT / "docs" / "evaluation" / "verifier-lora-split-v0.json"
FROZEN = ROOT / "docs" / "evaluation" / "verifier-lora-train-subset-v0.json"


def load_module():
    spec = importlib.util.spec_from_file_location("build_verifier_training_subset", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class VerifierTrainingSubsetTests(unittest.TestCase):
    def require_module(self):
        if not SCRIPT.is_file():
            self.skipTest("training subset builder not implemented yet")
        return load_module()

    def test_builder_script_exists(self):
        self.assertTrue(SCRIPT.is_file())

    def test_selection_is_deterministic_unique_and_input_order_independent(self):
        module = self.require_module()
        split = {
            "version": "verifier-lora-v0",
            "train": [
                {"instance_id": "r1", "repo": "Textualize/rich", "patch_bucket": "1-10"},
                {"instance_id": "r2", "repo": "Textualize/rich", "patch_bucket": "11-30"},
                {"instance_id": "r3", "repo": "Textualize/rich", "patch_bucket": "31-80"},
                {"instance_id": "r4", "repo": "Textualize/rich", "patch_bucket": "81+"},
                {"instance_id": "f1", "repo": "fastapi/fastapi", "patch_bucket": "1-10"},
                {"instance_id": "f2", "repo": "fastapi/fastapi", "patch_bucket": "11-30"},
                {"instance_id": "f3", "repo": "fastapi/fastapi", "patch_bucket": "31-80"},
                {"instance_id": "q1", "repo": "psf/requests", "patch_bucket": "1-10"},
                {"instance_id": "q2", "repo": "psf/requests", "patch_bucket": "11-30"},
            ],
            "holdout": [{"instance_id": "held", "repo": "Textualize/rich", "patch_bucket": "1-10"}],
            "excluded": [{"instance_id": "excluded", "repo": "fastapi/fastapi", "patch_bucket": "1-10"}],
        }
        quota = {"Textualize/rich": 3, "fastapi/fastapi": 2, "psf/requests": 2}

        first = module.build_training_subset(split, quota)
        second = module.build_training_subset({**split, "train": list(reversed(split["train"]))}, quota)

        self.assertEqual(first, second)
        ids = [item["instance_id"] for item in first["tasks"]]
        self.assertEqual(len(ids), 7)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertNotIn("held", ids)
        self.assertNotIn("excluded", ids)

    def test_selection_round_robins_patch_buckets_before_second_item(self):
        module = self.require_module()
        train = []
        for bucket in ("1-10", "11-30", "31-80", "81+"):
            for suffix in ("a", "b"):
                train.append(
                    {
                        "instance_id": f"rich-{bucket}-{suffix}",
                        "repo": "Textualize/rich",
                        "patch_bucket": bucket,
                    }
                )
        split = {"version": "verifier-lora-v0", "train": train, "holdout": [], "excluded": []}

        result = module.build_training_subset(split, {"Textualize/rich": 4})
        buckets = [item["patch_bucket"] for item in result["tasks"]]

        self.assertEqual(buckets, ["1-10", "11-30", "31-80", "81+"])

    def test_quota_larger_than_repo_pool_fails_loudly(self):
        module = self.require_module()
        split = {
            "version": "verifier-lora-v0",
            "train": [{"instance_id": "q1", "repo": "psf/requests", "patch_bucket": "1-10"}],
            "holdout": [],
            "excluded": [],
        }

        with self.assertRaisesRegex(ValueError, "not enough training tasks"):
            module.build_training_subset(split, {"psf/requests": 2})

    def test_real_manifest_freezes_18_train_only_tasks_with_expected_repo_counts(self):
        module = self.require_module()
        split = json.loads(SPLIT.read_text(encoding="utf-8"))

        result = module.build_training_subset(split)
        ids = [item["instance_id"] for item in result["tasks"]]
        train_ids = {item["instance_id"] for item in split["train"]}
        holdout_ids = {item["instance_id"] for item in split["holdout"]}
        excluded_ids = {item["instance_id"] for item in split["excluded"]}

        self.assertEqual(result["version"], "verifier-lora-v0-train-harvest")
        self.assertEqual(result["source_split_version"], "verifier-lora-v0")
        self.assertEqual(result["counts"]["tasks"], 18)
        self.assertEqual(
            result["counts"]["by_repo"],
            {"Textualize/rich": 8, "fastapi/fastapi": 8, "psf/requests": 2},
        )
        self.assertEqual(len(ids), 18)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(set(ids) <= train_ids)
        self.assertFalse(set(ids) & holdout_ids)
        self.assertFalse(set(ids) & excluded_ids)

    def test_frozen_manifest_exactly_matches_current_builder_output(self):
        module = self.require_module()
        split = json.loads(SPLIT.read_text(encoding="utf-8"))
        frozen = json.loads(FROZEN.read_text(encoding="utf-8"))

        self.assertEqual(frozen, module.build_training_subset(split))


if __name__ == "__main__":
    unittest.main()
