"""CPU check of the tracked-only checkpoint protocol; no task data or model."""
import subprocess, tempfile, unittest
from pathlib import Path

class ForkCheckpoint(unittest.TestCase):
    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/"repo"; root.mkdir()
            def run(*args):
                return subprocess.run(args,cwd=root,check=True,capture_output=True).stdout
            run("git","init","-q")
            run("git","config","user.name","CPU test")
            run("git","config","user.email","cpu@example.invalid")
            p=root/"source.py"; p.write_text("x = 0\n")
            run("git","add","source.py");run("git","commit","-qm","base")
            a=Path(tmp)/"a.patch"; b=Path(tmp)/"b.patch"
            p.write_text("x = 1\n");a.write_bytes(run("git","diff","--binary","HEAD"))
            p.write_text("x = 2\n");b.write_bytes(run("git","diff","--binary","HEAD"))
            run("git","apply","--reverse","--check",str(b))
            run("git","apply","--reverse",str(b))
            run("git","apply","--check",str(a));run("git","apply",str(a))
            self.assertEqual(p.read_text(),"x = 1\n")
            self.assertEqual(run("git","diff","--binary","HEAD"),a.read_bytes())
if __name__=="__main__":unittest.main()
