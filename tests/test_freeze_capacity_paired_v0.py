"""No-GPU synthetic contract tests for deterministic 4+12 metadata-only allocation."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts import freeze_capacity_paired_v0 as frozen
from scripts import render_capacity_replacement_noop_v0 as noop

ROOT = Path(__file__).resolve().parents[1]


def fake_noop():
    ids = noop.get_gold_pass_items(ROOT)
    rows = [{
        "instance_id": x["instance_id"], "repo": x["repo"],
        "status": "completed", "test_exit_code": 1,
        "noop_fail": True, "noop_pass": False,
        "ambiguous": False, "error_type": None,
    } for x in ids]
    return {
        "version": "capacity-v0-replacement-noop-eligibility",
        "source_run_id": frozen.NOOP_RUN_ID,
        "source_artifact_id": frozen.NOOP_ARTIFACT_ID,
        "source_artifact_zip_sha256": frozen.NOOP_ARTIFACT_SHA256,
        "source_gold_run_id": noop.GOLD_RUN,
        "source_gold_artifact_id": noop.GOLD_ARTIFACT,
        "source_gold_artifact_zip_sha256": noop.GOLD_ARTIFACT_SHA256,
        "source_selector_sha256": frozen.replacements.FROZEN_SELECTOR,
        "screened": len(rows),
        "noop_fail_count": len(rows),
        "noop_pass_count": 0,
        "ambiguous_count": 0,
        "results": rows,
        "contains_raw_patch_or_task_text": False,
    }


class FreezePairedCohortTests(unittest.TestCase):
    def run_with(self, data):
        with tempfile.TemporaryDirectory() as td:
            f = Path(td) / "screen.json"
            f.write_text(json.dumps(data), encoding="utf-8")
            return frozen.freeze(ROOT, f)

    def test_all_ten_replacements_noop_fail_produces_fixed_four_plus_twelve(self):
        out = self.run_with(fake_noop())
        self.assertEqual(out["version"], "capacity-v0-paired-denominator-v1")
        self.assertEqual(out["totals"]["replacements_used"], 6)
        self.assertFalse(out["contains_raw_patch_or_task_text"])
        self.assertFalse(out["model_evaluation_executed"])
        self.assertFalse(out["certifies_blind"])
        self.assertEqual([len(out["feasibility"]), len(out["confirmation"])], [4, 12])
        self.assertEqual(sum(x["source"]=="replacement" for x in out["feasibility"]), 1)
        self.assertEqual(sum(x["source"]=="replacement" for x in out["confirmation"]), 5)
        ids = [r["instance_id"] for key in ("feasibility", "confirmation") for r in out[key]]
        self.assertEqual(len(ids), len(set(ids)))
        for name, expected in (("feasibility", 2), ("confirmation", 6)):
            self.assertEqual(sum(x["repo"]=="Textualize/rich" for x in out[name]), expected)
            self.assertEqual(sum(x["repo"]=="fastapi/fastapi" for x in out[name]), expected)

    def test_one_noop_passing_fastapi_skips_without_cherry_picking(self):
        data = fake_noop()
        index = next(i for i, row in enumerate(data["results"]) if row["repo"] == "fastapi/fastapi")
        data["results"][index].update(
            noop_fail=False, noop_pass=True, test_exit_code=0,
        )
        data["noop_fail_count"] -= 1
        data["noop_pass_count"] += 1
        out = self.run_with(data)
        used = {x["instance_id"] for group in ("feasibility","confirmation") for x in out[group]}
        self.assertNotIn(data["results"][index]["instance_id"], used)
        self.assertEqual(out["totals"]["replacements_used"], 6)

    def test_shortage_fails_closed_without_partial_denom(self):
        data = fake_noop()
        fast = [r for r in data["results"] if r["repo"]=="fastapi/fastapi"]
        for row in fast[:2]:
            row.update(noop_fail=False, noop_pass=True, test_exit_code=0)
        data["noop_fail_count"] -= 2
        data["noop_pass_count"] += 2
        with self.assertRaisesRegex(ValueError, "insufficient"):
            self.run_with(data)

    def test_archived_actual_cohort_matches_allocator_exactly(self):
        path = ROOT / "docs/evaluation/capacity-v0-paired-cohort-2026-11-04.json"
        archived = json.loads(path.read_text(encoding="utf-8"))
        generated = frozen.freeze(ROOT)
        self.assertEqual(archived, generated)
        self.assertEqual(archived["source_selector_sha256"], frozen.replacements.FROZEN_SELECTOR)
        self.assertFalse(archived["certifies_blind"])

    def test_tampering_fails_closed(self):
        operations = [
            lambda d: d.update(source_run_id=0),
            lambda d: d.update(source_artifact_id=0),
            lambda d: d.update(source_artifact_zip_sha256="drift"),
            lambda d: d.update(source_gold_artifact_id=0),
            lambda d: d.update(source_gold_artifact_zip_sha256="drift"),
            lambda d: d.update(contains_raw_patch_or_task_text=True),
            lambda d: d["results"].reverse(),
            lambda d: d["results"][0].update(noop_fail=False, ambiguous=False),
            lambda d: d["results"][0].update(test_exit_code=0),
            lambda d: d.update(noop_fail_count=9),
            lambda d: d["results"].append(copy.deepcopy(d["results"][0])),
        ]
        for mutate in operations:
            with self.subTest(mutate=repr(mutate)):
                data = fake_noop()
                mutate(data)
                with self.assertRaises(ValueError):
                    self.run_with(data)


if __name__ == "__main__":
    unittest.main()
