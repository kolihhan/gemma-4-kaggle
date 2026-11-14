"""One private prospective 31B code-surface experiment versus the exact scored 0.180 agent.

Prespecified first two hash-ranked unseen public-dev FastAPI and Rich IDs per
repo. No post-hoc task substitution; gold-pass/no-op-fail preflight before any
model issue evaluation. Both arms identical except semantic-surface Skill +
minimal invocation instruction. No training or competition submission.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

from scripts.build_public_prompt_only_control_20261111 import make_zip
from scripts.build_toolcap60_timeout_recovery import build as build_champion, files_for_candidate
from scripts.build_semantic_surface_31b import candidate_files
from scripts.render_patch_checkpoint_31b import CHAMPION_SHA
from scripts.render_repro_first_31b import INTEGRITY
from scripts.render_public_prompt_vs_v2_paired_31b import render_pair
from scripts.render_v2_toolcap_31b_pilot import (
    MODEL, MODEL_SOURCE, TEMPLATE_PATH, replace_one, replace_section,
)
from scripts.render_earlyedit_v2_paired_31b import IMAGE

ROOT = Path(__file__).resolve().parents[1]
VERSION = "gemma-31b-semantic-surface-prospective-v0"
ARMS = ("champion", "semantic_surface")
RESULT = "semantic_surface_summary.json"
KERNEL_PREFIX = "kolihhan/gemma4-semantic-surface-"
SALT = "prospective-31b-semantic-surface-repair-20261114-v0"
# No refs/hints/feedback from these task IDs enter candidate prompts.
EXCLUDED = (
    "fastapi_11194", "rich_3935", "fastapi_14419", "rich_3470",
    "fastapi_15800", "rich_3518", "rich_4075", "fastapi_14492",
    "fastapi_14458", "fastapi_15589", "rich_3894", "rich_3905",
    "fastapi_14487", "rich_3782", "requests_7427",
    "requests_7328", "requests_103", "rich_3278",
    "fastapi_14448", "fastapi_14463", "rich_3061", "fastapi_14873",
    "rich_3934", "rich_4079", "rich_3105", "rich_3942",
    "fastapi_15280", "fastapi_9425",
)
COUNT_PER_REPO = 2


def select_ids(ids: list[str]) -> list[str]:
    exclude = set(EXCLUDED)
    output = []
    for prefix in ("fastapi_", "rich_"):
        candidates = sorted(x for x in set(ids) if x.startswith(prefix) and x not in exclude)
        chosen = sorted(candidates, key=lambda x: (
            hashlib.sha256((SALT + "|" + x).encode()).hexdigest(), x))[:COUNT_PER_REPO]
        if len(chosen) != COUNT_PER_REPO:
            raise ValueError("not enough unseen public-development issues")
        output.extend(chosen)
    if len(output) != 4 or len(set(output)) != 4:
        raise ValueError("source-selected denominator drift")
    return output


SURFACE_FEEDBACK = '''def observed_surface(trace):
    if trace is None:
        return {"trace_found": False, "skill_loads": None,
                "script_calls": None, "native_edit_calls": None}
    loads = scripts = edits = 0
    for event in trace.entries:
        if event.event_type != "tool_call":
            continue
        if event.tool_name == "load_skill":
            loads += 1
        elif event.tool_name == "run_skill_script":
            scripts += 1
        elif event.tool_name in ("edit_file", "write_file"):
            edits += 1
    return {"trace_found": True, "skill_loads": loads,
            "script_calls": scripts, "native_edit_calls": edits}
'''


def render(repo: Path, source_zip: bytes, out: Path, kernel_ref: str) -> None:
    if not re.fullmatch(r"kolihhan/gemma4-semantic-surface-[0-9]+", kernel_ref):
        raise ValueError("invalid one-shot private kernel reference")
    if out.exists():
        raise FileExistsError("refuse to overwrite")
    control = files_for_candidate(source_zip)
    treatment = candidate_files(source_zip)
    if hashlib.sha256(build_champion(source_zip)).hexdigest() != CHAMPION_SHA:
        raise ValueError("scored champion byte digest drift")
    if set(treatment) - set(control) != {
        "skills/semantic-surface/SKILL.md", "skills/semantic-surface/scripts/surface.py"
    }:
        raise ValueError("unexpected extra ability")
    if any(treatment[k] != control[k] for k in ("configs/sampling.yaml", "eval_config.yaml")):
        raise ValueError("changed budget or sampler")
    plan = {
        "version": VERSION, "arms": ARMS, "salt": SALT,
        "count_per_repo": COUNT_PER_REPO, "exclusions": list(EXCLUDED),
        "evaluation_count": 8, "source_is_public_dev": True,
    }
    runtime = render_pair((repo / TEMPLATE_PATH).read_text(),
                          control, treatment, plan)
    old = '''if not isinstance(files, dict) or set(files) != {
        "agent.yaml", "eval_config.yaml", "configs/sampling.yaml",
        "prompts/system.md",
    }:'''
    new = '''if not isinstance(files, dict) or set(files) != {
        "agent.yaml", "eval_config.yaml", "configs/sampling.yaml",
        "prompts/system.md", "skills/semantic-surface/SKILL.md",
        "skills/semantic-surface/scripts/surface.py",
    }:'''
    runtime = replace_one(runtime, old, new, "allow exact 2-file Skill payload")

    # Frozen population selection reads only public task IDs, never gold,
    # status, test patches or content. No changes after inference output.
    selector = (
        "def load_holdout_ids(public_tasks):\n"
        f"    ids = sorted({{task.instance_id for task in public_tasks}})\n"
        f"    excluded = set({EXCLUDED!r})\n"
        f"    salt = {SALT!r}\n"
        "    chosen = []\n"
        "    for prefix in ('fastapi_', 'rich_'):\n"
        "        candidates = sorted(x for x in ids if x.startswith(prefix) and x not in excluded)\n"
        "        ranked = sorted(candidates, key=lambda x: (hashlib.sha256((salt+'|'+x).encode()).hexdigest(), x))\n"
        "        chosen.extend(ranked[:2])\n"
        "    if len(chosen) != 4 or len(set(chosen)) != 4:\n"
        "        raise RuntimeError('missing frozen 4 task IDs')\n"
        "    print('SEMANTIC_SURFACE_FROZEN_SELECTED_PUBLIC_DEV_IDS='+json.dumps(chosen),flush=True)\n"
        "    return chosen\n\n"
        + INTEGRITY + "\n" + SURFACE_FEEDBACK
    )
    runtime = replace_section(runtime, "def load_holdout_ids(public_tasks) -> list[str]:",
                              "def run_maybe_async(", selector, "frozen unseen issues")

    # Before any model run, filter out invalid benchmark tasks as
    # fail-stop: no cherry-picked replacement once selected.
    preflight = (
        "            if not run_maybe_async(grade_integrity(evaluator, tasks_by_id[task_id])):\n"
        "                raise RuntimeError('STOP_GOLD_NOP_INTEGRITY_FAIL:'+task_id)\n"
        "            task_order = ("
    )
    runtime = replace_one(runtime, "            task_order = (", preflight, "gold/noop gate")
    runtime = replace_one(runtime, '"error_type": None,\n',
                          '"error_type": None, "surface": observed_surface(result.trace),\n',
                          "measure actual Skill invocation")
    runtime = replace_one(runtime, "if len(records) != 6:",
                          "if len(records) != 8:", "eight fixed model evaluations")
    runtime = replace_one(runtime, "if len(scored) != 3:",
                          "if len(scored) != 4:", "four fixed task denominator")
    runtime = replace_one(runtime, "if gpu_count < 1:", "if gpu_count != 4:",
                          "expected 4x L4")
    runtime = replace_one(runtime, "Kaggle baseline kernel has no visible GPU",
                          "31B semantic transfer needs four L4 GPUs", "GPU error")
    runtime = replace_one(runtime, '                "traceback": traceback.format_exc(),\n',
                          "", "remove private traceback from public log")
    runtime = replace_one(runtime, '                "error": str(exc),\n',
                          "", "no private error material")
    runtime = replace_one(runtime, "        write_failure(exc)\n        raise",
                          "        write_failure(exc)\n        raise RuntimeError(type(exc).__name__) from None",
                          "private fail-closed")
    runtime = (runtime.replace('"v2_5min"', repr(ARMS[0]))
                     .replace('"public_prompt_5min"', repr(ARMS[1]))
                     .replace("paired_prompt_v2_31b_results.json", RESULT)
                     .replace('"public-prompt-v2-paired-clean-v1"', repr(VERSION)))
    sha = hashlib.sha256(make_zip(treatment)).hexdigest()
    runtime = replace_one(runtime, '            "model": MODEL_NAME, "status": "completed",\n',
                          '            "model": MODEL_NAME, "status": "completed",\n'
                          f'            "treatment_zip_sha256": {sha!r},\n',
                          "pinned treatment digest")
    compile(runtime, "semantic_surface_private.py", "exec")
    for prohibited in ("competition_submit_code(", "task.test_patch", "agent_patch=truth.patch"):
        if prohibited == "competition_submit_code(" and prohibited in runtime:
            raise ValueError("unexpected Kaggle submission call")
    out.mkdir(parents=True, exist_ok=False)
    (out / "semantic_surface_private.py").write_text(runtime, encoding="utf-8")
    (out / "kernel-metadata.json").write_text(json.dumps({
        "id": kernel_ref, "title": kernel_ref.split("/", 1)[1],
        "code_file": "semantic_surface_private.py",
        "language": "python", "kernel_type": "script", "is_private": True,
        "enable_gpu": True, "enable_tpu": False, "enable_internet": False,
        "machine_shape": "NvidiaL4", "docker_image": IMAGE,
        "competition_sources": ["gemma-4-developer-agent"],
        "dataset_sources": ["metric/gemma-4-developer-agent-wheelhouse"],
        "model_sources": [MODEL_SOURCE], "kernel_sources": [],
    }, indent=2) + "\n")
    print("GEMMA_SEMANTIC_SURFACE_RENDER="+json.dumps({
        "version": VERSION, "task_count": 4, "evaluations": 8,
        "arms": ARMS, "champion_zip_sha256": CHAMPION_SHA,
        "treatment_zip_sha256": sha,
        "runtime_sha256": hashlib.sha256(runtime.encode()).hexdigest(),
        "GPU_inference_started": False, "official_submission": False},sort_keys=True),flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-zip", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--kernel-ref", required=True)
    args = parser.parse_args()
    render(ROOT, args.source_zip.read_bytes(), args.out, args.kernel_ref)
