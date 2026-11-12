"""Pure-CPU synthetic regression tests of the 31B early-edit paired renderer."""
from __future__ import annotations
import base64
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import render_earlyedit_v2_paired_31b as m
from scripts import render_public_prompt_vs_v2_paired_31b as p

ROOT = Path(__file__).resolve().parents[1]


class EarlyEditPinnedTests(unittest.TestCase):
    def setUp(self):
        self.source = b"synthetic-no-kaggle-data"
        self.sha = hashlib.sha256(self.source).hexdigest()
        self.base = {
            "agent.yaml": "agent_class: LlmAgent\nmodel: " + m.MODEL + "\n",
            "configs/sampling.yaml": "thinking_budget: 4096\n",
            "eval_config.yaml": "evaluation:\n  max_time_minutes: 8\n  max_tool_calls: 28\n  max_turns: 80\n",
            "prompts/system.md": "Repair only what the issue justifies.\n",
        }
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        for fname in (m.PLAN_FILE, p.MANIFEST_PATH, p.TEMPLATE_PATH):
            f = self.repo / fname
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_bytes((ROOT / fname).read_bytes())
        for file in (m.PLAN_FILE, p.MANIFEST_PATH):
            target = self.repo / file
            manifest = json.loads(target.read_text())
            if file == m.PLAN_FILE:
                manifest["control_source_zip_sha256"] = self.sha
            else:
                manifest["baseline_zip_sha256"] = self.sha
            target.write_text(json.dumps(manifest))

    def _generator(self):
        with (patch.object(m, "EXPECTED_ZIP_SHA256", self.sha),
              patch.object(p, "EXPECTED_ZIP_SHA256", self.sha),
              patch.object(m, "validate_source_zip", return_value=self.base),
              patch.object(p, "validate_source_zip", return_value=self.base)):
            return m.generate(self.repo, self.source)

    def test_only_prompt_changes_beyond_common_clock(self):
        with (patch.object(m, "EXPECTED_ZIP_SHA256", self.sha),
              patch.object(m, "validate_source_zip", return_value=self.base)):
            control, treatment = m.candidate_files(self.source)
        self.assertEqual(control["eval_config.yaml"], treatment["eval_config.yaml"])
        self.assertIn("max_time_minutes: 5", control["eval_config.yaml"])
        self.assertIn("by call 10", treatment["prompts/system.md"])
        self.assertIn("evidence", treatment["prompts/system.md"])
        self.assertNotIn("Time-aware repair", control["prompts/system.md"])
        self.assertEqual([k for k in control if control[k] != treatment[k]],
                         ["prompts/system.md"])

    def test_dual_evaluator_runtime_and_exact_four_frozen_tasks(self):
        code, report = self._generator()
        self.assertEqual(report["task_evaluations"], 8)
        self.assertEqual(report["arm_count"], 2)
        self.assertIn("EARLYEDIT_FROZEN_SELECTED_IDS", code)
        self.assertIn("early_edit_5min", code)
        self.assertIn("if len(records) != 8:", code)
        self.assertIn("if len(scored) != 4:", code)
        self.assertIn("treatment_evaluator = Evaluator(treatment_config)", code)
        self.assertIn("earlyedit_v2_31b_results.json", code)
        self.assertNotIn("competition_submit_code", code)
        compile(code, m.SCRIPT_NAME, "exec")

    def test_frozen_manifest_drift_fails_closed(self):
        target = self.repo / m.PLAN_FILE
        manifest = json.loads(target.read_text())
        manifest["tasks"][0]["instance_id"] = "fastapi_15589"
        target.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "frozen four task IDs drift"):
            self._generator()

    def test_runtime_contains_no_raw_reference_patch(self):
        code, report = self._generator()
        self.assertNotIn("agent_patch=task.patch", code)
        self.assertNotIn("task.patch", code)
        self.assertTrue(report["no_training_or_official_submission"])
        self.assertNotEqual(report["control_zip_sha256"],
                            report["treatment_zip_sha256"])


if __name__ == "__main__":
    unittest.main()
