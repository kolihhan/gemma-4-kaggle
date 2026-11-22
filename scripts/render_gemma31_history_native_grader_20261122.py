"""Render CPU-only, private and separate 31B Candidate History native grader.

No model/adapter in this notebook; do not expose gold/task verifier to the solver.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

from scripts.render_gemma31_pair import IMAGE,DATASET

REF="kolihhan/gemma31-history-native-grade-2issues-20261122-v1"
SOLVER="kolihhan/gemma31-candidate-history-2issues-20261122-v1"

def render(out):
    original=Path("kaggle/paired_three_task_integrity_cpu.py").read_text()
    if original.count("\nasync def evaluate_controls()")!=1:
        raise ValueError("original scorer wheelhouse helper drift")
    prefix=original.split("\nasync def evaluate_controls()",1)[0]
    body=Path("kaggle/gemma31_candidate_history_grade_cpu_20261122.py").read_text()
    # The render includes two modules with top-level future imports.
    future="from __future__ import annotations\n"
    if body.count(future)!=1:
        raise ValueError("grader source future-import drift")
    body=body.replace(future,"",1)
    if body.count("TASKS=((")!=1 or "eval_native" not in body:
        raise ValueError("private grader source drift")
    code=prefix+"\n"+body
    compile(code,"experiment.py","exec")
    out.mkdir(parents=True,exist_ok=False)
    (out/"experiment.py").write_text(code)
    meta={
        "id":REF,"title":REF.split("/")[-1],"code_file":"experiment.py",
        "language":"python","kernel_type":"script","is_private":True,
        "enable_gpu":False,"enable_tpu":False,"enable_internet":False,
        "docker_image":IMAGE,
        "competition_sources":["gemma-4-developer-agent"],
        "dataset_sources":[DATASET],"kernel_sources":[SOLVER],"model_sources":[]
    }
    (out/"kernel-metadata.json").write_text(json.dumps(meta,sort_keys=True,indent=2))
    print("GEMMA31_NATIVE_HISTORY_GRADER_CPU_STATIC_COMPILED=TRUE")
    print("GEMMA31_NATIVE_HISTORY_GRADER_SOLVER_SOURCE="+SOLVER)
    print("GEMMA31_NATIVE_HISTORY_GRADER_NO_GPU_NO_COMPETITION_SUBMISSION=TRUE")

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    render(args.out)
