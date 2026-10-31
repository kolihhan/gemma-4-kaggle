import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUBMISSION = ROOT / "submission"


class SubmissionLayoutTests(unittest.TestCase):
    def test_minimal_e4b_baseline_files_exist(self):
        for relative in (
            "agent.yaml",
            "eval_config.yaml",
            "configs/sampling.yaml",
            "prompts/system.md",
        ):
            self.assertTrue((SUBMISSION / relative).is_file(), relative)

    def test_agent_is_single_e4b_agent_with_official_tools(self):
        text = (SUBMISSION / "agent.yaml").read_text(encoding="utf-8")
        self.assertIn("model: gemma-4-e4b-it-qat-w4a16-ct", text)
        self.assertNotIn("adapter:", text)
        self.assertNotIn("sub_agents:", text)
        for tool in (
            "run_command",
            "read_file",
            "edit_file",
            "write_file",
            "get_status",
            "submit_patch",
            "get_code_neighbors",
            "search_similar_code",
            "get_code_subgraph",
        ):
            self.assertIn(f"- {tool}", text)

    def test_sampling_starts_from_official_example_values(self):
        text = (SUBMISSION / "configs" / "sampling.yaml").read_text(encoding="utf-8")
        self.assertIn("temperature: 0.2", text)
        self.assertIn("top_p: 0.95", text)
        self.assertIn("max_output_tokens: 16384", text)
        self.assertIn("thinking_budget: 4096", text)
        self.assertIn("include_thoughts: true", text)

    def test_eval_budget_is_explicitly_bounded(self):
        text = (SUBMISSION / "eval_config.yaml").read_text(encoding="utf-8")
        self.assertIn("timeout_seconds: 300", text)
        self.assertIn("max_tool_calls: 32", text)
        self.assertIn("max_time_minutes: 5", text)
        self.assertIn("max_turns: 64", text)


if __name__ == "__main__":
    unittest.main()
