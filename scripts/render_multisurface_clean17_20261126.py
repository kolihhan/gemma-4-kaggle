"""Preregister and render REAL Gemma 31B matched 17-issue scorer.

Control is exact scored Champion 0.18. Candidate changes prompts/system.md ONLY.
No public-dev task text, grader reference patch, hidden tests or prior model
attempts enter either agent prompt. Public task IDs selected before inference.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

from scripts import render_edit_grammar_paired31b_20261124 as prior
from scripts.build_gemma_edit_grammar_20261124 import files_for_pair as old_pair
from scripts.build_multisurface_scope_20261126 import (
    build_pair, eligible_source_paths, files_for_pair,
)

KERNEL = "kolihhan/gemma4-multisurface-clean17-paired-20261126-v1"
MODEL_SOURCE = prior.MODEL_SOURCE
SOURCE = "lynnsakurai/gemma-4-budget-fit-agent-w-bounded-rescue/2"
RESULT = "paired_multisurface31b_clean17_results.json"
RUNTIME = "multisurface31b_clean17_runtime.py"
VERSION = "multisurface-clean17-31b-paired-v1"
MEMBERSHIP_SHA = "231db5d504930562c4dc78f696a56009635f02bfcf4a79023531d2a3a7eb8bd2"
N = 17
ARMS = ("champion_5min", "multisurface_5min")

def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def one(s: str, a: str, b: str) -> str:
    if s.count(a)!=1:
        raise ValueError("unexpected renderer marker count")
    return s.replace(a,b,1)

def selection_hash(ids:list[str]) -> str:
    return sha("|".join(ids).encode())

def render(repo:Path, source:bytes, selected:list[str], output:Path):
    ids=eligible_source_paths(selected)
    if selection_hash(ids)!=MEMBERSHIP_SHA:
        raise ValueError("17-member frozen CPU-validated cohort changed")
    c,t=files_for_pair(source)
    cz,tz=build_pair(source)
    assert sha(cz)=="ff08c10240a38e151a2ea1d0478e999ee5d2f437d2dad5571d912cf12859922b"
    assert {k for k in c if c[k]!=t[k]}=={"prompts/system.md"}
    old_c,old_t=old_pair(source)
    plan=json.loads((repo/prior.MANIFEST_PATH).read_text())
    script=prior.render_runtime((repo/prior.TEMPLATE_PATH).read_text(),source,plan)
    script=one(script,repr(prior.payload(old_c)),repr(prior.payload(c)))
    script=one(script,repr(prior.payload(old_t)),repr(prior.payload(t)))
    selector='''def load_holdout_ids(public_tasks) -> list[str]:
    chosen = __FROZEN_IDS__
    public_ids={x.instance_id for x in public_tasks}
    if len(chosen)!=17 or len(set(chosen))!=17 or not set(chosen)<=public_ids:
        raise RuntimeError("frozen 17 scored issue identities unavailable")
    print("FROZEN17_PRIVATE_SCORER_IDS_SHA256=__FROZEN_SHA__",flush=True)
    return chosen

'''.replace("__FROZEN_IDS__",repr(ids)).replace("__FROZEN_SHA__",MEMBERSHIP_SHA)
    start=script.index("def load_holdout_ids(public_tasks) -> list[str]:")
    stop=script.index("def run_maybe_async(",start)
    script=script[:start]+selector+script[stop:]
    for a,b in (
        ("edit-grammar-31b-5min-paired-v1",VERSION),
        ("edit_grammar_5min",ARMS[1]),
        ("paired-edit-grammar-5min","paired-multisurface-5min"),
        ("paired-edit-grammar-private-results","paired-multisurface-private-results"),
        ("paired_edit_grammar31b_5min_results.json",RESULT),
    ):
        if a not in script:raise ValueError("old evaluation marker missing")
        script=script.replace(a,b)
    script=one(script,"if len(records) != 16:","if len(records) != 34:")
    script=one(script,"if len(scored) != 8:","if len(scored) != 17:")
    # The raw patches stay in private Kaggle output; output downloaded only for
    # aggregate metric calculation, never uploaded to public CI artifacts.
    script=one(script,
       '                    row = {\n                        "arm": arm,',
       '                    if patch:\n'
       '                        patch_dir = RESULTS_DIR / "private-final-patches" / arm\n'
       '                        patch_dir.mkdir(parents=True,exist_ok=True)\n'
       '                        (patch_dir / (task_id + ".patch")).write_text(patch,encoding="utf-8")\n'
       '                    row = {\n                        "arm": arm,')
    # Previously used renderer already created two fully isolated Evaluators.
    assert "treatment_evaluator = Evaluator(treatment_config)" in script
    assert "competition_submit_code" not in script
    assert script.count(MEMBERSHIP_SHA)==1
    assert "max_time_minutes: 5" in c["eval_config.yaml"]
    assert "max_tool_calls: 60" in c["eval_config.yaml"]
    assert "max_turns: 80" in c["eval_config.yaml"]
    compile(script,RUNTIME,"exec")
    if output.exists():raise FileExistsError("private scorer already rendered")
    output.mkdir(parents=True)
    (output/RUNTIME).write_text(script)
    metadata={
       "id":KERNEL,"title":KERNEL.split("/")[1],"code_file":RUNTIME,
       "language":"python","kernel_type":"script","is_private":True,
       "enable_gpu":True,"enable_tpu":False,"enable_internet":False,
       "machine_shape":"NvidiaL4",
       "docker_image":"gcr.io/kaggle-private-byod/python@sha256:37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461",
       "competition_sources":["gemma-4-developer-agent"],
       "dataset_sources":["metric/gemma-4-developer-agent-wheelhouse"],
       "model_sources":[MODEL_SOURCE],"kernel_sources":[]
    }
    (output/"kernel-metadata.json").write_text(json.dumps(metadata,sort_keys=True,indent=2)+"\n")
    return {"model":prior.MODEL,"official_submission":False,
            "cpu_preflight_only":True,"new_model_inference":False,
            "paired_clean_issues":N,"evaluations":2*N,
            "frozen_membership_sha256":MEMBERSHIP_SHA,
            "control_sha256":sha(cz),"candidate_sha256":sha(tz),
            "only_changed":"prompts/system.md","budget_minutes":5,
            "tool_calls":60,"turns":80,"issue_gold_noop_valid_17":True}

def assess(data:dict)->dict:
    """Conservative blinded paired correctness gate, exact cohort or fail."""
    if data.get("status")!="completed" or data.get("version")!=VERSION:
        raise ValueError("incomplete or wrong-version private 31B run")
    rows=data.get("results")
    if not isinstance(rows,list) or len(rows)!=2*N:
        raise ValueError("missing 34 paired real runs")
    keys={(r.get("instance_id"),r.get("arm")) for r in rows}
    ids={r.get("instance_id") for r in rows}
    if len(ids)!=N or len(keys)!=2*N or set(keys)!={(i,a) for i in ids for a in ARMS}:
        raise ValueError("missing/duplicate task-arm scores")
    if selection_hash(sorted(ids))!=MEMBERSHIP_SHA:
        raise ValueError("frozen cohort mismatch")
    by={(r["instance_id"],r["arm"]):r for r in rows}
    score, time_s, tool_calls={a:0 for a in ARMS},{a:0.0 for a in ARMS},{a:0 for a in ARMS}
    err={a:0 for a in ARMS}
    matrix={k:0 for k in ("both","control_only","candidate_only","neither")}
    for tid in ids:
        items=[by[(tid,a)] for a in ARMS]
        for a,r in zip(ARMS,items):
            if r.get("status")!="completed" or type(r.get("resolved")) is not bool:
                err[a]+=1
                continue
            seconds=r.get("duration_seconds")
            calls=r.get("tool_calls")
            if type(seconds) not in (int,float) or seconds<0 or seconds>7200 or \
               type(calls) is not int or calls<0:
                err[a]+=1
                continue
            score[a]+=int(r["resolved"])
            time_s[a]+=seconds
            tool_calls[a]+=calls
        if all(r.get("status")=="completed" and type(r.get("resolved")) is bool for r in items):
            left,right=(r["resolved"] for r in items)
            k=("both" if left and right else "control_only" if left
               else "candidate_only" if right else "neither")
            matrix[k]+=1
    net=matrix["candidate_only"]-matrix["control_only"]
    ratio=(time_s[ARMS[1]]/time_s[ARMS[0]]) if time_s[ARMS[0]] else None
    calls_ratio=(tool_calls[ARMS[1]]/tool_calls[ARMS[0]]) if tool_calls[ARMS[0]] else None
    eligible=(sum(err.values())==0 and
              sum(matrix.values())==N and
              net>=2 and matrix["control_only"]<=1 and
              ratio is not None and ratio<=1.15 and
              calls_ratio is not None and calls_ratio<=1.15)
    return {
       "paired_issues":N,"evaluations":2*N,
       "outcomes":matrix,"resolved":score,
       "sum_task_seconds":{k:round(v,2) for k,v in time_s.items()},
       "sum_tool_calls":tool_calls,
       "error_evaluations":err,
       "net_rescues_minus_regressions":net,
       "time_ratio":None if ratio is None else round(ratio,4),
       "tool_call_ratio":None if calls_ratio is None else round(calls_ratio,4),
       "official_submit_eligible":eligible,
       "threshold":"net>=2,regressions<=1,0_errors,task_seconds<=115%,tools<=115%",
       "candidate_better_than_champion_proven_on_hidden":False,
       "raw_task_ids_patches_exported":False,
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source",type=Path,required=True)
    ap.add_argument("--ids-json",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    ids=json.loads(args.ids_json.read_text())
    output=render(Path("."),args.source.read_bytes(),ids,args.out)
    print("MULTISURFACE_REAL31B_PREPARED="+json.dumps(output,sort_keys=True),flush=True)
if __name__=="__main__":main()
