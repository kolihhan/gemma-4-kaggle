"""Final grades do not establish whether earlier good candidates existed."""

import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from scripts.inventory_candidate_history import inventory


class HistoryInventoryTests(unittest.TestCase):
    def test_final_outcome_only_archive_stays_unknown_about_generation_and_selection(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "archive.zip"
            with zipfile.ZipFile(archive, "w") as zipped:
                zipped.writestr("verifier_baseline_results.json", json.dumps({
                    "model": "fixture", "results": [
                        {"instance_id": "changed", "has_patch": True, "resolved": False, "test_exit_code": 1},
                        {"instance_id": "empty", "has_patch": False, "resolved": False, "test_exit_code": -1},
                    ],
                }))
                for task, steps in (("changed", []), ("empty", [{
                    "tool_calls": [{"function_name": "edit_file", "arguments": {}}],
                    "observation": {
                        "content": json.dumps({"status": "error", "error_type": "FileEditError", "error_message": "old_string not found"}),
                        "extra": {"tool_name": "edit_file", "elapsed_s": 0.01, "timestamp": 1.0, "author": "fixture"},
                    },
                }])):
                    zipped.writestr(f"output/traces/trace_{task}.json", json.dumps({"steps": steps}))
            report = inventory(archive)
            self.assertEqual(report["counts"]["unresolved_nonempty_patch"], 1)
            self.assertEqual(report["counts"]["no_patch_with_edit_error"], 1)
            self.assertEqual(report["generation_vs_selection_unknown"], 2)


if __name__ == "__main__":
    unittest.main()
