import unittest
from scripts.join_scale_swe_parquet_eight import replay_fields

def source():
    return {"instance_id":"fakeowner_fakerepo_pr99","repo":"fakeowner/fakerepo",
            "license":"MIT"}

def result():
    return {"instance_id":"fakeowner_fakerepo_pr99","user":"fakeowner","repo":"fakerepo",
            "parent_commit":"b"*40,"pr_commit":"a"*40,
            "problem_statement":"short synthetic task","image_url":"docker.example/foo",
            "f2p_patch":"diff --git a/test.py b/test.py","f2p_script":"",
            "FAIL_TO_PASS":'["test_one"]'}

class ScaleParquetJoinTests(unittest.TestCase):
    def test_exact_provenance_without_gold_patch(self):
        self.assertEqual(replay_fields(result(),source()),
                         "source_parent_sha_and_test_inputs_joined_NOT_REPLAYED")
        for diff,reason in [
            ({"instance_id":"other"},"instance_id_mismatch"),
            ({"user":"other"},"source_repository_mismatch"),
            ({"parent_commit":"bad"},"parent_commit_invalid"),
            ({"pr_commit":None},"fixing_commit_invalid"),
            ({"image_url":""},"replay_image_missing"),
            ({"f2p_patch":"","f2p_script":""},"reproduction_script_missing"),
            ({"FAIL_TO_PASS":"bad json"},"fail_to_pass_invalid_json"),
            ({"FAIL_TO_PASS":"[]"},"fail_to_pass_unavailable")]:
            self.assertEqual(replay_fields({**result(),**diff},source()),reason)

if __name__=="__main__":
    unittest.main()
