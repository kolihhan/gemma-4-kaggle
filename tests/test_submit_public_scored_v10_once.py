"""No network or official submission: exact-score reproducibility and SDK gates."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib,io,json,unittest
from unittest.mock import patch
import zipfile
from scripts import submit_public_scored_v10_once as s


def fake_blob():
    files={
        "agent.yaml":"agent_class: LlmAgent\nmodel: "+s.MODEL+"\nname: direct\n",
        "configs/sampling.yaml":"thinking_budget: 4096\n",
        "eval_config.yaml":"evaluation:\n  max_time_minutes: 8\n  max_tool_calls: 28\n  max_turns: 80\n",
        "prompts/system.md":"Perform targeted repairs\n",
    }
    out=io.BytesIO()
    with zipfile.ZipFile(out,"w") as z:
        for key,value in files.items():z.writestr(key,value)
    data=out.getvalue()
    sha={k:hashlib.sha256(v.encode()).hexdigest() for k,v in files.items()}
    payload_sha=hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest()
    return data,sha,payload_sha


@dataclass
class Response:
    version_number: int | None = 2
    versionNumber: int | None = 2
    ref: str | None = "/code/"+s.KERNEL
    url: str | None = "https://www.kaggle.com/code/"+s.KERNEL
    error: str = ""


class OneShotControls(unittest.TestCase):
    def test_package_identity_and_exact_per_file_hashes(self):
        blob,sha,payload=fake_blob()
        with patch.object(s,"EXPECTED_SHA",s.digest(blob)),\
             patch.object(s,"EXPECTED_MEMBERS",sha),\
             patch.object(s,"EXPECTED_FILES_SHA",payload):
            result=s.verify_source(blob)
            self.assertEqual(set(result),set(sha))
            with self.assertRaisesRegex(RuntimeError,"ZIP_HASH_DRIFT"):
                s.verify_source(blob+b" ")

    def test_real_kaggle_sdk_reference_both_supported(self):
        self.assertEqual(s.verified_version(Response()),2)
        self.assertEqual(s.verified_version(Response(ref=s.KERNEL)),2)
        for kw in (
            {"versionNumber":3},
            {"ref":"/code/different-user/unrelated-kernel"},
            {"url":"https://evil.com/code/"+s.KERNEL},
            {"url":"https://www.kaggle.com/code/other/slug"},
            {"error":"failed"},
            {"version_number":None,"versionNumber":None},
        ):
            with self.subTest(kw=kw),self.assertRaises(RuntimeError):
                s.verified_version(Response(**kw))

    def test_submission_marker_idempotent(self):
        marker={"description":s.MARKER,"ref":"9999","status":"SubmissionStatus.PENDING",
                "publicScore":""}
        self.assertEqual(s.matching_receipt([marker])["ref"],"9999")
        self.assertIsNone(s.matching_receipt([{"description":"unrelated"}]))
        with self.assertRaisesRegex(RuntimeError,"DUPLICATE"):
            s.matching_receipt([marker,marker])
        self.assertIn("flexonafft",s.PUBLIC_SOURCE)

    def test_no_competition_call_outside_final_submission(self):
        from pathlib import Path
        text=Path(s.__file__).read_text()
        self.assertEqual(text.count("api.competition_submit_code("),1)
        self.assertIn("if not check_quota():",text)
        self.assertIn("if got!=local:",text)
        self.assertIn("PUBLIC_V10_AUTHENTICATED_COMPETITION_RECEIPT=",text)
        self.assertEqual(s.EXPECTED_SHA,"6ff73d104725cc31deadd18787f3f55e5ce534889cec82387e3b280637d34887")

if __name__=="__main__":
    unittest.main()
