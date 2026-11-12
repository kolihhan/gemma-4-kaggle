import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from scripts import build_matched_12b_31b_capacity as b
from scripts import prepare_public_budgetfit_v2 as v2


F = {
    "agent.yaml": "agent_class: LlmAgent\nname: swe_coder\nmodel: gemma-4-31b-it-qat-w4a16-ct\ntools:\n  - read_file\n",
    "eval_config.yaml":"evaluation:\n  max_time_minutes: 8\n  max_tool_calls: 28\n  max_turns: 80\n",
    "prompts/system.md":"synthetic test only; no competition task or code\n",
    "configs/sampling.yaml":"thinking_budget: 4096\n",
}


def make_original():
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,"w") as z:
        for name, value in sorted(F.items()):
            z.writestr(name,value.encode())
    return buf.getvalue()


class TestModelClassFrozen(unittest.TestCase):
    def patched_source(self):
        src=make_original()
        return src, {
            "EXPECTED_ZIP_SHA256":v2.digest(src),
            "EXPECTED_MEMBERS":{n:v2.digest(content.encode()) for n,content in F.items()},
        }

    def test_model_only_diff_and_equal_budget(self):
        source, pins=self.patched_source()
        with patch.multiple(v2,**pins), patch.object(b,"EXPECTED_ZIP_SHA256",v2.digest(source)):
            arms=b.candidate_files(source)
            self.assertEqual(set(arms),{"v2_31b","v2_12b"})
            a,c=arms["v2_31b"],arms["v2_12b"]
            self.assertEqual({k for k in a if a[k]!=c[k]},{"agent.yaml"})
            self.assertIn("model: "+b.BASE_MODEL,a["agent.yaml"])
            self.assertIn("model: "+b.SMALL_MODEL,c["agent.yaml"])
            self.assertEqual(a["prompts/system.md"],c["prompts/system.md"])
            self.assertEqual(a["configs/sampling.yaml"],c["configs/sampling.yaml"])
            self.assertEqual(a["eval_config.yaml"],c["eval_config.yaml"])
            self.assertIn("max_time_minutes: 5",a["eval_config.yaml"])
            blobs={x:b.archive(y) for x,y in arms.items()}
            self.assertNotEqual(blobs["v2_31b"],blobs["v2_12b"])
            for arm,blob in blobs.items():
                with zipfile.ZipFile(io.BytesIO(blob)) as z:
                    self.assertEqual(set(z.namelist()),set(F))
                    self.assertEqual(z.testzip(),None)

    def test_tamper_fails_closed(self):
        source,pins=self.patched_source()
        with patch.multiple(v2,**pins), patch.object(b,"EXPECTED_ZIP_SHA256",v2.digest(source)):
            with self.assertRaises(ValueError):
                b.candidate_files(source+b"tampered")

    def test_no_external_zip_or_gpu(self):
        self.assertEqual(set(b.ARMS),{"v2_31b","v2_12b"})


if __name__=="__main__":
    unittest.main()
