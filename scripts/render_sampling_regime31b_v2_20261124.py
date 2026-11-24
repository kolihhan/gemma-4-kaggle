"""Repair the pre-inference selection failure in sampling v1, not the agent.

No scores or reference patches are consulted. Keep both exact candidate
payloads; preserve all 65 prior exclusions. Satisfy original strata where
possible, fill any shortage deterministically from other unexposed public
development IDs. Freeze eight pairs or stop BEFORE starting vLLM.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from scripts import render_sampling_regime31b_20261124 as v1

KERNEL="kolihhan/gemma4-sampling-regime-paired-20261124-v2"
RESULT=v1.RESULT
VERSION="sampling-regime-31b-5min-paired-v2"

def select_ids(ids,excluded,counts,salt,n=8):
    pool=set(ids)-set(excluded)
    def rank(items):
        return sorted(items,key=lambda x:(hashlib.sha256((salt+"|"+x).encode()).hexdigest(),x))
    available={p:sum(i.startswith(p) for i in pool) for p in counts}
    print("SAMPLING_SELECTION_CAPACITY="+json.dumps({"strata":available,"total_remaining":len(pool),"target_pairs":n},sort_keys=True),flush=True)
    if len(pool)<n:
        raise ValueError("not enough untouched tasks overall; no model run")
    chosen=[]
    for p,count in counts.items():
        chosen.extend(rank(i for i in pool-set(chosen) if i.startswith(p))[:count])
    chosen.extend(rank(pool-set(chosen))[:n-len(chosen)])
    assert len(chosen)==n and len(set(chosen))==n and not set(chosen)&set(excluded)
    actual={p:sum(i.startswith(p) for i in chosen) for p in counts}
    print("SAMPLING_SELECTION_ACTUAL="+json.dumps({"strata":actual,"other":n-sum(actual.values()),"pairs":n},sort_keys=True),flush=True)
    return chosen

def render(repo,source,out,previous):
    report=v1.render(repo,source,out,previous)
    script=out/"sampling_regime_runtime.py"
    text=script.read_text()
    import inspect
    helper=inspect.getsource(select_ids)
    old='''    chosen = []
    for prefix, count in sel["counts_by_repo"].items():
        candidates = sorted(x for x in ids if x.startswith(prefix) and x not in excluded)
        if len(candidates) < count:
            raise ValueError("not enough untouched tasks in " + prefix)
        ranked = sorted(candidates, key=lambda item: (
            hashlib.sha256((sel["salt"] + "|" + item).encode()).hexdigest(), item))
        chosen.extend(ranked[:count])
'''
    new='''    chosen = select_ids(ids, excluded, sel["counts_by_repo"], sel["salt"], n=8)
'''
    assert text.count(old)==1
    text=text.replace(old,new,1).replace("def load_holdout_ids(public_tasks)",helper+"\n\ndef load_holdout_ids(public_tasks)",1)
    text=text.replace(v1.VERSION,VERSION)
    # Replace the manifest policy only. Candidate bytes and budgets unchanged.
    text=text.replace("ID-only selection; all previous recorded pilot IDs excluded","ID-only selection; all previous recorded pilot IDs excluded; target strata when possible, deterministic remaining public-development fill before model startup")
    compile(text,str(script),"exec")
    script.write_text(text)
    meta=json.loads((out/"kernel-metadata.json").read_text())
    meta.update(id=KERNEL,title=KERNEL.split("/")[1])
    (out/"kernel-metadata.json").write_text(json.dumps(meta,indent=2))
    assert report["control_sha256"]=="ff08c10240a38e151a2ea1d0478e999ee5d2f437d2dad5571d912cf12859922b"
    assert report["candidate_sha256"]=="6183b58d06209f5a2a0b399b57cfcaa766129ad3615d633ba2e2c9bc2b7fd50a"
    report.update(private_kernel=KERNEL,selection_fix_only=True,failed_v1_no_scored_trials=True)
    return report

def selftest():
    counts={"fastapi_":3,"rich_":3,"requests_":2}
    pool={"fastapi_"+str(i) for i in range(6)}|{"rich_"+str(i) for i in range(4)}|{"requests_0"}
    excluded={"fastapi_0","rich_0","requests_0"}
    selected=select_ids(pool,excluded,counts,"fixed-test-salt")
    assert len(selected)==8 and not set(selected)&excluded
    assert selected==select_ids(sorted(pool,reverse=True),excluded,counts,"fixed-test-salt")
    try:
        select_ids({"rich_0"},set(),counts,"fixed-test-salt")
    except ValueError:pass
    else:raise AssertionError("insufficient cohort must stop")
    print("SAMPLING_SELECTOR_FIXTURE_PASS",flush=True)

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--source",type=Path,required=True)
    a.add_argument("--out",type=Path,required=True)
    a.add_argument("--previous",type=Path,nargs=3,required=True)
    o=a.parse_args()
    selftest()
    print("SAMPLING_V2_CPU_PREFLIGHT="+json.dumps(render(Path("."),o.source.read_bytes(),o.out,o.previous),sort_keys=True),flush=True)

if __name__=="__main__":main()
