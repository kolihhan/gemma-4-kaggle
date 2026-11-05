"""Eligibility-only cohort assembly tests with synthetic sanitized control flags."""
import json
import tempfile
import unittest
from pathlib import Path

from scripts.discriminating_evidence_exploratory import ROOT, build_exploratory
from scripts.finalize_discriminating_evidence_eligible import build_ready

GOLD_RUN = 42066105011
NOOP_RUN = 42067120930


def safe_sources(folder, *, excluded=(), few=False):
    selected = build_exploratory(ROOT)
    ids = (selected["pilot_ids"] + selected["exploratory_ids"]
           + selected["replacement_ids"])
    excluded = set(excluded)
    gold_rows = []
    for id in ids:
        gold = (id not in excluded and (not few or id.startswith("rich_")))
        gold_rows.append({
            "instance_id": id,
            "repo": "Textualize/rich" if id.startswith("rich_") else "fastapi/fastapi",
            "gold_pass": gold,
            "status": "completed",
            "test_exit_code": 0 if gold else 1,
        })
    gold = {
        "version": "discriminating-evidence-v0-exploratory-gold-screen",
        "source_run_id": GOLD_RUN,
        "source_selector_sha256": selected["selection_digest_sha256"],
        "screened": 30,
        "gold_pass_count": sum(x["gold_pass"] for x in gold_rows),
        "results": gold_rows,
        "contains_raw_patch_or_task_text": False,
        "certifies_blind": False,
        "model_evaluation_executed": False,
    }
    noop_rows = [{
        "instance_id": x["instance_id"], "repo": x["repo"],
        "noop_fail": True, "status": "completed", "test_exit_code": 1,
    } for x in gold_rows if x["gold_pass"]]
    noop = {
        "version": "discriminating-evidence-v0-exploratory-noop-screen",
        "source_gold_action_run_id": GOLD_RUN,
        "source_noop_action_run_id": NOOP_RUN,
        "source_selector_sha256": selected["selection_digest_sha256"],
        "screened": len(noop_rows),
        "noop_fail_count": len(noop_rows),
        "results": noop_rows,
        "contains_raw_patch_or_task_text": False,
        "certifies_blind": False,
        "model_evaluation_executed": False,
    }
    g, n = folder / "gold.json", folder / "noop.json"
    g.write_text(json.dumps(gold))
    n.write_text(json.dumps(noop))
    return g, n


class ReadyCohortTests(unittest.TestCase):
    def test_all_controls_eligible_leaves_frozen_originals(self):
        with tempfile.TemporaryDirectory() as d:
            g, n = safe_sources(Path(d))
            got = build_ready(ROOT, g, n)
            original = build_exploratory(ROOT)
            self.assertEqual(got["pilot_ids"], original["pilot_ids"])
            self.assertEqual(got["exploratory_ids"], original["exploratory_ids"])
            self.assertEqual(got["status"], "ELIGIBILITY_READY_NOT_BLIND_CERTIFIED")
            self.assertFalse(got["model_evaluation_executed"])

    def test_ineligible_replaced_in_frozen_same_repo_order(self):
        with tempfile.TemporaryDirectory() as d:
            blocked = ("rich_3471", "rich_3506", "fastapi_14303", "fastapi_14356")
            g, n = safe_sources(Path(d), excluded=blocked)
            got = build_ready(ROOT, g, n)
            self.assertEqual(got["pilot_ids"],
                ["rich_3006", "rich_3480", "fastapi_13537", "fastapi_14099"])
            self.assertEqual(got["exploratory_ids"][:6],
                ["rich_3468", "rich_3944", "rich_3675", "rich_2943",
                 "rich_3938", "rich_3469"])
            self.assertEqual(got["exploratory_ids"][6:],
                ["fastapi_14512", "fastapi_5624", "fastapi_14964",
                 "fastapi_14791", "fastapi_14455", "fastapi_14372"])
            self.assertEqual(got["status"], "ELIGIBILITY_READY_NOT_BLIND_CERTIFIED")

    def test_insufficient_repo_eligible_is_no_go(self):
        with tempfile.TemporaryDirectory() as d:
            g, n = safe_sources(Path(d), few=True)
            got = build_ready(ROOT, g, n)
            self.assertEqual(got["status"], "NO_GO_INSUFFICIENT_ELIGIBLE_TASKS")
            self.assertLess(len(got["pilot_ids"])+len(got["exploratory_ids"]), 16)
            self.assertFalse(got["gpu_or_submission_authorized"])

    def test_malformed_gold_provenance_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            g, n = safe_sources(Path(d))
            bad = json.loads(g.read_text())
            bad["source_selector_sha256"] = "unknown"
            g.write_text(json.dumps(bad))
            with self.assertRaises(ValueError):
                build_ready(ROOT, g, n)


if __name__ == "__main__":
    unittest.main()
