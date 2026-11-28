"""Six-native-tool vs nine-native-tool structural ablation, private exploration only.
Prior qualified reused development cases; not independent holdout and no promotion.
"""
import argparse,base64,hashlib,json,re
from pathlib import Path
from scripts.build_behavioral_probe_timeout_safe_20261123 import _source_files,_pack,CHAMPION_SHA256,MODEL
from scripts.render_budget_factorial_real31b_20261127 import one,write

SLUG="kolihhan/gemma4-core6-structural-paired-20261129-v1"
RESULT="core6_structural_paired.json"
GRAPH=("get_code_neighbors","search_similar_code","get_code_subgraph")
CORE=("run_command","read_file","edit_file","write_file","get_status","submit_patch")
N=4

def arms(source):
    control=_source_files(source)
    assert hashlib.sha256(_pack(control)).hexdigest()==CHAMPION_SHA256
    treatment=dict(control)
    # Fail closed rather than retain instructions referring to unavailable tools.
    references=[line for line in control["prompts/system.md"].splitlines() if any(t in line for t in GRAPH)]
    if references:
        print("CORE6_PROMPT_GRAPH_REFERENCES="+json.dumps(references),flush=True)
        raise ValueError("explicit graph references require reviewed consistent treatment")
    cfg=treatment["agent.yaml"]
    for tool in GRAPH:
        cfg=one(cfg,"  - "+tool+"\n","")
    assert all(cfg.count("  - "+tool+"\n")==1 for tool in CORE)
    assert not any(t in cfg for t in GRAPH)
    treatment["agent.yaml"]=cfg
    assert {k for k in control if treatment[k]!=control[k]}=={"agent.yaml"}
    return {"champion":control,"core6":treatment}

def choose(previous):
    x=json.loads(previous.read_text())
    ids=sorted(x["selected_public_dev_ids"])
    assert x["status"]=="completed" and len(ids)==len(set(ids))==17 and len(x["results"])==34
    assert hashlib.sha256("|".join(ids).encode()).hexdigest()=="231db5d504930562c4dc78f696a56009635f02bfcf4a79023531d2a3a7eb8bd2"
    return sorted(ids,key=lambda t:hashlib.sha256(("core6-structure-20261129-v1|"+t).encode()).hexdigest())[:N]

