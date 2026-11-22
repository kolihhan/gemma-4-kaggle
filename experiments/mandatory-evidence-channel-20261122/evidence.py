"""Bounded evidence channel for Gemma 4 SWE agent.

Tool-input-controlled subprocess choices. No shell interpolation, network or
reference patches. Exposes live source hits, focused pytest, and git diff
checks. No claimed hidden correctness: execution feedback is factual only.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import time

ROOT = Path("/workspace")
MAXOUT = 5500
STOP = {"docs","examples","benchmarks","build","dist",".git","__pycache__",
        ".venv","venv","node_modules","site-packages"}
ALLOWED = {"locate","test","diff","status"}


def relpath(value: str, *, need_file: bool=False)->str:
    if not isinstance(value,str) or not value or len(value)>200 or "\\" in value:
        raise ValueError("invalid path")
    p=PurePosixPath(value)
    if p.is_absolute() or any(i in {".",".."} for i in p.parts):
        raise ValueError("path traversal or absolute path")
    full=(ROOT / p.as_posix()).resolve()
    if not full.is_relative_to(ROOT.resolve()):
        raise ValueError("symlink escapes workspace")
    if need_file and not full.is_file():
        raise ValueError("selected test file does not exist")
    return p.as_posix()


def cmd(args:list[str], timeout:int)->dict:
    t=time.monotonic()
    try:
        p=subprocess.run(args,cwd=ROOT,text=True,capture_output=True,
                         timeout=timeout,check=False)
    except subprocess.TimeoutExpired:
        return {"status":"timeout","exit_code":None,
                "duration_s":round(time.monotonic()-t,2)}
    except OSError as exc:
        return {"status":"environment_error","error_type":type(exc).__name__}
    return {"status":"ok" if p.returncode==0 else "nonzero",
            "exit_code":p.returncode,
            "stdout":p.stdout[-MAXOUT:],"stderr":p.stderr[-1000:],
            "duration_s":round(time.monotonic()-t,2)}


def locate(query:str)->dict:
    if not isinstance(query,str) or len(query)<3 or len(query)>100:
        raise ValueError("query must be 3..100 chars")
    if not re.fullmatch(r"[\w .:/-]+",query,re.ASCII):
        raise ValueError("query restricted to code identifiers and path tokens")
    tokens=set(re.findall(r"[a-z][a-z0-9_]{2,}",query.lower()))
    if not tokens:raise ValueError("query has no meaningful identifier")
    # Try Git tracked source; no arbitrary shell, bounded output. A source
    # regex hit is NOT proof of causation and unseen/ignored files may exist.
    hits={}
    for term in sorted(tokens,key=len,reverse=True)[:4]:
        res=cmd(["git","grep","-n","-I","-i","-F","--",term],timeout=5)
        for line in res.get("stdout","").splitlines():
            m=re.match(r"([^:]+):(\d+):(.*)",line)
            if not m:continue
            path,lineno,frag=m.groups()
            try: safe=relpath(path)
            except ValueError:continue
            suffix=Path(safe).suffix
            parts=set(Path(safe).parts)
            if (suffix not in {".py",".js",".ts",".tsx",".go",".rs",".java"} or
                any(p in STOP or p.startswith(".") for p in parts) or
                Path(safe).name.startswith("test_") or
                "/tests/" in f"/{safe}/"):
                continue
            score=(5 if term in Path(safe).stem.lower() else 0)+(
                2 if term in frag.lower() else 0)
            key=(safe,int(lineno))
            prior=hits.get(key)
            if prior is None or prior["score"]<score:
                hits[key]={"path":safe,"line":int(lineno),
                           "score":score,"evidence":frag.strip()[:180]}
    found=sorted(hits.values(),key=lambda x:(-x["score"],x["path"],x["line"]))[:9]
    return {"mode":"locate","query":query,"matches":found,
            "coverage":"tracked searchable source lines only; top 9; no-hit is not absence",
            "next":"read_file around top source candidates; compare behavior with issue"
                   if found else "try narrower or related identifier; no-match not proof"}


def test(path:str, selector:str="")->dict:
    name=relpath(path,need_file=True)
    if selector and (not isinstance(selector,str) or
                     not re.fullmatch(r"(?:::[A-Za-z_][A-Za-z_0-9]*){1,4}",selector)):
        raise ValueError("invalid pytest selector")
    if not name.endswith(".py"):
        raise ValueError("focused pytest needs a Python test file")
    # Strict bounded test path; pytest can write its cache files, not source.
    out=cmd(["python","-m","pytest",name+selector,"-q",
             "--disable-warnings","--maxfail=1","-p","no:cacheprovider"],timeout=75)
    return {"mode":"test","path":name,"selector":selector,**out,
            "interpretation":"exit 0 means selected checks passed, not hidden grader PASS"}


def diff()->dict:
    result=cmd(["git","diff","--check"],timeout=6)
    stat=cmd(["git","diff","--stat"],timeout=6)
    return {"mode":"diff","check":result,
            "stat":stat,
            "note":"inspect actual changed lines with read_file; no hidden correctness asserted"}


def status()->dict:
    return {"mode":"status","result":cmd(["git","status","--short"],timeout=6)}


def run(request:dict)->dict:
    if not ROOT.is_dir() or not (ROOT/".git").exists():
        raise RuntimeError("workspace must be Git checkout")
    if not isinstance(request,dict) or request.get("mode") not in ALLOWED:
        raise ValueError("mode must be locate|test|diff|status")
    if request["mode"]=="locate":
        return locate(request.get("query"))
    if request["mode"]=="test":
        return test(request.get("path"),request.get("selector",""))
    if request["mode"]=="diff":
        return diff()
    return status()


def main()->None:
    p=argparse.ArgumentParser()
    p.add_argument("--request",required=True)
    p.add_argument("--workspace",default="/workspace")
    args=p.parse_args()
    if Path(args.workspace).resolve()!=ROOT.resolve():
        raise ValueError("must stay in /workspace")
    try:
        result=run(json.loads(args.request))
        print(json.dumps(result,sort_keys=True))
    except Exception as e:
        # Explicit errors, no hidden grader info.
        print(json.dumps({"status":"error","type":type(e).__name__,
                          "message":str(e)[:250]}))


if __name__=="__main__":
    main()
