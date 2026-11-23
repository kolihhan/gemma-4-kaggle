"""Pure CPU matched-arm construction and notebook-timeout guard tests."""
import hashlib
import io
import unittest
from unittest.mock import patch
import zipfile

from scripts import build_behavioral_probe_timeout_safe_20261123 as b

FIXTURE = {
    "agent.yaml": """agent_class: LlmAgent
name: swe_coder
model: gemma-4-31b-it-qat-w4a16-ct
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
""",
    "eval_config.yaml": "evaluation:\n  timeout_seconds: 240\n  max_time_minutes: 5\n  max_tool_calls: 60\n  max_turns: 80\n",
    "configs/sampling.yaml": "temperature: 0.2\nthinking_budget: 4096\n",
    "prompts/system.md": "Original frozen Champion prompt.\n",
}


class BoundedProbeTests(unittest.TestCase):
    def setUp(self):
        self.patches = [
            patch.object(b, "champion_files", return_value=dict(FIXTURE)),
            patch.object(b, "build_scored_champion", return_value=b"frozen-champion-zip"),
            patch.object(b, "CHAMPION_SHA256", hashlib.sha256(b"frozen-champion-zip").hexdigest()),
        ]
        for obj in self.patches:
            obj.start()
            self.addCleanup(obj.stop)

    def test_only_prompt_differs_between_matched_four_minute_arms(self):
        base, candidate = b.files_for_pair(b"source")
        self.assertEqual(set(base), set(candidate))
        self.assertEqual([k for k in base if base[k] != candidate[k]], ["prompts/system.md"])
        self.assertEqual(base["eval_config.yaml"], candidate["eval_config.yaml"])
        self.assertIn("max_time_minutes: 4", candidate["eval_config.yaml"])
        self.assertIn("max_tool_calls: 60", candidate["eval_config.yaml"])
        self.assertIn("max_turns: 80", candidate["eval_config.yaml"])
        self.assertEqual(base["agent.yaml"], FIXTURE["agent.yaml"])
        self.assertIn("timeout 20s", candidate["prompts/system.md"])

    def test_archive_deterministic_and_valid(self):
        a1, b1 = b.build_pair(b"source")
        a2, b2 = b.build_pair(b"source")
        self.assertEqual((a1, b1), (a2, b2))
        self.assertNotEqual(a1, b1)
        for data in (a1, b1):
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                self.assertIsNone(z.testzip())
                self.assertEqual(set(z.namelist()), b.EXPECTED_FILES)

    def test_bad_champion_digest_fails_closed(self):
        with patch.object(b, "CHAMPION_SHA256", "0" * 64):
            with self.assertRaisesRegex(ValueError, "exact scored"):
                b.files_for_pair(b"source")

    def test_mutated_source_budget_fails_closed(self):
        drift = dict(FIXTURE)
        drift["eval_config.yaml"] = drift["eval_config.yaml"].replace("max_time_minutes: 5", "max_time_minutes: 8")
        with patch.object(b, "champion_files", return_value=drift):
            with self.assertRaisesRegex(ValueError, "budget mismatch"):
                b.files_for_pair(b"source")

    def test_forecast_hidden_set_size_sensitivity(self):
        self.assertTrue(b.timeout_forecast(tasks=120, mean_setup_seconds=45)["safe_under_assumptions"])
        self.assertFalse(b.timeout_forecast(tasks=140, mean_setup_seconds=45)["safe_under_assumptions"])
        with self.assertRaises(ValueError):
            b.timeout_forecast(tasks=0, mean_setup_seconds=45)

    def test_experiment_never_claims_score_or_submits(self):
        data = b.describe(b"source")
        self.assertFalse(data["official_submission"])
        self.assertFalse(data["proven_resolved_task_gain"])
        self.assertEqual(data["per_task_minutes"], 4)
        self.assertEqual(data["only_difference_between_arms"], "prompts/system.md")


if __name__ == "__main__":
    unittest.main()
