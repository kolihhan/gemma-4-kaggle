# Private, CPU-only runtime appended to existing official wheelhouse installer.
# No original task test_patch or original grader targets enter the witness replay.
import dataclasses
from collections import Counter,defaultdict
CASES=json.loads(__PRIVATE_PAYLOAD__)
OUT=WORKING_DIR/"visible_witness_replay_safe.json"

def visible_task(task,target):
    # Construct a separate evaluator task. Fail closed on unsupported schemas.
    values={"test_patch":"","FAIL_TO_PASS":[target],"PASS_TO_PASS":[]}
    if hasattr(task,"test_files"):
        values["test_files"]=[target.split("::")[0]]
    if hasattr(task,"patch"):values["patch"]=""
    if hasattr(task,"model_copy"):
        obj=task.model_copy(update=values)
    elif dataclasses.is_dataclass(task):
        obj=dataclasses.replace(task,**values)
    else:
        raise TypeError("unsupported task schema")
    assert not obj.test_patch and list(obj.FAIL_TO_PASS)==[target] and not obj.PASS_TO_PASS
    if hasattr(obj,"test_files"):assert list(obj.test_files)==[target.split("::")[0]]
    return obj

async def replay():
    from swegemma.config import EvalConfig
    from swegemma.models import load_tasks
    from swegemma.evaluate import Evaluator
    from swegemma.deduplication import resolve_task_snapshot_paths
    from swegemma.harness.verification import verify_task
    from adk_submission import ModelRegistry
    cfg=EvalConfig(tasks_path=DATA_DIR/"tasks.jsonl",snapshots_dir=DATA_DIR/"snapshots",results_dir=WORKING_DIR/"visible-replay-results",submission_dir=WORKING_DIR/"visible-replay-empty",models=ModelRegistry(),sandbox="subprocess",wheels_dir=DATA_DIR/"wheels",timeout_seconds=180,verification_timeout_seconds=60,verbose=False)
    cfg.results_dir.mkdir(parents=True,exist_ok=True);cfg.submission_dir.mkdir(parents=True,exist_ok=True)
    ev=Evaluator(cfg)
    ids={c["id"] for c in CASES}
    original={t.instance_id:t for t in load_tasks(DATA_DIR/"tasks.jsonl") if t.instance_id in ids}
    assert set(original)==ids
    agg=defaultdict(Counter); records=[]
    for i,c in enumerate(CASES):
        g=c["group"];a=agg[g];a["tasks"]+=1
        outcome={}
        try:
            t=original[c["id"]]
            witness=visible_task(t,c["target"])
            # Hydrate reference ONLY for evaluator-side comparison, never for witness target selection.
            reference=ev._hydrate_task_from_secret(t).patch
            if not reference:raise ValueError("no reference")
            assert not witness.test_patch and list(witness.FAIL_TO_PASS)==[c["target"]] and not witness.PASS_TO_PASS
            snapshot,base,patch_path=resolve_task_snapshot_paths(DATA_DIR/"snapshots",t.instance_id,t.repo)
            variants={"noop":"","reference":reference,**c["patches"]}
            cache={}
            for k,patch in variants.items():
                if patch in cache:outcome[k]=cache[patch];continue
                try:
                    v=await verify_task(ev.docker,ev.config,witness,snapshot,base_snapshot_path=base,patch_path=patch_path,agent_patch=patch,agent_error=None,trace=None,start_time=time.perf_counter())
                    # A skipped/failed setup is NOT a meaningful test failure.
                    output=str(getattr(v,"test_output","") or "")
                    exit_code=getattr(v,"test_exit_code",None)
                    if exit_code==0 and bool(v.resolved):label="PASS"
                    elif exit_code==1 and re.search(r"\b(?:[1-9]\d*) failed\b",output):label="FAIL"
                    else:label="BLOCKED"
                except BaseException:label="BLOCKED"
                cache[patch]=label;outcome[k]=label
            a["unique_patch_runs"]+=len(cache)
            a["baseline_fail_reference_pass"]+=int(outcome["noop"]=="FAIL" and outcome["reference"]=="PASS")
            a["baseline_pass_reference_pass"]+=int(outcome["noop"]=="PASS" and outcome["reference"]=="PASS")
            a["control_blocked"]+=int("BLOCKED" in (outcome["noop"],outcome["reference"]))
            for arm,resolved in c["original_resolved"].items():
                a["original_"+("correct" if resolved else "wrong")+"_witness_"+outcome[arm].lower()]+=1
                if outcome["noop"]=="FAIL" and outcome["reference"]=="PASS":
                    a["discriminating_"+("correct" if resolved else "wrong")+"_witness_"+outcome[arm].lower()]+=1
        except BaseException as exc:
            a["task_setup_blocked"]+=1
            outcome={"setup":"BLOCKED_"+type(exc).__name__}
        records.append({"ordinal":i+1,"group":g,"outcomes":outcome})
        print("VISIBLE_REPLAY_PROGRESS="+str(i+1)+"/"+str(len(CASES)),flush=True)
    return {"tasks":len(CASES),"by_group":agg,"records":records,"original_grader_used_as_label_only":True,"private_content_exported":False,"new_gpu":False,"model_inference":False,"official_submission":False,"limitation":"original visible target replay under sanitized verifier, not exact shell environment; blocked outcomes not failures"}

if __name__=="__main__":
    import re
    try:
        install_official_wheelhouse()
        report=asyncio.run(replay())
        OUT.write_text(json.dumps(report,sort_keys=True))
        print("VISIBLE_WITNESS_REPLAY_SAFE="+json.dumps({k:v for k,v in report.items() if k!="records"},sort_keys=True),flush=True)
    except BaseException as e:
        print("VISIBLE_REPLAY_BLOCKER="+type(e).__name__,flush=True)
        raise RuntimeError("PRIVATE_VISIBLE_WITNESS_REPLAY_BLOCKED") from None
