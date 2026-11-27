"""CPU-only exact-Champion factorial configuration builder and matched result assessor."""
from __future__ import annotations
import argparse, hashlib, io, json, math, re, zipfile
from pathlib import Path
from scripts.build_behavioral_probe_timeout_safe_20261123 import _source_files, _pack, CHAMPION_SHA256

ARMS={"champion":(60,4096),"A":(28,4096),"B":(60,2048),"C":(60,1024),"D":(28,2048)}
FILES={"agent.yaml","prompts/system.md","configs/sampling.yaml","eval_config.yaml"}

def change_number(text,key,old,new):
    pat=re.compile(r"(?m)^([ \t]*"+re.escape(key)+r":[ \t]*)"+str(old)+r"([ \t]*(?:#.*)?)$")
    if len(re.findall(r"(?m)^[ \t]*"+re.escape(key)+r"[ \t]*:",text))!=1 or len(pat.findall(text))!=1:
        raise ValueError("config key drift: "+key)
    return pat.sub(lambda m:m[1]+str(new)+m[2],text,count=1)

def arm_files(control):
    if set(control)!=FILES:raise ValueError("bundle membership drift")
    if control["agent.yaml"].count("model: gemma-4-31b-it-qat-w4a16-ct")!=1:raise ValueError("wrong model")
    change_number(control["eval_config.yaml"],"max_time_minutes",5,5)
    change_number(control["eval_config.yaml"],"max_turns",80,80)
    result={}
    for arm,(calls,thinking) in ARMS.items():
        x=dict(control)
        x["eval_config.yaml"]=change_number(x["eval_config.yaml"],"max_tool_calls",60,calls)
        x["configs/sampling.yaml"]=change_number(x["configs/sampling.yaml"],"thinking_budget",4096,thinking)
        assert change_number(x["eval_config.yaml"],"max_tool_calls",calls,60)==control["eval_config.yaml"]
        assert change_number(x["configs/sampling.yaml"],"thinking_budget",thinking,4096)==control["configs/sampling.yaml"]
        assert all(x[k]==control[k] for k in ("agent.yaml","prompts/system.md"))
        result[arm]=x
    return result

def build(source_zip,out):
    arms=arm_files(_source_files(source_zip))
    bundles={a:_pack(x) for a,x in arms.items()}
    assert hashlib.sha256(bundles["champion"]).hexdigest()==CHAMPION_SHA256
    out.mkdir(parents=True,exist_ok=False)
    hashes={}
    for arm,data in bundles.items():
        (out/(arm+".zip")).write_bytes(data)
        hashes[arm]=hashlib.sha256(data).hexdigest()
    report={"arms":ARMS,"bundle_sha256":hashes,"model":"gemma-4-31b-it-qat-w4a16-ct","time_minutes":5,"turns":80,"official_submission":False,"new_model_inference":False}
    (out/"manifest.json").write_text(json.dumps(report,indent=2,sort_keys=True))
    return report

def schedule(ids):
    # Five rotations and their reversals; use deterministic frozen task order.
    if not ids or len(ids)!=len(set(ids)) or any(not isinstance(t,str) or not t for t in ids):raise ValueError("bad frozen tasks")
    arms=list(ARMS)
    order=sorted(ids,key=lambda t:hashlib.sha256(("budget-factorial-v1|"+t).encode()).hexdigest())
    return [(tid,a) for i,tid in enumerate(order) for a in ((arms[i%5:]+arms[:i%5])[::-1] if i%10>=5 else (arms[i%5:]+arms[:i%5]))]

def assess(rows,ids):
    expected=set(schedule(ids))
    keys=[(r["instance_id"],r["arm"]) for r in rows]
    if len(keys)!=len(expected) or set(keys)!=expected:raise ValueError("incomplete/duplicate frozen matched results")
    idx={k:r for k,r in zip(keys,rows)}
    for r in rows:
        if r.get("status")!="completed" or type(r.get("resolved")) is not bool:raise ValueError("invalid scorer result")
        t,c=r.get("duration_seconds"),r.get("tool_calls")
        if type(t) not in (int,float) or not math.isfinite(t) or t<0 or type(c) is not int or c<0:raise ValueError("invalid cost")
    n=len(ids)
    sums={a:{"resolved":sum(idx[t,a]["resolved"] for t in ids),"seconds":sum(idx[t,a]["duration_seconds"] for t in ids),"calls":sum(idx[t,a]["tool_calls"] for t in ids)} for a in ARMS}
    pairs={}
    for a in list(ARMS)[1:]:
        wins=sum(idx[t,a]["resolved"] and not idx[t,"champion"]["resolved"] for t in ids)
        losses=sum(not idx[t,a]["resolved"] and idx[t,"champion"]["resolved"] for t in ids)
        s=sums[a];b=sums["champion"]
        pairs[a]={"rescues":wins,"regressions":losses,"net":wins-losses,"exploratory_gate":wins-losses>=2 and losses<=1 and b["seconds"]>0 and b["calls"]>0 and s["seconds"]<=1.15*b["seconds"] and s["calls"]<=1.15*b["calls"]}
    effects=[int(idx[t,"D"]["resolved"])-int(idx[t,"A"]["resolved"])-int(idx[t,"B"]["resolved"])+int(idx[t,"champion"]["resolved"]) for t in ids]
    return {"tasks":n,"evaluations":len(rows),"arms":sums,"paired":pairs,"factorial_interaction":sum(effects)/n,"interaction_task_counts":{str(i):effects.count(i) for i in range(-2,3)},"automatic_promotion":False,"official_submission":False}

def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest="cmd",required=True)
    b=sub.add_parser("build");b.add_argument("--source",type=Path,required=True);b.add_argument("--out",type=Path,required=True)
    a=sub.add_parser("assess");a.add_argument("--results",type=Path,required=True);a.add_argument("--ids",type=Path,required=True)
    x=p.parse_args()
    print(json.dumps(build(x.source.read_bytes(),x.out) if x.cmd=="build" else assess(json.loads(x.results.read_text()),json.loads(x.ids.read_text())),sort_keys=True))
if __name__=="__main__":main()
