#!/usr/bin/env python3
"""Render a SINGLE genuine 12B public-dev Kaggle trial matched to frozen 31B V2.

No model training, no reference patch, no Kaggle official submission and no
second 31B run. Source, tools, sampling and 5min/28call budget are frozen.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path
import re

from scripts.prepare_public_budgetfit_v2 import (
    validate_source_zip,
    EXPECTED_ZIP_SHA256,
)
from scripts.render_contract_impact_31b_pilot import replace_one, replace_section

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "experiments/solver-v3/pro-12b-vs-frozen31b-20261116.json"
OLD_PLAN_PATH = ROOT / "experiments/solver-v3/pro-v3r-vs-v2-fresh-paired-20261115.json"
TEMPLATE_PATH = ROOT / "kaggle/verifier_baseline_runtime.py"
MODEL = "gemma-4-12b-it-qat-w4a16-ct"
OLD_MODEL = "gemma-4-31b-it-qat-w4a16-ct"
VERSION = "gemma-12b-vs-existing31b-20261116-v1"
KERNEL_FILE = "model_size_12b_matched_runtime.py"
MODEL_SOURCE = "google/gemma-4/Other/gemma-4-12b-it-qat-w4a16-ct/2"
HF_OVERRIDE = '{"architectures": ["Gemma4ForCausalLM"], "model_type": "gemma4"}'


def validate_plans(plan: dict, frozen: dict) -> None:
    if plan.get("version") != VERSION:
        raise ValueError("wrong_size_experiment")
    if plan["control"]["pinned_source_zip_sha256"] != EXPECTED_ZIP_SHA256:
        raise ValueError("source_zip_contract_drift")
    if plan["treatment"]["model"] != MODEL or plan["control"]["model"] != OLD_MODEL:
        raise ValueError("model_size_contract_drift")
    if plan["shared"]["selection_existing_manifest"] != str(OLD_PLAN_PATH.relative_to(ROOT)):
        raise ValueError("selection_provenance_changed")
    if any(plan["shared"][k] != v for k, v in {
        "max_time_minutes": 5,
        "max_tool_calls": 28,
        "max_turns": 80,
        "n_tasks": 3,
        "n_new_evaluations": 3,
    }.items()):
        raise ValueError("unmatched_budget")
    if frozen.get("version") != "v3r-vs-v2-fresh-paired-20261115-v1":
        raise ValueError("wrong_original_matched_trial")
    if frozen["selection"]["repo_prefixes"] != ["fastapi_", "rich_", "requests_"]:
        raise ValueError("original_task_strata_drift")
    if frozen["experiment"]["tasks"] != 3:
        raise ValueError("wrong_original_task_count")
    if any(frozen["shared_budget"][k] != plan["shared"][k] for k in (
        "max_time_minutes", "max_tool_calls", "max_turns",
    )):
        raise ValueError("unfair_budget")


def frozen_agent(source_zip: bytes) -> dict[str, str]:
    if hashlib.sha256(source_zip).hexdigest() != EXPECTED_ZIP_SHA256:
        raise ValueError("source_zip_digest_changed")
    reference = validate_source_zip(source_zip)
    if set(reference) != {
        "agent.yaml", "prompts/system.md", "configs/sampling.yaml",
        "eval_config.yaml",
    }:
        raise ValueError("source_files_drift")
    agent = reference["agent.yaml"]
    before = "model: " + OLD_MODEL
    if agent.count(before) != 1:
        raise ValueError("old_model_identity_drift")
    cfg = reference["eval_config.yaml"]
    if any(cfg.count(term) != 1 for term in (
        "max_time_minutes: 8", "max_tool_calls: 28", "max_turns: 80"
    )):
        raise ValueError("original_eval_budget_drift")
    files = dict(reference)
    files["agent.yaml"] = agent.replace(before, "model: " + MODEL, 1)
    files["eval_config.yaml"] = cfg.replace(
        "max_time_minutes: 8", "max_time_minutes: 5", 1
    )
    if any(files[name] != reference[name] for name in (
        "prompts/system.md", "configs/sampling.yaml"
    )):
        raise ValueError("unexpected_policy_or_sampling_mutation")
    if files["agent.yaml"].replace(
        "model: " + MODEL, before, 1
    ) != reference["agent.yaml"]:
        raise ValueError("unexpected_model_config_mutation")
    if files["eval_config.yaml"].replace(
        "max_time_minutes: 5", "max_time_minutes: 8", 1
    ) != reference["eval_config.yaml"]:
        raise ValueError("unexpected_budget_mutation")
    return files


def render_runtime(template: str, source_zip: bytes,
                   plan: dict, frozen: dict) -> str:
    validate_plans(plan, frozen)
    files = frozen_agent(source_zip)
    encoded = base64.b64encode(json.dumps(
        files, sort_keys=True, separators=(",", ":")
    ).encode()).decode()
    selection = {
        "version": VERSION,
        "frozen_selection": frozen["selection"],
    }
    text = replace_one(
        template, "import json\n", "import json\nimport hashlib\n",
        "hash selector import"
    )
    text = replace_one(
        text, '"__SUBMISSION_PAYLOAD_B64__"', repr(encoded),
        "exact candidate agent payload"
    )
    text = replace_one(
        text,
        'HOLDOUT_MANIFEST_JSON = "__VERIFIER_LORA_HOLDOUT_MANIFEST_JSON__"',
        "HOLDOUT_MANIFEST_JSON = " + repr(json.dumps(selection, sort_keys=True)),
        "unchanged task selection manifest"
    )
    text = replace_one(
        text, 'MODEL_NAME = "gemma-4-e4b-it-qat-w4a16-ct"',
        'MODEL_NAME = "' + MODEL + '"', "12B model identity"
    )
    text = replace_one(
        text, 'AGENT_DIR = WORKING_DIR / "submission"',
        'AGENT_DIR = WORKING_DIR / "model-size12b"',
        "private-only submission directory"
    )
    text = replace_one(
        text, 'RESULTS_DIR = WORKING_DIR / "verifier-baseline-results"',
        'RESULTS_DIR = WORKING_DIR / "model-size12b-results"',
        "isolated 12B trace destination"
    )
    text = replace_one(
        text, 'SUMMARY_PATH = WORKING_DIR / "verifier_baseline_results.json"',
        'SUMMARY_PATH = WORKING_DIR / "model_size_12b_matched_results.json"',
        "private scorer result location"
    )
    text = text.replace("verifier-lora-v0", VERSION)
    selector = '''
def load_holdout_ids(public_tasks) -> list[str]:
    plan = json.loads(HOLDOUT_MANIFEST_JSON)
    if plan.get("version") != "gemma-12b-vs-existing31b-20261116-v1":
        raise ValueError("wrong_frozen_model_size_protocol")
    selection = plan["frozen_selection"]
    salt = selection["salt"]
    excluded = set(selection["exclude_instance_ids"])
    ids = {task.instance_id for task in public_tasks}
    chosen = []
    for prefix in selection["repo_prefixes"]:
        candidates = sorted(x for x in ids if x.startswith(prefix) and x not in excluded)
        if not candidates:
            raise ValueError("unavailable_original_repo_stratum")
        pick = min(candidates, key=lambda item: (
            hashlib.sha256((salt + "|" + item).encode()).hexdigest(), item))
        chosen.append(pick)
    if len(chosen) != 3 or len(set(chosen)) != 3:
        raise ValueError("not_exact_three_original_paired_tasks")
    print("MODEL_SIZE_12B_MATCHED_TASK_IDS_REPRODUCED=" + json.dumps(chosen),
          flush=True)
    return chosen

'''
    text = replace_section(
        text,
        "def load_holdout_ids() -> list[str]:",
        "def run_maybe_async(",
        selector,
        "restore EXACT old matched selection without task peeking",
    )
    text = replace_one(text, "    holdout_ids = load_holdout_ids()\n",
                       "", "select only after task IDs are present")
    text = replace_one(
        text, "    public_tasks = load_tasks(tasks_path)\n",
        "    public_tasks = load_tasks(tasks_path)\n"
        "    holdout_ids = load_holdout_ids(public_tasks)\n",
        "reuse old task manifest"
    )
    text = replace_one(
        text,
        '    model_path = Path(f"/kaggle/input/models/google/gemma-4/other/{MODEL_NAME}/2")',
        '    model_path = Path(f"/kaggle/input/models/google/gemma-4/other/{MODEL_NAME}/2")',
        "leave official model mount expression unchanged"
    ) if False else text
    text = replace_one(
        text, "                extra_args=(),",
        "                extra_args=('--hf-overrides', " + repr(HF_OVERRIDE) + "),",
        "official staff-required 12B vLLM architecture override"
    )
    text = replace_one(text, "E4B model weights not found:",
                       "12B model weights not found:", "model error label")
    text = replace_one(
        text, '        print("BASELINE_RESULT", json.dumps(record, sort_keys=True), flush=True)',
        '        print("PRIVATE_12B_REAL_RESULT_SAFE=" + json.dumps('
        '{k: v for k, v in record.items() if k not in ("instance_id", "error")}, '
        'sort_keys=True), flush=True)',
        "safe task aggregates only"
    )
    text = replace_one(
        text, '            print(f"baseline error for {task_id}: {type(exc).__name__}: {exc}", flush=True)',
        '            print("PRIVATE_12B_EVAL_EXCEPTION_TYPE=" + type(exc).__name__, flush=True)',
        "never print private raw exception"
    )
    text = replace_one(
        text, '            print(f"[{index:02d}/{len(holdout_ids):02d}] baseline {task_id}", flush=True)',
        '            print(f"PRIVATE_12B_TASK_NUMBER={index}/{len(holdout_ids)}", flush=True)',
        "no task identifiers in stdout"
    )
    text = replace_one(
        text, '    print("MODEL_SIZE_12B_MATCHED_TASK_IDS_REPRODUCED=" + json.dumps(chosen),',
        '    print("MODEL_SIZE_12B_MATCHED_TASK_COUNT=" + str(len(chosen)),',
        "no task identifiers printed"
    )
    compile(text, KERNEL_FILE, "exec")
    if "__SUBMISSION_PAYLOAD_B64__" in text or "__VERIFIER_LORA_HOLDOUT_MANIFEST_JSON__" in text:
        raise ValueError("unrendered_runtime_tokens")
    if text.count("MODEL_SIZE_12B_MATCHED_TASK_COUNT") != 1 or text.count("--hf-overrides") != 1:
        raise ValueError("model_size_runtime_injection_corrupt")
    if "competition_submit" in text:
        raise ValueError("unexpected_official_submission")
    return text


def render(repo: Path, source_zip: bytes, out: Path, kernel_ref: str) -> dict:
    if not re.fullmatch(r"kolihhan/[a-z0-9-]{12,100}", kernel_ref):
        raise ValueError("bad_unique_private_kernel_ref")
    if out.exists() and any(out.iterdir()):
        raise FileExistsError("no_runtime_overwrite")
    plan = json.loads((repo / PLAN_PATH.relative_to(ROOT)).read_text())
    frozen = json.loads((repo / OLD_PLAN_PATH.relative_to(ROOT)).read_text())
    runtime = render_runtime(
        (repo / TEMPLATE_PATH.relative_to(ROOT)).read_text(),
        source_zip, plan, frozen
    )
    out.mkdir(parents=True, exist_ok=True)
    (out / KERNEL_FILE).write_text(runtime)
    metadata = {
        "id": kernel_ref,
        "title": kernel_ref.split("/", 1)[1],
        "code_file": KERNEL_FILE,
        "language": "python",
        "kernel_type": "script",
        "is_private": True,
        "enable_gpu": True,
        "enable_tpu": False,
        "enable_internet": False,
        "machine_shape": "NvidiaL4",
        "docker_image": "gcr.io/kaggle-private-byod/python@sha256:37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461",
        "dataset_sources": ["metric/gemma-4-developer-agent-wheelhouse"],
        "competition_sources": ["gemma-4-developer-agent"],
        "kernel_sources": [],
        "model_sources": [MODEL_SOURCE],
    }
    (out / "kernel-metadata.json").write_text(json.dumps(
        metadata, indent=2, sort_keys=True
    ) + "\n")
    result = {
        "model": MODEL,
        "reference": "existing exact frozen 31B V2 matched task results (1/3)",
        "evaluation_tasks": 3,
        "new_gpu_runs": 0,
        "new_competition_submission": False,
        "source_sha256": hashlib.sha256(source_zip).hexdigest(),
        "generated_source_sha256": hashlib.sha256(runtime.encode()).hexdigest(),
        "HF_OVERRIDE": True,
        "actual_correctness_tested": False,
    }
    print("GEMMA_PRO_MODEL_SIZE_12B_CPU_RENDER=" + json.dumps(result, sort_keys=True), flush=True)
    return result


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--repo", type=Path, default=Path("."))
    p.add_argument("--source-zip", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--kernel-ref", required=True)
    opt = p.parse_args()
    render(opt.repo.resolve(), opt.source_zip.read_bytes(),
           opt.out.resolve(), opt.kernel_ref)


if __name__ == "__main__":
    main()
