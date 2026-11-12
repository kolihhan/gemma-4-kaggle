"""Regenerate the existing official no-model gold/noop integrity screen for the
four early-edit pilot issues at the current Kaggle scorer epoch.

This is independent verifier eligibility context, not model selection or a
rerun of any agent. It never exports gold/reference patch or test text.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re

from scripts import render_earlyedit_v2_paired_31b as study
from scripts.render_paired_three_task_integrity_cpu import CONTAINER

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "kaggle/paired_three_task_integrity_cpu.py"
FILENAME = "earlyedit_controls_cpu.py"
OUTPUT = "earlyedit_four_task_integrity_cpu.json"
BEFORE = '''TASKS = (
    ("fastapi_14487", "fastapi/fastapi"),
    ("rich_3782", "Textualize/rich"),
    ("requests_7427", "psf/requests"),
)'''
VERSION = "gemma4-earlyedit-four-current-scorer-controls-v1"


def build(repo: Path) -> str:
    plan = json.loads((repo / study.PLAN_FILE).read_text(encoding="utf-8"))
    study.validate_plan(plan)
    source = (repo / SOURCE).read_text(encoding="utf-8")
    if source.count(BEFORE) != 1:
        raise ValueError("gold/noop template no longer matches reviewed source")
    task_source = "TASKS = (\n" + "".join(
        "    (" + repr(t["instance_id"]) + ", " + repr(t["repo"]) + "),\n"
        for t in plan["tasks"]
    ) + ")"
    out = source.replace(BEFORE, task_source, 1)
    out = out.replace("paired_three_task_integrity_cpu.json", OUTPUT)
    out = out.replace("gemma4-paired-31b-three-task-integrity-v1", VERSION)
    out = out.replace('"original_31b_paired_run": 43057377220,',
                      '"independent_current_scorer_gold_noop_check": True,')
    if "agent_patch=patch" not in out:
        raise ValueError("official verifier path removed")
    if out.count(OUTPUT) != 1:
        raise ValueError("unexpected result output destination")
    for t in plan["tasks"]:
        if out.count("(" + repr(t["instance_id"]) + ", " + repr(t["repo"]) + ")") != 1:
            raise ValueError("frozen verifier cohort drift")
    if "competition_submit_code" in out or "VllmServer" in out:
        raise ValueError("unexpected inference/submit code")
    compile(out,FILENAME,"exec")
    return out


def render(repo: Path, out: Path, kernel_ref: str) -> dict:
    if not re.fullmatch(r"kolihhan/[a-z0-9-]{15,100}", kernel_ref):
        raise ValueError("invalid CPU-only kernel ref")
    if out.exists() and any(out.iterdir()):
        raise FileExistsError("refuse duplicate output")
    code = build(repo)
    out.mkdir(parents=True, exist_ok=True)
    (out / FILENAME).write_text(code, encoding="utf-8")
    meta = {
        "id": kernel_ref, "title": kernel_ref.rsplit("/",1)[1],
        "code_file": FILENAME, "language":"python", "kernel_type":"script",
        "is_private":True, "enable_gpu":False, "enable_tpu":False,
        "enable_internet":False, "docker_image":CONTAINER,
        "competition_sources":["gemma-4-developer-agent"],
        "dataset_sources":["metric/gemma-4-developer-agent-wheelhouse"],
        "model_sources":[], "kernel_sources":[],
    }
    (out / "kernel-metadata.json").write_text(json.dumps(meta,indent=2,sort_keys=True)+"\n")
    return {"version":VERSION,"task_count":4,"kernel":kernel_ref,
            "code_sha256":hashlib.sha256(code.encode()).hexdigest(),
            "no_gpu_inference_training_or_submission":True}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--repo",type=Path,default=ROOT)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--kernel-ref",required=True)
    a=p.parse_args()
    print("EARLYEDIT_CURRENT_CONTROLS_RENDER="+json.dumps(
        render(a.repo.resolve(),a.out.resolve(),a.kernel_ref),sort_keys=True))


if __name__=="__main__":
    main()
