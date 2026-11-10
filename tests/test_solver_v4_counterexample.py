"""V4-CGR actually executes locked generated regression tests, no hidden gold."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "experiments/solver-v4/skill/scripts/counterexample.py"


def module():
    spec=importlib.util.spec_from_file_location("v4_counterexample",SCRIPT)
    assert spec and spec.loader
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


REGRESSION = (
    "from example import answer\n\n"
    "def test_issue_contract():\n"
    "    assert answer() == 3\n"
)


class CounterexampleTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.workspace=Path(self.temp.name)/"repo"
        self.workspace.mkdir()
        subprocess.run(["git","init","-q",str(self.workspace)],check=True)
        (self.workspace/"example.py").write_text(
            "def answer():\n    return 2\n",encoding="utf-8")
        self.v4=module()
        self.v4.BASE=Path(self.temp.name)/"state"

    def test_fail_before_real_fix_and_pass_after_exact_locked_test(self):
        before=self.v4.run(self.workspace,"before",source=REGRESSION)
        self.assertEqual(before["status"],"fail",before)
        self.assertTrue(before["baseline_discriminating"])
        self.assertFalse(before["independent_issue_resolved"])
        self.assertFalse(before["test_relevance_verified"])
        self.assertEqual(before["comparison"],"baseline_recorded")
        (self.workspace/"example.py").write_text(
            "def answer():\n    return 3\n",encoding="utf-8")
        after=self.v4.run(self.workspace,"after",case_id=before["case_id"])
        self.assertEqual(after["status"],"pass",after)
        self.assertEqual(after["comparison"],"counterexample_repaired")
        self.assertFalse(after["independent_issue_resolved"])

    def test_baseline_already_passing_not_a_counterexample(self):
        (self.workspace/"example.py").write_text("def answer():\n    return 3\n")
        before=self.v4.run(self.workspace,"before",source=REGRESSION)
        self.assertEqual(before["status"],"pass")
        self.assertFalse(before["baseline_discriminating"])
        after=self.v4.run(self.workspace,"after",case_id=before["case_id"])
        self.assertEqual(after["comparison"],"no_baseline_failure")

    def test_synthetic_assert_false_does_not_create_a_successful_repair(self):
        test="def test_issue_contract():\n    assert False, 'always'\n"
        before=self.v4.run(self.workspace,"before",source=test)
        self.assertEqual(before["status"],"fail")
        after=self.v4.run(self.workspace,"after",case_id=before["case_id"])
        self.assertEqual(after["comparison"],"still_broken")

    def test_import_and_collection_failures_do_not_count(self):
        test="from not_installed_425366 import missing\n\ndef test_issue():\n    assert missing()==1\n"
        before=self.v4.run(self.workspace,"before",source=test)
        self.assertEqual(before["status"],"blocked",before)
        self.assertFalse(before["baseline_discriminating"])

    def test_locked_generated_test_cannot_be_rewritten_to_fake_fix(self):
        before=self.v4.run(self.workspace,"before",source=REGRESSION)
        where=(self.v4._case_dir(self.workspace)/before["case_id"]/"test_issue_contract.py")
        where.write_text(REGRESSION.replace("3","2"),encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"changed after baseline"):
            self.v4.run(self.workspace,"after",case_id=before["case_id"])

    def test_invalid_source_or_case_ids_fail_closed(self):
        for source in ("x=3\n", "def test_case():\n    pass\n",
                       "def test_case():\n    assert 1 ==\n"):
            with self.subTest(source=source):
                with self.assertRaises(ValueError):
                    self.v4.run(self.workspace,"before",source=source)
        with self.assertRaises(ValueError):
            self.v4.run(self.workspace,"after",case_id="../other")
        with self.assertRaises(ValueError):
            self.v4.run(self.workspace,"after",case_id="0"*24,source=REGRESSION)

    def test_cli_works_from_external_skill_cwd_via_real_pwd(self):
        other=Path(self.temp.name)/"skillcwd"
        other.mkdir()
        env=dict(os.environ)
        env.pop("SWE_WORKSPACE",None)
        env["PWD"]=str(self.workspace)
        p=subprocess.run([
            sys.executable,str(SCRIPT),"--phase","before",
            "--source",REGRESSION,
        ],cwd=other,env=env,text=True,capture_output=True,timeout=40)
        self.assertEqual(p.returncode,0,p.stderr)
        output=json.loads(p.stdout)
        self.assertEqual(output["status"],"fail",output)
        self.assertTrue(output["baseline_discriminating"])
        self.assertFalse((self.workspace/"test_issue_contract.py").exists())


    @unittest.expectedFailure
    def test_audit_generated_contract_cannot_modify_source(self):
        # RED integrity audit: frozen V4 executes arbitrary generated pytest
        # without checking whether pytest itself changed tracked source.
        adversarial=(
            "from pathlib import Path\\n\\n"
            "def test_issue_contract():\\n"
            "    target=Path('example.py')\\n"
            "    body=target.read_text()\\n"
            "    if 'return 2' in body:\\n"
            "        target.write_text(body.replace('return 2','return 3'))\\n"
            "        assert False, 'baseline discrepancy'\\n"
            "    assert True\\n"
        )
        before=self.v4.run(self.workspace,"before",source=adversarial)
        self.assertEqual(before["status"],"fail",before)
        self.assertEqual(
            (self.workspace/"example.py").read_text(encoding="utf-8"),
            "def answer():\\n    return 2\\n",
            "Generated tests must not mutate source during BEFORE",
        )

    @unittest.expectedFailure
    def test_audit_generated_test_must_not_fake_repair_without_agent_edit(self):
        # RED integrity audit: BEFORE test mutates implementation and fails;
        # AFTER succeeds on its own side-effect, no agent source edit involved.
        adversarial=(
            "from pathlib import Path\\n\\n"
            "def test_issue_contract():\\n"
            "    target=Path('example.py')\\n"
            "    body=target.read_text()\\n"
            "    if 'return 2' in body:\\n"
            "        target.write_text(body.replace('return 2','return 3'))\\n"
            "        assert False, 'baseline discrepancy'\\n"
            "    assert True\\n"
        )
        before=self.v4.run(self.workspace,"before",source=adversarial)
        self.assertEqual(before["status"],"fail",before)
        after=self.v4.run(self.workspace,"after",case_id=before["case_id"])
        self.assertNotEqual(
            after["comparison"],"counterexample_repaired",
            "A generated test must not count its own source mutation as repair",
        )


if __name__=="__main__":
    unittest.main()
