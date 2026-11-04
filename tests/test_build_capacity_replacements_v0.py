"""CPU-only regression tests for the frozen capacity replacement queue."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import build_capacity_replacements_v0 as repl


ROOT = Path(__file__).resolve().parents[1]


class CapacityReplacementQueueTests(unittest.TestCase):
    def test_vetted_gold_and_noop_sources_bind_to_original_frozen_selector(self):
        result = repl.build_plan(ROOT)
        self.assertEqual(result["source_selector_sha256"], repl.FROZEN_SELECTOR)
        self.assertEqual(result["source_noop_artifact_id"], 13300818683)
        self.assertEqual(result["original_screened"], 16)
        self.assertEqual(result["original_doubly_eligible"], 10)
        self.assertEqual(
            result["missing_by_cohort"],
            {
                "feasibility": {"Textualize/rich": 0, "fastapi/fastapi": 1},
                "confirmation": {"Textualize/rich": 1, "fastapi/fastapi": 4},
            },
        )
        self.assertEqual(result["replacement_slots_total"], 6)
        self.assertFalse(result["contains_task_text"])
        self.assertEqual(result["status"], "FROZEN_ORDER_UNSCREENED_NOT_BLIND_CERTIFIED")

    def test_replacement_rank_is_deterministic_disjoint_and_from_original_train_metadata(self):
        first = repl.build_plan(ROOT)
        second = repl.build_plan(ROOT)
        self.assertEqual(first, second)
        selected = first["original_ids"]
        all_queue = [x for q in first["queues"].values() for x in q]
        self.assertEqual(len(all_queue), len(set(all_queue)))
        self.assertFalse(set(all_queue) & set(selected))
        self.assertGreaterEqual(len(first["queues"]["Textualize/rich"]), 1)
        self.assertGreaterEqual(len(first["queues"]["fastapi/fastapi"]), 5)
        for repo_name, queue in first["queues"].items():
            self.assertTrue(all(x.startswith("rich_" if repo_name == "Textualize/rich" else "fastapi_") for x in queue))

    def test_noop_artifact_tampering_or_mismatched_ids_fails_closed(self):
        official = json.loads((ROOT / repl.NOOP_METADATA).read_text(encoding="utf-8"))
        changed_cases = []
        changed = json.loads(json.dumps(official))
        changed["results"][0]["noop_fail"] = False
        changed_cases.append(changed)
        changed = json.loads(json.dumps(official))
        changed["results"][0]["instance_id"] = "fastapi_999999"
        changed_cases.append(changed)
        changed = json.loads(json.dumps(official))
        changed["selector_sha256"] = "bad"
        changed_cases.append(changed)
        changed = json.loads(json.dumps(official))
        changed["results"][0]["test_exit_code"] = 0
        changed_cases.append(changed)
        for corrupted in changed_cases:
            with self.subTest(corrupted=corrupted["results"][0]):
                with patch.object(repl, "read_noop", return_value=corrupted):
                    with self.assertRaises(ValueError):
                        repl.build_plan(ROOT)

    def test_refuses_overwrite_and_serializes_only_metadata(self):
        plan = repl.build_plan(ROOT)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "replacements.json"
            repl.write_plan(plan, path)
            restored = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(plan, restored)
            forbidden = ("reference_patch", "test_patch", "agent_patch", "issue_text", "problem_statement")
            serialized = path.read_text(encoding="utf-8").lower()
            for sensitive in forbidden:
                self.assertNotIn('"' + sensitive + '"', serialized)
            with self.assertRaises(FileExistsError):
                repl.write_plan(plan, path)


if __name__ == "__main__":
    unittest.main()
