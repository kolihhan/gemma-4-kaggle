"""CPU-only tests for post-hoc matched five-minute direct V2 control."""
from __future__ import annotations
import json, unittest
from pathlib import Path
from unittest.mock import patch
from scripts import render_v2_5min_requests7328_control as c

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=json.loads((ROOT/c.MANIFEST_PATH).read_text())
TEMPLATE=(ROOT/c.TEMPLATE_PATH).read_text()
BASE={
  "agent.yaml":"name: direct\nmodel: "+c.MODEL+"\ntools:\n  - read_file\n  - edit_file\n",
  "eval_config.yaml":"evaluation:\n  max_time_minutes: 8\n  max_tool_calls: 28\n  max_turns: 80\n",
  "configs/sampling.yaml":"thinking_budget: 4096\n",
  "prompts/system.md":"Original V2 prompt\n",
}
class V2FiveMinuteTests(unittest.TestCase):
    @patch.object(c,"validate_source_zip",return_value=dict(BASE))
    def test_only_time_cap_is_modified(self,_):
        result=c.control_files(b"placeholder")
        self.assertEqual(result["eval_config.yaml"],
            BASE["eval_config.yaml"].replace("max_time_minutes: 8","max_time_minutes: 5"))
        for k in BASE:
            if k!="eval_config.yaml":self.assertEqual(result[k],BASE[k])
        self.assertNotIn("agent_tool",result["agent.yaml"])

    @patch.object(c,"validate_source_zip",return_value=dict(BASE))
    def test_render_single_selected_case_and_official_evaluator(self,_):
        source=c.render_runtime(TEMPLATE,b"fixture",MANIFEST)
        self.assertIn('MODEL_NAME = "gemma-4-31b-it-qat-w4a16-ct"',source)
        self.assertIn("requests_7328",source)
        self.assertIn("v2_5min_requests7328_results.json",source)
        self.assertNotIn('"__SUBMISSION_PAYLOAD_B64__"',source)
        self.assertNotIn("competition_submit_code",source)
        compile(source,"v2_control_runtime.py","exec")

    @patch.object(c,"validate_source_zip",return_value=dict(BASE))
    def test_resource_drift_fail_closed(self,_):
        p=dict(BASE)
        p["eval_config.yaml"]=p["eval_config.yaml"].replace("max_tool_calls: 28","max_tool_calls: 50")
        with patch.object(c,"validate_source_zip",return_value=p):
            with self.assertRaisesRegex(ValueError,"resource contract"):
                c.control_files(b"fixture")

    def test_manifest_is_posthoc_and_not_a_claim_of_holdout(self):
        self.assertEqual(MANIFEST["task"],"requests_7328")
        self.assertEqual(MANIFEST["evaluations"],1)
        self.assertEqual(MANIFEST["max_time_minutes"],5)
        self.assertIn("POST-HOC",MANIFEST["classification"])
        self.assertIn("private",MANIFEST["safety"].lower())

if __name__=="__main__":unittest.main()
