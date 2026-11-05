"""Test counterfactual evidence B/C package invariants without model inference."""
import unittest

from scripts.discriminating_evidence_schema import build_arm_pair
from scripts.discriminating_evidence_exploratory import ROOT


class DiscriminatingEvidenceSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.b, cls.c = build_arm_pair(ROOT)

    def test_both_use_same_unchanged_official_eval_budget(self):
        from scripts.render_untrained_31b_submission import payload
        _, baseline = payload(ROOT)
        for arm in (self.b, self.c):
            self.assertEqual(arm["eval_config.yaml"], baseline["eval_config.yaml"])
            self.assertEqual(arm["configs/sampling.yaml"], baseline["configs/sampling.yaml"])
            self.assertNotIn("adapter:", "".join(arm.values()))
            self.assertEqual(sorted(arm), sorted(self.b))

    def test_workflow_is_root_llm_agenttool_wrapping_sequential(self):
        for arm in (self.b, self.c):
            self.assertIn("agent_class: LlmAgent", arm["agent.yaml"])
            self.assertIn("sub_agents/sequence.yaml", arm["agent.yaml"])
            self.assertIn("agent_tool:", arm["agent.yaml"])
            self.assertIn("agent_class: SequentialAgent",
                          arm["sub_agents/sequence.yaml"])
            self.assertIn("config_path: sub_agents/evidence.yaml",
                          arm["sub_agents/sequence.yaml"])
            self.assertIn("config_path: sub_agents/coder.yaml",
                          arm["sub_agents/sequence.yaml"])

    def test_identical_evidence_stage_with_state_output(self):
        self.assertEqual(self.b["sub_agents/evidence.yaml"],
                         self.c["sub_agents/evidence.yaml"])
        self.assertEqual(self.b["prompts/evidence.md"], self.c["prompts/evidence.md"])
        self.assertIn("output_key: evidence_packet", self.b["sub_agents/evidence.yaml"])
        self.assertNotIn("edit_file", self.b["sub_agents/evidence.yaml"])
        self.assertNotIn("submit_patch", self.b["sub_agents/evidence.yaml"])

    def test_only_information_interpolation_differs(self):
        keys = [k for k in self.b if self.b[k] != self.c[k]]
        self.assertEqual(keys, ["prompts/coder_stage.md"])
        self.assertIn("{evidence_packet}", self.c["prompts/coder_stage.md"])
        self.assertNotIn("{evidence_packet}", self.b["prompts/coder_stage.md"])
        self.assertIn("{problem_description}", self.c["prompts/coder_stage.md"])
        self.assertIn("{problem_description}", self.b["prompts/coder_stage.md"])
        self.assertEqual(self.b["sub_agents/coder.yaml"], self.c["sub_agents/coder.yaml"])
        self.assertIn("include_contents: none", self.b["sub_agents/coder.yaml"])


if __name__ == "__main__":
    unittest.main()
