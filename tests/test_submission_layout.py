import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUBMISSION = ROOT / "submission"


class SubmissionLayoutTests(unittest.TestCase):
    def test_minimal_e4b_submission_files_exist(self):
        for relative in (
            "agent.yaml",
            "eval_config.yaml",
            "configs/sampling.yaml",
            "sub_agents/coder.yaml",
            "sub_agents/verifier.yaml",
            "prompts/coder.md",
            "prompts/verifier.md",
        ):
            self.assertTrue((SUBMISSION / relative).is_file(), relative)

    def test_root_is_exactly_two_stage_sequential_agent(self):
        root = (SUBMISSION / "agent.yaml").read_text(encoding="utf-8")
        self.assertIn("agent_class: SequentialAgent", root)
        self.assertIn("name: swe_e4b_coder_verifier", root)
        self.assertEqual(root.count("config_path:"), 2)
        self.assertIn("config_path: sub_agents/coder.yaml", root)
        self.assertIn("config_path: sub_agents/verifier.yaml", root)
        self.assertNotIn("model:", root)
        self.assertNotIn("submit_patch", root)

    def test_coder_and_verifier_share_e4b_but_only_verifier_can_submit(self):
        coder = (SUBMISSION / "sub_agents" / "coder.yaml").read_text(encoding="utf-8")
        verifier = (SUBMISSION / "sub_agents" / "verifier.yaml").read_text(encoding="utf-8")

        for text in (coder, verifier):
            self.assertIn("model: gemma-4-e4b-it-qat-w4a16-ct", text)
            self.assertNotIn("adapter:", text)
            self.assertNotIn("- write_file", text)
            self.assertIn("- run_command", text)
            self.assertIn("- read_file", text)
            self.assertIn("- edit_file", text)
            self.assertIn("- get_status", text)
            self.assertIn("generate_content_config: !include ../configs/sampling.yaml", text)

        self.assertNotIn("- submit_patch", coder)
        self.assertIn("- submit_patch", verifier)
        self.assertIn("instruction: !include ../prompts/coder.md", coder)
        self.assertIn("instruction: !include ../prompts/verifier.md", verifier)

    def test_sub_agent_includes_are_relative_to_the_sub_agent_yaml(self):
        coder = (SUBMISSION / "sub_agents" / "coder.yaml").read_text(encoding="utf-8")
        verifier = (SUBMISSION / "sub_agents" / "verifier.yaml").read_text(encoding="utf-8")
        self.assertNotIn("!include prompts/", coder)
        self.assertNotIn("!include configs/", coder)
        self.assertNotIn("!include prompts/", verifier)
        self.assertNotIn("!include configs/", verifier)

    def test_both_prompts_receive_problem_context(self):
        coder = (SUBMISSION / "prompts" / "coder.md").read_text(encoding="utf-8")
        verifier = (SUBMISSION / "prompts" / "verifier.md").read_text(encoding="utf-8")
        self.assertIn("{problem_description}", coder)
        self.assertIn("{problem_description}", verifier)

    def test_coder_keeps_bounded_edit_and_test_policy(self):
        prompt = (SUBMISSION / "prompts" / "coder.md").read_text(encoding="utf-8")
        for phrase in (
            "After two failed `edit_file` attempts",
            "tiny `run_command` script",
            "assert the exact old text",
            "inspect `git diff`",
            "targeted verification",
            "Do not submit",
        ):
            self.assertIn(phrase, prompt)

    def test_verifier_owns_final_test_repair_and_submit_gate(self):
        prompt = (SUBMISSION / "prompts" / "verifier.md").read_text(encoding="utf-8")
        for phrase in (
            "Start from the existing working tree",
            "inspect `git diff`",
            "targeted verification",
            "one evidence-backed narrow repair",
            "If targeted verification still fails",
            "smallest defensible patch",
            "call `submit_patch` as your final tool action",
        ):
            self.assertIn(phrase, prompt)

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
