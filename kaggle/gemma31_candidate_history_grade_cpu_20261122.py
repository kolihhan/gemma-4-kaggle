"""Private CPU-only native grader for the 31B Candidate History experiment.

Exact two issue IDs; independent official verifier scores control/noop/reference,
every eligible observed patch (within a fixed cap), actual submit-boundary
snapshot, and final snapshot. No model, no GPU, no official Kaggle submission.
Reference patches/tests never appear in the solver or public output.
"""
from __future__ import annotations

import asyncio
from hashlib import sha256
import json
from pathlib import Path
import time

TASKS=(("rich_3506","Textualize/rich"),("fastapi_15588","fastapi/fastapi"))
MAX_REVISIONS_PER_TASK=14

def find_unique(name):
    matches=list(Path("/kaggle/input").rglob(name))
    if len(matches)!=1:
        raise ValueError("missing_or_ambiguous_output_"+name)
    return matches[0]

def load_history(task_id):
    folders=[p.parent for p in Path("/kaggle/input").rglob("history.json")
             if p.parent.parent.name==task_id+".history" or p.parent.name=="snapshots"]
    # Kaggle kernel outputs can include their original private working directory.
    candidates=[]
    for folder in folders:
        if folder.name!="snapshots":continue
        parent=folder.parent
        if parent.name==task_id+".history":
            candidates.append(folder)
    if len(candidates)!=1:
        raise RuntimeError("candidate_history_input_missing_or_ambiguous")
    directory=candidates[0]
    history=json.loads((directory/"history.json").read_text())
    if history.get("complete") is not True or history.get("finished") is not True:
        raise RuntimeError("candidate_history_incomplete")
    events=history.get("events",[])
    if not events or events[-1].get("tool")!="<final>":
        raise RuntimeError("no_observed_final_revision")
    revisions=history.get("revisions",{})
    if not isinstance(revisions,dict):
        raise TypeError("malformed_revisions")
    return directory,events,revisions

async def eval_native(task, snapshot, base, delta, evaluator, patch):
    from swegemma.harness.verification import verify_task
    start=time.perf_counter()
    result=await verify_task(evaluator.docker,evaluator.config,task,snapshot,
                             base_snapshot_path=base,patch_path=delta,
                             agent_patch=patch,trace=None,start_time=start)
    if type(result.resolved) is not bool:
        raise TypeError("invalid_official_grader_bool")
    return result.resolved,round(time.perf_counter()-start,2)

def select_revisions(events,revisions):
    all_nonempty={k for k,size in revisions.items() if size}
    ordered=list(dict.fromkeys(e.get("revision") for e in events
                               if e.get("revision") in all_nonempty))
    if set(ordered)!=all_nonempty:raise ValueError("unobserved_revision_in_history")
    submits=[e.get("revision") for e in events if e.get("tool")=="submit_patch" and e.get("phase")=="attempt"]
    final=events[-1].get("revision")
    essential={x for x in (*submits,final,ordered[0] if ordered else None) if x in all_nonempty}
    if len(essential)>MAX_REVISIONS_PER_TASK:
        raise ValueError("more_essential_revisions_than_cap")
    chosen=set(essential)
    for digest in ordered:
        if len(chosen)>=MAX_REVISIONS_PER_TASK:break
        chosen.add(digest)
    return [d for d in ordered if d in chosen],submits,final,len(ordered)

