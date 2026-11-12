"""Synthetic-only regression tests; never use actual Kaggle issue text or patches."""
from __future__ import annotations
import json
from pathlib import Path
import tempfile
import unittest

from scripts import audit_clean_capacity_feedback as app


class CleanCapacityFeedbackTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.ids = sorted(app.EXPECTED_IDS)
        for arm in app.ARMS:
            folder = self.root / arm
            folder.mkdir()
            records = [
                {
                    "instance_id": name, "status": "completed",
                    "resolved": (i in (0, 3) if arm == "v2_12b" else i in (0, 2, 3)),
                    "has_patch": (i in (0, 3) if arm == "v2_12b" else True),
                    "patch_chars": 100 if (i in (0, 3) or arm == "v2_31b") else 0,
                    "duration_seconds": 111.5, "tool_calls": 12,
                    "test_exit_code": (0 if i in (0, 3) else 1),
                }
                for i, name in enumerate(self.ids)
            ]
            payload = {"status": "completed", "model": app.ARMS[arm],
                       "requested": len(records), "results": records}
            (folder / f"capacity_{arm}_results.json").write_text(json.dumps(payload))
        trace = {
            "steps": [
                {"tool_calls": [{"function_name": "edit_file",
                                 "arguments": {"content": "SECRET NEVER PRINT"}}]},
                {"tool_calls": [{"function_name": "run_command",
                                 "arguments": {"command": "pytest SECRET NEVER PRINT"}}],
                 "observation": {"content": '{"exit_code": 1}'}},
                {"tool_calls": [{"function_name": "submit_patch", "arguments": {}}]},
            ]
        }
        (self.root / "v2_31b" / f"trace_{self.ids[1]}.json").write_text(json.dumps(trace))

    def test_exact_frozen_matched_result_and_trace_classification(self):
        result = app.audit(self.root)
        self.assertEqual(result["by_arm"]["v2_12b"]["resolved"], 2)
        self.assertEqual(result["by_arm"]["v2_31b"]["resolved"], 3)
        self.assertEqual(result["paired"]["31b_only_resolved"], 1)
        self.assertEqual(result["paired"]["12b_only_resolved"], 0)
        self.assertEqual(result["by_arm"]["v2_31b"]["traces_found"], 1)
        self.assertEqual(result["tasks"][self.ids[1]]["v2_31b"]["feedback"]["explicit_or_inline_tests"], 1)

    def test_raw_commands_or_patch_never_exported(self):
        s = json.dumps(app.audit(self.root))
        self.assertNotIn("SECRET NEVER PRINT", s)
        self.assertNotIn("trace_", s)
        self.assertNotIn("pytest ", s)
        self.assertNotIn("arguments", s)

    def test_wrong_model_fails_closed(self):
        p = self.root / "v2_12b" / "capacity_v2_12b_results.json"
        a = json.loads(p.read_text())
        a["model"] = "wrong"
        p.write_text(json.dumps(a))
        with self.assertRaisesRegex(ValueError, "frozen model"):
            app.audit(self.root)

    def test_dropped_or_duplicate_task_fails_closed(self):
        p = self.root / "v2_31b" / "capacity_v2_31b_results.json"
        a = json.loads(p.read_text())
        a["results"][0]["instance_id"] = a["results"][1]["instance_id"]
        p.write_text(json.dumps(a))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            app.audit(self.root)

    def test_missing_trace_is_unobserved(self):
        r = app.audit(self.root)
        self.assertEqual(r["tasks"][self.ids[0]]["v2_12b"]["feedback"],
                         {"trace_found": False})


if __name__ == "__main__":
    unittest.main()
