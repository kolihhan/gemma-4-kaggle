"""CPU-only contract checks for matched recovery-role archives.

No model, Kaggle API, competition data, or real source ZIP is needed here.
The pinned source hash is validated by the production entry point, which
these unit tests mock to isolate the structural transformation.
"""
import hashlib
import io
import unittest
from unittest.mock import patch
import zipfile

from scripts import build_recovery_decision_candidate as b


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
  - submit_patch
  - get_status
  - get_code_neighbors
  - search_similar_code
  - get_code_subgraph
generate_content_config: !include configs/sampling.yaml
""",
    "prompts/system.md": "Original pinned V2 instruction.\n",
    "configs/sampling.yaml": "temperature: 0.2\n",
    "eval_config.yaml": "evaluation:\n  max_time_minutes: 8\n  max_tool_calls: 28\n  max_turns: 80\n",
}


class RecoveryDecisionBuilderTests(unittest.TestCase):
    def setUp(self):
        self.mocked = patch.object(b, "validate_source_zip", return_value=dict(V2))
        self.mocked.start()
        self.addCleanup(self.mocked.stop)

    def test_arms_only_vary_child_instruction(self):
        a = b.candidate_files(b"source", "fresh_coder")
        c = b.candidate_files(b"source", "recovery_reviewer")
        changed = {name for name in a if a[name] != c[name]}
        self.assertEqual(changed, {"prompts/recovery-adviser.md"})
        self.assertIn("ordinary coding assistant", a["prompts/recovery-adviser.md"])
        self.assertIn("independent recovery critic", c["prompts/recovery-adviser.md"])
        self.assertEqual(a["configs/sampling.yaml"], V2["configs/sampling.yaml"])
        self.assertEqual(a["eval_config.yaml"], V2["eval_config.yaml"])
        self.assertTrue(a["prompts/system.md"].startswith(V2["prompts/system.md"]))
        for tool in ("run_command", "read_file", "edit_file",
                     "write_file", "submit_patch", "get_status",
                     "get_code_neighbors", "search_similar_code", "get_code_subgraph"):
            self.assertIn(f"  - {tool}\n", a["agent.yaml"])
        self.assertEqual(a["agent.yaml"].count("agent_tool:"), 1)
        self.assertEqual(a["agent.yaml"].count("submit_patch"), 1)
        self.assertIn("model: gemma-4-31b-it-qat-w4a16-ct",
                      a["sub_agents/recovery-adviser.yaml"])
        self.assertIn("tools: []", a["sub_agents/recovery-adviser.yaml"])
        self.assertIn("include_contents: none", a["sub_agents/recovery-adviser.yaml"])
        self.assertIn("instruction: !include ../prompts/recovery-adviser.md",
                      a["sub_agents/recovery-adviser.yaml"])
        self.assertIn("thinking_budget: 256", a["sub_agents/recovery-adviser.yaml"])

    def test_build_is_deterministic_and_checks_comparison(self):
        one = b.build(b"source")
        two = b.build(b"source")
        self.assertEqual(one, two)
        self.assertEqual(set(one), set(b.ARMS))
        self.assertNotEqual(hashlib.sha256(one["fresh_coder"]).hexdigest(),
                            hashlib.sha256(one["recovery_reviewer"]).hexdigest())
        for arm, content in one.items():
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                self.assertIsNone(archive.testzip())
                self.assertEqual(set(archive.namelist()),
                                 set(V2) | {
                                     "sub_agents/recovery-adviser.yaml",
                                     "prompts/recovery-adviser.md",
                                 })

    def test_fail_closed_for_invalid_source_contract(self):
        with self.assertRaisesRegex(ValueError, "unknown arm"):
            b.candidate_files(b"source", "magic")
        with patch.object(b, "validate_source_zip", return_value={
                **V2, "unexpected.txt": "oops"}):
            with self.assertRaisesRegex(ValueError, "unexpected pinned"):
                b.candidate_files(b"source", "fresh_coder")
        bad = dict(V2)
        bad["agent.yaml"] = bad["agent.yaml"].replace(
            "  - submit_patch\n", ""
        )
        with patch.object(b, "validate_source_zip", return_value=bad):
            with self.assertRaisesRegex(ValueError, "native tool contract"):
                b.candidate_files(b"source", "fresh_coder")
        bad = dict(V2)
        bad["agent.yaml"] = bad["agent.yaml"].replace(
            "\ngenerate_content_config:", "\n  - agent_tool: old\n"
            "generate_content_config:"
        )
        with patch.object(b, "validate_source_zip", return_value=bad):
            with self.assertRaisesRegex(ValueError, "unexpected agent structure"):
                b.candidate_files(b"source", "fresh_coder")


if __name__ == "__main__":
    unittest.main()
