"""Tests of the runner interface only; no claim about repair ability."""
import tempfile
import unittest
from pathlib import Path
from scripts.contrast_probe_runner_20261128 import run_pair


class TestRunner(unittest.TestCase):
    def test_contrast(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"w.py"
            p.write_text("import os,json\nv=json.loads(os.environ['CONTRAST_INPUT_JSON'])\nprint(v*0.5)\n")
            r=run_pair(p,45,"45",cwd=Path(d))
            self.assertTrue(r["different"])
            self.assertEqual(r["cases"][0]["stdout"].strip(),"22.5")
            self.assertNotEqual(r["cases"][1]["exit_code"],0)
    def test_equal(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"w.py";p.write_text("print('same')")
            self.assertFalse(run_pair(p,1,2,cwd=Path(d))["different"])
    def test_timeout(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"w.py";p.write_text("import time;time.sleep(2)")
            r=run_pair(p,1,2,cwd=Path(d),timeout=0.1)
            self.assertIsNone(r["different"])
    def test_truncation(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"w.py";p.write_text("print('x'*5000)")
            self.assertIsNone(run_pair(p,1,2,cwd=Path(d))["different"])
    def test_limit(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"w.py";p.write_text("pass")
            with self.assertRaises(ValueError):
                run_pair(p,1,2,cwd=Path(d),timeout=11)
            with self.assertRaises(ValueError):
                run_pair(p,"x"*5000,2,cwd=Path(d))
if __name__=="__main__":
    unittest.main()
