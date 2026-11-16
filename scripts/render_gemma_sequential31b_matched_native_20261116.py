#!/usr/bin/env python3
"""One 31B private public-development grader run: mandatory sequential verifier.

Uses same three frozen existing V2 31B issue IDs; no 31B baseline rerun.
No reference solutions, no new training, no Kaggle official submission.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path
import re

from scripts.build_gemma_sequential_native_verifier_v0_20261116 import (
    VERSION, MODEL, build_payload, build_zip,
)
from scripts.prepare_public_budgetfit_v2 import EXPECTED_ZIP_SHA256
from scripts.render_contract_impact_31b_pilot import replace_one, replace_section

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "experiments/solver-v3/pro-sequential31b-native-verifier-20261116.json"
OLD_PLAN = ROOT / "experiments/solver-v3/pro-v3r-vs-v2-fresh-paired-20261115.json"
TEMPLATE = ROOT / "kaggle/verifier_baseline_runtime.py"
KERNEL_FILE = "mandatory_sequential_31b_matched_runtime.py"
MODEL_SOURCE = f"google/gemma-4/Other/{MODEL}/2"
PINNED_CANDIDATE_SHA = "dd3b582cd6d97ef2314ffdef64738b06b302c6cc0234fb7513258858e38a2c0a"


def validate_contract(plan: dict, frozen: dict, source_zip: bytes) -> dict:
    if plan.get("version") != VERSION:
        raise ValueError("wrong_preregistered_sequential_experiment")
    if plan.get("candidate_zip_sha256") != PINNED_CANDIDATE_SHA:
        raise ValueError("preregistered_candidate_hash_drift")
    if plan.get("source_zip_sha256") != EXPECTED_ZIP_SHA256:
        raise ValueError("frozen_competitor_source_drift")
    if hashlib.sha256(source_zip).hexdigest() != EXPECTED_ZIP_SHA256:
        raise ValueError("actual_reference_zip_digest_drift")
    if hashlib.sha256(build_zip(source_zip)).hexdigest() != PINNED_CANDIDATE_SHA:
        raise ValueError("actual_two_stage_candidate_zip_digest_drift")
    if frozen.get("version") != "v3r-vs-v2-fresh-paired-20261115-v1":
        raise ValueError("wrong_old_control_trial")
    if frozen["selection"]["repo_prefixes"] != ["fastapi_", "rich_", "requests_"]:
        raise ValueError("old_control_task_strata_changed")
    if frozen["experiment"]["tasks"] != 3:
        raise ValueError("old_control_task_count_changed")
    if any(frozen["shared_budget"][k] != v for k, v in (
            ("max_time_minutes",5),("max_tool_calls",28),("max_turns",80))):
        raise ValueError("unfair_budget_vs_prior_control")
    return build_payload(source_zip)


def render_runtime(template: str, plan: dict, frozen: dict, source_zip: bytes) -> str:
    files=validate_contract(plan,frozen,source_zip)
    encoded=base64.b64encode(json.dumps(
        files,sort_keys=True,separators=(",",":")).encode()).decode()
    selection={"version":VERSION, "frozen_selection":frozen["selection"]}
    text=replace_one(template,"import json\n","import json\nimport hashlib\n",
                     "original salted task selection import")
    text=replace_one(text,'"__SUBMISSION_PAYLOAD_B64__"',repr(encoded),
                     "only this frozen 31B legal submission payload")
    text=replace_one(text,
          'HOLDOUT_MANIFEST_JSON = "__VERIFIER_LORA_HOLDOUT_MANIFEST_JSON__"',
          "HOLDOUT_MANIFEST_JSON = " + repr(json.dumps(selection,sort_keys=True)),
          "original frozen task selector")
    text=replace_one(text,'MODEL_NAME = "gemma-4-e4b-it-qat-w4a16-ct"',
                     f'MODEL_NAME = "{MODEL}"',"frozen 31B model")
    text=replace_one(text,'AGENT_DIR = WORKING_DIR / "submission"',
                     'AGENT_DIR = WORKING_DIR / "native-sequential31b"',
                     "isolated private candidate")
    text=replace_one(text,'RESULTS_DIR = WORKING_DIR / "verifier-baseline-results"',
                     'RESULTS_DIR = WORKING_DIR / "native-sequential31b-traces"',
                     "private trace directory")
    text=replace_one(text,
         'SUMMARY_PATH = WORKING_DIR / "verifier_baseline_results.json"',
         'SUMMARY_PATH = WORKING_DIR / "native_sequential31b_matched_results.json"',
         "private scored output")
    text=text.replace("verifier-lora-v0",VERSION)
    selector=f'''
def load_holdout_ids(public_tasks) -> list[str]:
    plan = json.loads(HOLDOUT_MANIFEST_JSON)
    if plan.get("version") != "{VERSION}":
        raise ValueError("wrong_sequential_31b_protocol")
    pick=plan["frozen_selection"]
    seen={{t.instance_id for t in public_tasks}}
    excluded=set(pick["exclude_instance_ids"])
    chosen=[]
    for prefix in pick["repo_prefixes"]:
        eligible=sorted(k for k in seen if k.startswith(prefix) and k not in excluded)
        if not eligible:
            raise ValueError("missing_original_pair_stratum")
        task_id=min(eligible,key=lambda k:(
           hashlib.sha256((pick["salt"]+"|"+k).encode()).hexdigest(),k))
        chosen.append(task_id)
    if len(chosen)!=3 or len(set(chosen))!=3:
        raise ValueError("not_exact_original_three_tasks")
    print("GEMMA_PRO_SEQUENTIAL_MATCHED_TASK_COUNT="+str(len(chosen)),flush=True)
    return chosen

'''
    text=replace_section(text,"def load_holdout_ids() -> list[str]:",
                         "def run_maybe_async(",selector,
                         "original hashed task selection restore")
    text=replace_one(text,"    holdout_ids = load_holdout_ids()\n","",
                    "defer selection until tasks hydrated")
    text=replace_one(text,"    public_tasks = load_tasks(tasks_path)\n",
                    "    public_tasks = load_tasks(tasks_path)\n"
                    "    holdout_ids = load_holdout_ids(public_tasks)\n",
                    "recompute same three tasks")
    text=replace_one(text,"E4B model weights not found:",
                     "31B model weights not found:","accurate error name")
    text=replace_one(text,
        '        print("BASELINE_RESULT", json.dumps(record, sort_keys=True), flush=True)',
        '        print("GEMMA_PRO_SEQUENTIAL_REAL_TASK_SAFE=" + json.dumps('
        '{k:v for k,v in record.items() if k not in ("instance_id","error")},'
        'sort_keys=True), flush=True)',
        "no raw task identity in public GH logs")
    text=replace_one(text,
        '            print(f"baseline error for {task_id}: {type(exc).__name__}: {exc}", flush=True)',
        '            print("GEMMA_PRO_SEQUENTIAL_TASK_ERROR_TYPE="+type(exc).__name__,flush=True)',
        "avoid task text/exception leak")
    text=replace_one(text,
        '            print(f"[{index:02d}/{len(holdout_ids):02d}] baseline {task_id}", flush=True)',
        '            print(f"GEMMA_PRO_SEQUENTIAL_TASK_NUMBER={index}/{len(holdout_ids)}",flush=True)',
        "avoid task identifier log")
    compile(text,KERNEL_FILE,"exec")
    if "__SUBMISSION_PAYLOAD_B64__" in text or "__VERIFIER_LORA_HOLDOUT_MANIFEST_JSON__" in text:
        raise ValueError("unrendered template placeholder")
    if text.count("GEMMA_PRO_SEQUENTIAL_MATCHED_TASK_COUNT")!=1:
        raise ValueError("frozen selection missing")
    if "competition_submit" in text:
        raise ValueError("unexpected new competition submission")
    if "--hf-overrides" in text:
        raise ValueError("31B control must not inherit 12B model override")
    return text


def render(repo:Path,source_zip:bytes,out:Path,kernel_ref:str)->dict:
    if not re.fullmatch(r"kolihhan/[a-z0-9-]{12,100}",kernel_ref):
        raise ValueError("unsafe private kernel id")
    if out.exists() and any(out.iterdir()):
        raise FileExistsError("refuse to overwrite existing kernel")
    plan=json.loads((repo/PLAN.relative_to(ROOT)).read_text())
    old=json.loads((repo/OLD_PLAN.relative_to(ROOT)).read_text())
    code=render_runtime((repo/TEMPLATE.relative_to(ROOT)).read_text(),
                        plan,old,source_zip)
    out.mkdir(parents=True,exist_ok=True)
    (out/KERNEL_FILE).write_text(code,encoding="utf-8")
    meta={
       "id":kernel_ref,"title":kernel_ref.split("/",1)[1],
       "code_file":KERNEL_FILE,"language":"python","kernel_type":"script",
       "is_private":True,"enable_gpu":True,"enable_tpu":False,
       "enable_internet":False,"machine_shape":"NvidiaL4",
       "docker_image":"gcr.io/kaggle-private-byod/python@sha256:37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461",
       "dataset_sources":["metric/gemma-4-developer-agent-wheelhouse"],
       "competition_sources":["gemma-4-developer-agent"],
       "kernel_sources":[],"model_sources":[MODEL_SOURCE],
    }
    (out/"kernel-metadata.json").write_text(json.dumps(meta,indent=2,sort_keys=True)+"\n")
    result={
       "model":MODEL,"candidate_zip_sha256":PINNED_CANDIDATE_SHA,
       "runtime_sha256":hashlib.sha256(code.encode()).hexdigest(),
       "original_frozen_same_task_reference":"31B V2 1/3, 62 calls, 604.94 sec",
       "new_private_tasks":3,"new_GPU_launch_by_renderer":False,
       "new_official_submission":False,"new_training":False,
    }
    print("GEMMA_PRO_SEQUENTIAL31B_NEW_PRIVATE_RUNTIME_RENDER="+json.dumps(
         result,sort_keys=True),flush=True)
    return result


def main()->None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--repo",type=Path,default=Path("."))
    parser.add_argument("--source-zip",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--kernel-ref",required=True)
    opt=parser.parse_args()
    render(opt.repo.resolve(),opt.source_zip.read_bytes(),opt.out.resolve(),
           opt.kernel_ref)


if __name__=="__main__":
    main()
