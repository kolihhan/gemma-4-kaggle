"""CPU-only contract tests for one-task live Gemma 31B adoption instrument."""
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from scripts import render_wrapped_scope_31b_adoption_probe as m

ROOT=Path(__file__).resolve().parents[1]
PLAN=json.loads((ROOT/m.MANIFEST_PATH).read_text())
TEMPLATE=(ROOT/m.TEMPLATE_PATH).read_text()
FAKE={
"agent.yaml":"agent_class: LlmAgent\nname: repair_orchestrator\nmodel: "+m.MODEL+"\n",
"eval_config.yaml":"evaluation:\n  max_time_minutes: 5\n  max_tool_calls: 28\n  max_turns: 80\n",
"configs/sampling.yaml":"temperature: 0.2\n",
"workflow.yaml":"agent_class: SequentialAgent\n",
"sub_agents/scope.yaml":"tools:\n  - read_file\n",
"sub_agents/coder.yaml":"tools:\n  - edit_file\n",
"prompts/orchestrator.md":"Use exactly one AgentTool",
}


def render():
    with patch.object(m,"validate_source_zip",return_value=FAKE),\
         patch.object(m,"wrapped_files",return_value=dict(FAKE)):
        return m.render_runtime(TEMPLATE,b"test-source",PLAN)


class AdoptionRenderTests(unittest.TestCase):
    def test_instrumented_real_adk_and_one_task(self):
        code=render()
        self.assertIn("AgentTool.run_async=recorded_agenttool_run",code)
        self.assertIn('self.name != "mandatory_scope_then_patch"',code)
        self.assertIn("REAL_31B_AGENTTOOL_UPTAKE",code)
        self.assertIn("wrapped_scope_31b_adoption_results.json",code)
        self.assertIn('MODEL_NAME = "gemma-4-31b-it-qat-w4a16-ct"',code)
        self.assertIn('max_time_minutes',code)
        self.assertNotIn('"__SUBMISSION_PAYLOAD_B64__"',code)
        self.assertNotIn("competition_submit_code",code)
        compile(code,"private_probe_runtime.py","exec")

    def test_salted_one_task_is_order_independent(self):
        scope={"__name__":"cpu_only_no_main"}
        exec(compile(render(),"private_probe_runtime.py","exec"),scope)
        ids=[SimpleNamespace(instance_id=f"requests_{n}") for n in range(101,115)]
        ids.append(SimpleNamespace(instance_id="rich_3064"))
        a=scope["load_holdout_ids"](ids)
        b=scope["load_holdout_ids"](list(reversed(ids)))
        self.assertEqual(a,b)
        self.assertEqual(len(a),1)
        self.assertTrue(a[0].startswith("requests_"))

    def test_frozen_manifest_and_budget_fail_closed(self):
        bad=dict(PLAN)
        bad["selected_tasks"]=2
        with self.assertRaisesRegex(ValueError,"one model task"):
            m.validate_manifest(bad)
        t=dict(FAKE);t["eval_config.yaml"]=t["eval_config.yaml"].replace("max_time_minutes: 5","max_time_minutes: 8")
        with patch.object(m,"validate_source_zip",return_value=t),\
             patch.object(m,"wrapped_files",return_value=t):
            with self.assertRaisesRegex(ValueError,"5min budget"):
                m.render_runtime(TEMPLATE,b"test-source",PLAN)

    def test_source_and_candidate_digest_pinned(self):
        self.assertEqual(len(m.SOURCE_SHA256),64)
        self.assertEqual(len(m.CANDIDATE_SHA256),64)
        self.assertEqual(PLAN["source_zip_sha256"],m.SOURCE_SHA256)
        self.assertEqual(PLAN["candidate_zip_sha256"],m.CANDIDATE_SHA256)


if __name__=="__main__":
    unittest.main()
