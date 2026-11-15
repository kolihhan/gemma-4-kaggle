import unittest
from scripts.gemma_pro_mechanism_existing_traces import summarize

class MechanismAuditTests(unittest.TestCase):
    def make(self):
        out=[]
        for issue in ["fastapi_14487","rich_3782","requests_7427"]:
            for arm in ["v2_5min","public_prompt_5min"]:
                out.append({"arm":arm,"instance_id":issue,"resolved":False,
                            "trace_found":True,"total_edit_actions":1,
                            "explicit_or_inline_tests":1,
                            "recorded_action_count":12,"first_edit_action":4,
                            "tests_after_first_edit":1,"tests_with_structured_exit":{"nonzero":1},
                            "nonzero_test_then_edit":0,"nonzero_commands_after_last_edit":1,
                            "unclassified_opaque_commands":0})
        return {"tasks":out}
    def test_mechanism_specific_observables(self):
        data=self.make()
        x=summarize(data)
        self.assertEqual(x["paired_resolved_difference"],0)
        self.assertFalse(x["independent_holdout"])
        self.assertEqual(x["by_arm"]["v2_5min"]["failed_test_without_observed_reedit"],3)
        self.assertEqual(x["by_arm"]["public_prompt_5min"]["ever_edited"],3)
        self.assertEqual(x["by_arm"]["public_prompt_5min"]["late_first_edit_over_half_actions"],0)
    def test_missing_trace_is_unknown_not_no_edit(self):
        data=self.make()
        data["tasks"][0]={"arm":"v2_5min","instance_id":"fastapi_14487",
                          "resolved":False,"trace_found":False}
        x=summarize(data)
        self.assertEqual(x["by_arm"]["v2_5min"]["incomplete_or_missing_traces"],1)
        self.assertEqual(x["by_arm"]["v2_5min"]["no_edit"],0)
    def test_denominator_pairing_failclosed(self):
        data=self.make()
        with self.assertRaises(ValueError):summarize({"tasks":data["tasks"][:5]})
        data["tasks"][0]["instance_id"]="unknown"
        with self.assertRaises(ValueError):summarize(data)

if __name__=="__main__":
    unittest.main()
