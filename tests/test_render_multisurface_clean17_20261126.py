"""Unit tests for strict 17-task matched real 31B score gate."""
import unittest
from unittest.mock import patch
from scripts.render_multisurface_clean17_20261126 import (
    VERSION, ARMS, MEMBERSHIP_SHA, assess,
)

IDS=["fastapi_"+str(1000+i) for i in range(9)]+[
    "rich_"+str(2000+i) for i in range(8)
]

def trial(control=(0,1,2,3), candidate=(0,1,2,3,4,5),
          slow=1.0, error=False):
    rows=[]
    for i,task in enumerate(IDS):
        for arm in ARMS:
            control_arm=arm==ARMS[0]
            result={"instance_id":task,"arm":arm,
                "resolved": i in (control if control_arm else candidate),
                "status":"error" if error and i==0 and not control_arm else "completed",
                "duration_seconds":100.0 if control_arm else 100.0*slow,
                "tool_calls":12 if control_arm else 12}
            rows.append(result)
    return {"version":VERSION,"status":"completed","results":rows}

class GateTests(unittest.TestCase):
    def review(self,data):
        with patch("scripts.render_multisurface_clean17_20261126.selection_hash",
                   return_value=MEMBERSHIP_SHA):
            return assess(data)

    def test_accepts_two_net_rescues_zero_regressions_at_equal_cost(self):
        r=self.review(trial())
        self.assertTrue(r["official_submit_eligible"])
        self.assertEqual(r["net_rescues_minus_regressions"],2)
        self.assertEqual(r["outcomes"]["candidate_only"],2)

    def test_does_not_promote_single_lucky_rescue(self):
        self.assertFalse(self.review(trial(candidate=(0,1,2,3,4)))["official_submit_eligible"])

    def test_does_not_promote_two_regressions_even_with_net_gain(self):
        self.assertFalse(self.review(
            trial(control=(0,1,2,3),candidate=(2,3,4,5,6,7)))["official_submit_eligible"])

    def test_rejects_slower_treatment(self):
        self.assertFalse(self.review(trial(slow=1.25))["official_submit_eligible"])

    def test_rejects_incomplete_or_scorer_exception(self):
        self.assertFalse(self.review(trial(error=True))["official_submit_eligible"])
        d=trial()
        d["results"].pop()
        with self.assertRaises(ValueError):self.review(d)

    def test_rejects_pair_duplication(self):
        d=trial()
        d["results"][0]=dict(d["results"][1])
        with self.assertRaises(ValueError):self.review(d)

if __name__=="__main__":
    unittest.main()
