"""Synthetic only: full 8-task denominator and safe trace classification."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts import audit_earlyedit_existing_traces as audit
from scripts.render_earlyedit_v2_paired_31b import PLAN_FILE

ROOT = Path(__file__).resolve().parents[1]


class TestPairedTraceAnalysis(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder=Path(self.tmp.name)
        self.manifest=ROOT/PLAN_FILE
        self.plan=json.loads(self.manifest.read_text())
        self.tasks=[x["instance_id"] for x in self.plan["tasks"]]
        self.rows=[]
        for arm in audit.ARMS:
            for task in self.tasks:
                self.rows.append({
                    "arm":arm, "instance_id":task, "status":"completed",
                    "resolved":(arm=="early_edit_5min" and task==self.tasks[0]),
                    "has_patch":True,"tool_calls":10,
                    "duration_seconds":250.0,
                    "agent_patch":"SECRET SHOULD NEVER BE EXPORTED",
                    "error_type":None,
                })
        self.payload={
            "version":self.plan["version"],
            "status":"completed",
            "model":self.plan["model"],
            "selected_public_dev_ids":self.tasks,
            "total_evaluations":8,
            "results":self.rows,
        }
        self.save()

    def save(self):
        (self.folder / audit.RESULT).write_text(json.dumps(self.payload))

    def test_denominator_and_recorded_early_edit(self):
        trace={
            "steps":[
                {"tool_calls":[{"function_name":"read_file",
                               "arguments":{"path":"SECRET PATH"}}]},
                {"tool_calls":[{"function_name":"edit_file",
                               "arguments":{"content":"SECRET PATCH"}}]},
                {"tool_calls":[{"function_name":"run_command",
                               "arguments":{"command":"pytest tests/test.py"}}],
                 "observation":{"content":'{"exit_code": 0}'}},
            ]
        }
        d=self.folder/"paired-prompt-private-results"/"public-prompt"
        d.mkdir(parents=True)
        (d/f"trace_{self.tasks[0]}.json").write_text(json.dumps(trace))
        r=audit.audit(self.folder,self.manifest)
        self.assertEqual(r["by_arm"]["early_edit_5min"]["resolved"],1)
        self.assertEqual(r["by_arm"]["v2_5min"]["resolved"],0)
        self.assertEqual(r["by_arm"]["early_edit_5min"]["traces_found"],1)
        self.assertEqual(r["by_arm"]["early_edit_5min"]["tasks_first_edit_by_call_10"],1)
        self.assertEqual(r["by_arm"]["early_edit_5min"]["recognized_explicit_tests"],1)
        output=json.dumps(r)
        self.assertNotIn("SECRET",output)
        self.assertNotIn("pytest tests",output)
        self.assertNotIn("arguments",output)

    def test_duplicate_or_unexpected_task_fails_closed(self):
        self.rows[0]["instance_id"]=self.rows[1]["instance_id"]
        self.save()
        with self.assertRaisesRegex(ValueError,"duplicate"):
            audit.audit(self.folder,self.manifest)

    def test_missing_result_is_not_zero_score(self):
        self.rows.pop()
        self.payload["total_evaluations"]=7
        self.save()
        with self.assertRaisesRegex(ValueError,"evaluation"):
            audit.audit(self.folder,self.manifest)

    def test_premature_run_fails_closed(self):
        self.payload["status"]="in_progress"
        self.save()
        with self.assertRaisesRegex(ValueError,"not complete"):
            audit.audit(self.folder,self.manifest)

    def test_ambiguous_trace_fails_closed(self):
        for prefix in ("a","b"):
            d=self.folder/prefix
            d.mkdir()
            (d/f"trace_{self.tasks[0]}.json").write_text('{"steps":[]}')
        with self.assertRaisesRegex(ValueError,"ambiguous"):
            audit.audit(self.folder,self.manifest)


if __name__ == "__main__":
    unittest.main()
