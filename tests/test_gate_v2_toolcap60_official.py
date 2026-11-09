"""Tests for the pre-submission evidence gate: no Kaggle interaction."""
import unittest
from scripts.gate_v2_toolcap60_official import assess, VERSION, MODEL

IDS = ["fastapi_1000","fastapi_1001","rich_1000","rich_1001"]
MANIFEST = {"version": VERSION, "arms": ["baseline_v2_28","v2_60_calls"],
            "exclusions": ["old_1"]}


def candidate(base_correct=0, alt_correct=1, extra_calls=True, slow=False):
    records = []
    for idx, id_ in enumerate(IDS):
        records.append({
            "instance_id": id_, "arm": "baseline_v2_28",
            "status": "completed", "resolved": idx < base_correct,
            "duration_seconds": 300.0, "tool_calls": 28,
        })
        records.append({
            "instance_id": id_, "arm": "v2_60_calls",
            "status": "completed", "resolved": idx < alt_correct,
            "duration_seconds": 420.0 if slow else 290.0,
            "tool_calls": 42 if extra_calls else 28,
        })
    return {
        "version": VERSION, "status": "completed", "model": MODEL,
        "instance_ids": IDS, "records": records,
    }


class OfficialGateTests(unittest.TestCase):
    def test_rescue_plus_more_calls_can_qualify_exploratory_submission(self):
        result=assess(candidate(),MANIFEST)
        self.assertEqual(result["status"],"ELIGIBLE_EXPLORATORY_SUBMISSION")
        self.assertFalse(result["proven_stronger"])

    def test_equal_score_without_exercising_tool_cap_is_not_novel(self):
        result=assess(candidate(0,0,False),MANIFEST)
        self.assertEqual(result["status"],"BLOCKED_NO_ADDED_VALUE")

    def test_regression_blocks_submit_even_if_more_calls(self):
        result=assess(candidate(2,1),MANIFEST)
        self.assertEqual(result["status"],"BLOCKED_NO_ADDED_VALUE")

    def test_no_gain_with_additional_calls_allows_independent_score_check(self):
        result=assess(candidate(0,0,True),MANIFEST)
        self.assertEqual(result["status"],"ELIGIBLE_EXPLORATORY_SUBMISSION")

    def test_uncontrolled_wall_time_blocks(self):
        result=assess(candidate(0,1,True,True),MANIFEST)
        self.assertEqual(result["status"],"BLOCKED_NO_ADDED_VALUE")

    def test_denominator_drift_blocks(self):
        c=candidate()
        c["records"].pop()
        with self.assertRaisesRegex(ValueError,"evaluation row count"):
            assess(c,MANIFEST)

    def test_prior_exposure_reuse_blocks(self):
        with self.assertRaisesRegex(ValueError,"previously inspected"):
            assess(candidate(),{**MANIFEST,"exclusions":[IDS[0]]})


if __name__=="__main__":
    unittest.main()
