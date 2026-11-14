import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from scripts.probe_external_join_search_two import search_one


class SearchAlternativeTests(unittest.TestCase):
    def test_positive_exact_case_needs_matching_source_and_tests(self):
        source={"instance_id":"example__repo-42","repo":"example/repo","license":"MIT"}
        row={**source,"base_commit":"a"*40,
             "FAIL_TO_PASS":["test_true"],"test_patch":"diff --git a/a b/a"}
        with patch("scripts.probe_external_join_search_two.get_json",
                   return_value={"partial":False,"rows":[{"row":row}]}):
            self.assertEqual(search_one(source),"exact_source_commit_and_tests_found_no_replay")
        with patch("scripts.probe_external_join_search_two.get_json",
                   return_value={"partial":True,"rows":[{"row":row}]}):
            self.assertEqual(search_one(source),"search_partial_index")
        with patch("scripts.probe_external_join_search_two.get_json",
                   side_effect=HTTPError("https://example.invalid",500,"broken",None,None)):
            self.assertEqual(search_one(source),"search_http_500")


if __name__=="__main__":
    unittest.main()
