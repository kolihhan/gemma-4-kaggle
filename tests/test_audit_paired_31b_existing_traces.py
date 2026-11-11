import json
from pathlib import Path
import tempfile
import unittest

from scripts.audit_paired_31b_existing_traces import (
    audit, read_safe_results, test_invocation
)


class PairedTraceAuditTests(unittest.TestCase):
    def setup_data(self, root):
        rows = []
        for task_id in ("fastapi_14487", "rich_3782", "requests_7427"):
            for arm in ("v2_5min", "public_prompt_5min"):
                rows.append({
                    "arm": arm, "instance_id": task_id,
                    "resolved": False, "has_patch": True,
                    "test_exit_code": 1, "tool_calls": 5,
                    "duration_seconds": 210,
                })
                sub = root / "paired-prompt-private-results"
                if arm == "public_prompt_5min":
                    sub /= "public-prompt"
                sub.mkdir(parents=True, exist_ok=True)
                trace = {"steps": [
                    {"tool_calls": [{"function_name": "read_file"}]},
                    {"tool_calls": [{"function_name": "edit_file"}]},
                    {"tool_calls": [{"function_name": "run_command",
                                    "arguments": {"command": "pytest -q"}}]},
                    {"tool_calls": [{"function_name": "edit_file"}]},
                    {"tool_calls": [{"function_name": "submit_patch"}]},
                ]}
                (sub / f"trace_{task_id}.json").write_text(json.dumps(trace))
        (root / "paired_prompt_v2_31b_results.json").write_text(json.dumps({
            "version": "public-prompt-v2-paired-clean-v1",
            "results": rows,
        }))

    def test_six_synthetic_traces(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.setup_data(root)
            result = audit(root)
            self.assertEqual(result["by_arm"]["v2_5min"]["traces_found"], 3)
            self.assertEqual(result["by_arm"]["public_prompt_5min"]["resolved"], 0)
            self.assertTrue(all(r["possible_repair_after_test"] for r in result["tasks"]))
            self.assertTrue(all(r["edits"] == 2 for r in result["tasks"]))

    def test_absent_trace_is_unobserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.setup_data(root)
            (root / "paired-prompt-private-results" / "trace_rich_3782.json").unlink()
            rows = audit(root)["tasks"]
            row = next(r for r in rows if r["arm"] == "v2_5min" and r["instance_id"] == "rich_3782")
            self.assertIs(row["trace_found"], False)
            self.assertNotIn("edits", row)

    def test_duplicate_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.setup_data(root)
            path = root / "paired_prompt_v2_31b_results.json"
            payload = json.loads(path.read_text())
            payload["results"][1]["arm"] = "v2_5min"
            path.write_text(json.dumps(payload))
            with self.assertRaises(ValueError):
                read_safe_results(path)

    def test_false_mention_is_not_a_test(self):
        self.assertFalse(test_invocation("echo pytest -q"))
        self.assertTrue(test_invocation("python -m pytest test_api.py"))


if __name__ == "__main__":
    unittest.main()
