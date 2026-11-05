"""CPU-only tests for discriminating-evidence v0's metadata-only fail-closed gate."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.discriminating_evidence_preflight import build_preflight, main, ROOT


class DiscriminatingEvidencePreflightTests(unittest.TestCase):
    def test_current_frozen_sources_prohibit_promotion(self) -> None:
        result = build_preflight(ROOT)
        self.assertEqual(
            result["candidate_counts"],
            {"Textualize/rich": 14, "fastapi/fastapi": 16},
        )
        self.assertEqual(
            result["replacement_counts"],
            {"Textualize/rich": 0, "fastapi/fastapi": 2},
        )
        self.assertEqual(result["status"], "NO_GO_INADEQUATE_REPLACEMENT_BUFFER")
        self.assertFalse(result["certifies_blind"])
        self.assertFalse(result["gold_noop_eligible"])
        self.assertFalse(result["history_audit_complete"])
        self.assertFalse(result["GPU_or_Kaggle_submission_authorized"])
        self.assertFalse(result["model_evaluation_executed"])

    def test_selection_is_deterministic_and_disjoint(self) -> None:
        a, b = build_preflight(ROOT), build_preflight(ROOT)
        self.assertEqual(a, b)
        self.assertEqual(len(a["pilot_ids"]), 4)
        self.assertEqual(len(a["confirmation_ids"]), 24)
        ids = a["pilot_ids"] + a["confirmation_ids"] + a["replacement_ids"]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(ids), 30)

    def test_reserved_capacity_denominator_is_excluded(self) -> None:
        capacity = json.loads(
            (ROOT / "docs/evaluation/capacity-v0-paired-cohort-2026-11-04.json")
            .read_text(encoding="utf-8")
        )
        reserved = {
            item["instance_id"] for key in ("feasibility", "confirmation")
            for item in capacity[key]
        }
        result = build_preflight(ROOT)
        candidate = set(
            result["pilot_ids"] + result["confirmation_ids"]
            + result["replacement_ids"]
        )
        self.assertFalse(candidate & reserved)

    def test_preflight_contains_no_task_text_or_patch(self) -> None:
        result = build_preflight(ROOT)
        self.assertEqual(
            set(result).intersection({
                "task_text", "reference_patch", "problem_description",
                "test_outputs", "candidate_patch",
            }),
            set(),
        )
        self.assertEqual(
            len(result["source_sha256"]), 11,
            "Every metadata source must be fingerprinted.",
        )


if __name__ == "__main__":
    unittest.main()
