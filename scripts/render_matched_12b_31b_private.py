"""Render real private Gemma 4 V2 capacity benchmark, matched 12B vs 31B.

One Kaggle kernel declares one base model. Two separate private kernels evaluate
the SAME four previously gold-pass/no-op-fail public-development tasks with
identical V2 prompt/tools/sampling/5-minute agent policy. No competition submit.
The original source is pinned to a public Kaggle notebook hash. Gold reference
patches never enter agent prompts or output artifacts.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path
import re
import zipfile
import io

from scripts.build_matched_12b_31b_capacity import (
    ARMS, BASE_MODEL, SMALL_MODEL, candidate_files, archive,
)
from scripts.prepare_public_budgetfit_v2 import EXPECTED_ZIP_SHA256, validate_source_zip

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = "kaggle/verifier_baseline_runtime.py"
FROZEN = (
    ("fastapi_14458", "fastapi/fastapi"),
    ("fastapi_15589", "fastapi/fastapi"),
    ("rich_3894", "Textualize/rich"),
    ("rich_3905", "Textualize/rich"),
)
EXPECTED = {
    "v2_31b": "0dc7dc782a7be300388ab53937d53e9dfe9bd4679a82b21971557d846fc1778c",
    "v2_12b": "4e065d23011664459fbf8b64cbe6750f15ffb37f693198844f6d533fd3acf669",
}
D_IMAGE = "gcr.io/kaggle-private-byod/python@sha256:37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461"
FILENAME = "frozen_model_capacity_runtime.py"


def replace_exact(src: str, before: str, after: str) -> str:
    if src.count(before) != 1:
        raise ValueError("non-unique template anchor: " + before[:50])
    return src.replace(before, after, 1)


def manifest() -> dict:
    return {"version":"verifier-lora-v0",
            "experiment":"matched-v2-12b-31b-public-development-only",
            "holdout":[{"instance_id":i,"repo":r,"patch_bucket":"metadata-only"} for i,r in FROZEN]}


def render_runtime(template: str, source_zip: bytes, arm: str) -> str:
    if arm not in ARMS:
        raise ValueError("unexpected arm")
    original=validate_source_zip(source_zip)
    files=candidate_files(source_zip)[arm]
    if set(files)!=set(original):
        raise ValueError("member set drift")
    zip_data=archive(files)
    if hashlib.sha256(zip_data).hexdigest()!=EXPECTED[arm]:
        raise ValueError("frozen archive hash mismatch")
    model=ARMS[arm]
    # Exact equivalent V2 payload for each arm. Reuse official-task Evaluator
    # rather than writing a parallel simplified scorer.
    payload=base64.b64encode(json.dumps(files,sort_keys=True,
               separators=(",",":")).encode("utf-8")).decode("ascii")
    text=replace_exact(template, 'SUBMISSION_PAYLOAD_B64 = "__SUBMISSION_PAYLOAD_B64__"',
                       "SUBMISSION_PAYLOAD_B64 = "+repr(payload))
    text=replace_exact(text,'HOLDOUT_MANIFEST_JSON = "__VERIFIER_LORA_HOLDOUT_MANIFEST_JSON__"',
                       "HOLDOUT_MANIFEST_JSON = "+repr(json.dumps(manifest(),sort_keys=True)))
    text=replace_exact(text,'MODEL_NAME = "gemma-4-e4b-it-qat-w4a16-ct"',
                       'MODEL_NAME = '+repr(model))
    text=replace_exact(text,'AGENT_DIR = WORKING_DIR / "submission"',
                       'AGENT_DIR = WORKING_DIR / '+repr("capacity-"+arm))
    text=replace_exact(text,'RESULTS_DIR = WORKING_DIR / "verifier-baseline-results"',
                       'RESULTS_DIR = WORKING_DIR / '+repr("capacity-results-"+arm))
    text=replace_exact(text,'SUMMARY_PATH = WORKING_DIR / "verifier_baseline_results.json"',
                       'SUMMARY_PATH = WORKING_DIR / '+repr("capacity_"+arm+"_results.json"))
    text=replace_exact(text,"E4B model weights not found:","Capacity model weights not found:")
    # The 12B is a unified Gemma4 checkpoint. Kaggle staff documented an
    # architecture override for the vLLM text-only serving path; the 31B
    # already uses the native architecture and must remain byte-equivalent.
    # This changes runtime startup only, never the agent payload or scoring.
    extra_args = (
        "--hf-overrides",
        '{"architectures": ["Gemma4ForCausalLM"], "model_type": "gemma4"}',
    ) if arm == "v2_12b" else ()
    text=replace_exact(text, "                extra_args=(),",
                       "                extra_args="+repr(extra_args)+",")

    # Keep the only true user-facing evidence as the official scorer task
    # result. Do not reinterpret test exit=1 as semantic patch failure.
    compile(text,FILENAME,"exec")
    for token in ("__SUBMISSION_PAYLOAD_B64__","__VERIFIER_LORA_HOLDOUT_MANIFEST_JSON__"):
        if token in text:
            raise ValueError("template marker left unrendered")
    if text.count("Evaluator(eval_config)")!=1:
        raise ValueError("expected exactly one official evaluator")
    if "competition_submit_code" in text:
        raise ValueError("unexpected contest submit")
    return text


def render(repo: Path, source_zip: bytes, arm: str, out: Path, kernel_ref: str) -> dict:
    if not re.fullmatch(r"kolihhan/[a-z0-9-]{15,90}",kernel_ref):
        raise ValueError("private kernel ref invalid")
    if out.exists() and any(out.iterdir()):
        raise FileExistsError("refuse reusing rendered dir")
    text=render_runtime((repo/TEMPLATE).read_text(),source_zip,arm)
    out.mkdir(parents=True,exist_ok=True)
    (out/FILENAME).write_text(text,encoding="utf-8")
    meta={
        "id":kernel_ref,"title":kernel_ref.rsplit("/",1)[1],
        "code_file":FILENAME,"language":"python","kernel_type":"script",
        "is_private":True,"enable_gpu":True,"enable_tpu":False,"enable_internet":False,
        "machine_shape":"NvidiaL4","docker_image":D_IMAGE,
        "competition_sources":["gemma-4-developer-agent"],
        "dataset_sources":["metric/gemma-4-developer-agent-wheelhouse"],
        "model_sources":[f"google/gemma-4/Other/{ARMS[arm]}/2"],
        "kernel_sources":[],
    }
    (out/"kernel-metadata.json").write_text(json.dumps(meta,sort_keys=True,indent=2)+"\n")
    return {
        "arm":arm,"model":ARMS[arm],"kernel":kernel_ref,
        "source_zip_sha256":EXPECTED_ZIP_SHA256,
        "candidate_zip_sha256":EXPECTED[arm],"issue_count":len(FROZEN),
        "same_prompt_tools_sampling":True,"max_minutes":5,
        "max_tool_calls":28,"max_turns":80,
        "private":True,"internet":False,"new_official_submission":False,
    }


def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--repo",type=Path,default=ROOT)
    p.add_argument("--source-zip",type=Path,required=True)
    p.add_argument("--arm",choices=sorted(ARMS),required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--kernel-ref",required=True)
    a=p.parse_args()
    report=render(a.repo.resolve(),a.source_zip.read_bytes(),
                  a.arm,a.out.resolve(),a.kernel_ref)
    print("MATCHED_MODEL_CAPACITY_RENDER="+json.dumps(report,sort_keys=True))


if __name__=="__main__":
    main()
