"""Tests for safe, conservative analysis of previously completed 31B patch attempts."""
import json
import unittest

from scripts.audit_requirements_coverage_private_20261126 import (
    patch_evidence,
    spec_evidence,
    summarize_cohort,
)

def diff(path, line=10):
    return ("--- a/" + path + "\n"
            + "+++ b/" + path + "\n"
            + "@@ -" + str(line) + ",1 +" + str(line) + ",1 @@\n"
            + "-old\n+new\n")

class CoverageResearchTests(unittest.TestCase):
    def test_partial_reference_scope_not_semantic_proof(self):
        row = patch_evidence(diff("rich/a.py")+diff("rich/b.py"),
                             diff("rich/a.py", 11))
        self.assertEqual(row["scope_label"], "partial_reference_source_overlap")
        self.assertEqual(row["reference_source_file_count"], 2)
        self.assertEqual(row["candidate_source_file_count"], 1)
        self.assertEqual(row["near_reference_hunk"], True)
        self.assertIsNone(row["explicit_requirement_omitted"])

    def test_wrong_source_scope_stays_suspect(self):
        row = patch_evidence(diff("pkg/a.py"), diff("pkg/z.py"))
        self.assertEqual(row["scope_label"], "no_reference_source_overlap")
        self.assertIsNone(row["explicit_requirement_omitted"])

    def test_missing_patch_not_equated_to_empty(self):
        row = patch_evidence(diff("pkg/a.py"), None)
        self.assertEqual(row["scope_label"], "patch_artifact_unavailable")
        self.assertIsNone(row["explicit_requirement_omitted"])

    def test_short_external_spec_risk_only(self):
        row = spec_evidence("Fix issue https://github.com/example/repo/issues/11")
        self.assertTrue(row["short_external_reference_risk"])
        self.assertIsNone(row["specification_sufficient"])

    def test_sanitized_aggregate_preserves_unknowns(self):
        ids = ["fastapi_101","fastapi_102","rich_103",
               "rich_104","requests_105","requests_106"]
        tasks = {i: {"instance_id":i,"patch":diff("internal/secret_patch.py"),
                      "problem_statement":"Fix https://example.org/issue and edge behavior"}
                 for i in ids}
        rows = []
        patches = {}
        for tid in ids:
            for arm in ["fastpath_4min","single_edit_4min"]:
                rows.append({"instance_id":tid,"arm":arm,"resolved":False,
                             "has_patch":True,"tool_calls":22,
                             "duration_seconds":145.2})
                patches[(tid,arm)] = diff("internal/secret_patch.py")
        result = summarize_cohort({"status":"completed","results":rows},
                                  tasks,patches)
        self.assertEqual(result["unique_tasks"], 6)
        self.assertEqual(result["scored_evaluations"], 12)
        self.assertEqual(result["arms"]["fastpath_4min"]["recovered_patch"], 6)
        self.assertIsNone(result["confirmed_explicit_requirement_omissions"])
        self.assertFalse(result["agent_improvement_demonstrated"])
        self.assertEqual(result["gold_noop_controls"], "UNVERIFIED")
        serialized = json.dumps(result)
        for tid in ids:
            self.assertNotIn(tid, serialized)
        self.assertNotIn("internal/secret_patch.py", serialized)
        self.assertNotIn("https://example.org/issue", serialized)

    def test_duplicate_task_arm_rejected(self):
        ids = ["fastapi_101","fastapi_102","rich_103",
               "rich_104","requests_105","requests_106"]
        tasks = {i: {"instance_id":i,"patch":diff("pkg/a.py"),
                     "problem_statement":"Check foo"} for i in ids}
        rows = [{"instance_id":tid,"arm":arm,"resolved":False,"has_patch":False}
                for tid in ids for arm in ["fastpath_4min","single_edit_4min"]]
        rows[-1] = dict(rows[0])
        with self.assertRaises(ValueError):
            summarize_cohort({"status":"completed","results":rows},tasks,{})

if __name__ == "__main__":
    unittest.main()
