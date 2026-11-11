#!/usr/bin/env python3
"""Render a ONE-task private 31B adoption probe, not an official submission.

This observes actual Gemma 31B invocation of the nested AgentTool. It does
not by itself estimate improvement against V2 and publishes NO raw traces.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path
import re

from scripts.build_wrapped_scope_coder_candidate import files as wrapped_files
from scripts.prepare_public_budgetfit_v2 import validate_source_zip
from scripts.render_contract_impact_31b_pilot import replace_one, replace_section

MODEL = "gemma-4-31b-it-qat-w4a16-ct"
SOURCE_SHA256 = "a4b10f6b8034fd7fffa144a7ee3fbd8faf9a84503ffb1349d1522ba048b534d3"
CANDIDATE_SHA256 = "25a656d65d580d3ed1bf4c54ab5a622a05afe231f1dd46fb2d861749fd08a1bd"
MANIFEST_PATH = "experiments/wrapped-scope-31b-adoption-v1/manifest.json"
TEMPLATE_PATH = "kaggle/verifier_baseline_runtime.py"
KERNEL_FILE = "wrapped_scope_31b_adoption_runtime.py"
MODEL_SOURCE = f"google/gemma-4/Other/{MODEL}/2"


def validate_manifest(plan: dict) -> None:
    if plan.get("version") != "wrapped-scope-31b-adoption-v1":
        raise ValueError("manifest version drift")
    if plan.get("task_repositories") != ["requests"]:
        raise ValueError("repository not frozen")
    if plan.get("selected_tasks") != 1 or plan.get("maximum_model_evaluations") != 1:
        raise ValueError("must be one model task")
    salt = plan.get("salt","")
    if not isinstance(salt,str) or not re.fullmatch(r"[a-zA-Z0-9-]{18,100}",salt):
        raise ValueError("salt missing")
    excluded = plan.get("exclude_instance_ids")
    if not isinstance(excluded,list) or len(excluded)!=len(set(excluded)):
        raise ValueError("exclusion list corrupted")
    if plan.get("agent") != "wrapped_scope_coder" or plan.get("budget_minutes") != 5:
        raise ValueError("agent or budget drift")


def render_runtime(template: str, source_zip: bytes, plan: dict) -> str:
    validate_manifest(plan)
    validate_source_zip(source_zip)
    treatment = wrapped_files(source_zip)
    if treatment["eval_config.yaml"].count("max_time_minutes: 5") != 1:
        raise ValueError("unexpected candidate 5min budget")
    if treatment["eval_config.yaml"].count("max_tool_calls: 28") != 1:
        raise ValueError("unexpected 28 tool calls")
    if treatment["eval_config.yaml"].count("max_turns: 80") != 1:
        raise ValueError("unexpected 80 turns")
    if not all(n in treatment for n in
               ("workflow.yaml","sub_agents/scope.yaml",
                "sub_agents/coder.yaml","prompts/orchestrator.md")):
        raise ValueError("missing mandatory inner workflow")

    payload=base64.b64encode(json.dumps(
        treatment,sort_keys=True,separators=(",",":")
    ).encode("utf-8")).decode("ascii")
    text=replace_one(template, '"__SUBMISSION_PAYLOAD_B64__"',
                     repr(payload),"agent payload")
    text=replace_one(text,
                     'HOLDOUT_MANIFEST_JSON = "__VERIFIER_LORA_HOLDOUT_MANIFEST_JSON__"',
                     "HOLDOUT_MANIFEST_JSON = "+repr(json.dumps(plan,sort_keys=True)),
                     "manifest payload")
    text=replace_one(text,'MODEL_NAME = "gemma-4-e4b-it-qat-w4a16-ct"',
                     f'MODEL_NAME = "{MODEL}"',"model")
    text=replace_one(text,
                     'AGENT_DIR = WORKING_DIR / "submission"',
                     'AGENT_DIR = WORKING_DIR / "submission-wrapped-adoption"',
                     "submission root")
    text=replace_one(text,
                     'RESULTS_DIR = WORKING_DIR / "verifier-baseline-results"',
                     'RESULTS_DIR = WORKING_DIR / "wrapped-adoption-private-results"',
                     "private results root")
    text=replace_one(text,
                     'SUMMARY_PATH = WORKING_DIR / "verifier_baseline_results.json"',
                     'SUMMARY_PATH = WORKING_DIR / "wrapped_scope_31b_adoption_results.json"',
                     "summary file")

    selector = '''def load_holdout_ids(public_tasks) -> list[str]:
    import hashlib
    plan=json.loads(HOLDOUT_MANIFEST_JSON)
    if plan["version"]!="wrapped-scope-31b-adoption-v1":
        raise ValueError("bad frozen version")
    excluded=set(plan["exclude_instance_ids"])
    pool=sorted({
        t.instance_id for t in public_tasks
        if t.instance_id.startswith("requests_") and
           t.instance_id not in excluded
    })
    if len(pool)<1:
        raise ValueError("no uninspected requests task available")
    ranked=sorted(pool,key=lambda name:(
        hashlib.sha256((plan["salt"]+"|"+name).encode()).hexdigest(),name))
    chosen=ranked[:1]
    print("WRAPPED_ADOPTION_SELECTED_IDS",json.dumps(chosen),flush=True)
    return chosen
'''
    text=replace_section(text,"def load_holdout_ids() -> list[str]:",
                         "def run_maybe_async(",selector,"task selector")
    text=replace_one(text,"    holdout_ids = load_holdout_ids()\n","",
                     "selector after data hydration")
    text=replace_one(text,
                     '    public_tasks = load_tasks(tasks_path)\n'
                     '    tasks_by_id = {task.instance_id: task for task in public_tasks if task.instance_id in set(holdout_ids)}',
                     '    public_tasks = load_tasks(tasks_path)\n'
                     '    holdout_ids = load_holdout_ids(public_tasks)\n'
                     '    tasks_by_id = {task.instance_id: task for task in public_tasks if task.instance_id in set(holdout_ids)}',
                     "late task hydration")
    text=replace_one(text,"E4B model weights not found:",
                     "31B model weights not found:","weight error")

    # The observer patches ONLY the existing official ADK AgentTool.run_async.
    # It counts actual model-driven tool invocations without reading/logging
    # task content, reference patches, prompts, tool args or private traces.
    # Instrumentation is outside the Agent ZIP and competition submission.
    observer = '''        from google.adk.tools.agent_tool import AgentTool
        from time import perf_counter
        observed={"calls":0,"returns":0,"errors":0,"seconds":0.0}
        native_agenttool_run=AgentTool.run_async

        async def recorded_agenttool_run(self, *, args, tool_context):
            if self.name != "mandatory_scope_then_patch":
                return await native_agenttool_run(
                    self,args=args,tool_context=tool_context)
            observed["calls"]+=1
            start=perf_counter()
            try:
                value=await native_agenttool_run(
                    self,args=args,tool_context=tool_context)
                observed["returns"]+=1
                return value
            except BaseException:
                observed["errors"]+=1
                raise
            finally:
                observed["seconds"]+=perf_counter()-start

        AgentTool.run_async=recorded_agenttool_run
        records: list[dict[str, object]] = []
'''
    text=replace_one(text,
                     '        records: list[dict[str, object]] = []',
                     observer.rstrip(),"exact typed AgentTool observer")
    text=replace_one(text,
                     '            records.append(record)\n'
                     '            print("BASELINE_RESULT", json.dumps(record, sort_keys=True), flush=True)',
                     '            record["agenttool_calls"]=observed["calls"]\n'
                     '            record["agenttool_returns"]=observed["returns"]\n'
                     '            record["agenttool_errors"]=observed["errors"]\n'
                     '            record["agenttool_seconds"]=round(observed["seconds"],3)\n'
                     '            records.append(record)\n'
                     '            print("REAL_31B_AGENTTOOL_UPTAKE",json.dumps({'
                     '"task_id":task_id,'
                     '"called":observed["calls"],'
                     '"returned":observed["returns"],'
                     '"errors":observed["errors"],'
                     '"tool_seconds":round(observed["seconds"],3),'
                     '"resolved":record.get("resolved",False),'
                     '"has_patch":record.get("has_patch",False),'
                     '"total_tool_calls":record.get("tool_calls"),'
                     '"total_seconds":record.get("duration_seconds"),'
                     '},sort_keys=True),flush=True)',
                     "single-task adoption result")
    text=text.replace('"version": "verifier-lora-v0"',
                      '"version": "wrapped-scope-31b-adoption-v1"')
    compile(text,KERNEL_FILE,"exec")
    if '"__SUBMISSION_PAYLOAD_B64__"' in text or '"__VERIFIER_LORA_HOLDOUT_MANIFEST_JSON__"' in text:
        raise ValueError("unrendered placeholders")
    if "AgentTool.run_async=recorded_agenttool_run" not in text:
        raise ValueError("missing actual AgentTool observer")
    return text


def render(repo: Path, source_zip: bytes, output: Path, kernel_ref: str) -> dict:
    if not re.fullmatch(r"kolihhan/[a-z0-9-]+",kernel_ref):
        raise ValueError("private kernel id mismatch")
    if output.exists() and any(output.iterdir()):
        raise FileExistsError("will not overwrite an existing kernel")
    source_hash=hashlib.sha256(source_zip).hexdigest()
    if source_hash!=SOURCE_SHA256:
        raise ValueError("external V2 reference ZIP has changed")
    plan=json.loads((repo/MANIFEST_PATH).read_text())
    template=(repo/TEMPLATE_PATH).read_text()
    source=render_runtime(template,source_zip,plan)
    import zipfile,io
    with zipfile.ZipFile(io.BytesIO(source_zip)) as z:
        if z.testzip() is not None:raise ValueError("source ZIP CRC invalid")
    from scripts.build_wrapped_scope_coder_candidate import build as build_candidate
    actual_candidate_hash=hashlib.sha256(build_candidate(source_zip)).hexdigest()
    if actual_candidate_hash!=CANDIDATE_SHA256:
        raise ValueError("experiment agent ZIP changed since scripted CPU gate")

    output.mkdir(parents=True,exist_ok=True)
    (output/KERNEL_FILE).write_text(source)
    meta={
        "id":kernel_ref,"title":kernel_ref.split("/",1)[1],
        "code_file":KERNEL_FILE,"language":"python",
        "kernel_type":"script","is_private":True,
        "enable_gpu":True,"enable_tpu":False,
        "enable_internet":False,"machine_shape":"NvidiaL4",
        "docker_image":"gcr.io/kaggle-private-byod/python@sha256:37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461",
        "dataset_sources":["metric/gemma-4-developer-agent-wheelhouse"],
        "competition_sources":["gemma-4-developer-agent"],
        "kernel_sources":[],"model_sources":[MODEL_SOURCE],
    }
    (output/"kernel-metadata.json").write_text(json.dumps(meta,indent=2)+"\n")
    note={"status":"private_cpu_renderer_only","candidate_sha256":actual_candidate_hash,
          "source_sha256":source_hash,"manifest_sha256":hashlib.sha256(
              (repo/MANIFEST_PATH).read_bytes()).hexdigest(),
          "gpu_inference_executed":False,"competition_submission_created":False}
    print("WRAPPED_ADOPTION_RENDER",json.dumps(note,sort_keys=True),flush=True)
    return note


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--repo",type=Path,default=Path("."))
    p.add_argument("--source-zip",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--kernel-ref",required=True)
    o=p.parse_args()
    render(o.repo.resolve(),o.source_zip.read_bytes(),o.out.resolve(),o.kernel_ref)


if __name__=="__main__":
    main()
