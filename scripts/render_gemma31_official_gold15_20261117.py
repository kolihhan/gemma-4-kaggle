"""Current-scorer gold verification for EXACTLY the 15 official-dev tasks
among the frozen 31-case Gemma pilot; the other 16 are EXTERNAL Click cases.

CPU-only private Kaggle kernel. No solver, GPU, paid service, hidden task
export, or official competition submission.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MEMBERSHIP="docs/evaluation/gemma-31-matched-validation-membership-2026-11-17.json"
PREVIOUS="docs/evaluation/discriminating-evidence-v0-gold-screen-2026-11-06.json"
TEMPLATE="kaggle/gold_control_sweep.py"
D_IMAGE="gcr.io/kaggle-private-byod/python@sha256:37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461"

def render(repo:Path,out:Path,ref:str)->dict:
    import runpy
    m=json.loads((repo/MEMBERSHIP).read_text())
    prev=json.loads((repo/PREVIOUS).read_text())
    cases=m["cases"]
    assert len(cases)==31
    ids=[c["instance_id"] for c in cases]
    assert len(set(ids))==31
    official=[c for c in cases if c["source"]=="official_development"]
    external=[c for c in cases if c["source"]=="original_upstream_issue"]
    if len(official)!=15 or len(external)!=16:
        raise ValueError("FROZEN_31_OFFICIAL_EXTERNAL_DENOMINATOR_DRIFT")
    by_old={r["instance_id"]:r for r in prev["results"]}
    if any(by_old.get(c["instance_id"],{}).get("gold_pass") is not True for c in official):
        raise ValueError("OFFICIAL_15_PREVIOUS_GOLD_SCREEN_NOT_ALL_PASS")
    if not ref.startswith("kolihhan/gemma31-official-gold15-cpu-"):
        raise ValueError("UNSAFE_KERNEL_ID")
    if out.exists():
        raise FileExistsError("REFUSE_EXISTING_KERNEL_DIR")
    runtime=runpy.run_path(str(repo/TEMPLATE))
    manifest={
        "version":"verifier-lora-v0",
        "experiment":"gemma31-official-dev-gold15-current-scorer-cpu",
        "holdout":[{"instance_id":c["instance_id"],"repo":c["repo"],
                   "patch_bucket":"official_gold_reference"} for c in official],
    }
    txt=runtime["render_kernel_source"]((repo/TEMPLATE).read_text(),
                                       json.dumps(manifest,sort_keys=True))
    compile(txt,"gold_control_sweep.py","exec")
    out.mkdir(parents=True)
    (out/"gold_control_sweep.py").write_text(txt)
    metadata={
        "id":ref,"title":ref.split("/")[1],"code_file":"gold_control_sweep.py",
        "language":"python","kernel_type":"script",
        "is_private":True,"enable_gpu":False,"enable_tpu":False,"enable_internet":False,
        "docker_image":D_IMAGE,
        "competition_sources":["gemma-4-developer-agent"],
        "dataset_sources":["metric/gemma-4-developer-agent-wheelhouse"],
        "model_sources":[],"kernel_sources":[],
    }
    (out/"kernel-metadata.json").write_text(json.dumps(metadata,indent=2,sort_keys=True)+"\n")
    return {
        "frozen_cases":31,"official_dev_verifiable":15,"external_click_needs_separate_oracle":16,
        "previous_official_gold_pass":15,"current_gold_status":"UNRUN",
        "cpu_only":True,"model_inference":False,"competition_submission":False,
        "generated_runtime_sha256":hashlib.sha256(txt.encode()).hexdigest(),
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--repo",type=Path,default=ROOT)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--kernel-ref",required=True)
    a=p.parse_args()
    print("GEMMA31_CURRENT_GOLD15_RENDER="+json.dumps(
        render(a.repo.resolve(),a.out.resolve(),a.kernel_ref),sort_keys=True),flush=True)
if __name__=="__main__":
    main()
