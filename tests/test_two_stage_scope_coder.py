"""Architecture-only tests: enforce stage ordering and read-only investigator.

The test fixture imitates just the four-file source ZIP's parsed content.
The official CI separately downloads and hashes the real pinned V2 source.
"""
from __future__ import annotations

import io
import unittest
from unittest.mock import patch
import zipfile

from scripts import build_two_stage_scope_coder_candidate as staged


def fake_source():
    root=(
        "agent_class: LlmAgent\n"
        "name: original\n"
        "model: "+staged.MODEL+"\n"
        "tools:\n"+ "".join(f"  - {name}\n" for name in staged.WRITER_TOOLS)
        + "generate_content_config: !include configs/sampling.yaml\n"
    )
    return {
        "agent.yaml":root,
        "prompts/system.md":"Original V2 prompt",
        "configs/sampling.yaml":"temperature: 0.2",
        "eval_config.yaml":"evaluation:\n  max_time_minutes: 8\n  max_tool_calls: 28\n  max_turns: 80\n",
    }


class MandatoryScopeArchitectureTests(unittest.TestCase):
    @patch.object(staged,"validate_source_zip",return_value=fake_source())
    def test_scope_cannot_mutate_and_always_precedes_coder(self,_):
        files=staged.files(b"source")
        root=files["agent.yaml"]
        self.assertIn("agent_class: SequentialAgent",root)
        self.assertLess(root.index("config_path: sub_agents/scope.yaml"),
                        root.index("config_path: sub_agents/coder.yaml"))
        scope=files["sub_agents/scope.yaml"]
        coder=files["sub_agents/coder.yaml"]
        self.assertIn("output_key: scope_packet",scope)
        self.assertIn("{scope_packet}",files["prompts/coder.md"])
        self.assertIn("read_file",scope)
        for name in ("edit_file","write_file","run_command","submit_patch"):
            self.assertNotIn("  - "+name+"\n",scope)
        self.assertIn("  - submit_patch\n",coder)
        self.assertIn("  - edit_file\n",coder)
        self.assertNotIn("skills:",root)
        self.assertEqual(set(files)-set(fake_source()),{
            "prompts/scope.md","prompts/coder.md",
            "sub_agents/scope.yaml","sub_agents/coder.yaml"})
        self.assertNotIn("prompts/system.md",files)

    @patch.object(staged,"validate_source_zip",return_value=fake_source())
    def test_shared_task_budget_and_zip_deterministic(self,_):
        a=staged.build(b"baseline")
        b=staged.build(b"baseline")
        self.assertEqual(a,b)
        with zipfile.ZipFile(io.BytesIO(a)) as z:
            self.assertIsNone(z.testzip())
            budget=z.read("eval_config.yaml").decode()
            self.assertIn("max_time_minutes: 5",budget)
            self.assertIn("max_tool_calls: 28",budget)
            self.assertIn("max_turns: 80",budget)

    @patch.object(staged,"validate_source_zip",return_value=fake_source())
    def test_unexpected_model_or_budget_rejected(self, mock):
        for key,original,replacement in (
            ("agent.yaml",staged.MODEL,"some-other-model"),
            ("eval_config.yaml","max_time_minutes: 8","max_time_minutes: 5"),
            ("agent.yaml","  - submit_patch\n",""),
        ):
            x=fake_source()
            x[key]=x[key].replace(original,replacement)
            mock.return_value=x
            with self.subTest(key=key,changed=original):
                with self.assertRaises(ValueError):
                    staged.files(b"wrong")

    @patch.object(staged,"validate_source_zip",return_value=fake_source())
    def test_all_native_writer_tools_present_exactly_once(self,_):
        files=staged.files(b"baseline")
        coder=files["sub_agents/coder.yaml"]
        for name in staged.WRITER_TOOLS:
            self.assertEqual(coder.count("  - "+name+"\n"),1)


if __name__=="__main__":
    unittest.main()
