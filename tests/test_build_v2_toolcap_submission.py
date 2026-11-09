"""Isolated tests of V2 60-call Kaggle ZIP candidate (CPU, no Kaggle)."""
import hashlib
import io
import unittest
from unittest.mock import patch
import zipfile

from scripts import build_v2_toolcap_submission as b

V2 = {
    "agent.yaml": """agent_class: LlmAgent
name: swe_coder
model: gemma-4-31b-it-qat-w4a16-ct
instruction: !include prompts/system.md
tools:
  - run_command
  - read_file
  - edit_file
  - submit_patch
generate_content_config: !include configs/sampling.yaml
""",
    "prompts/system.md": "Original pinned Budget-Fit prompt\n",
    "configs/sampling.yaml": "temperature: 0.2\nthinking_config:\n  thinking_budget: 4096\n",
    "eval_config.yaml": "evaluation:\n  max_time_minutes: 8\n  max_tool_calls: 28\n  max_turns: 80\n",
}


class V2ToolcapSubmissionTests(unittest.TestCase):
    def setUp(self):
        p = patch.object(b, "validate_source_zip", return_value=dict(V2))
        p.start()
        self.addCleanup(p.stop)

    def test_only_different_field_is_max_tool_calls(self):
        files = b.files_for_candidate(b"fixture")
        self.assertEqual(set(files),set(V2))
        for name in V2:
            if name=="eval_config.yaml":
                self.assertEqual(files[name], V2[name].replace(
                    "max_tool_calls: 28","max_tool_calls: 60"))
            else:
                self.assertEqual(files[name], V2[name])
        self.assertIn("max_time_minutes: 8", files["eval_config.yaml"])
        self.assertIn("max_turns: 80", files["eval_config.yaml"])

    def test_reproducible_minimal_archive(self):
        a=b.build(b"fixture")
        c=b.build(b"fixture")
        self.assertEqual(a,c)
        with zipfile.ZipFile(io.BytesIO(a)) as z:
            self.assertEqual(set(z.namelist()),set(V2))
            self.assertIsNone(z.testzip())
            self.assertIn(b"max_tool_calls: 60", z.read("eval_config.yaml"))

    def test_fail_closed_if_source_contract_drifted(self):
        bad=dict(V2)
        bad["eval_config.yaml"]=bad["eval_config.yaml"].replace(
            "max_tool_calls: 28","max_tool_calls: 64")
        with patch.object(b, "validate_source_zip",return_value=bad):
            with self.assertRaisesRegex(ValueError,"contract drift"):
                b.files_for_candidate(b"fixture")

    def test_fail_closed_for_unexpected_extra_file(self):
        with patch.object(b,"validate_source_zip",return_value={
                **V2,"adapters/unknown.bin":"bad"}):
            with self.assertRaisesRegex(ValueError,"unexpected control"):
                b.files_for_candidate(b"fixture")


if __name__=="__main__":
    unittest.main()
