"""Build one PRIVATE CPU-only visible-test replay kernel from real retained traces.
No raw artifacts in Git or public logs. Never replay arbitrary agent shell.
"""
from __future__ import annotations
import argparse,json,re,hashlib
from pathlib import Path
from collections import Counter,defaultdict
from scripts.audit_four_arm_evidence_20261127 import commands,load
from scripts.render_fork_v1_20261127 import assess as af,RESULT as F
from scripts.render_multisurface_clean17_20261126 import assess as am,RESULT as M

SLUG="kolihhan/gemma4-visible-witness-replay-20261127-v2"
TARGET=re.compile(r"(?:tests?/)?(?:[A-Za-z0-9_]+/)*(?:test_[A-Za-z0-9_]+|[A-Za-z0-9_]+_test)\.py(?:::[A-Za-z0-9_]+){0,2}")
FLAGS={"-q","-v","-vv","-x","-s","--tb=short","--tb=long","--disable-warnings","--maxfail=1","--maxfail=2"}
def targets(cmd):
    out=set()
    for seg in commands(cmd):
        if not seg:continue
        exe=seg[0].rsplit("/",1)[-1]
        if exe in ("python","python3") and seg[1:3]==["-m","pytest"]:args=seg[3:]
        elif exe in ("pytest","py.test"):args=seg[1:]
        else:continue
        args=[x for x in args if x not in FLAGS]
        if len(args)!=1:continue
        p=args[0].removeprefix("/workspace/").removeprefix("./")
        if TARGET.fullmatch(p) and ".." not in Path(p.split("::")[0]).parts:out.add(p)
    return out

def prepare(fork,prior,out):
    groups=defaultdict(dict); requests=defaultdict(Counter); patches=defaultdict(dict)
    for name,root,filename,assess,arms,folder in (
        ("F",fork,F,af,("champion_5min","fork_5min"),"paired-fork-private-results"),
        ("M",prior,M,am,("champion_5min","multisurface_5min"),"paired-multisurface-private-results")):
        rows=load(root,filename,assess)
        for (tid,arm),r in rows.items():
            key=name+str(arms.index(arm))
            groups[tid][key]=r["resolved"]
            p=root/folder/"private-final-patches"/arm/(tid+".patch")
            raw=p.read_text() if p.is_file() else ""
            if len(raw)!=r["patch_chars"] or bool(raw.strip())!=r["has_patch"]:raise ValueError("patch length mismatch")
            patches[tid][key]=raw
        seen=set()
        for p in root.rglob("trace_*.json"):
            tid=p.stem.removeprefix("trace_")
            arm=arms[int("public-prompt" in p.relative_to(root).parts)]
            if (tid,arm) not in rows:continue
            key=(tid,arm)
            if key in seen:raise ValueError("ambiguous trace")
            seen.add(key)
            found=set()
            for step in json.loads(p.read_text())["steps"]:
                for c in step.get("tool_calls") or []:
                    a=c.get("arguments")
                    if c.get("function_name")=="run_command" and isinstance(a,dict):
                        found.update(targets(a.get("command")))
            requests[tid].update(found)
        if len(seen)!=len(rows):raise ValueError("trace missing")
    assert len(groups)==17 and all(len(v)==4 for v in groups.values())
    # Use the most frequently requested safe target; prefer node over entire file
    # only on ties; no gold/test labels in target choice.
    eligible=defaultdict(list)
    for tid,v in groups.items():
        if not requests[tid]:continue
        n=sum(v.values());g="always_fail" if n==0 else "always_pass" if n==4 else "mixed"
        target=sorted(requests[tid],key=lambda p:(-requests[tid][p],-p.count("::"),p))[0]
        eligible[g].append((tid,target))
    cases=[]
    # All eligible stable failures up to 5; at most two from each contrast group.
    for g,limit in (("always_fail",5),("mixed",2),("always_pass",2)):
        ranked=sorted(eligible[g],key=lambda x:hashlib.sha256(("visible-witness-replay-v1|"+x[0]).encode()).hexdigest())
        for tid,target in ranked[:limit]:
            cases.append({"id":tid,"group":g,"target":target,"patches":patches[tid],"original_resolved":groups[tid]})
    print("VISIBLE_REPLAY_TARGET_CENSUS="+json.dumps({"eligible":{g:len(eligible[g]) for g in ("always_fail","mixed","always_pass")},"selected":dict(Counter(c["group"] for c in cases)),"n":len(cases)},sort_keys=True),flush=True)
    if not any(c["group"]=="always_fail" for c in cases):
        return False
    source=Path("kaggle/gold_control_sweep.py").read_text().split('if __name__ == "__main__":',1)[0]
    runtime=Path("kaggle/visible_witness_replay_v2_20261127.py").read_text()
    source+="\n"+runtime.replace("__PRIVATE_PAYLOAD__",repr(json.dumps(cases,separators=(",",":"))))
    compile(source,"main.py","exec")
    import dataclasses
    ns={"dataclasses":dataclasses,"json":json}
    # Exercise the actual clone code against a schema with derived aliases.
    helper=runtime.split("def field_names(",1)[1].split("async def replay(",1)[0]
    exec("def field_names("+helper,ns)
    @dataclasses.dataclass
    class TaskFixture:
        test_patch:str="private"
        fail_to_pass:tuple=("old",)
        pass_to_pass:tuple=("old",)
        patch:str="private"
        @property
        def FAIL_TO_PASS(self):return self.fail_to_pass
        @property
        def PASS_TO_PASS(self):return self.pass_to_pass
        @property
        def test_files(self):return [x.split("::")[0] for x in self.fail_to_pass]
    old=TaskFixture();new=ns["visible_task"](old,"tests/test_x.py::test_y")
    assert old.test_patch=="private" and new.test_patch=="" and new.FAIL_TO_PASS==("tests/test_x.py::test_y",)
    print("VISIBLE_SCHEMA_CLONE_FIXTURE=PASS",flush=True)
    out.mkdir(parents=True,exist_ok=False)
    (out/"main.py").write_text(source)
    meta={"id":SLUG,"title":SLUG.split("/")[1],"code_file":"main.py","language":"python","kernel_type":"script","is_private":True,"enable_gpu":False,"enable_tpu":False,"enable_internet":False,"docker_image":"gcr.io/kaggle-private-byod/python@sha256:37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461","competition_sources":["gemma-4-developer-agent"],"dataset_sources":["metric/gemma-4-developer-agent-wheelhouse"],"model_sources":[],"kernel_sources":[]}
    (out/"kernel-metadata.json").write_text(json.dumps(meta))
    return True

def smoke():
    assert targets("timeout 15s python -m pytest tests/test_x.py::test_y -q")=={"tests/test_x.py::test_y"}
    assert not targets("pytest -q")
    assert not targets("pytest tests/test_x.py -k 'foo'")
    assert not targets("pytest ../../tests/test_x.py")
    assert not targets("pytest tests/test_x.py tests/test_y.py")
if __name__=="__main__":
    smoke()
    p=argparse.ArgumentParser();p.add_argument("--fork",type=Path,required=True);p.add_argument("--prior",type=Path,required=True);p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();prepare(a.fork,a.prior,a.out)
