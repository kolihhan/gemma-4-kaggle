"""Tests are synthetic only; not a claim of actual 31B skill uptake."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.audit_pro_v3r_real31b_uptake_20261115 import (
    VERSION, validate, summarize_trace, trace_path, audit
)


class RealSkillAuditTests(unittest.TestCase):
    def _records(self):
        ids=["fastapi_101", "rich_102", "requests_103"]
        return {"version":VERSION,"results":[
            {"instance_id":id_, "arm":arm,
             "resolved":id_=="fastapi_101" and arm=="v3r_5min"}
            for id_ in ids for arm in ("v2_5min","v3r_5min")
        ]}

    def _trace(self):
        return {"steps":[
            {"tool_calls":[{"function_name":"load_skill","arguments":{"skill_name":"repair-witness"}}]},
            {"tool_calls":[{"function_name":"run_skill_script","arguments":{"skill_name":"repair-witness","file_path":"scripts/witness.py","args":{"phase":"before"}}}]},
            {"tool_calls":[{"function_name":"edit_file","arguments":{"filepath":"source.py"}}]},
            {"tool_calls":[{"function_name":"run_skill_script","arguments":{"skill_name":"repair-witness","file_path":"scripts/witness.py","args":{"phase":"after"}}}]},
            {"tool_calls":[{"function_name":"edit_file","arguments":{"filepath":"source.py"}}]},
            {"tool_calls":[{"function_name":"submit_patch","arguments":{}}]},
        ]}

    def test_records_must_be_exact_and_paired(self):
        d=self._records()
        self.assertEqual(len(validate(d)),6)
        d["results"][0]["instance_id"]="fastapi_999"
        with self.assertRaises(ValueError):validate(d)

    def test_skill_sequence_means_invocation_not_correctness(self):
        stats=summarize_trace(self._trace())
        self.assertEqual(stats["witness_before_calls"],1)
        self.assertEqual(stats["witness_after_calls"],1)
        self.assertTrue(stats["has_before_edit_after_sequence"])
        self.assertTrue(stats["observed_reedit_after_after_check"])
        self.assertEqual(stats["submit_patch_calls"],1)

    def test_missing_trace_unknown_and_stats_scored_by_grader(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/"paired_prompt_v2_31b_results.json").write_text(json.dumps(self._records()))
            folder=root/"paired-prompt-private-results"/"v3r-skill"
            folder.mkdir(parents=True)
            (folder/"trace_fastapi_101.json").write_text(json.dumps(self._trace()))
            self.assertIsNotNone(trace_path(root,"v3r_5min","fastapi_101"))
            self.assertIsNone(trace_path(root,"v2_5min","fastapi_101"))
            out=audit(root)
            self.assertEqual((out["rescues"],out["regressions"],out["net"]),(1,0,1))
            self.assertFalse(out["actual_skill_uptake_evidence_complete"])
            self.assertEqual(out["by_arm"]["v3r_5min"]["traces_found"],1)
            self.assertEqual(out["by_arm"]["v2_5min"]["traces_found"],0)

    def test_unknown_skill_args_never_count_as_witness(self):
        tr={"steps":[{"tool_calls":[{"function_name":"run_skill_script","arguments":{
            "skill_name":"other","file_path":"scripts/witness.py","args":{"phase":"before"}}}]}]}
        stats=summarize_trace(tr)
        self.assertEqual(stats["witness_before_calls"],0)
        self.assertEqual(stats["unrecognized_skill_script_calls"],1)


if __name__=="__main__":
    unittest.main()
