"""Synthetic frozen new-source selection, no dataset text or private training."""
import unittest
from unittest.mock import patch
from scripts.freeze_next_scale_swe_cohort import collect_new_cohort

def sample(idx:int,passed:bool=True)->dict:
    return {"row":{
        "instance_id":f"owner_{idx}_case","resolved":int(passed),
        "hf_dataset_name":"AweAI-Team/Scale-SWE",
        "repo":f"owner/proj{idx}","license":"MIT","language":"python",
        "trajectory_id":f"task_{idx}",
        "metadata":{"model_patch":{"patch":f"diff --git a/a{idx}.py b/a{idx}.py\n+fix"}},
        "messages":[{"role":"assistant"},{"role":"tool"},{"role":"user"}]
    }}

class CohortContractTests(unittest.TestCase):
    def test_fixed_eight_positive_and_original_source_order(self):
        source=[sample(i,i%3!=0) for i in range(12)]
        # Exactly eight successes among twelve (i 0,3,6,9 not selected).
        def mock(path,args):
            self.assertEqual(path,"/rows")
            self.assertIn(args["offset"],[18,24])
            lo=0 if args["offset"]==18 else 6
            return {"rows":source[lo:lo+6]}
        with patch("scripts.freeze_next_scale_swe_cohort.get_json",side_effect=mock):
            result=collect_new_cohort()
        self.assertEqual(len(result),8)
        self.assertEqual(list(result),[f"owner_{i}_case" for i in (1,2,4,5,7,8,10,11)])
    def test_changed_denominator_must_fail_not_replace_tasks(self):
        source=[sample(i,True) for i in range(12)]
        with patch("scripts.freeze_next_scale_swe_cohort.get_json",
                   side_effect=[{"rows":source[:6]},{"rows":source[6:]}]):
            with self.assertRaisesRegex(ValueError,"exactly eight"):
                collect_new_cohort()

if __name__=="__main__":
    unittest.main()
