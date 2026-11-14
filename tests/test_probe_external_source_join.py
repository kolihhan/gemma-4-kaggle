"""Mocked source join; tests never import real task text or patches."""
import unittest
from urllib.error import HTTPError
from unittest.mock import patch
from scripts.probe_external_source_join import filtered_join


def row(**kwargs):
    base={"instance_id":"example__repo-1","repo":"example/repo","license":"MIT"}
    base.update(kwargs)
    return base


def target(**kwargs):
    base={**row(),
          "base_commit":"a"*40,
          "FAIL_TO_PASS":["tests/test_fix.py::test_bug"],
          "test_patch":"diff --git a/test.py b/test.py\n+assert True",
          "problem_statement":"Fix issue",
          "image_name":"docker.io/synthetic-image:abc"}
    base.update(kwargs)
    return base


class SourceJoinTests(unittest.TestCase):
    def test_only_exact_id_repo_license_and_base_test_replay_prerequisites(self):
        with patch("scripts.probe_external_source_join.get_json",
                   return_value={"rows":[{"row":target()}]}) as call:
            self.assertEqual(filtered_join(row()), "source_context_found_replay_pending")
            params=call.call_args.args[1]
            self.assertEqual(params["where"], '"instance_id"=\'example__repo-1\'')
        for change,reason in [
            ({"instance_id":"someone__other-1"},"mismatched_instance_id"),
            ({"repo":"other/repo"},"mismatched_repository"),
            ({"license":"GPL"},"mismatched_license"),
            ({"base_commit":"invalid"},"missing_base_commit"),
            ({"FAIL_TO_PASS":[]},"missing_fail_to_pass"),
            ({"test_patch":""},"missing_test_patch"),
            ({"problem_statement":""},"missing_problem_statement"),
            ({"image_name":""},"missing_replay_image"),
        ]:
            with patch("scripts.probe_external_source_join.get_json",
                       return_value={"rows":[{"row":target(**change)}]}):
                self.assertEqual(filtered_join(row()),reason)

    def test_partial_or_failed_filter_cannot_claim_absence(self):
        for output,expected in [
            ({"partial":True,"rows":[{"row":target()}]},"partial_index_unreliable"),
            ({"rows":[]},"not_found_or_index_gap"),
            ({"rows":[{"row":target()},{"row":target()}]},"duplicate_source_match"),
        ]:
            with patch("scripts.probe_external_source_join.get_json",return_value=output):
                self.assertEqual(filtered_join(row()),expected)
        with patch("scripts.probe_external_source_join.get_json",
                   side_effect=HTTPError("https://example.invalid/",422,"unavailable",None,None)):
            self.assertEqual(filtered_join(row()),"filter_http_422")
        with patch("scripts.probe_external_source_join.get_json",side_effect=OSError):
            self.assertEqual(filtered_join(row()),"filter_unavailable")


if __name__=="__main__":
    unittest.main()
