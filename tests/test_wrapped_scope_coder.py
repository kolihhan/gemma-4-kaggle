"""Static contracts for the root LlmAgent / mandatory nested workflow arm."""
from __future__ import annotations

import io
import unittest
from unittest.mock import patch
import zipfile

from scripts import build_two_stage_scope_coder_candidate as staged
from scripts import build_wrapped_scope_coder_candidate as wrapped
from tests.test_two_stage_scope_coder import fake_source


class WrappedRootTests(unittest.TestCase):
    @patch.object(staged,"validate_source_zip",return_value=fake_source())
    def test_only_nested_workflow_has_mutation_tools(self,_):
        files=wrapped.files(b"source")
        root=files["agent.yaml"]
        self.assertIn("agent_class: LlmAgent",root)
        self.assertIn("model: "+staged.MODEL,root)
        self.assertEqual(root.count("agent_tool:"),1)
        self.assertIn("config_path: workflow.yaml",root)
        for tool in staged.WRITER_TOOLS:
            self.assertNotIn("  - "+tool+"\n",root)
        nested=files["workflow.yaml"]
        self.assertIn("agent_class: SequentialAgent",nested)
        self.assertLess(nested.index("sub_agents/scope.yaml"),
                        nested.index("sub_agents/coder.yaml"))
        scope=files["sub_agents/scope.yaml"]
        for tool in ("run_command","edit_file","write_file","submit_patch"):
            self.assertNotIn("  - "+tool+"\n",scope)
        self.assertIn("  - submit_patch\n",files["sub_agents/coder.yaml"])
        self.assertIn("{scope_packet}",files["prompts/coder.md"])
        self.assertEqual(files["eval_config.yaml"],staged.files(b"source")["eval_config.yaml"])

    @patch.object(staged,"validate_source_zip",return_value=fake_source())
    def test_archive_reproducible(self,_):
        first=wrapped.build(b"test")
        self.assertEqual(first,wrapped.build(b"test"))
        with zipfile.ZipFile(io.BytesIO(first)) as z:
            self.assertIsNone(z.testzip())
            self.assertEqual(z.read("agent.yaml").decode(),wrapped.ROOT_YAML)
            self.assertIn(b"max_time_minutes: 5",z.read("eval_config.yaml"))


if __name__=="__main__":
    unittest.main()
