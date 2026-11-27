"""Authorized private budget factorial: qualify 10 unused issues on CPU, then 50 actual model runs.
Render only. Never submit to competition. No private raw content in public output.
"""
from __future__ import annotations
import argparse,base64,hashlib,json,re
from pathlib import Path
from scripts.budget_factorial_20261127 import ARMS,arm_files,schedule,assess
from scripts.build_behavioral_probe_timeout_safe_20261123 import _source_files,_pack,CHAMPION_SHA256
from scripts.render_six_gold_noop_cpu_20261126 import SAFE_RUNTIME,TEMPLATE
CPU="kolihhan/gemma4-budget-factorial-eligibility-20261127-v1"
GPU="kolihhan/gemma4-budget-factorial-31b-20261127-v1"
RESULT="budget_factorial_real31b.json"
MODEL="gemma-4-31b-it-qat-w4a16-ct"
IMAGE="gcr.io/kaggle-private-byod/python@sha256:37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461"
PRIOR=(("behavior","paired_behavioral_probe31b_4min_results.json",8),("grammar","paired_edit_grammar31b_5min_results.json",8),("single","paired_single_edit_channel31b_4min_results.json",6),("fork","paired_fork31b_results.json",17))
def one(s,a,b):
    if s.count(a)!=1:raise ValueError("renderer marker drift")
    return s.replace(a,b,1)
def meta(slug,accelerator):
    m={"id":slug,"title":slug.split("/")[1],"code_file":"main.py","language":"python","kernel_type":"script","is_private":True,"enable_gpu":accelerator,"enable_tpu":False,"enable_internet":False,"docker_image":IMAGE,"competition_sources":["gemma-4-developer-agent"],"dataset_sources":["metric/gemma-4-developer-agent-wheelhouse"],"model_sources":["google/gemma-4/Other/"+MODEL+"/2"] if accelerator else [],"kernel_sources":[]}
    if accelerator:m["machine_shape"]="NvidiaL4"
    return m
def write(out,src,slug,gpu):
    assert "competition_submit_code" not in src
    compile(src,"main.py","exec")
    out.mkdir(parents=True,exist_ok=False)
    (out/"main.py").write_text(src)
    (out/"kernel-metadata.json").write_text(json.dumps(meta(slug,gpu),sort_keys=True))
def cpu_render(previous,tasks,out):
    plan=json.loads(Path("experiments/edit-grammar-paired-20261124/manifest.json").read_text())
    used=set(plan["selection"]["exclude_instance_ids"])
    assert len(used)==43
    for folder,name,n in PRIOR:
        x=json.loads((previous/folder/name).read_text())
        ids=set(x["selected_public_dev_ids"])
        assert x["status"]=="completed" and len(ids)==n and len(x["results"])==2*n and not used&ids
        used.update(ids)
    assert len(used)==82
    rows=[json.loads(x) for x in tasks.read_text().splitlines() if x.strip()]
    assert len({x["instance_id"] for x in rows})==len(rows)
    candidates=[]
    for t in rows:
        s=t.get("problem_statement") or ""
        if t["instance_id"] not in used and s.strip() and not (len(s.strip())<160 and re.search(r"https?://",s)):
            candidates.append(t["instance_id"])
    candidates=sorted(candidates,key=lambda t:hashlib.sha256(("budget-factorial-independent-20261127-v1|"+t).encode()).hexdigest())
    if len(candidates)<10:raise ValueError("fewer than ten unused non-pointer issues")
    src=Path(TEMPLATE).read_text().split('if __name__ == "__main__":',1)[0]
    safe=SAFE_RUNTIME.replace("__SELECTED_IDS__",repr(candidates)).replace("gemma31_six_gold_noop_safe.json","budget_factorial_eligibility.json")
    safe=one(safe,"    rows=[]\n","    rows=[]\n    qualified=[]\n")
    safe=one(safe,'                    record[kind+"_pass"]=bool(v.resolved)','                    record[kind+"_pass"]=bool(v.resolved)\n                    if kind=="noop":record["noop_actual_test_failure"]=getattr(v,"test_exit_code",None)==1')
    safe=one(safe,'        rows.append(record)','        rows.append(record)\n        if record["gold_pass"] is True and record["noop_pass"] is False and record.get("noop_actual_test_failure") is True:\n            qualified.append(task_id)')
    safe=one(safe,'    complete=[x for x in rows','        if len(qualified)==10:break\n    complete=[x for x in rows')
    safe=one(safe,'          "rows":rows,','          "rows":rows,"qualified_ids":qualified,"qualified_count":len(qualified),')
    safe=one(safe,'if k!="rows"','if k not in ("rows","qualified_ids")')
    write(out,src+"\n"+safe,CPU,False)
    return {"excluded_previous_known":len(used),"candidate_count":len(candidates),"candidate_membership_sha256":hashlib.sha256("|".join(candidates).encode()).hexdigest(),"required_qualified":10,"no_gpu":True}
