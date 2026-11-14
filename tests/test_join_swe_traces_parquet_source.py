"""Pure tests for source parquet join; no source rows exposed."""
from __future__ import annotations

from types import SimpleNamespace
import unittest
from scripts.join_swe_traces_parquet_source import may_contain, verify_replay_metadata


def source():
    return {"instance_id":"example__repo__issue-1",
            "repo":"example/repo","license":"mit"}


def record():
    return {**source(), "license":"MIT", "base_commit":"a"*40,
            "FAIL_TO_PASS":["tests/test_example.py::test_case"],
            "test_patch":"diff --git a/tests/test_example.py b/tests/test_example.py",
            "image_name":"some.registry/opaque",
            "problem_statement":"Opaque task text"}


class ParquetJoinTests(unittest.TestCase):
    def test_full_provenance_and_no_spurious_approval(self):
        self.assertEqual(verify_replay_metadata(record(),source()),
                         "matched_replay_metadata_not_executed")
        for key,value,reason in [
            ("instance_id","other","id_mismatch"),
            ("repo","other/repo","repo_mismatch"),
            ("license","GPL-3.0","license_mismatch"),
            ("base_commit","deadbeef","missing_base_commit"),
            ("FAIL_TO_PASS",[],"missing_fail_to_pass"),
            ("test_patch","","missing_test_patch"),
            ("problem_statement","","missing_problem_statement"),
            ("image_name","","missing_image"),
        ]:
            row={**record(),key:value}
            self.assertEqual(verify_replay_metadata(row,source()), reason)

    def test_row_group_stats_conservative_and_exact(self):
        targets={"example_100","repo_8"}
        self.assertTrue(may_contain(None,targets))
        self.assertTrue(may_contain(SimpleNamespace(has_min_max=False), targets))
        self.assertFalse(may_contain(SimpleNamespace(has_min_max=True,
                         min="z",max="zz"),targets))
        self.assertTrue(may_contain(SimpleNamespace(has_min_max=True,
                        min="example_099",max="example_101"),targets))
        self.assertTrue(may_contain(SimpleNamespace(has_min_max=True,
                        min=b"repo_0",max=b"repo_9"),targets))
        self.assertTrue(may_contain(SimpleNamespace(has_min_max=True,
                        min="zz",max="aa"),targets))


if __name__=="__main__":
    unittest.main()
