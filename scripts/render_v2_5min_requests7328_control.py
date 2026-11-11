#!/usr/bin/env python3
"""Private 5-minute V2 control on the EXACT completed V5 diagnostic task.

This is deliberately POST-HOC, not an independent benchmark: the task is
requests_7328 because wrapped V5 already failed it. No claim of hidden
distribution improvement, no competition submission and no raw trace export.
"""
from __future__ import annotations
import argparse,base64,hashlib,json,re
from pathlib import Path
from scripts.prepare_public_budgetfit_v2 import validate_source_zip, EXPECTED_ZIP_SHA256
from scripts.render_contract_impact_31b_pilot import replace_one

MODEL="gemma-4-31b-it-qat-w4a16-ct"
KERNEL_FILE="v2_5min_requests7328_control_runtime.py"
TASK="requests_7328"
V5_COMPARATOR="kolihhan/gemma4-wrapped-uptake-42988852829"
MODEL_SOURCE="google/gemma-4/Other/gemma-4-31b-it-qat-w4a16-ct/2"
TEMPLATE_PATH="kaggle/verifier_baseline_runtime.py"
MANIFEST_PATH="experiments/v2-5min-requests7328-posthoc-control/manifest.json"


def control_files(source: bytes) -> dict[str,str]:
    baseline=validate_source_zip(source)
    config=baseline["eval_config.yaml"]
    if (config.count("max_time_minutes: 8")!=1 or
        config.count("max_tool_calls: 28")!=1 or
        config.count("max_turns: 80")!=1):
        raise ValueError("baseline resource contract not known")
    result=dict(baseline)
    result["eval_config.yaml"]=config.replace(
        "max_time_minutes: 8","max_time_minutes: 5",1)
    if set(result)!=set(baseline) or any(result[p]!=baseline[p] for p in result if p!="eval_config.yaml"):
        raise ValueError("V2 control modified beyond time cap")
    return result


def render_runtime(template: str, source: bytes, manifest: dict) -> str:
    if (manifest.get("version")!="v2-5min-requests7328-posthoc-v1" or
        manifest.get("task")!=TASK or
        manifest.get("max_time_minutes")!=5 or
        manifest.get("max_tool_calls")!=28 or
        manifest.get("max_turns")!=80 or
        manifest.get("evaluations")!=1 or
        manifest.get("comparator")!=V5_COMPARATOR):
        raise ValueError("posthoc diagnostic preregistration mismatch")
    files=control_files(source)
    payload=base64.b64encode(json.dumps(files,sort_keys=True,separators=(",",":")).encode()).decode()
    # Standard score evaluator's selector accepts a frozen single ID. No
    # reference patch is encoded in the model payload or public logs.
    holdout={"version":"verifier-lora-v0","holdout":[{"instance_id":TASK}]}
    code=replace_one(template,'"__SUBMISSION_PAYLOAD_B64__"',repr(payload),"V2 source")
    code=replace_one(code,
        'HOLDOUT_MANIFEST_JSON = "__VERIFIER_LORA_HOLDOUT_MANIFEST_JSON__"',
        "HOLDOUT_MANIFEST_JSON = "+repr(json.dumps(holdout,sort_keys=True)),
        "one-task selection")
    code=replace_one(code,
        'MODEL_NAME = "gemma-4-e4b-it-qat-w4a16-ct"',
        f'MODEL_NAME = "{MODEL}"',"31B model")
    code=replace_one(code,
        'AGENT_DIR = WORKING_DIR / "submission"',
        'AGENT_DIR = WORKING_DIR / "v2-5min-requests7328"', "agent dir")
    code=replace_one(code,
        'RESULTS_DIR = WORKING_DIR / "verifier-baseline-results"',
        'RESULTS_DIR = WORKING_DIR / "v2-5min-control-private-results"',"result dir")
    code=replace_one(code,
        'SUMMARY_PATH = WORKING_DIR / "verifier_baseline_results.json"',
        'SUMMARY_PATH = WORKING_DIR / "v2_5min_requests7328_results.json"',"summary file")
    code=replace_one(code,
        'E4B model weights not found:',
        '31B model weights not found:',"weight error")
    compile(code,KERNEL_FILE,"exec")
    if "__SUBMISSION_PAYLOAD_B64__" in code or "__VERIFIER_LORA_HOLDOUT_MANIFEST_JSON__" in code:
        raise ValueError("unrendered placeholders")
    if "max_time_minutes: 8" in files["eval_config.yaml"]:
        raise ValueError("8-minute control leaked into 5-minute test")
    return code


def render(repo: Path, source: bytes, output: Path, kernel_ref: str) -> dict:
    if not re.fullmatch(r"kolihhan/[a-z0-9-]+",kernel_ref):
        raise ValueError("unexpected private kernel identity")
    if output.exists() and any(output.iterdir()):
        raise FileExistsError("will not overwrite existing Notebook")
    if hashlib.sha256(source).hexdigest()!=EXPECTED_ZIP_SHA256:
        raise ValueError("unpinned control source")
    manifest=json.loads((repo/MANIFEST_PATH).read_text())
    runtime=render_runtime((repo/TEMPLATE_PATH).read_text(),source,manifest)
    output.mkdir(parents=True,exist_ok=True)
    (output/KERNEL_FILE).write_text(runtime)
    metadata={
        "id":kernel_ref,"title":kernel_ref.split("/",1)[1],
        "code_file":KERNEL_FILE,"language":"python","kernel_type":"script",
        "is_private":True,"enable_gpu":True,"enable_tpu":False,
        "enable_internet":False,"machine_shape":"NvidiaL4",
        "docker_image":"gcr.io/kaggle-private-byod/python@sha256:37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461",
        "dataset_sources":["metric/gemma-4-developer-agent-wheelhouse"],
        "competition_sources":["gemma-4-developer-agent"],
        "kernel_sources":[],"model_sources":[MODEL_SOURCE],
    }
    (output/"kernel-metadata.json").write_text(json.dumps(metadata,indent=2)+"\n")
    report={
        "model":MODEL,"task":TASK,"time_minutes":5,
        "max_tool_calls":28,"max_turns":80,
        "reference_zip_sha256":hashlib.sha256(source).hexdigest(),
        "control_config_sha256":hashlib.sha256(control_files(source)["eval_config.yaml"].encode()).hexdigest(),
        "manifest_sha256":hashlib.sha256((repo/MANIFEST_PATH).read_bytes()).hexdigest(),
        "evaluation_executed":False,"competition_submitted":False
    }
    print("V2_5MIN_POSTHOC_CONTROL_RENDER="+json.dumps(report,sort_keys=True),flush=True)
    return report


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-zip",type=Path,required=True)
    p.add_argument("--repo",type=Path,default=Path("."))
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--kernel-ref",required=True)
    a=p.parse_args()
    render(a.repo.resolve(),a.source_zip.read_bytes(),a.out.resolve(),a.kernel_ref)


if __name__=="__main__":
    main()
