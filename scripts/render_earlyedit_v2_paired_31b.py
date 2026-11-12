"""Generate a matched 31B early-edit vs pinned V2 Kaggle-private pilot.

Reuses the already real-model-tested paired evaluator renderer, preserving
the official scorer and two isolated evaluators. The only agent-level change
is an appended system-prompt policy. No training or competition submission.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from unittest.mock import patch

from scripts import render_public_prompt_vs_v2_paired_31b as previous
from scripts.build_public_prompt_only_control_20261111 import make_zip
from scripts.prepare_public_budgetfit_v2 import EXPECTED_ZIP_SHA256, validate_source_zip
from scripts.render_contract_impact_31b_pilot import replace_one, replace_section

ROOT = Path(__file__).resolve().parents[1]
PLAN_FILE = "experiments/31b-earlyedit-v2-paired-20261112/manifest.json"
MODEL = "gemma-4-31b-it-qat-w4a16-ct"
SCRIPT_NAME = "earlyedit_v2_31b_runtime.py"
RESULT_NAME = "earlyedit_v2_31b_results.json"
IMAGE = "gcr.io/kaggle-private-byod/python@sha256:37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461"

POLICY = """
## Time-aware repair and feedback policy
Use the existing native tools and solve the actual issue, not an imagined test.
- First identify a concrete failing behavior and likely edit location. Use
  targeted evidence: issue symbols, a relevant file, and at most one narrow
  repository search. Stop repeating broad searches without a new hypothesis.
- By around tool call 8, decide if evidence is sufficient for a minimal edit.
  If sufficient, prefer to create the first real source edit by call 10
  rather than browsing until the time limit. Never fabricate or guess a fix
  just to meet this target; a necessary focused diagnostic takes priority.
- After your first edit, prioritize one relevant focused test or reproduction.
  Read the actual outcome, and make one evidence-driven revision on failure.
  If tests are unavailable, inspect the final diff and run the narrowest
  available static check. Never claim an unrun check passed.
- At around tool call 20, stop opening new search branches. Preserve time
  for checking the actual diff, correcting mistakes, and leaving a valid patch.
- A correct minimal patch beats a large unverified patch. Never change code
  that the issue cannot justify.
