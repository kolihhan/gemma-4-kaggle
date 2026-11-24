"""Matched sampling-regime experiment motivated by rank-2 v24.

Retain the official 0.18 Champion, no copied prompt, architecture, tools, or
weights. Alter only the two sampling settings that differ in the author's
published v19-to-v24 comparison. Private evaluation, not competition submit.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import yaml
from scripts import render_edit_grammar_paired31b_20261124 as prior
from scripts.build_gemma_edit_grammar_20261124 import files_for_pair as prior_files
from scripts.build_behavioral_probe_timeout_safe_20261123 import _source_files
from scripts.build_toolcap60_timeout_recovery import build as build_champion
from scripts.render_single_edit_channel31b_20261124 import pack,sha,load_excluded

VERSION = "sampling-regime-31b-5min-paired-v1"
KERNEL = "kolihhan/gemma4-sampling-regime-paired-20261124-v1"
RESULT = "paired_sampling_regime31b_5min_results.json"
CONTROL_SHA = "ff08c10240a38e151a2ea1d0478e999ee5d2f437d2dad5571d912cf12859922b"
N = 8

def make_pair(source:bytes):
    c = _source_files(source)
    czip = build_champion(source)
    assert sha(czip)==CONTROL_SHA
    p = dict(c)
    old=yaml.safe_load(c["configs/sampling.yaml"])
    assert isinstance(old,dict) and old["temperature"]==0.2
    assert old["thinking_config"]["thinking_budget"]==4096
    assert old["max_output_tokens"]==8192 and old["top_p"]==0.95
    new=dict(old,temperature=1.0,top_k=64)
    p["configs/sampling.yaml"]=yaml.safe_dump(new,sort_keys=False)
    assert {k for k in p if p[k]!=c[k]}=={"configs/sampling.yaml"}
    assert {k for k in new if new[k]!=old.get(k)}.issubset({"temperature","top_k"})
    return c,p,czip,pack(p),old,new

def render(repo:Path,source:bytes,out:Path,previous:list[Path]):
    old_plan=json.loads((repo/prior.MANIFEST_PATH).read_text())
    old_c,old_t=prior_files(source)
    c,t,czip,tzip,old,new=make_pair(source)
    excluded=load_excluded(repo,previous[:2])
    last=json.loads(previous[2].read_text())
    ids=set(last["selected_public_dev_ids"])
    assert last["status"]=="completed" and len(ids)==6 and len(last["results"])==12
    assert not ids.intersection(excluded)
    excluded.update(ids)
    plan=dict(version=VERSION,model=prior.MODEL,
        selection=dict(salt="gemma-v24-sampling-regime-20261124-v1",counts_by_repo={"fastapi_":3,"rich_":3,"requests_":2},exclude_instance_ids=sorted(excluded),policy="ID-only selection; all previous recorded pilot IDs excluded"),
        shared_budget=dict(max_time_minutes=5,max_tool_calls=60,max_turns=80,timeout_seconds=240),
        control_sha256=sha(czip),candidate_sha256=sha(tzip),
        private_only=True,official_submission=False)
    text=prior.render_runtime((repo/prior.TEMPLATE_PATH).read_text(),source,old_plan)
    def once(a,b):
        nonlocal text
        if text.count(a)!=1:raise ValueError("render marker drift")
        text=text.replace(a,b,1)
    once(repr(prior.payload(old_c)),repr(prior.payload(c)))
    once(repr(prior.payload(old_t)),repr(prior.payload(t)))
    once(repr(json.dumps(old_plan,sort_keys=True)),repr(json.dumps(plan,sort_keys=True)))
    text=text.replace("edit-grammar-31b-5min-paired-v1",VERSION)
    text=text.replace("edit_grammar_5min","sampling_5min")
    text=text.replace("paired-edit-grammar-5min","paired-sampling-5min")
    text=text.replace("paired-edit-grammar-private-results","paired-sampling-private-results")
    text=text.replace("paired_edit_grammar31b_5min_results.json",RESULT)
    once('                    row = {\n                        "arm": arm,',
         '                    if patch:\n'
         '                        patch_dir = RESULTS_DIR / "private-final-patches" / arm\n'
         '                        patch_dir.mkdir(parents=True, exist_ok=True)\n'
         '                        (patch_dir / (task_id + ".patch")).write_text(patch, encoding="utf-8")\n'
         '                    row = {\n                        "arm": arm,')
    compile(text,"sampling_regime_runtime.py","exec")
    assert "competition_submit_code" not in text
    assert "treatment_evaluator = Evaluator(treatment_config)" in text
    out.mkdir(parents=True,exist_ok=False)
    (out/"sampling_regime_runtime.py").write_text(text)
    meta={"id":KERNEL,"title":KERNEL.split("/")[1],
          "code_file":"sampling_regime_runtime.py","language":"python","kernel_type":"script",
          "is_private":True,"enable_gpu":True,"enable_tpu":False,"enable_internet":False,
          "machine_shape":"NvidiaL4",
          "docker_image":"gcr.io/kaggle-private-byod/python@sha256:37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461",
          "dataset_sources":["metric/gemma-4-developer-agent-wheelhouse"],
          "competition_sources":["gemma-4-developer-agent"],"kernel_sources":[],
          "model_sources":[prior.MODEL_SOURCE]}
    (out/"kernel-metadata.json").write_text(json.dumps(meta,indent=2))
    return dict(control_sha256=sha(czip),candidate_sha256=sha(tzip),
                matched_pairs=N,evaluations=N*2,prior_ids_excluded=len(excluded),
                control_sampling=old,candidate_sampling=new,
                only_changed="configs/sampling.yaml",private_kernel=KERNEL,
                official_submission=False,no_training=True)

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--source",type=Path,required=True)
    a.add_argument("--out",type=Path,required=True)
    a.add_argument("--previous",type=Path,nargs=3,required=True)
    o=a.parse_args()
    print("SAMPLING_CPU_PREFLIGHT="+json.dumps(render(Path("."),o.source.read_bytes(),o.out,o.previous),sort_keys=True),flush=True)

if __name__=="__main__":main()
