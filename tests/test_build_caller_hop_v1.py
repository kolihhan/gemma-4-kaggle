"""CPU-only one-mechanism gate: production config and archive, not a PASS test."""
import hashlib
import io
import unittest
from unittest.mock import patch
import zipfile

from scripts import build_caller_hop_v1 as candidate
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
    "prompts/system.md": "Frozen base policy",
    "configs/sampling.yaml": "temperature: 0.2\nthinking_budget: 4096\n",
    "eval_config.yaml": "evaluation:\n  max_time_minutes: 8\n  max_tool_calls: 28\n  max_turns: 80\n",
}

class CallerHopCandidateTests(unittest.TestCase):
    def setUp(self):
        p=patch.object(parent,"validate_source_zip",return_value=dict(V2))
        p.start()
        self.addCleanup(p.stop)

    def test_exactly_one_prompt_difference_vs_scored_018(self):
        from scripts.build_toolcap60_timeout_recovery import files_for_candidate as control
        base=control(b"pinned")
        treatment=candidate.files_for_candidate(b"pinned")
        self.assertEqual(set(base),set(treatment))
        for key in base:
            if key=="prompts/system.md":
                self.assertNotEqual(treatment[key],base[key])
                self.assertTrue(treatment[key].startswith(base[key]))
            else:
                self.assertEqual(treatment[key],base[key])
        self.assertIn("max_time_minutes: 5",treatment["eval_config.yaml"])
        self.assertIn("max_tool_calls: 60",treatment["eval_config.yaml"])
        self.assertIn("max_turns: 80",treatment["eval_config.yaml"])
        self.assertEqual(treatment["agent.yaml"].count("model: gemma-4-31b-it-qat-w4a16-ct"),1)

    def test_one_hop_conditional_not_unbounded(self):
        text=candidate.files_for_candidate(b"pinned")["prompts/system.md"]
        self.assertIn("If two or more different definitions",text)
        self.assertIn("make ONE targeted",text)
        self.assertIn("SKIP graph expansion",text)
        self.assertIn("do not\nretry or widen",text)
        self.assertIn("submit_patch",text)

    def test_reproducible_crc_and_no_extra_tools(self):
        a=candidate.build(b"pinned")
        self.assertEqual(hashlib.sha256(a).digest(),hashlib.sha256(candidate.build(b"pinned")).digest())
        with zipfile.ZipFile(io.BytesIO(a)) as z:
            self.assertIsNone(z.testzip())
            self.assertEqual(set(z.namelist()),set(V2))
            self.assertIn(b"one-hop implementation localization",z.read("prompts/system.md"))
            self.assertEqual(z.read("agent.yaml").decode(),V2["agent.yaml"])

    def test_fail_closed_wrong_model_or_missing_graph(self):
        wrong=dict(V2)
        wrong["agent.yaml"]=wrong["agent.yaml"].replace("gemma-4-31b-it-qat-w4a16-ct","gemma-4-12b-it-qat-w4a16-ct")
        with patch.object(parent,"validate_source_zip",return_value=wrong):
            with self.assertRaisesRegex(ValueError,"wrong model|31B control model drift"):
                candidate.files_for_candidate(b"pinned")
        wrong=dict(V2)
        wrong["agent.yaml"]=wrong["agent.yaml"].replace("  - get_code_neighbors\n","")
        with patch.object(parent,"validate_source_zip",return_value=wrong):
            with self.assertRaisesRegex(ValueError,"Missing existing native graph tools"):
                candidate.files_for_candidate(b"pinned")

    def test_fails_closed_on_budget_drift(self):
        wrong=dict(V2)
        wrong["eval_config.yaml"]=wrong["eval_config.yaml"].replace("max_time_minutes: 8","max_time_minutes: 7")
        with patch.object(parent,"validate_source_zip",return_value=wrong):
            with self.assertRaisesRegex(ValueError,"task-time configuration"):
                candidate.files_for_candidate(b"pinned")

if __name__=="__main__":
    unittest.main()