async def grade():
    from adk_submission import ModelRegistry
    from swegemma.config import EvalConfig
    from swegemma.deduplication import resolve_task_snapshot_paths
    from swegemma.evaluate import Evaluator
    from swegemma.models import load_tasks
    root=Path("/kaggle/working")
    config=EvalConfig(tasks_path=DATA_DIR/"tasks.jsonl",
        snapshots_dir=DATA_DIR/"snapshots",
        results_dir=root/"candidate-history-native-grade",
        submission_dir=root/"candidate-history-no-agent-submission",
        models=ModelRegistry(),sandbox="subprocess",wheels_dir=DATA_DIR/"wheels",
        timeout_seconds=300,verification_timeout_seconds=240,verbose=False)
    config.results_dir.mkdir(parents=True,exist_ok=True)
    config.submission_dir.mkdir(parents=True,exist_ok=True)
    evaluator=Evaluator(config)
    visible={t.instance_id:t for t in load_tasks(DATA_DIR/"tasks.jsonl")}
    output=[]
    for task_id,expected_repo in TASKS:
        result={"task":task_id,"eligible":False,"error_type":None,
                "history_complete":False,"candidate_revisions_observed":None}
        try:
            task=evaluator._hydrate_task_from_secret(visible[task_id])
            if task.repo!=expected_repo or not (task.test_patch or task.FAIL_TO_PASS or task.PASS_TO_PASS):
                raise ValueError("task_hydration_or_tests_invalid")
            snapshot,base,delta=resolve_task_snapshot_paths(config.snapshots_dir,task_id,task.repo)
            folder,events,revisions=load_history(task_id)
            chosen,attempts,final,all_observed=select_revisions(events,revisions)
            result["candidate_revisions_observed"]=all_observed
            result["candidate_revisions_graded"]=len(chosen)
            result["complete_candidate_coverage"]=len(chosen)==all_observed
            result["history_complete"]=True
            noop,_=await eval_native(task,snapshot,base,delta,evaluator,"")
            if not isinstance(task.patch,str):
                raise RuntimeError("gold_reference_missing")
            gold,_=await eval_native(task,snapshot,base,delta,evaluator,task.patch)
            result["noop_resolved"]=noop
            result["gold_resolved"]=gold
            if noop or not gold:
                result["error_type"]="noninformative_gold_noop_controls"
                output.append(result)
                continue
            result["eligible"]=True
            grades={}
            for digest in chosen:
                patch_path=folder/(digest+".patch")
                patch=patch_path.read_bytes()
                if sha256(patch).hexdigest()!=digest or len(patch)!=revisions[digest]:
                    raise ValueError("model_candidate_patch_checksum_mismatch")
                try:
                    resolved,seconds=await eval_native(task,snapshot,base,delta,evaluator,patch.decode("utf-8"))
                    grades[digest]={"resolved":resolved,"seconds":seconds}
                except Exception as exc:
                    grades[digest]={"resolved":None,"error_type":type(exc).__name__}
            passing={d for d,v in grades.items() if v.get("resolved") is True}
            final_correct=final in passing if final in grades else None
            submit_correct=[a in passing if a in grades else None for a in attempts]
            result.update({
                "passing_candidates_graded":len(passing),
                "any_passing":bool(passing) if result["complete_candidate_coverage"] else None,
                "submit_attempt_count":len(attempts),
                "submitted_candidate_pass":submit_correct[0] if len(submit_correct)==1 else None,
                "final_candidate_pass":final_correct,
                "passing_candidate_lost_before_submission":(
                    bool(passing) and len(submit_correct)==1 and submit_correct[0] is False
                    if result["complete_candidate_coverage"] else None),
                "native_grader_errors":sum(v.get("resolved") is None for v in grades.values()),
                "candidate_grader_seconds":round(sum(v.get("seconds",0) for v in grades.values()),1),
            })
        except Exception as exc:
            result["error_type"]=type(exc).__name__
        output.append(result)
        print("GEMMA31_HISTORY_NATIVE_GRADE_SAFE="+json.dumps(result,sort_keys=True),flush=True)
    summary={"version":"gemma31-candidate-history-official-native-grade-v1",
             "tasks_requested":len(TASKS),"tasks_eligible":sum(x["eligible"] for x in output),
             "tasks_complete_revision_coverage":sum(x.get("complete_candidate_coverage") is True for x in output),
             "any_passing_eligible":sum(x.get("any_passing") is True for x in output),
             "submitted_passing_eligible":sum(x.get("submitted_candidate_pass") is True for x in output),
             "no_model_inference":True,"no_gpu":True,"no_competition_submission":True,
             "reports":output}
    (root/"gemma31-candidate-history-native-grade-safe.json").write_text(json.dumps(summary,indent=2,sort_keys=True))
    print("GEMMA31_HISTORY_NATIVE_GRADE_COMPLETE="+json.dumps(
        {k:summary[k] for k in summary if k!="reports"},sort_keys=True),flush=True)

def main():
    install_wheelhouse()
    asyncio.run(grade())

if __name__=="__main__":
    main()
