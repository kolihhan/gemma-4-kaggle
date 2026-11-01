import unittest

from scripts.freeze_verifier_training_gold_screen import GoldScreenError, freeze_screen


TRAINING = {
    "version": "verifier-lora-v0-train-harvest",
    "tasks": [
        {"instance_id": "rich_1", "repo": "Textualize/rich", "patch_bucket": "1-10"},
        {"instance_id": "fastapi_2", "repo": "fastapi/fastapi", "patch_bucket": "11-30"},
    ],
}


def sweep(results):
    clean = sorted(
        item["instance_id"]
        for item in results
        if item.get("status") == "completed"
        and item.get("resolved") is True
        and item.get("test_exit_code") == 0
    )
    confounded = sorted({item["instance_id"] for item in results} - set(clean))
    return {
        "version": "verifier-lora-v0",
        "status": "completed",
        "control": "gold_reference_patch",
        "requested": 2,
        "completed": 2,
        "clean": len(clean),
        "confounded": len(confounded),
        "clean_instance_ids": clean,
        "confounded_instance_ids": confounded,
        "results": results,
    }


class FreezeTrainingGoldScreenTests(unittest.TestCase):
    def test_freezes_only_metadata_for_exact_training_denominator(self):
        output = freeze_screen(
            training_manifest=TRAINING,
            sweep=sweep(
                [
                    {
                        "instance_id": "rich_1",
                        "repo": "Textualize/rich",
                        "status": "completed",
                        "resolved": True,
                        "test_exit_code": 0,
                        "reference_patch_sha256": "a" * 64,
                    },
                    {
                        "instance_id": "fastapi_2",
                        "repo": "fastapi/fastapi",
                        "status": "completed",
                        "resolved": False,
                        "test_exit_code": 1,
                        "reference_patch_sha256": "b" * 64,
                    },
                ]
            ),
            source_run_id=123,
            source_artifact_id=456,
            source_artifact_digest="sha256:" + "c" * 64,
        )
        self.assertEqual(output["version"], "verifier-lora-v0-training-gold-screen")
        self.assertEqual(output["status"], "frozen")
        self.assertEqual(output["source_training_manifest"], "verifier-lora-v0-train-harvest")
        self.assertEqual(output["clean_instance_ids"], ["rich_1"])
        self.assertEqual(output["confounded_instance_ids"], ["fastapi_2"])
        self.assertEqual(output["counts"], {"requested": 2, "clean": 1, "confounded": 1})
        self.assertNotIn("results", output)
        self.assertNotIn("reference_patch", repr(output))

    def test_rejects_incomplete_or_wrong_denominator(self):
        base = sweep(
            [
                {"instance_id": "rich_1", "repo": "Textualize/rich", "status": "completed", "resolved": True, "test_exit_code": 0},
                {"instance_id": "fastapi_2", "repo": "fastapi/fastapi", "status": "completed", "resolved": True, "test_exit_code": 0},
            ]
        )
        bad = dict(base, completed=1)
        with self.assertRaises(GoldScreenError):
            freeze_screen(TRAINING, bad, 1, 2, "sha256:x")

        wrong_ids = dict(base)
        wrong_ids["results"] = [
            base["results"][0],
            {"instance_id": "blind_9", "repo": "x/y", "status": "completed", "resolved": True, "test_exit_code": 0},
        ]
        wrong_ids["clean_instance_ids"] = ["blind_9", "rich_1"]
        with self.assertRaises(GoldScreenError):
            freeze_screen(TRAINING, wrong_ids, 1, 2, "sha256:x")

    def test_recomputes_summary_and_rejects_tampered_clean_ids(self):
        result = sweep(
            [
                {"instance_id": "rich_1", "repo": "Textualize/rich", "status": "completed", "resolved": True, "test_exit_code": 0},
                {"instance_id": "fastapi_2", "repo": "fastapi/fastapi", "status": "completed", "resolved": False, "test_exit_code": 1},
            ]
        )
        result["clean_instance_ids"] = ["fastapi_2"]
        result["confounded_instance_ids"] = ["rich_1"]
        with self.assertRaisesRegex(GoldScreenError, "summary"):
            freeze_screen(TRAINING, result, 1, 2, "sha256:x")

    def test_rejects_raw_reference_patch_leakage(self):
        result = sweep(
            [
                {
                    "instance_id": "rich_1",
                    "repo": "Textualize/rich",
                    "status": "completed",
                    "resolved": True,
                    "test_exit_code": 0,
                    "reference_patch": "secret",
                },
                {"instance_id": "fastapi_2", "repo": "fastapi/fastapi", "status": "completed", "resolved": False, "test_exit_code": 1},
            ]
        )
        with self.assertRaisesRegex(GoldScreenError, "reference_patch"):
            freeze_screen(TRAINING, result, 1, 2, "sha256:x")


if __name__ == "__main__":
    unittest.main()
