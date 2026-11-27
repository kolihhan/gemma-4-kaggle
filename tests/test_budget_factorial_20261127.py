import unittest
from scripts.budget_factorial_20261127 import ARMS,arm_files,schedule,assess
from tests.test_build_toolcap60_timeout_recovery import V2

class TestBudgetFactorial(unittest.TestCase):
    def setUp(self):
        self.base=dict(V2)
        self.base["eval_config.yaml"]=self.base["eval_config.yaml"].replace("max_time_minutes: 8","max_time_minutes: 5").replace("max_tool_calls: 28","max_tool_calls: 60")
    def test_all_arms(self):
        a=arm_files(self.base)
        self.assertEqual(a["champion"],self.base)
        self.assertEqual(set(a),set(ARMS))
        for name,(c,b) in ARMS.items():
            self.assertIn("max_tool_calls: "+str(c),a[name]["eval_config.yaml"])
            self.assertIn("thinking_budget: "+str(b),a[name]["configs/sampling.yaml"])
            self.assertEqual(a[name]["prompts/system.md"],self.base["prompts/system.md"])
            self.assertEqual(a[name]["agent.yaml"],self.base["agent.yaml"])
    def test_duplicate_budget_rejected(self):
        self.base["configs/sampling.yaml"]+="thinking_budget: 4096\n"
        with self.assertRaises(ValueError):arm_files(self.base)
    def test_changed_time_rejected(self):
        self.base["eval_config.yaml"]=self.base["eval_config.yaml"].replace("max_time_minutes: 5","max_time_minutes: 4")
        with self.assertRaises(ValueError):arm_files(self.base)
    def test_schedule_balanced(self):
        ids=[str(i) for i in range(10)]
        s=schedule(ids)
        self.assertEqual(len(s),50)
        for j in range(5):
            self.assertEqual({a:sum(s[i][1]==a for i in range(j,len(s),5)) for a in ARMS},{a:2 for a in ARMS})
    def test_interaction(self):
        ids=["t1","t2","t3"]
        rows=[{"instance_id":t,"arm":a,"status":"completed","resolved":a=="D" and t!="t3","duration_seconds":100,"tool_calls":10} for t,a in schedule(ids)]
        x=assess(rows,ids)
        self.assertEqual(x["factorial_interaction"],2/3)
        self.assertEqual(x["paired"]["D"]["rescues"],2)
        self.assertTrue(x["paired"]["D"]["exploratory_gate"])
        self.assertFalse(x["automatic_promotion"])
        with self.assertRaises(ValueError):assess(rows[:-1],ids)
        with self.assertRaises(ValueError):assess(rows[:-1]+rows[:1],ids)
    def test_errors_fail_closed(self):
        ids=["t1"];rows=[{"instance_id":t,"arm":a,"status":"completed","resolved":False,"duration_seconds":100,"tool_calls":10} for t,a in schedule(ids)]
        rows[0]["status"]="error"
        with self.assertRaises(ValueError):assess(rows,ids)
