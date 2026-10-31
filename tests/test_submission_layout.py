import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUBMISSION = ROOT / "submission"


class SubmissionLayoutTests(unittest.TestCase):
    def test_minimal_12b_submission_files_exist(self):
        for relative in (
            "agent.yaml",
            "eval_config.yaml",
            "configs/sampling.yaml",
            "sub_agents/verifier.yaml",
            "prompts/coder.md",
            "prompts/verifier.md",
        ):
            self.assertTrue((SUBMISSION / relative).is_file(), relative)
        self.assertFalse((SUBMISSION / "sub_agents" / "coder.yaml").exists())

    def test_root_is_compaction_safe_llm_coder_with_verifier_agent_tool(self):
        root = (SUBMISSION / "agent.yaml").read_text(encoding="utf-8")
        self.assertIn("agent_class: LlmAgent", root)
        self.assertIn("name: swe_e4b_coder", root)
        self.assertIn("model: gemma-4-12b-it-qat-w4a16-ct", root)
        self.assertIn("instruction: !include prompts/coder.md", root)
        self.assertIn("generate_content_config: !include configs/sampling.yaml", root)
        for tool in (
            "- run_command",
            "- read_file",
            "- edit_file",
            "- get_status",
            "- get_code_neighbors",
            "- search_similar_code",
            "- get_code_subgraph",
        ):
            self.assertIn(tool, root)
        self.assertIn("- agent_tool:", root)
        self.assertIn("config_path: sub_agents/verifier.yaml", root)
        self.assertIn("skip_summarization: true", root)
        self.assertNotIn("sub_agents:", root)
        self.assertNotIn("- submit_patch", root)
        self.assertNotIn("- write_file", root)

    def test_root_and_verifier_share_12b_but_only_verifier_can_submit(self):
        root = (SUBMISSION / "agent.yaml").read_text(encoding="utf-8")
        verifier = (SUBMISSION / "sub_agents" / "verifier.yaml").read_text(encoding="utf-8")

        for text in (root, verifier):
            self.assertIn("model: gemma-4-12b-it-qat-w4a16-ct", text)
            self.assertNotIn("adapter:", text)
            self.assertNotIn("- write_file", text)
            self.assertIn("- run_command", text)
            self.assertIn("- read_file", text)
            self.assertIn("- edit_file", text)
            self.assertIn("- get_status", text)

        self.assertNotIn("- submit_patch", root)
        self.assertIn("- submit_patch", verifier)
        self.assertIn("generate_content_config: !include configs/sampling.yaml", root)
        self.assertIn("generate_content_config: !include ../configs/sampling.yaml", verifier)
        self.assertIn("instruction: !include ../prompts/verifier.md", verifier)

    def test_verifier_includes_are_relative_to_its_yaml(self):
        verifier = (SUBMISSION / "sub_agents" / "verifier.yaml").read_text(encoding="utf-8")
        self.assertNotIn("!include prompts/", verifier)
        self.assertNotIn("!include configs/", verifier)
        self.assertIn("!include ../prompts/verifier.md", verifier)
        self.assertIn("!include ../configs/sampling.yaml", verifier)

    def test_both_prompts_receive_problem_context(self):
        coder = (SUBMISSION / "prompts" / "coder.md").read_text(encoding="utf-8")
        verifier = (SUBMISSION / "prompts" / "verifier.md").read_text(encoding="utf-8")
        self.assertIn("{problem_description}", coder)
        self.assertIn("{problem_description}", verifier)

    def test_coder_keeps_bounded_edit_test_and_verifier_handoff_policy(self):
        prompt = (SUBMISSION / "prompts" / "coder.md").read_text(encoding="utf-8")
        for phrase in (
            "After two failed `edit_file` attempts",
            "tiny `run_command` script",
            "assert the exact old text",
            "inspect `git diff`",
            "targeted verification",
            "Do not submit",
            "Call `swe_e4b_verifier` exactly once",
        ):
            self.assertIn(phrase, prompt)

    def test_verifier_uses_evidence_first_targeted_gate(self):
        prompt = (SUBMISSION / "prompts" / "verifier.md").read_text(encoding="utf-8")
        for phrase in (
            "Start from the existing working tree",
            "inspect `git diff`",
            "smallest directly relevant test",
            "Do not begin with the full test suite",
            "read the failing test",
            "one evidence-backed narrow repair",
            "re-run the same targeted verification",
        ):
            self.assertIn(phrase, prompt)

    def test_verifier_never_submits_a_known_failing_patch(self):
        prompt = (SUBMISSION / "prompts" / "verifier.md").read_text(encoding="utf-8")
        self.assertIn("Only call `submit_patch` after targeted verification passes", prompt)
        self.assertIn("If targeted verification still fails", prompt)
        self.assertIn("do not call `submit_patch`", prompt)
        self.assertNotIn("preserve the **smallest defensible patch**", prompt)
        self.assertNotIn("call `submit_patch` as your final tool action to terminate this task once", prompt)

    def test_sampling_uses_bounded_12b_thinking_budget(self):
        text = (SUBMISSION / "configs" / "sampling.yaml").read_text(encoding="utf-8")
        self.assertIn("temperature: 0.2", text)
        self.assertIn("top_p: 0.95", text)
        self.assertIn("max_output_tokens: 16384", text)
        self.assertIn("thinking_budget: 1024", text)
        self.assertIn("include_thoughts: true", text)

    def test_eval_budget_is_explicitly_bounded(self):
        text = (SUBMISSION / "eval_config.yaml").read_text(encoding="utf-8")
        self.assertIn("timeout_seconds: 300", text)
        self.assertIn("max_tool_calls: 32", text)
        self.assertIn("max_time_minutes: 5", text)
        self.assertIn("max_turns: 64", text)


if __name__ == "__main__":
    unittest.main()