def gpu_render(source,qualification,out):
    x=json.loads(qualification.read_text())
    ids=x["qualified_ids"]
    assert x["qualified_count"]==10 and len(ids)==len(set(ids))==10 and not x["gpu"] and not x["model_inference"]
    files=arm_files(_source_files(source.read_bytes()))
    assert hashlib.sha256(_pack(files["champion"])).hexdigest()==CHAMPION_SHA256
    payload=base64.b64encode(json.dumps(files["champion"],sort_keys=True).encode()).decode()
    arms_payload=repr(json.dumps(files,sort_keys=True))
    src=Path("kaggle/verifier_baseline_runtime.py").read_text()
    src=one(src,'SUBMISSION_PAYLOAD_B64 = "__SUBMISSION_PAYLOAD_B64__"',"SUBMISSION_PAYLOAD_B64 = "+repr(payload))
    src=one(src,'HOLDOUT_MANIFEST_JSON = "__VERIFIER_LORA_HOLDOUT_MANIFEST_JSON__"',"HOLDOUT_MANIFEST_JSON = "+repr(json.dumps({"version":"verifier-lora-v0","holdout":[{"instance_id":t} for t in ids]})))
    src=one(src,'MODEL_NAME = "gemma-4-e4b-it-qat-w4a16-ct"',"MODEL_NAME = "+repr(MODEL))
    src=one(src,'SUMMARY_PATH = WORKING_DIR / "verifier_baseline_results.json"','SUMMARY_PATH = WORKING_DIR / '+repr(RESULT)+'\nFACTORIAL_PAYLOAD = '+arms_payload+'\nORDER = '+repr(schedule(ids)))
    src=one(src,'    validate_directory(AGENT_DIR, limits=limits)\n','''    arm_files=json.loads(FACTORIAL_PAYLOAD)
    arm_dirs={}
    for arm,files in arm_files.items():
        root=WORKING_DIR/("budget-arm-"+arm)
        root.mkdir(parents=True,exist_ok=False)
        for relative,content in files.items():
            target=(root/relative).resolve()
            if root.resolve() not in target.parents:raise ValueError("path escape")
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_text(content)
        validate_directory(root,limits=limits)
        if discover_declared_models(root)!={MODEL_NAME}:raise ValueError("model drift")
        if getattr(discover_adapters(str(root),adapter_extensions=ALLOWED_ADAPTER_EXTENSIONS),"adapters",None):raise ValueError("adapter drift")
        arm_dirs[arm]=root
    validate_directory(AGENT_DIR,limits=limits)
''')
    src=one(src,'        evaluator = Evaluator(eval_config)\n','''        import dataclasses
        evaluators={}
        for arm,root in arm_dirs.items():
            budget=yaml.safe_load((root/"eval_config.yaml").read_text())
            budget=budget.get("evaluation",budget)
            updates={"submission_dir":root,"results_dir":RESULTS_DIR/arm,"max_tool_calls":int(budget["max_tool_calls"])}
            if dataclasses.is_dataclass(eval_config):cfg=dataclasses.replace(eval_config,**updates)
            elif hasattr(eval_config,"model_copy"):cfg=eval_config.model_copy(update=updates)
            else:raise TypeError("unsupported EvalConfig")
            assert cfg.max_tool_calls==int(budget["max_tool_calls"]) and cfg.max_time_minutes==5 and cfg.max_turns==80
            assert Path(cfg.submission_dir)==root
            evaluators[arm]=Evaluator(cfg)
''')
    a=src.index("        records: list[dict[str, object]] = []")
    b=src.index("    finally:\n",a)
    src=src[:a]+'''        records=[]
        assert len(ORDER)==50 and len(set(ORDER))==50
        assert set(ORDER)=={(t,a) for t in holdout_ids for a in arm_dirs}
        for index,(task_id,arm) in enumerate(ORDER,1):
            try:
                result=run_maybe_async(evaluators[arm].evaluate_task(task=tasks_by_id[task_id],task_index=holdout_ids.index(task_id)+1,total_tasks=10))
                record={"instance_id":task_id,"arm":arm,"status":"completed","resolved":bool(result.resolved),"duration_seconds":result.duration_seconds,"tool_calls":result.tool_calls,"has_patch":bool((result.agent_patch or "").strip()),"test_exit_code":result.test_exit_code}
            except BaseException as e:
                record={"instance_id":task_id,"arm":arm,"status":"error","error_type":type(e).__name__,"resolved":False}
            records.append(record)
            SUMMARY_PATH.write_text(json.dumps({"status":"running","selected_public_dev_ids":holdout_ids,"results":records}))
            print("FACTORIAL_PROGRESS="+str(index)+"/50",flush=True)
        assert len(records)==50
        SUMMARY_PATH.write_text(json.dumps({"status":"completed","selected_public_dev_ids":holdout_ids,"results":records,"official_submission":False,"training":False}))
'''+src[b:]
    write(out,src,GPU,True)
    return {"tasks":10,"evaluations":50,"cohort_sha256":hashlib.sha256("|".join(ids).encode()).hexdigest(),"arms":ARMS,"bundle_hashes":{a:hashlib.sha256(_pack(f)).hexdigest() for a,f in files.items()},"official_submission":False}
def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest="mode",required=True)
    c=sub.add_parser("cpu");c.add_argument("--previous",type=Path,required=True);c.add_argument("--tasks",type=Path,required=True);c.add_argument("--out",type=Path,required=True)
    g=sub.add_parser("gpu");g.add_argument("--source",type=Path,required=True);g.add_argument("--qualification",type=Path,required=True);g.add_argument("--out",type=Path,required=True)
    x=p.parse_args()
    print(json.dumps(cpu_render(x.previous,x.tasks,x.out) if x.mode=="cpu" else gpu_render(x.source,x.qualification,x.out),sort_keys=True),flush=True)
if __name__=="__main__":main()
