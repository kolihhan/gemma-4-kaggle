"""Freeze V4 vs V3 changes to issue-specific counterexample evidence."""
from __future__ import annotations

import hashlib
import io
from unittest.mock import patch
import unittest
import zipfile

from scripts import build_solver_v4_cgr_candidate as v4

V3_FIXTURE={
    "agent.yaml": "agent_class: LlmAgent\nname: swe_agent\nmodel: gemma-4-31b-it-qat-w4a16-ct\n"
                 "skills:\n  - skills/repair-witness\n",
    "prompts/system.md": "Pinned V3-R system prompt.\n",
    "configs/sampling.yaml": "temperature: 0.2\ntop_p: 0.95\n",
    "eval_config.yaml": "evaluation:\n  max_tool_calls: 28\n  max_time_minutes: 5\n  max_turns: 80\n",
    "skills/repair-witness/SKILL.md": "---\nname: repair-witness\n---\nUse real pytest.\n",
    "skills/repair-witness/scripts/witness.py": "print('real V3 instrument')\n",
}


class CandidateTests(unittest.TestCase):
    def setUp(self):
        p=patch.object(v4.v3,"payload",return_value=dict(V3_FIXTURE))
        p.start()
        self.addCleanup(p.stop)

    def test_new_observable_without_model_or_budget_drift(self):
        result=v4.payload(b"frozen-control")
        self.assertEqual(result["agent.yaml"],V3_FIXTURE["agent.yaml"])
        self.assertEqual(result["eval_config.yaml"],V3_FIXTURE["eval_config.yaml"])
        self.assertEqual(result["configs/sampling.yaml"],V3_FIXTURE["configs/sampling.yaml"])
        self.assertEqual(result["skills/repair-witness/scripts/witness.py"],
                         V3_FIXTURE["skills/repair-witness/scripts/witness.py"])
        self.assertIn("counterexample.py",result["skills/repair-witness/SKILL.md"])
        self.assertIn("before",result[v4.MEMBER])
        self.assertIn("after",result[v4.MEMBER])
        self.assertIn("No imports from hidden grader",result["prompts/system.md"])
        self.assertIn("one",result["prompts/system.md"].lower())

    def test_deterministic_source_to_zip_and_safety(self):
        a=v4.build(b"frozen-control")
        self.assertEqual(a,v4.build(b"frozen-control"))
        with zipfile.ZipFile(io.BytesIO(a)) as archive:
            self.assertIsNone(archive.testzip())
            self.assertEqual(set(archive.namelist()),set(V3_FIXTURE)|{v4.MEMBER})
            self.assertEqual(archive.read("agent.yaml"),
                             V3_FIXTURE["agent.yaml"].encode())
        self.assertEqual(hashlib.sha256(a).digest(),
                         hashlib.sha256(v4.build(b"frozen-control")).digest())

    def test_refuse_duplicate_counterexample_and_budget_drift(self):
        duplicate=dict(V3_FIXTURE)
        duplicate[v4.MEMBER]="bad"
        with patch.object(v4.v3,"payload",return_value=duplicate):
            with self.assertRaises(ValueError):
                v4.payload(b"frozen-control")
        drift=dict(V3_FIXTURE)
        drift["eval_config.yaml"]=drift["eval_config.yaml"].replace(
            "max_time_minutes: 5","max_time_minutes: 8")
        with patch.object(v4.v3,"payload",return_value=drift):
            with self.assertRaisesRegex(ValueError,"budget drift"):
                v4.payload(b"frozen-control")


if __name__=="__main__":
    unittest.main()
