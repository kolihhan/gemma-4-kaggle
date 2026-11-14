"""Pure source verifier tests; no real task contents committed."""
import unittest
from urllib.error import HTTPError
from unittest.mock import patch
from scripts.probe_scale_swe_two_join import verification, inspect_source

def source():
    return {"instance_id":"owner_project_pr123","repo":"owner/project","license":"MIT"}

def record():
    return {"instance_id":"owner_project_pr123","user":"owner","repo":"project",
            "parent_commit":"a"*40,"problem_statement":"Example",
            "image_url":"example.invalid/img","f2p_patch":"diff --git a/tests/test.py b/tests/test.py",
            "f2p_script":"","FAIL_TO_PASS":'["tests/test_bug.py::test_bug"]'}

class ScaleJoinTests(unittest.TestCase):
    def test_verified_match_and_fail_closed_replay_prerequisites(self):
        self.assertEqual(verification(record(),source()),
                         "source_commit_and_test_inputs_found_replay_pending")
        for change, expected in [
            ({"instance_id":"oops"},"source_id_mismatch"),
            ({"user":"different"},"source_repo_mismatch"),
            ({"parent_commit":"oops"},"missing_parent_commit"),
            ({"f2p_patch":"","f2p_script":""},"missing_reproduction_tests"),
            ({"FAIL_TO_PASS":"[bad"},"test_names_not_json"),
            ({"FAIL_TO_PASS":"[]"},"empty_test_names"),
        ]:
            self.assertEqual(verification({**record(),**change},source()),expected)
    def test_filters_are_exact_id_and_no_partial_index(self):
        with patch("scripts.probe_scale_swe_two_join.get_json",
                   return_value={"partial":False,"rows":[{"row":record()}]}) as mocked:
            self.assertEqual(inspect_source(source()),"source_commit_and_test_inputs_found_replay_pending")
            self.assertEqual(mocked.call_args.args[1]["where"],
                             '"instance_id"=\'owner_project_pr123\'')
        with patch("scripts.probe_scale_swe_two_join.get_json",
                   return_value={"partial":True,"rows":[{"row":record()}]}):
            self.assertEqual(inspect_source(source()),"source_filter_partial_index")
        with patch("scripts.probe_scale_swe_two_join.get_json",
                   side_effect=HTTPError("https://example.invalid",500,"bad",None,None)):
            self.assertEqual(inspect_source(source()),"filter_http_500")

if __name__=="__main__":
    unittest.main()
