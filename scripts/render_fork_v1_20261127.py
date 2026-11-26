"""FORK V1 exploratory full-policy replacement, private paired scorer only."""
from __future__ import annotations
import argparse, json, hashlib
from pathlib import Path
from scripts import render_multisurface_clean17_20261126 as base
from scripts import render_edit_grammar_paired31b_20261124 as prior
from scripts.build_multisurface_scope_20261126 import files_for_pair
from scripts.build_behavioral_probe_timeout_safe_20261123 import _pack, CHAMPION_SHA256

KERNEL="kolihhan/gemma4-fork-v1-paired-20261127"
RUNTIME="fork31b_paired_runtime.py"
RESULT="paired_fork31b_results.json"
VERSION="fork-v1-clean17-paired"
PROMPT=Path("experiments/fork-v1-20261127/system.md")

def render(source:bytes, ids:list[str], out:Path):
    root=Path(".")
    report=base.render(root,source,ids,out)
    control,old=files_for_pair(source)
    new=dict(control)
    new["prompts/system.md"]=PROMPT.read_text()
    assert set(new)==set(control)
    assert new["prompts/system.md"]!=control["prompts/system.md"]
    assert hashlib.sha256(_pack(control)).hexdigest()==CHAMPION_SHA256
    assert {p for p in control if control[p]!=new[p]}=={"prompts/system.md"}
    oldpath=out/base.RUNTIME
    script=base.one(oldpath.read_text(),repr(prior.payload(old)),repr(prior.payload(new)))
    for a,b in ((base.VERSION,VERSION),(base.ARMS[1],"fork_5min"),(base.RESULT,RESULT),
                ("paired-multisurface-5min","paired-fork-5min"),
                ("paired-multisurface-private-results","paired-fork-private-results")):
        assert a in script
        script=script.replace(a,b)
    assert "competition_submit_code" not in script
    compile(script,RUNTIME,"exec")
    (out/RUNTIME).write_text(script)
    oldpath.unlink()
    meta=json.loads((out/"kernel-metadata.json").read_text())
    meta.update(id=KERNEL,title=KERNEL.split("/")[1],code_file=RUNTIME)
    assert meta["is_private"] and meta["enable_gpu"] and not meta["enable_internet"]
    (out/"kernel-metadata.json").write_text(json.dumps(meta,indent=2)+"\n")
    report.update(candidate_sha256=hashlib.sha256(_pack(new)).hexdigest(),
                  candidate="FORK V1 full solver policy replacement",
                  reused_dev_cohort=True, hard_host_controller=False)
    return report

def assess(data):
    assert data["version"]==VERSION
    # Reuse the existing strictly validated scorer and frozen-membership gate.
    d=dict(data,version=base.VERSION,results=[dict(r,arm=base.ARMS[1] if r["arm"]=="fork_5min" else r["arm"]) for r in data["results"]])
    result=base.assess(d)
    for k in ("resolved","sum_task_seconds","sum_tool_calls","error_evaluations"):
        result[k]["fork_5min"]=result[k].pop(base.ARMS[1])
    result.pop("official_submit_eligible",None)
    result["official_submission"]=False
    result["reused_dev_cohort"]=True
    return result

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--source",type=Path,required=True)
    ap.add_argument("--ids-json",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    print("FORK_RENDER="+json.dumps(render(a.source.read_bytes(),json.loads(a.ids_json.read_text()),a.out),sort_keys=True))
