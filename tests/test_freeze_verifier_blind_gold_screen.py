import unittest

from scripts.freeze_verifier_blind_gold_screen import BlindFreezeError, freeze_blind


RESERVATION = {
    "version": "verifier-lora-v0-blind-reservation",
    "tasks": [
        {"instance_id": "rich_1", "repo": "Textualize/rich", "patch_bucket": "1-10"},
        {"instance_id": "fastapi_2", "repo": "fastapi/fastapi", "patch_bucket": "11-30"},
    ],
}

CONTRACT = {
    "version": "verifier-lora-v0-eval-contract-v1",
    "blind_evaluation": {
        "status": "pending_freeze",
        "instance_ids": [],
        "automated_gold_control_only": True,
        "base_failure_traces_uninspected_before_adapter_freeze": True,
    },
    "promotion": {"requires_frozen_blind_evaluation": True},
}


def sweep(*, clean=True):
    results = [
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
            "resolved": clean,
            "test_exit_code": 0 if clean else 1,
            "reference_patch_sha256": "b" * 64,
        },
    ]
    clean_ids = ["fastapi_2", "rich_1"] if clean else ["rich_1"]
    confounded_ids = [] if clean else ["fastapi_2"]
    return {
        "version": "verifier-lora-v0",
        "status": "completed",
        "control": "gold_reference_patch",
        "requested": 2,
        "completed": 2,
        "clean": len(clean_ids),
        "confounded": len(confounded_ids),
        "clean_instance_ids": clean_ids,
        "confounded_instance_ids": confounded_ids,
        "results": results,
    }


class FreezeBlindGoldScreenTests(unittest.TestCase):
    def test_freezes_exact_clean_reservation_and_updates_contract(self):
        screen, contract = freeze_blind(
            reservation=RESERVATION,
            sweep=sweep(clean=True),
            eval_contract=CONTRACT,
            source_run_id=123,
            source_artifact_id=456,
            source_artifact_digest="sha256:" + "c" * 64,
        )
        self.assertEqual(screen["version"], "verifier-lora-v0-blind-gold-screen")
        self.assertEqual(screen["status"], "frozen")
        self.assertEqual(screen["instance_ids"], ["rich_1", "fastapi_2"])
        self.assertEqual(screen["counts"], {"requested": 2, "clean": 2, "confounded": 0})
        self.assertNotIn("results", screen)
        self.assertNotIn("reference_patch", repr(screen))

        blind = contract["blind_evaluation"]
        self.assertEqual(blind["status"], "frozen")
        self.assertEqual(blind["instance_ids"], ["rich_1", "fastapi_2"])
        self.assertEqual(blind["gold_screen_source"], "docs/evaluation/verifier-lora-blind-gold-screen-v0.json")
        self.assertTrue(blind["automated_gold_control_only"])
        self.assertTrue(blind["base_failure_traces_uninspected_before_adapter_freeze"])

    def test_refuses_freeze_when_any_candidate_is_confounded(self):
        with self.assertRaisesRegex(BlindFreezeError, "confounded"):
            freeze_blind(
                RESERVATION,
                sweep(clean=False),
                CONTRACT,
                123,
                456,
                "sha256:x",
            )

    def test_refuses_incomplete_or_mismatched_denominator(self):
        bad = sweep(clean=True)
        bad["completed"] = 1
        with self.assertRaises(BlindFreezeError):
            freeze_blind(RESERVATION, bad, CONTRACT, 1, 2, "sha256:x")

        wrong = sweep(clean=True)
        wrong["results"][1]["instance_id"] = "blind_other"
        wrong["clean_instance_ids"] = ["blind_other", "rich_1"]
        with self.assertRaises(BlindFreezeError):
            freeze_blind(RESERVATION, wrong, CONTRACT, 1, 2, "sha256:x")

    def test_refuses_tampered_summary_or_reference_patch_leakage(self):
        tampered = sweep(clean=True)
        tampered["clean_instance_ids"] = ["rich_1"]
        with self.assertRaisesRegex(BlindFreezeError, "summary"):
            freeze_blind(RESERVATION, tampered, CONTRACT, 1, 2, "sha256:x")

        leaked = sweep(clean=True)
        leaked["results"][0]["reference_patch"] = "secret"
        with self.assertRaisesRegex(BlindFreezeError, "reference_patch"):
            freeze_blind(RESERVATION, leaked, CONTRACT, 1, 2, "sha256:x")

    def test_refuses_nonpending_or_wrong_contract(self):
        already = {
            **CONTRACT,
            "blind_evaluation": {**CONTRACT["blind_evaluation"], "status": "frozen"},
        }
        with self.assertRaises(BlindFreezeError):
            freeze_blind(RESERVATION, sweep(clean=True), already, 1, 2, "sha256:x")


if __name__ == "__main__":
    unittest.main()
