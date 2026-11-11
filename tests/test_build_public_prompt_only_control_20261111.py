"""No inference: exact one-variable public Prompt-vs-V2 experiment contract."""
from __future__ import annotations
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from scripts import build_public_prompt_only_control_20261111 as p


class PublicPromptContractTests(unittest.TestCase):
    def setUp(self):
        self.old_prompt="Original baseline prompt for tests."
        self.public_prompt="Public competitor prompt for tests."
        self.base={
            "agent.yaml":"name: direct\nmodel: gemma-4-31b-it-qat-w4a16-ct",
            "configs/sampling.yaml":"thinking_budget: 4096",
            "eval_config.yaml":"evaluation:\n  max_time_minutes: 8\n  max_tool_calls: 28\n  max_turns: 80\n",
            "prompts/system.md":self.old_prompt,
        }
        self.new=dict(self.base)
        self.new["prompts/system.md"]=self.public_prompt

    def test_literal_notebook_extract_without_execution(self):
        notebook={"cells":[{"cell_type":"code",
                   "source":["BUNDLE = "+repr(self.new)]}]}
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"public.ipynb"
            path.write_text(json.dumps(notebook))
            with patch.object(p,"EXPECTED_PUBLIC_PROMPT_SHA",
                hashlib.sha256(self.public_prompt.encode()).hexdigest()):
                actual=p.notebook_bundle(path)
            self.assertEqual(actual,self.new)

    def test_only_prompt_differs_original_8_minutes(self):
        with patch.object(p,"validate_source_zip",return_value=self.base),\
             patch.object(p,"EXPECTED_V2_PROMPT_SHA",
                          hashlib.sha256(self.old_prompt.encode()).hexdigest()),\
             patch.object(p,"EXPECTED_PUBLIC_PROMPT_SHA",
                          hashlib.sha256(self.public_prompt.encode()).hexdigest()):
            candidate=p.candidate_files(b"reference",self.new,minutes=8)
        self.assertEqual(candidate,self.new)

    def test_exact_5_minute_clock_only(self):
        with patch.object(p,"validate_source_zip",return_value=self.base),\
             patch.object(p,"EXPECTED_V2_PROMPT_SHA",
                          hashlib.sha256(self.old_prompt.encode()).hexdigest()),\
             patch.object(p,"EXPECTED_PUBLIC_PROMPT_SHA",
                          hashlib.sha256(self.public_prompt.encode()).hexdigest()):
            candidate=p.candidate_files(b"reference",self.new,minutes=5)
        self.assertEqual(candidate["eval_config.yaml"],
                         self.base["eval_config.yaml"].replace("max_time_minutes: 8",
                                                              "max_time_minutes: 5"))
        for k in self.base:
            if k not in ("prompts/system.md","eval_config.yaml"):
                self.assertEqual(candidate[k],self.base[k])
        self.assertEqual(p.make_zip(candidate),p.make_zip(candidate))
        with zipfile.ZipFile(io.BytesIO(p.make_zip(candidate))) as z:
            self.assertIsNone(z.testzip())

    def test_non_prompt_source_drift_rejected(self):
        self.new["agent.yaml"]="name: different"
        with patch.object(p,"validate_source_zip",return_value=self.base),\
             patch.object(p,"EXPECTED_V2_PROMPT_SHA",
                          hashlib.sha256(self.old_prompt.encode()).hexdigest()),\
             patch.object(p,"EXPECTED_PUBLIC_PROMPT_SHA",
                          hashlib.sha256(self.public_prompt.encode()).hexdigest()):
            with self.assertRaisesRegex(ValueError,"changed another file"):
                p.candidate_files(b"reference",self.new,minutes=5)


if __name__=="__main__":
    unittest.main()
