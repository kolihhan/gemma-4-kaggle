"""CPU-only time-budget recovery checks against the frozen V2 fixture."""
import hashlib
import io
import unittest
from unittest.mock import patch
import zipfile

from scripts import build_toolcap60_timeout_recovery as r
from scripts import build_v2_toolcap_submission as parent

V2 = {
    "agent.yaml": """agent_class: LlmAgent
name: swe_coder
model: gemma-4-31b-it-qat-w4a16-ct
instruction: !include prompts/system.md
tools:
  - run_command
  - read_file
  - edit_file
  - write_file
  - get_status
  - submit_patch
  - get_code_neighbors
  - search_similar_code
  - get_code_subgraph
generate_content_config: !include configs/sampling.yaml
""",
    "prompts/system.md": "Exactly pinned Budget-Fit V2 prompt",
    "configs/sampling.yaml": "temperature: 0.2\nthinking_budget: 4096\n",
    "eval_config.yaml": "evaluation:\n  timeout_seconds: 240\n  max_time_minutes: 8\n  max_tool_calls: 28\n  max_turns: 80\n",
}


class TimeoutRecoveryTests(unittest.TestCase):
    def setUp(self):
        p = patch.object(parent, "validate_source_zip", return_value=dict(V2))
        p.start()
        self.addCleanup(p.stop)

    def test_only_time_changes_from_60_call_failed_candidate(self):
        original = parent.files_for_candidate(b"source")
        recovered = r.files_for_candidate(b"source")
        self.assertEqual(set(original), set(recovered))
        for name in original:
            if name == "eval_config.yaml":
                self.assertEqual(recovered[name],
                                 original[name].replace("max_time_minutes: 8",
                                                        "max_time_minutes: 5"))
            else:
                self.assertEqual(recovered[name], original[name])
        self.assertIn("max_tool_calls: 60", recovered["eval_config.yaml"])
        self.assertIn("max_turns: 80", recovered["eval_config.yaml"])

    def test_reproducible_archive(self):
        a = r.build(b"source")
        self.assertEqual(a, r.build(b"source"))
        self.assertEqual(hashlib.sha256(a).hexdigest(),
                         hashlib.sha256(r.build(b"source")).hexdigest())
        with zipfile.ZipFile(io.BytesIO(a)) as zip_file:
            self.assertEqual(set(zip_file.namelist()), set(V2))
            self.assertIsNone(zip_file.testzip())
            self.assertIn(b"max_time_minutes: 5", zip_file.read("eval_config.yaml"))

    def test_drift_fails_closed(self):
        drift = dict(V2)
        drift["eval_config.yaml"] = drift["eval_config.yaml"].replace(
            "max_time_minutes: 8", "max_time_minutes: 6"
        )
        with patch.object(parent, "validate_source_zip", return_value=drift):
            with self.assertRaisesRegex(ValueError, "task-time configuration"):
                r.files_for_candidate(b"source")

    def test_rejects_unrecognized_toolcall_contract(self):
        drift = dict(V2)
        drift["eval_config.yaml"] = drift["eval_config.yaml"].replace(
            "max_tool_calls: 28", "max_tool_calls: 99"
        )
        with patch.object(parent, "validate_source_zip", return_value=drift):
            with self.assertRaisesRegex(ValueError, "pinned baseline"):
                r.files_for_candidate(b"source")

    def test_budget_exposure_acknowledged(self):
        detail = r.summary(b"source")
        self.assertEqual(detail["task_time_minutes"], 5)
        self.assertEqual(detail["tool_calls_cap"], 60)
        self.assertFalse(detail["claimed_correctness_gain"])
        self.assertFalse(detail["official_submission"])


if __name__ == "__main__":
    unittest.main()
