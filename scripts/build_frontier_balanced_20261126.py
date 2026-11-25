"""Time-frontier candidate: independent Champion prompt, rank-2 efficiency evidence.

No inference, no official submission. Candidate is a multi-config intervention,
not a proven single-variable causal improvement. 5.5 min is a compromise:
6 min * 120 = 12h before startup, while 5 min missed most v31 late wins.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import yaml
from scripts.render_sampling_regime31b_20261124 import make_pair
from scripts.render_single_edit_channel31b_20261124 import pack
from scripts.submit_v2_toolcap60_official_once import compile_without_inference

BASE_SHA = "6183b58d06209f5a2a0b399b57cfcaa766129ad3615d633ba2e2c9bc2b7fd50a"

def build(source: bytes):
    control, sampling, champion_zip, sampling_zip, _, _ = make_pair(source)
    assert hashlib.sha256(sampling_zip).hexdigest() == BASE_SHA
    old = yaml.safe_load(sampling["eval_config.yaml"])
    old_gen = yaml.safe_load(sampling["configs/sampling.yaml"])
    expected = {"timeout_seconds":240,"max_tool_calls":60,"max_time_minutes":5,"max_turns":80}
    assert old["evaluation"] == expected
    assert old_gen["temperature"] == 1.0 and old_gen["top_k"] == 64
    cfg = dict(expected, timeout_seconds=120, max_tool_calls=40, max_time_minutes=5.5)
    gen = dict(old_gen, max_output_tokens=4096, thinking_config=dict(old_gen["thinking_config"],thinking_budget=2048))
    out = dict(sampling)
    out["eval_config.yaml"] = yaml.safe_dump({"evaluation":cfg},sort_keys=False)
    out["configs/sampling.yaml"] = yaml.safe_dump(gen,sort_keys=False)
    assert {k for k in out if out[k]!=sampling[k]} == {"eval_config.yaml","configs/sampling.yaml"}
    assert out["prompts/system.md"] == control["prompts/system.md"]
    assert out["agent.yaml"] == control["agent.yaml"]
    return pack(out),cfg,gen

def frontier(path: Path):
    rows = [json.loads(x) for x in path.read_text().splitlines() if x.strip()]
    a = {r["task"]:r for r in rows if r["agent"]=="v31" and r["set"]=="heldout66"}
    b = {r["task"]:r for r in rows if r["agent"]=="v24" and r["set"]=="heldout66"}
    assert len(a)==66 and set(a)==set(b)
    scenarios=[]
    for scale in (.8,1,1.2,1.6):
        for cap in (300,330,360):
            # Censored historical durations are planning scenarios, not actual
            # Kaggle latency or valid counterfactual solve estimates.
            mean = sum(min(cap,scale*r["seconds"]) for r in a.values())/len(a)
            for overhead in (15,30,45):
                seconds=1800+120*(mean+overhead)
                scenarios.append(dict(scale=scale,cap_s=cap,overhead_s=overhead,
                    assumed_tasks=120,assumed_startup_s=1800,estimated_hours=round(seconds/3600,3),
                    slack_minutes=round((43200-seconds)/60,2),
                    observed_successes_within_scaled_cap=sum(r["resolved"] and scale*r["seconds"]<=cap for r in a.values())))
    return scenarios

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--runs",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    print("FRONTIER_RUNTIME_SCENARIOS="+json.dumps(frontier(args.runs)),flush=True)
    blob,cfg,gen=build(args.source.read_bytes())
    compile_without_inference(blob)
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/"submission.zip").write_bytes(blob)
    report={"sha256":hashlib.sha256(blob).hexdigest(),"base_sha256":BASE_SHA,
        "evaluation":cfg,"sampling":gen,"official_submission":False,
        "new_model_inference":False,"gain_proven":False,
        "runtime_guarantee":False,"max_task_only_minutes_at_120":660,
        "decision":"prepare candidate; require official slot and compare Sampling result before submission"}
    (args.out/"candidate.json").write_text(json.dumps(report,indent=2))
    print("FRONTIER_CANDIDATE="+json.dumps(report),flush=True)

if __name__=="__main__":main()