def render(source,previous,out):
    files=arms(source)
    ids=choose(previous)
    order=[(t,a) for i,t in enumerate(ids) for a in (("champion","core6") if i%2==0 else ("core6","champion"))]
    src=Path("kaggle/verifier_baseline_runtime.py").read_text()
    payload=base64.b64encode(json.dumps(files["champion"],sort_keys=True).encode()).decode()
    src=one(src,'SUBMISSION_PAYLOAD_B64 = "__SUBMISSION_PAYLOAD_B64__"',"SUBMISSION_PAYLOAD_B64 = "+repr(payload))
    src=one(src,'HOLDOUT_MANIFEST_JSON = "__VERIFIER_LORA_HOLDOUT_MANIFEST_JSON__"',"HOLDOUT_MANIFEST_JSON = "+repr(json.dumps({"version":"verifier-lora-v0","holdout":[{"instance_id":t} for t in ids]})))
    src=one(src,'MODEL_NAME = "gemma-4-e4b-it-qat-w4a16-ct"',"MODEL_NAME = "+repr(MODEL))
    src=one(src,'SUMMARY_PATH = WORKING_DIR / "verifier_baseline_results.json"',"SUMMARY_PATH = WORKING_DIR / "+repr(RESULT)+"\nARM_PAYLOAD = "+repr(json.dumps(files,sort_keys=True))+"\nORDER = "+repr(order))
    src=one(src,'    validate_directory(AGENT_DIR, limits=limits)\n','''    arm_dirs={}
    for arm,files in json.loads(ARM_PAYLOAD).items():
        root=WORKING_DIR/("core6-arm-"+arm)
        root.mkdir(parents=True,exist_ok=False)
        for relative,content in files.items():
            target=(root/relative).resolve()
            if root.resolve() not in target.parents:raise ValueError("path escape")
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_text(content)
        validate_directory(root,limits=limits)
        assert discover_declared_models(root)=={MODEL_NAME}
        assert not getattr(discover_adapters(str(root),adapter_extensions=ALLOWED_ADAPTER_EXTENSIONS),"adapters",None)
        arm_dirs[arm]=root
    validate_directory(AGENT_DIR,limits=limits)
''')
    src=one(src,'        evaluator = Evaluator(eval_config)\n','''        import dataclasses
        evaluators={}
        for arm,root in arm_dirs.items():
            updates={"submission_dir":root,"results_dir":RESULTS_DIR/arm}
            if dataclasses.is_dataclass(eval_config):cfg=dataclasses.replace(eval_config,**updates)
            elif hasattr(eval_config,"model_copy"):cfg=eval_config.model_copy(update=updates)
            else:raise TypeError("unsupported EvalConfig")
            assert cfg.max_tool_calls==60 and cfg.max_time_minutes==5 and cfg.max_turns==80
            assert Path(cfg.submission_dir)==root
            evaluators[arm]=Evaluator(cfg)
''')
    a=src.index("        records: list[dict[str, object]] = []")
    b=src.index("    finally:\n",a)
    src=src[:a]+'''        records=[]
        assert len(ORDER)==8 and len(set(ORDER))==8
        assert set(ORDER)=={(t,a) for t in holdout_ids for a in arm_dirs}
        for index,(task_id,arm) in enumerate(ORDER,1):
            try:
                result=run_maybe_async(evaluators[arm].evaluate_task(task=tasks_by_id[task_id],task_index=holdout_ids.index(task_id)+1,total_tasks=4))
                record={"instance_id":task_id,"arm":arm,"status":"completed","resolved":bool(result.resolved),"duration_seconds":result.duration_seconds,"tool_calls":result.tool_calls,"has_patch":bool((result.agent_patch or "").strip()),"test_exit_code":result.test_exit_code}
            except BaseException as e:
                record={"instance_id":task_id,"arm":arm,"status":"error","error_type":type(e).__name__,"resolved":False}
            records.append(record)
            SUMMARY_PATH.write_text(json.dumps({"status":"running","selected_public_dev_ids":holdout_ids,"results":records}))
            print("CORE6_PROGRESS="+str(index)+"/8",flush=True)
        assert len(records)==8
        SUMMARY_PATH.write_text(json.dumps({"status":"completed","selected_public_dev_ids":holdout_ids,"results":records,"official_submission":False,"training":False}))
'''+src[b:]
    write(out,src,SLUG,True)
    return {"tasks":N,"evaluations":2*N,"reused":True,"independent_holdout":False,
            "cohort_sha256":hashlib.sha256("|".join(ids).encode()).hexdigest(),
            "bundle_hashes":{a:hashlib.sha256(_pack(f)).hexdigest() for a,f in files.items()},
            "only_change":"agent.yaml: remove exactly three graph tools","official_submission":False}

def assess(data,previous):
    ids=choose(previous)
    assert data["status"]=="completed" and data["selected_public_dev_ids"]==ids and not data["official_submission"] and not data["training"]
    rows=data["results"];assert len(rows)==8
    pairs={(r["instance_id"],r["arm"]):r for r in rows}
    assert set(pairs)=={(t,a) for t in ids for a in ("champion","core6")}
    if any(r["status"]!="completed" for r in rows):raise ValueError("incomplete real evaluations")
    a,b=([pairs[t,arm] for t in ids] for arm in ("champion","core6"))
    return {"resolved":{arm:sum(r["resolved"] for r in v) for arm,v in (("champion",a),("core6",b))},
            "rescues":sum(not x["resolved"] and y["resolved"] for x,y in zip(a,b)),
            "regressions":sum(x["resolved"] and not y["resolved"] for x,y in zip(a,b)),
            "calls":{arm:sum(r["tool_calls"] for r in v) for arm,v in (("champion",a),("core6",b))},
            "seconds":{arm:sum(r["duration_seconds"] for r in v) for arm,v in (("champion",a),("core6",b))},
            "n":N,"reused":True,"independent_holdout":False,"promotion":False,"official_submission":False}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path);p.add_argument("--previous",type=Path,required=True)
    p.add_argument("--out",type=Path);p.add_argument("--assess",type=Path)
    a=p.parse_args()
    result=assess(json.loads(a.assess.read_text()),a.previous) if a.assess else render(a.source.read_bytes(),a.previous,a.out)
    print(("CORE6_ACTUAL=" if a.assess else "CORE6_RENDER=")+json.dumps(result,sort_keys=True),flush=True)
