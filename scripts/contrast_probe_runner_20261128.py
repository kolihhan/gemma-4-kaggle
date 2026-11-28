"""CPU research prototype: execute an issue-derived contrast in two fresh processes.

Not a submission skill. Caller supplies a trusted, reviewed Python witness and
two JSON inputs, not gold or hidden tests. Run only in an existing isolated
offline sandbox. This module is not a security sandbox or correctness oracle.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

MAX_INPUT = 4096
MAX_OUTPUT = 4096
MAX_SECONDS = 10


def run_pair(script: Path, a, b, *, cwd: Path, timeout=MAX_SECONDS):
    if not 0 < timeout <= MAX_SECONDS:
        raise ValueError("timeout outside bounded range")
    script = script.resolve(strict=True)
    if not script.is_file() or script.stat().st_size > 32768:
        raise ValueError("invalid witness script")
    records = []
    start = time.monotonic()
    for label, value in (("A", a), ("B", b)):
        encoded = json.dumps(value, allow_nan=False, sort_keys=True)
        if len(encoded.encode()) > MAX_INPUT:
            raise ValueError("input too large")
        remaining = timeout - (time.monotonic() - start)
        if remaining <= 0:
            records.append({"case":label,"status":"TIMEOUT"})
            continue
        with tempfile.TemporaryDirectory(prefix="contrast-") as tmp:
            # Standard subprocesses share the repository filesystem. Caller must
            # use disposable offline workspace; do not claim read-only enforcement.
            env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1",
                       CONTRAST_INPUT_JSON=encoded, TMPDIR=tmp)
            out = Path(tmp)/"stdout"
            err = Path(tmp)/"stderr"
            try:
                with out.open("wb") as o, err.open("wb") as e:
                    p = subprocess.run([sys.executable,str(script)], cwd=cwd,
                        env=env, stdout=o, stderr=e, timeout=remaining)
                def bounded(path):
                    with path.open("rb") as f:
                        raw = f.read(MAX_OUTPUT+1)
                    return raw[:MAX_OUTPUT].decode("utf-8","replace"),len(raw)>MAX_OUTPUT
                stdout, so = bounded(out)
                stderr, se = bounded(err)
                records.append({"case":label,"status":"EXIT","exit_code":p.returncode,
                                "stdout":stdout,"stderr":stderr,"truncated":so or se})
            except subprocess.TimeoutExpired:
                records.append({"case":label,"status":"TIMEOUT"})
    comparable = all(r["status"]=="EXIT" and not r["truncated"] for r in records)
    different = None
    if comparable:
        different = any(records[0][k]!=records[1][k] for k in ("exit_code","stdout","stderr"))
    return {"cases":records,"different":different,"elapsed_seconds":round(time.monotonic()-start,3),
            "interpretation":"observations only; different does not mean correct",
            "sandbox_required":True}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--script",type=Path,required=True)
    p.add_argument("--a",required=True)
    p.add_argument("--b",required=True)
    p.add_argument("--cwd",type=Path,default=Path.cwd())
    p.add_argument("--timeout",type=float,default=MAX_SECONDS)
    args=p.parse_args()
    print(json.dumps(run_pair(args.script,json.loads(args.a),json.loads(args.b),cwd=args.cwd,timeout=args.timeout),
                     sort_keys=True))


if __name__ == "__main__":
    main()
