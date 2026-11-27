"""CPU-only FORK retrospective; no private raw data printed or persisted in Git."""
from pathlib import Path
from collections import Counter,defaultdict
import argparse,json,re
from scripts import audit_clean17_saved_patches as audit
from scripts.render_fork_v1_20261127 import assess,RESULT

ARMS=("champion_5min","fork_5min")

def run(root,tasks,prior_root):
    data=json.loads((root/RESULT).read_text())
    score=assess(data)
    audit.ARMS=ARMS
    audit.RESULT=RESULT
    audit.assess=assess
    # The prior helper hardcodes its original private results directory.
    old=audit.saved_patch
    def saved(root,row):
        task,arm=row["instance_id"],row["arm"]
        p=root/"paired-fork-private-results"/"private-final-patches"/arm/(task+".patch")
        patch=p.read_bytes().decode("utf-8") if p.is_file() else ""
        if len(patch)!=row["patch_chars"] or bool(patch.strip())!=row["has_patch"]:
            raise ValueError("retained patch metadata mismatch")
        return patch
    audit.saved_patch=saved
    summary=audit.analyze(root,tasks)
    by=defaultdict(Counter)
    rows={(r["instance_id"],r["arm"]):r for r in data["results"]}
    for (task,arm),r in rows.items():
        g=by[(arm,"pass" if r["resolved"] else "fail")]
        g["n"]+=1
        g["tool_calls"]+=r["tool_calls"]
        g["seconds"]+=r["duration_seconds"]
        g["calls_ge_28"]+=int(r["tool_calls"]>=28)
        g["calls_ge_55"]+=int(r["tool_calls"]>=55)
    uptake=defaultdict(Counter)
    seen=set()
    for p in root.rglob("trace_*.json"):
        task=p.stem.removeprefix("trace_")
        arm=ARMS[int("public-prompt" in p.relative_to(root).parts)]
        if (task,arm) not in rows:continue
        if (task,arm) in seen:raise ValueError("ambiguous trace")
        seen.add((task,arm))
        r=rows[task,arm]
        g=uptake[(arm,"pass" if r["resolved"] else "fail")]
        g["traces"]+=1
        cmds=[]
        for step in json.loads(p.read_text())["steps"]:
            for c in step.get("tool_calls") or []:
                a=c.get("arguments")
                if c.get("function_name")=="run_command" and isinstance(a,dict) and isinstance(a.get("command"),str):
                    cmds.append(a["command"])
        g["checkpoint_request"]+=int(any("/tmp/fork_a.patch" in x and "git diff" in x for x in cmds))
        g["reverse_apply_request"]+=int(any("git apply" in x and "--reverse" in x for x in cmds))
        g["bounded_test_request"]+=int(any(re.search(r"timeout\s+\d+s?\s+.*pytest",x) for x in cmds))
    earlier=json.loads((prior_root/"paired_multisurface31b_clean17_results.json").read_text())
    from scripts.render_multisurface_clean17_20261126 import assess as assess_prior
    assess_prior(earlier)
    previous={(r["instance_id"],r["arm"]):r["resolved"] for r in earlier["results"]}
    ids={k[0] for k in rows}
    if ids!={k[0] for k in previous}:raise ValueError("cohort mismatch")
    matrix=Counter(tuple(int(v) for v in (previous[t,"champion_5min"],previous[t,"multisurface_5min"],rows[t,"champion_5min"]["resolved"],rows[t,"fork_5min"]["resolved"])) for t in ids)
    print("FORK_CPU_AUDIT="+json.dumps({"score":score,"retained":summary,"by_arm_outcome":{"|".join(k):v for k,v in by.items()},"uptake_requests_not_execution":{"|".join(k):v for k,v in uptake.items()},"four_arm_outcome_patterns":{"".join(map(str,k)):v for k,v in matrix.items()}},sort_keys=True))

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True);p.add_argument("--tasks",type=Path,required=True);p.add_argument("--prior-root",type=Path,required=True)
    a=p.parse_args();run(a.root,a.tasks,a.prior_root)
