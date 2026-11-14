"""Synthetic freeze checks: exact 24-record source window, no cherry-picking."""
from unittest.mock import patch
import unittest
from scripts.freeze_scale_swe_wave3 import collect_wave3,OFFSETS

def source(i:int,success:bool)->dict:
    return {"row":{
      "resolved":int(success),"repo":f"author/repo{i}","language":"python",
      "license":"MIT","trajectory_id":f"trajectory{i}","instance_id":f"issue_{i}",
      "hf_dataset_name":"AweAI-Team/Scale-SWE",
      "metadata":{"model_patch":{"patch":f"diff --git a/a{i}.py b/a{i}.py\n+change"}},
      "messages":[{"role":"user"},{"role":"assistant"},{"role":"tool"}]
    }}

class Wave3Tests(unittest.TestCase):
    def test_first_twelve_eligible_in_24_exact_rows(self):
        records=[source(i,i%3!=0) for i in range(24)]
        def fake(offset):
            self.assertIn(offset,OFFSETS)
            start=offset-30
            return records[start:start+6]
        with patch("scripts.freeze_scale_swe_wave3.page",side_effect=fake):
            rows=collect_wave3()
        self.assertEqual(len(rows),12)
        self.assertEqual(list(rows),[f"issue_{i}" for i in
                         (1,2,4,5,7,8,10,11,13,14,16,17)])
    def test_no_unregistered_offset_or_fewer_than_twelve(self):
        with patch("scripts.freeze_scale_swe_wave3.page",
                   side_effect=lambda o:[source(o+i,i==1) for i in range(6)]):
            with self.assertRaisesRegex(ValueError,"not enough"):
                collect_wave3()

if __name__=="__main__":
    unittest.main()
