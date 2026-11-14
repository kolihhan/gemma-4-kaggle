"""No remote data, no Docker; strict first-case F2P selector contract."""
import unittest
from scripts.replay_scale_swe_one_in_docker import workdir_sane, test_selectors

class DockerF2PContracts(unittest.TestCase):
    def test_task_workdir_safe(self):
        self.assertTrue(workdir_sane("/workspace/project"))
        for bad in ("/etc/project","/workspace/../secret","/workspace//a",
                    "workspace/a","/workspace/./a"):
            self.assertFalse(workdir_sane(bad))
    def test_f2p_test_selection_capped_and_no_shell(self):
        self.assertEqual(test_selectors({"f2p_script":"def test_it():\n assert True",
                          "FAIL_TO_PASS":'["tests/test_bug.py"]'}),["test_fail_to_pass.py"])
        self.assertEqual(test_selectors({"f2p_patch":"patch",
                          "FAIL_TO_PASS":'["tests/test_a.py::test_b", "tests/test_c.py"]'}),
                         ["tests/test_a.py::test_b","tests/test_c.py"])
        for bad in ('["../../secret.py"]','["tests/test.py;cat /etc/passwd"]',
                    '["tests/test.py", "tests/test_b.py", "tests/test_c.py", "tests/test_d.py"]'):
            got=test_selectors({"f2p_patch":"patch","FAIL_TO_PASS":bad})
            self.assertTrue(got==[] or len(got)<=3)
        self.assertEqual(test_selectors({"FAIL_TO_PASS":'["x"]'}),[])

if __name__=="__main__":
    unittest.main()
