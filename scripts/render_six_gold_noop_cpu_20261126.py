#!/usr/bin/env python3
"""Build a private CPU-only, real swegemma gold/noop control for six EXISTING issues.

IDs are loaded from an already completed private scorer result at build time.
No IDs, raw test output, patches, or issue text are committed or logged.
No agent/model inference, GPU, hidden oracle, or official Kaggle submission.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import textwrap

TEMPLATE = "kaggle/gold_control_sweep.py"
KERNEL = "kolihhan/gemma31-six-gold-noop-20261126-v1"

# The official Kaggle CPU runtime carries original gold-control wheelhouse
# installation and verification helpers; we replace the task selection,
# control execution, logging and outputs. In particular NO original
# 'main' is invoked (it can print task IDs or test snippets).
SAFE_RUNTIME = r"""
from swegemma.config import EvalConfig
from swegemma.models import load_tasks
from swegemma.evaluate import Evaluator
from swegemma.deduplication import resolve_task_snapshot_paths
from swegemma.harness.verification import verify_task
from adk_submission import ModelRegistry

SELECTED_IDS = __SELECTED_IDS__
RESULT_PATH = Path("/kaggle/working/gemma31_six_gold_noop_safe.json")

async def run_six_safe():
    original = {task.instance_id: task for task in load_tasks(DATA_DIR / "tasks.jsonl")
                if task.instance_id in SELECTED_IDS}
    if set(original) != set(SELECTED_IDS):
        raise RuntimeError("public dev task missing")
    results = WORKING_DIR / "gemma31-six-gold-noop-results"
    empty = WORKING_DIR / "gemma31-six-gold-noop-empty"
    results.mkdir(parents=True,exist_ok=True)
    empty.mkdir(parents=True,exist_ok=True)
    config=EvalConfig(tasks_path=DATA_DIR/"tasks.jsonl",snapshots_dir=DATA_DIR/"snapshots",
        results_dir=results,submission_dir=empty,models=ModelRegistry(),
        sandbox="subprocess",wheels_dir=DATA_DIR/"wheels",
        timeout_seconds=240,verification_timeout_seconds=180,verbose=False)
    evaluator=Evaluator(config)
    rows=[]
    for ordinal,task_id in enumerate(SELECTED_IDS,1):
        record={"ordinal":ordinal,"gold_pass":None,"noop_pass":None,
                "gold_error_type":None,"noop_error_type":None}
        try:
            task=evaluator._hydrate_task_from_secret(original[task_id])
            if task.instance_id!=task_id or not task.patch or not task.patch.strip():
                raise RuntimeError("task hydration mismatch")
            snapshot,base,patch_path=resolve_task_snapshot_paths(
                DATA_DIR/"snapshots",task.instance_id,task.repo)
            for kind,patch in (("gold",task.patch),("noop","")):
                try:
                    v=await verify_task(evaluator.docker, evaluator.config, task,
                        snapshot,base_snapshot_path=base,patch_path=patch_path,
                        agent_patch=patch,agent_error=None,trace=None,
                        start_time=time.perf_counter())
                    record[kind+"_pass"]=bool(v.resolved)
                    record[kind+"_error_type"]=(
                        None if not v.error else
                        "verification_error" if v.test_exit_code is None
                        else "test_or_patch_failure")
                except BaseException as e:
                    record[kind+"_error_type"]=type(e).__name__
        except BaseException as e:
            record["gold_error_type"]="SETUP_"+type(e).__name__
            record["noop_error_type"]="SETUP_"+type(e).__name__
        rows.append(record)
        print("PRIVATE_CONTROL_PROGRESS="+str(ordinal)+"/"+str(len(SELECTED_IDS)),flush=True)
    complete=[x for x in rows if type(x["gold_pass"]) is bool and type(x["noop_pass"]) is bool]
    safe={"version":"gemma31-six-private-current-wheelhouse-gold-noop-v1",
          "tasks":len(rows),"control_pairs_completed":len(complete),
          "gold_pass":sum(x["gold_pass"] is True for x in complete),
          "noop_pass":sum(x["noop_pass"] is True for x in complete),
          "discriminating":sum(x["gold_pass"] is True and x["noop_pass"] is False for x in complete),
          "non_discriminating":sum(x["gold_pass"] is False or x["noop_pass"] is True for x in complete),
          "unknown":len(rows)-len(complete),
          "rows":rows,"official_hidden_scorer_equivalence_claimed":False,
          "private_source_material_exported":False,"gpu":False,
          "model_inference":False,"competition_submission":False}
    return safe

