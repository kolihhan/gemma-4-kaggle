"""V3-R ZIP provenance and budget checks: no model inference or Kaggle scores."""
from __future__ import annotations

import hashlib
import io
from unittest.mock import patch
import unittest
import zipfile

from scripts import build_solver_v3r_candidate as v3

V2 = {
    "agent.yaml": "agent_class: LlmAgent\nname: swe_coder\n"
                  "model: gemma-4-31b-it-qat-w4a16-ct\n"
                  "instruction: !include prompts/system.md\n"
                  "tools:\n  - run_command\n  - read_file\n"
                  "generate_content_config: !include configs/sampling.yaml\n",
    "prompts/system.md": "Pinned external Budget-Fit V2 base behavior.\n",
    "configs/sampling.yaml": "temperature: 0.2\nthinking_config:\n  thinking_budget: 4096\n",
    "eval_config.yaml": "evaluation:\n  timeout_seconds: 240\n"
                        "  max_tool_calls: 28\n  max_time_minutes: 8\n"
                        "  max_turns: 80\n",
}


class V3RCandidateTests(unittest.TestCase):
    def setUp(self):
        p=patch.object(v3, "validate_source_zip", return_value=dict(V2))
        p.start()
        self.addCleanup(p.stop)

    def test_31b_same_sampler_and_bounded_5min_28calls(self):
        files=v3.payload(b"fixture")
        self.assertEqual(files["configs/sampling.yaml"], V2["configs/sampling.yaml"])
        self.assertIn("model: gemma-4-31b-it-qat-w4a16-ct", files["agent.yaml"])
        self.assertIn("max_tool_calls: 28", files["eval_config.yaml"])
        self.assertIn("max_turns: 80", files["eval_config.yaml"])
        self.assertIn("max_time_minutes: 5", files["eval_config.yaml"])
        self.assertNotIn("max_time_minutes: 8", files["eval_config.yaml"])
        self.assertIn("skills:\n  - skills/repair-witness",files["agent.yaml"])
        self.assertIn("run_skill_script", files["prompts/system.md"])
        self.assertIn("skills/repair-witness/SKILL.md", files)
        self.assertIn("skills/repair-witness/scripts/witness.py", files)

    def test_actual_executable_witness_not_optional_empty_skill(self):
        files=v3.payload(b"fixture")
        self.assertIn("def run_witness(",files["skills/repair-witness/scripts/witness.py"])
        self.assertIn("before",files["skills/repair-witness/SKILL.md"])
        self.assertIn("after",files["skills/repair-witness/SKILL.md"])
        self.assertIn("status",files["skills/repair-witness/scripts/witness.py"])

    def test_zip_deterministic_and_only_expected_members(self):
        a=v3.build(b"fixture")
        self.assertEqual(a,v3.build(b"fixture"))
        with zipfile.ZipFile(io.BytesIO(a)) as archive:
            self.assertIsNone(archive.testzip())
            self.assertEqual(set(archive.namelist()),
                set(V2)|{"skills/repair-witness/SKILL.md",
                         "skills/repair-witness/scripts/witness.py"})
            self.assertTrue(archive.read("prompts/system.md").startswith(
                V2["prompts/system.md"].encode()))
            self.assertEqual(archive.read("configs/sampling.yaml"),
                             V2["configs/sampling.yaml"].encode())
        self.assertEqual(hashlib.sha256(a).hexdigest(),
                         hashlib.sha256(v3.build(b"fixture")).hexdigest())

    def test_fails_closed_on_drifted_budget_or_duplicate_skills(self):
        wrong=dict(V2)
        wrong["eval_config.yaml"]=wrong["eval_config.yaml"].replace(
            "max_time_minutes: 8","max_time_minutes: 15")
        with patch.object(v3,"validate_source_zip",return_value=wrong):
            with self.assertRaisesRegex(ValueError,"budget drift"):
                v3.payload(b"fixture")
        wrong2=dict(V2)
        wrong2["agent.yaml"] += "skills:\n  - skills/old\n"
        with patch.object(v3,"validate_source_zip",return_value=wrong2):
            with self.assertRaisesRegex(ValueError,"unexpected skill"):
                v3.payload(b"fixture")


if __name__=="__main__":
    unittest.main()