""".strip()


def validate_plan(plan: dict) -> list[str]:
    if plan.get("version") != "earlyedit-v2-paired-clean-v1":
        raise ValueError("early-edit manifest version changed")
    if plan.get("control_source_zip_sha256") != EXPECTED_ZIP_SHA256:
        raise ValueError("baseline source drift")
    if plan.get("model") != MODEL or plan.get("arms") != ["v2_5min", "early_edit_5min"]:
        raise ValueError("model/arm drift")
    if plan.get("budget") != {
        "max_time_minutes": 5, "max_tool_calls": 28,
        "max_turns": 80, "timeout_seconds": 240
    }:
        raise ValueError("unfair budget drift")
    tasks = plan.get("tasks")
    expected = [
        ("fastapi_14301", "fastapi/fastapi"),
        ("rich_3063", "Textualize/rich"),
        ("fastapi_14794", "fastapi/fastapi"),
        ("rich_3676", "Textualize/rich"),
    ]
    if (not isinstance(tasks, list) or
        [(t.get("instance_id"), t.get("repo")) for t in tasks] != expected):
        raise ValueError("frozen four task IDs drift")
    if not plan.get("no_training") or not plan.get("no_official_competition_submission"):
        raise ValueError("safety guard drift")
    return [task_id for task_id, _repo in expected]


def candidate_files(source_zip: bytes) -> tuple[dict[str, str], dict[str, str]]:
    base = validate_source_zip(source_zip)
    if hashlib.sha256(source_zip).hexdigest() != EXPECTED_ZIP_SHA256:
        raise ValueError("not byte-pinned Budget-Fit V2 source")
    original_config = base["eval_config.yaml"]
    if (original_config.count("max_time_minutes: 8") != 1 or
        original_config.count("max_tool_calls: 28") != 1 or
        original_config.count("max_turns: 80") != 1):
        raise ValueError("unrecognized control budget")
    control = dict(base)
    control["eval_config.yaml"] = original_config.replace(
        "max_time_minutes: 8", "max_time_minutes: 5")
    treatment = dict(control)
    if POLICY in base["prompts/system.md"]:
        raise ValueError("treatment policy already exists in control")
    treatment["prompts/system.md"] = base["prompts/system.md"].rstrip() + "\n\n" + POLICY + "\n"
    if set(control) != set(treatment):
        raise ValueError("file inventory drift")
    for path in control:
        if path != "prompts/system.md" and control[path] != treatment[path]:
            raise ValueError("nonprompt content drift")
    return control, treatment


def replace_line_starting(text: str, prefix: str, replacement: str) -> str:
    matches = [line for line in text.splitlines(keepends=True)
               if line.startswith(prefix)]
    if len(matches) != 1:
        raise ValueError("expected unique runtime manifest assignment")
    return text.replace(matches[0], replacement + "\n", 1)


def generate(repo: Path, source_zip: bytes) -> tuple[str, dict]:
    plan = json.loads((repo / PLAN_FILE).read_text(encoding="utf-8"))
    ids = validate_plan(plan)
    control, treatment = candidate_files(source_zip)
    control_sha = hashlib.sha256(make_zip(control)).hexdigest()
    treatment_sha = hashlib.sha256(make_zip(treatment)).hexdigest()
    text = (repo / previous.TEMPLATE_PATH).read_text(encoding="utf-8")
    # Reuse the formerly verified dual-evaluator generator with local,
    # explicitly bounded adaptors; its old task selector is replaced below.
    prior_plan = json.loads((repo / previous.MANIFEST_PATH).read_text(encoding="utf-8"))
    prompt_sha = hashlib.sha256(treatment["prompts/system.md"].encode()).hexdigest()
    prior_plan["source_prompt_sha256"] = prompt_sha
    prior_plan["prompt_only_5min_zip_sha256"] = treatment_sha
    with (patch.object(previous, "EXPECTED_PUBLIC_PROMPT_SHA", prompt_sha),
          patch.object(previous, "PROMPT_ZIP_SHA", treatment_sha),
          patch.object(previous, "candidate_files", return_value=treatment)):
        rendered = previous.render_runtime(text, source_zip, treatment, prior_plan)
    selector = (
        "def load_holdout_ids(public_tasks) -> list[str]:\n"
        "    chosen = " + repr(ids) + "\n"
        "    available = {task.instance_id for task in public_tasks}\n"
        "    if len(chosen) != 4 or len(set(chosen)) != 4 or not set(chosen) <= available:\n"
        "        raise RuntimeError('frozen four public-development tasks not found')\n"
        "    print('EARLYEDIT_FROZEN_SELECTED_IDS=' + json.dumps(chosen), flush=True)\n"
        "    return chosen\n\n"
    )
    rendered = replace_section(
        rendered, "def load_holdout_ids(public_tasks) -> list[str]:",
        "def run_maybe_async(", selector, "explicit 4-ID selector")
    rendered = replace_line_starting(
        rendered, "HOLDOUT_MANIFEST_JSON = ",
        "HOLDOUT_MANIFEST_JSON = " + repr(json.dumps(plan, sort_keys=True)))
    rendered = rendered.replace("public_prompt_5min", "early_edit_5min")
    rendered = rendered.replace("paired-public-prompt-5min", "paired-early-edit-5min")
    rendered = replace_one(rendered, "if len(records) != 6:",
                           "if len(records) != 8:", "pair denominator")
    rendered = replace_one(rendered, "if len(scored) != 3:",
                           "if len(scored) != 4:", "per-arm denominator")
    rendered = rendered.replace("paired_prompt_v2_31b_results.json", RESULT_NAME)
    rendered = rendered.replace("public-prompt-v2-paired-clean-v1",
                                "earlyedit-v2-paired-clean-v1")
    rendered = rendered.replace("PRIVATE_PAIRED_31B_", "PRIVATE_EARLYEDIT_31B_")
    if rendered.count("Evaluator(eval_config)") != 1:
        raise ValueError("unverified evaluator topology")
    if rendered.count("treatment_evaluator = Evaluator(treatment_config)") != 1:
        raise ValueError("unverified treatment evaluator")
    if "competition_submit_code" in rendered or "agent_patch=task.patch" in rendered:
        raise ValueError("unsafe runtime content")
    if rendered.count("EARLYEDIT_FROZEN_SELECTED_IDS") != 1:
        raise ValueError("missing frozen cohort")
    compile(rendered, SCRIPT_NAME, "exec")
    return rendered, {
        "version": plan["version"],
        "baseline_model": MODEL,
        "arm_count": 2,
        "task_count": 4,
        "task_evaluations": 8,
        "control_zip_sha256": control_sha,
        "treatment_zip_sha256": treatment_sha,
        "source_zip_sha256": EXPECTED_ZIP_SHA256,
        "policy_sha256": hashlib.sha256(POLICY.encode()).hexdigest(),
        "manifest_sha256": hashlib.sha256((repo / PLAN_FILE).read_bytes()).hexdigest(),
        "no_training_or_official_submission": True,
    }


def render(repo: Path, source_zip: bytes, out: Path, kernel_ref: str) -> dict:
    if not re.fullmatch(r"kolihhan/[a-z0-9-]{15,100}", kernel_ref):
        raise ValueError("invalid private Kaggle kernel reference")
    if out.exists() and any(out.iterdir()):
        raise FileExistsError("refuse to overwrite frozen private kernel")
    source, report = generate(repo, source_zip)
    out.mkdir(parents=True, exist_ok=True)
    (out / SCRIPT_NAME).write_text(source, encoding="utf-8")
    metadata = {
        "id": kernel_ref, "title": kernel_ref.split("/", 1)[1],
        "code_file": SCRIPT_NAME, "language": "python",
        "kernel_type": "script", "is_private": True,
        "enable_gpu": True, "enable_tpu": False, "enable_internet": False,
        "machine_shape": "NvidiaL4", "docker_image": IMAGE,
        "competition_sources": ["gemma-4-developer-agent"],
        "dataset_sources": ["metric/gemma-4-developer-agent-wheelhouse"],
        "kernel_sources": [],
        "model_sources": [f"google/gemma-4/Other/{MODEL}/2"],
    }
    (out / "kernel-metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {**report, "kernel": kernel_ref, "private": True}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, default=ROOT)
    ap.add_argument("--source-zip", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--kernel-ref", required=True)
    args = ap.parse_args()
    print("EARLYEDIT_PAIRED_RENDER=" + json.dumps(render(
        args.repo.resolve(), args.source_zip.read_bytes(),
        args.out.resolve(), args.kernel_ref), sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