def main_safe():
    WORKING_DIR.mkdir(parents=True,exist_ok=True)
    install_official_wheelhouse()
    report=asyncio.run(run_six_safe())
    RESULT_PATH.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print("REAL_GOLD_NOOP_CPU_SAFE="+json.dumps(
        {k:v for k,v in report.items() if k!="rows"},sort_keys=True),flush=True)

if __name__ == "__main__":
    try:
        main_safe()
    except BaseException as exc:
        RESULT_PATH.write_text(json.dumps({
          "status":"error","error_type":type(exc).__name__,
          "private_source_material_exported":False},sort_keys=True)+"\n")
        print("GOLD_NOOP_CPU_BLOCKER="+type(exc).__name__,flush=True)
        raise RuntimeError("PRIVATE_GOLD_NOOP_CONTROL_FAILED") from None
"""


def render(repo: Path, private_results: Path, out: Path) -> dict:
    data=json.loads(private_results.read_text())
    rows=data.get("results")
    if data.get("status")!="completed" or not isinstance(rows,list) or len(rows)!=12:
        raise ValueError("only completed real six-task scorer cohort supported")
    arms={"fastpath_4min","single_edit_4min"}
    ids=sorted({r.get("instance_id") for r in rows})
    if len(ids)!=6 or {(r.get("instance_id"),r.get("arm")) for r in rows} != {
            (i,a) for i in ids for a in arms}:
        raise ValueError("cohort identities are not paired")
    import re
    if any(not isinstance(i,str) or not re.fullmatch(r"(fastapi|rich|requests)_[0-9]+",i) for i in ids):
        raise ValueError("unexpected task kind")
    src=(repo/TEMPLATE).read_text()
    needle='if __name__ == "__main__":'
    if src.count(needle)!=1 or "async def run_sweep" not in src:
        raise ValueError("current gold control template changed")
    # Keep verified wheelhouse install helper, but never execute old main.
    original=src.split(needle,1)[0]
    safe=SAFE_RUNTIME.replace("__SELECTED_IDS__",repr(ids))
    runtime=original+"\n"+safe
    compile(runtime,"private_six_gold_noop.py","exec")
    # Don't expose IDs except in private output consumed by Kaggle.
    assert "competition_submit_code" not in runtime
    assert "from swegemma.harness.verification import verify_task" in runtime
    out.mkdir(parents=True,exist_ok=False)
    (out/"main.py").write_text(runtime)
    meta={"id":KERNEL,"title":KERNEL.split("/")[1],"code_file":"main.py",
          "language":"python","kernel_type":"script","is_private":True,
          "enable_gpu":False,"enable_tpu":False,"enable_internet":False,
          "docker_image":"gcr.io/kaggle-private-byod/python@sha256:37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461",
          "competition_sources":["gemma-4-developer-agent"],
          "dataset_sources":["metric/gemma-4-developer-agent-wheelhouse"],
          "model_sources":[],"kernel_sources":[]}
    (out/"kernel-metadata.json").write_text(json.dumps(meta,sort_keys=True,indent=2)+"\n")
    return {"selected_existing_tasks":len(ids),"verification_invocations_planned":2*len(ids),
            "private":True,"cpu_only":True,"model_inference":False,
            "official_submission":False,"raw_ids_exported":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--private-results",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    x=p.parse_args()
    print("SIX_GOLD_NOOP_CPU_RENDER_SAFE="+json.dumps(render(
        Path("."),x.private_results,x.out),sort_keys=True),flush=True)
if __name__=="__main__":
    main()
