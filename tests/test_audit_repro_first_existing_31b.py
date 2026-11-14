"""Smoke and fail-closed tests for completed-repro-first private trace audit."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts.audit_repro_first_existing_31b import (
    ARMS, TASKS, TREATMENT_SHA, VERSION, audit, safe_trace,
)


def example_trace() -> dict:
    return {"steps": [
        {"tool_calls": [{"function_name": "read_file", "arguments": {}}]},
        {"tool_calls": [{"function_name": "get_code_neighbors", "arguments": {}}]},
        {"tool_calls": [{"function_name": "edit_file", "arguments": {}}]},
        {"tool_calls": [{"function_name": "run_command",
                         "arguments": {"command": "python -m pytest -q"}}],
         "observation": {"content": json.dumps({"exit_code": 1})}},
        {"tool_calls": [{"function_name": "edit_file", "arguments": {}}]},
        {"tool_calls": [{"function_name": "submit_patch", "arguments": {}}]},
    ]}


class ReadOnlyFeedbackAuditTest(unittest.TestCase):
    def seed(self, root: Path) -> None:
        rows = []
        for arm in ARMS:
            for task in TASKS:
                rows.append({"arm": arm, "instance_id": task,
                             "status": "completed", "resolved": task == TASKS[0],
                             "has_patch": True, "test_exit_code": 0 if task == TASKS[0] else 1,
                             "tool_calls": 12, "duration_seconds": 110.0})
                folder = root / "run" / ("public-prompt" if arm == "repro_first" else "baseline")
                folder.mkdir(parents=True, exist_ok=True)
                (folder / f"trace_{task}.json").write_text(json.dumps(example_trace()))
        result = {
            "version": VERSION, "status": "completed",
            "treatment_zip_sha256": TREATMENT_SHA,
            "selected_public_dev_ids": list(TASKS),
            "total_evaluations": 8, "results": rows,
        }
        (root / "repro_first_summary.json").write_text(json.dumps(result))

    def test_frozen_real_source_shape_and_private_data_reduction(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.seed(root)
            report = audit(root)
            self.assertEqual(report["by_arm"]["champion"]["resolved"], 1)
            self.assertEqual(report["by_arm"]["repro_first"]["resolved"], 1)
            self.assertEqual(report["by_arm"]["champion"]["traces_found"], 4)
            self.assertEqual(report["by_arm"]["repro_first"]["graph_calls"], 4)
            self.assertEqual(report["by_arm"]["repro_first"]["explicit_or_inline_tests"], 4)
            self.assertEqual(report["by_arm"]["repro_first"]["read_calls"], 4)
            self.assertEqual(report["tasks"][0]["nonzero_test_then_edit"], 1)
            self.assertFalse(report["new_submission"])
            self.assertFalse(report["new_gpu_inference"])
            dump = json.dumps(report)
            for forbidden in ("python -m pytest -q", '"steps"', '"arguments"', '"observation"'):
                self.assertNotIn(forbidden, dump)

    def test_missing_trace_is_unobserved_not_zero(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.seed(root)
            (root / "run" / "public-prompt" / f"trace_{TASKS[2]}.json").unlink()
            result = audit(root)
            matching = [r for r in result["tasks"] if
                        r["arm"] == "repro_first" and r["task"] == TASKS[2]]
            self.assertEqual(matching, [{"arm": "repro_first", "task": TASKS[2],
                                         "resolved": False, "has_patch": True,
                                         "grader_exit": 1, "tool_calls": 12,
                                         "elapsed_s": 110.0, "trace_found": False}])
            self.assertEqual(result["by_arm"]["repro_first"]["traces_found"], 3)

    def test_wrong_treatment_digest_blocks_result(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.seed(root)
            p = root / "repro_first_summary.json"
            data = json.loads(p.read_text())
            data["treatment_zip_sha256"] = "bad"
            p.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "source run"):
                audit(root)

    def test_submit_loop_reports_only_response_categories(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "trace.json"
            source = {"steps": [
                {"tool_calls": [{"function_name": "submit_patch", "arguments": {}}],
                 "observation": {"content": json.dumps({"status": "error",
                     "error_message": "PRIVATE_SECRET_DO_NOT_EXPORT"})}},
                {"tool_calls": [{"function_name": "submit_patch", "arguments": {}}],
                 "observation": {"content": json.dumps({"status": "ok",
                     "patch_size": 212, "files_changed": 2})}},
            ]}
            path.write_text(json.dumps(source))
            result = safe_trace(path)
            self.assertEqual(result["submit_response_states"], {"error": 1, "ok": 1})
            self.assertEqual(result["submit_patch_nonempty_responses"], 1)
            self.assertEqual(result["max_consecutive_submit_calls"], 2)
            self.assertNotIn("PRIVATE_SECRET_DO_NOT_EXPORT", json.dumps(result))

    def test_direct_trace_reducer_no_raw_command(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "trace.json"
            path.write_text(json.dumps(example_trace()))
            r = safe_trace(path)
            self.assertEqual((r["read_calls"], r["graph_calls"],
                              r["command_calls"], r["edit_actions"]), (1, 1, 1, 2))
            self.assertNotIn("python -m pytest -q", json.dumps(r))


if __name__ == "__main__":
    unittest.main()
