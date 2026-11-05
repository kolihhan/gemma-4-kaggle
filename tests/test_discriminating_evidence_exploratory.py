"""Fail-closed exploratory cohort contract tests; no task text or model run."""
import json
import tempfile
import unittest
from pathlib import Path

from scripts.discriminating_evidence_exploratory import build_exploratory
from scripts.discriminating_evidence_preflight import build_preflight, ROOT


class ExploratoryCohortTests(unittest.TestCase):
    def test_4_plus_12_with_protected_replacement_buffer(self):
        r = build_exploratory(ROOT)
        self.assertEqual(len(r["pilot_ids"]), 4)
        self.assertEqual(len(r["exploratory_ids"]), 12)
        self.assertEqual(r["candidate_counts"], {"Textualize/rich": 14, "fastapi/fastapi": 16})
        self.assertEqual(r["replacement_counts"], {"Textualize/rich": 6, "fastapi/fastapi": 8})
        self.assertEqual(r["status"], "NO_GO_HISTORY_AND_ELIGIBILITY_UNCHECKED")
        self.assertFalse(r["certifies_blind"])
        self.assertFalse(r["gold_noop_eligible"])
        self.assertFalse(r["gpu_or_submission_authorized"])

    def test_nesting_preserves_original_ranked_selector(self):
        old = build_preflight(ROOT)
        new = build_exploratory(ROOT)
        self.assertEqual(new["pilot_ids"], old["pilot_ids"])
        self.assertEqual(new["exploratory_ids"][:6], old["confirmation_ids"][:6])
        self.assertEqual(new["exploratory_ids"][6:], old["confirmation_ids"][12:18])
        expected_replacements = (
            old["confirmation_ids"][6:12]
            + old["confirmation_ids"][18:24]
            + old["replacement_ids"]
        )
        self.assertEqual(new["replacement_ids"], expected_replacements)
        self.assertEqual(new["parent_selection_fingerprint_sha256"],
                         old["selection_fingerprint_sha256"])

    def test_all_30_ids_disjoint_from_existing_capacity_holdout(self):
        result = build_exploratory(ROOT)
        all_ids = result["pilot_ids"] + result["exploratory_ids"] + result["replacement_ids"]
        self.assertEqual(len(all_ids), 30)
        self.assertEqual(len(set(all_ids)), 30)
        reserved = json.loads(
            (ROOT / "docs/evaluation/capacity-v0-paired-cohort-2026-11-04.json")
            .read_text(encoding="utf-8")
        )
        reserved_ids = {
            i["instance_id"]
            for k in ("feasibility", "confirmation")
            for i in reserved[k]
        }
        self.assertFalse(reserved_ids.intersection(all_ids))

    def test_committed_manifest_matches_all_selected_ids_and_digest(self):
        manifest = json.loads(
            (ROOT / "docs/evaluation/discriminating-evidence-v0-exploratory-selection-2026-11-06.json")
            .read_text(encoding="utf-8")
        )
        generated = build_exploratory(ROOT)
        for key in ("version", "pilot_ids", "exploratory_ids", "replacement_ids",
                    "candidate_counts", "replacement_counts", "selection_digest_sha256"):
            self.assertEqual(manifest[key], generated[key], key)
        self.assertEqual(
            manifest["source_preflight_selection_digest"],
            generated["parent_selection_fingerprint_sha256"]
        )
        self.assertEqual(manifest["status"], "RESERVED_METADATA_ONLY_ELIGIBILITY_UNCHECKED")
        self.assertFalse(manifest["certifies_blind"])
        self.assertFalse(manifest["model_evaluation_executed"])

    def test_repeatable_and_metadata_only(self):
        result = build_exploratory(ROOT)
        self.assertEqual(result, build_exploratory(ROOT))
        self.assertTrue(result["selection_digest_sha256"])
        self.assertEqual(len(result["source_sha256"]), 11)
        self.assertFalse(result["history_audit_complete"])
        self.assertFalse(result["model_evaluation_executed"])
        self.assertEqual(
            set(result).intersection({"problem_description", "gold_patch", "test_logs", "task_text"}),
            set(),
        )


if __name__ == "__main__":
    unittest.main()
