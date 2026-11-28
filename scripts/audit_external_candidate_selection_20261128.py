"""Offline retrospective of external Phase 1 published compact episodes.
Input: exact public blob 16e3bbf15fc5f384893207339b3ea5ee520d195a.
No new inference, no reference-path features in selection, no official score proxy.
"""
import json
import sys
from collections import defaultdict
from pathlib import Path


def choose(a,b):
    def key(x):
        return (x["patch_chars"]>0, x["patch_submitted"] is True)
    return b if key(b)>key(a) else a


def summarize(pairs, retry=lambda a:True):
    out=dict(n=len(pairs),seed0=0,seed1=0,selected=0,random_expected=0,
             oracle=0,rescues=0,regressions=0,switches=0,discordant=0,
             strict_seed0=0,strict_selected=0,retries=0,seed0_seconds=0,
             policy_seconds=0)
    for a,b in pairs:
        second=retry(a)
        c=choose(a,b) if second else a
        out["seed0"]+=a["pass"]
        out["seed1"]+=b["pass"]
        out["selected"]+=c["pass"]
        out["random_expected"]+=(a["pass"]+b["pass"])/2
        out["oracle"]+=a["pass"] or b["pass"]
        out["rescues"]+=not a["pass"] and c["pass"]
        out["regressions"]+=a["pass"] and not c["pass"]
        out["switches"]+=c is b
        out["discordant"]+=a["pass"]!=b["pass"]
        out["strict_seed0"]+=a["strict_pass"]
        out["strict_selected"]+=c["strict_pass"]
        out["retries"]+=second
        out["seed0_seconds"]+=a["virtual_seconds"]
        out["policy_seconds"]+=a["virtual_seconds"]+(b["virtual_seconds"] if second else 0)
    out["relative_virtual_cost"]=out["policy_seconds"]/out["seed0_seconds"]
    return out


def run(path):
    rows=[json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
    groups=defaultdict(list)
    for r in rows:groups[r["task_id"],r["arm"]].append(r)
    assert len(rows)==900 and len(groups)==450
    assert len({r["task_id"] for r in rows})==150
    pairs=[sorted(v,key=lambda r:r["seed"]) for v in groups.values()]
    assert all(len(p)==2 and [x["seed"] for x in p]==[0,1] for p in pairs)
    assert all(all(a[k]==b[k] for k in ("stratum","task_id","arm","thinking_budget","r_gen")) for a,b in pairs)
    matched=[(a,b) for a,b in pairs if a["temperature"]==b["temperature"]]
    assert len(matched)==300
    return {"matched":summarize(matched),"temperature_mismatch_excluded":150,
            "arms":{k:summarize([p for p in pairs if p[0]["arm"]==k]) for k in sorted({r["arm"] for r in rows})},
            "strata":{k:summarize([p for p in matched if p[0]["stratum"]==k]) for k in sorted({r["stratum"] for r in rows})},
            "posthoc_retry": {
                "not_submitted_or_empty":summarize(matched,lambda a:not a["patch_submitted"] or a["patch_chars"]<=0),
                "empty_only":summarize(matched,lambda a:a["patch_chars"]<=0),
                "empty_before_half_virtual_budget":summarize(matched,lambda a:a["patch_chars"]<=0 and a["virtual_seconds"]<210)},
            "unique_tasks":150,"official_score_proxy":False,"real_walltime_measured":False}


if __name__=="__main__":
    print(json.dumps(run(sys.argv[1]),sort_keys=True))
