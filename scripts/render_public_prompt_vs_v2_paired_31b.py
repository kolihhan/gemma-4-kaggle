"""Render private, disjoint paired REAL Gemma 4 31B prompt-only vs V2 pilot.

NO third-party notebook execution. Both single-agent arms have identical model,
tools, sampling, task budget and task text; only prompts/system.md differs.
One private Kaggle Notebook starts one vLLM server, evaluates three ID-selected
tasks with each arm (six task evaluations), then exports safe aggregate metrics.
This pilot is public-development evidence, NOT an official leaderboard score.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path
import re

from scripts.build_public_prompt_only_control_20261111 import (
    candidate_files, digest, make_zip, notebook_bundle,
    EXPECTED_PUBLIC_PROMPT_SHA,
)
from scripts.prepare_public_budgetfit_v2 import validate_source_zip, EXPECTED_ZIP_SHA256
from scripts.render_contract_impact_31b_pilot import replace_one, replace_section

MODEL = "gemma-4-31b-it-qat-w4a16-ct"
KERNEL_FILE = "paired_prompt_vs_v2_31b_runtime.py"
MANIFEST_PATH = "experiments/public-prompt-vs-v2-disjoint-paired-20261112/manifest.json"
TEMPLATE_PATH = "kaggle/verifier_baseline_runtime.py"
PROMPT_ZIP_SHA = "fdb862b0f8391b0596f200ccb8e3bece40d9dc8f1e3d60e63537277ac626649d"
MODEL_SOURCE = f"google/gemma-4/Other/{MODEL}/2"


def validate_manifest(plan: dict) -> None:
    if plan.get("version") != "public-prompt-v2-paired-clean-v1":
        raise ValueError("manifest version mismatch")
    if plan.get("model") != MODEL or plan.get("source_prompt_sha256") != EXPECTED_PUBLIC_PROMPT_SHA:
        raise ValueError("pinned model or public prompt mismatch")
    if plan.get("baseline_zip_sha256") != EXPECTED_ZIP_SHA256 or plan.get("prompt_only_5min_zip_sha256") != PROMPT_ZIP_SHA:
        raise ValueError("pinned candidate provenance mismatch")
    spec = plan.get("shared_budget", {})
    if spec.get("max_time_minutes") != 5 or spec.get("max_tool_calls") != 28 or spec.get("max_turns") != 80:
        raise ValueError("unfair budget in manifest")
    exp = plan.get("experiment", {})
    if exp.get("arms") != ["v2_5min", "public_prompt_5min"] or exp.get("tasks") != 3 or exp.get("model_task_evaluations") != 6:
        raise ValueError("unfair or wrong number of evaluations")
    selection = plan.get("selection", {})
    if selection.get("repo_prefixes") != ["fastapi_", "rich_", "requests_"] or selection.get("count_per_repo") != 1:
        raise ValueError("task strata changed")
    if not re.fullmatch(r"[\w-]{20,100}", selection.get("salt", "")):
        raise ValueError("task salt invalid")
    excluded = selection.get("exclude_instance_ids")
    if not isinstance(excluded, list) or len(excluded) != len(set(excluded)):
        raise ValueError("task exclusion corrupted")
    if "requests_7328" not in excluded:
        raise ValueError("previous V5 diagnostic issue must remain excluded")


def payload(files: dict[str, str]) -> str:
    return base64.b64encode(json.dumps(files, sort_keys=True,
        separators=(",", ":")).encode("utf-8")).decode("ascii")


def render_runtime(template: str, source_zip: bytes, public: dict[str, str], plan: dict) -> str:
    validate_manifest(plan)
    baseline = validate_source_zip(source_zip)
    if digest(source_zip) != EXPECTED_ZIP_SHA256:
        raise ValueError("baseline source ZIP digest mismatch")
    control = dict(baseline)
    cfg = baseline["eval_config.yaml"]
    if cfg.count("max_time_minutes: 8") != 1 or cfg.count("max_tool_calls: 28") != 1 or cfg.count("max_turns: 80") != 1:
        raise ValueError("baseline source budget not recognized")
    control["eval_config.yaml"] = cfg.replace("max_time_minutes: 8", "max_time_minutes: 5")
    treatment = candidate_files(source_zip, public, minutes=5)
    if digest(make_zip(treatment)) != PROMPT_ZIP_SHA:
        raise ValueError("competitor prompt-only ZIP not pinned")
    if set(control) != set(treatment):
        raise ValueError("candidate files differ")
    if any(control[k] != treatment[k] for k in control if k != "prompts/system.md"):
        raise ValueError("uncontrolled change: only system prompt may differ")
    if control["prompts/system.md"] == treatment["prompts/system.md"]:
        raise ValueError("no treatment")
    if "max_time_minutes: 5" not in control["eval_config.yaml"]:
        raise ValueError("time cap mismatch")

    # The original E4B reference runtime does not import hashlib; the
    # frozen ID-only selector uses it. Inject only the standard-library import.
    text = replace_one(template, "import json\n", "import json\nimport hashlib\n",
                       "deterministic task selector import")
    text = replace_one(text, '"__SUBMISSION_PAYLOAD_B64__"', repr(payload(control)), "baseline payload")
    text = replace_one(text,
        'HOLDOUT_MANIFEST_JSON = "__VERIFIER_LORA_HOLDOUT_MANIFEST_JSON__"',
        "HOLDOUT_MANIFEST_JSON = " + repr(json.dumps(plan, sort_keys=True)), "manifest")
    text = replace_one(text, 'MODEL_NAME = "gemma-4-e4b-it-qat-w4a16-ct"',
                       f'MODEL_NAME = "{MODEL}"', "31B model")
    text = replace_one(text,
        'AGENT_DIR = WORKING_DIR / "submission"',
        'AGENT_DIR = WORKING_DIR / "paired-v2-5min"', "V2 dir")
    text = replace_one(text,
        'RESULTS_DIR = WORKING_DIR / "verifier-baseline-results"',
        'RESULTS_DIR = WORKING_DIR / "paired-prompt-private-results"', "results dir")
    text = replace_one(text,
        'SUMMARY_PATH = WORKING_DIR / "verifier_baseline_results.json"',
        'SUMMARY_PATH = WORKING_DIR / "paired_prompt_v2_31b_results.json"', "summary file")
    text = replace_one(text, "E4B model weights not found:", "31B model weights not found:", "weights label")

    # Both payloads generated only from SHA-pinned source, parsed public
    # Notebook literal cells. Do not execute any downloaded notebook cells.
    inject = (
        "\nTREATMENT_DIR = WORKING_DIR / 'paired-public-prompt-5min'\n"
        "TREATMENT_PAYLOAD_B64 = " + repr(payload(treatment)) + "\n"
    )
    text = replace_one(text,
        'SUMMARY_PATH = WORKING_DIR / "paired_prompt_v2_31b_results.json"',
        'SUMMARY_PATH = WORKING_DIR / "paired_prompt_v2_31b_results.json"' + inject,
        "treatment payload")

    # The second materializer preserves the same strict path containment
    # property as the competition's reference materializer.
    second_materializer = '''
def materialize_treatment() -> None:
    raw = base64.b64decode(TREATMENT_PAYLOAD_B64.encode("ascii")).decode("utf-8")
    files = json.loads(raw)
    if not isinstance(files, dict) or set(files) != {
        "agent.yaml", "eval_config.yaml", "configs/sampling.yaml",
        "prompts/system.md",
    }:
        raise ValueError("unexpected treatment files")
    if TREATMENT_DIR.exists():
        shutil.rmtree(TREATMENT_DIR)
    TREATMENT_DIR.mkdir(parents=True)
    root = TREATMENT_DIR.resolve()
    for relative, content in sorted(files.items()):
        target = (TREATMENT_DIR / relative).resolve()
        if root not in target.parents:
            raise ValueError("unsafe treatment path")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

'''
    text = replace_one(text, "def load_holdout_ids() -> list[str]:",
                       second_materializer + "def load_holdout_ids() -> list[str]:",
                       "second materializer")

    selector = '''
def load_holdout_ids(public_tasks) -> list[str]:
    plan = json.loads(HOLDOUT_MANIFEST_JSON)
    if plan["version"] != "public-prompt-v2-paired-clean-v1":
        raise ValueError("frozen task selection version mismatch")
    selection = plan["selection"]
    excluded = set(selection["exclude_instance_ids"])
    ids = set(task.instance_id for task in public_tasks)
    chosen = []
    for prefix in selection["repo_prefixes"]:
        candidates = sorted(x for x in ids if x.startswith(prefix)
                            and x not in excluded)
        if len(candidates) < 1:
            raise ValueError("no eligible task for repo prefix: " + prefix)
        ranked = sorted(candidates, key=lambda item: (
            hashlib.sha256((selection["salt"] + "|" + item).encode()).hexdigest(),
            item,
        ))
        chosen.append(ranked[0])
    assert len(chosen) == 3 and len(set(chosen)) == 3
    print("PAIRED_PROMPT_FROZEN_SELECTED_PUBLIC_DEV_IDS=" + json.dumps(chosen),
          flush=True)
    return chosen
'''
    text = replace_section(text, "def load_holdout_ids() -> list[str]:",
                           "def run_maybe_async(", selector, "deterministic ID selector")
    text = replace_one(text, "    materialize_submission()\n",
                       "    materialize_submission()\n    materialize_treatment()\n",
                       "second materialize")
    text = replace_one(text, "    holdout_ids = load_holdout_ids()\n", "",
                       "defer selection until public tasks hydrated")
    text = replace_one(text,
        '    public_tasks = load_tasks(tasks_path)\n',
        '    public_tasks = load_tasks(tasks_path)\n'
        '    holdout_ids = load_holdout_ids(public_tasks)\n',
        "tasks hydration")
    text = replace_one(text,
        '    validate_directory(AGENT_DIR, limits=limits)\n',
        '    validate_directory(AGENT_DIR, limits=limits)\n'
        '    validate_directory(TREATMENT_DIR, limits=limits)\n',
        "validate both")
    text = replace_one(text,
        '    if declared_models != {MODEL_NAME}:\n'
        '        raise RuntimeError(f"expected only {MODEL_NAME}, got {sorted(declared_models)}")',
        '    if declared_models != {MODEL_NAME}:\n'
        '        raise RuntimeError(f"expected only {MODEL_NAME}, got {sorted(declared_models)}")\n'
        '    treatment_models = discover_declared_models(TREATMENT_DIR)\n'
        '    if treatment_models != {MODEL_NAME}:\n'
        '        raise RuntimeError("mismatched treatment model")',
        "single allowed model both arms")

    # Construct two independent official Evaluators sharing the SAME vLLM
    # server, exact limits, snapshots and task data. Isolate output dirs.
    evaluator_bootstrap = '''        evaluator = Evaluator(eval_config)
        from dataclasses import is_dataclass, replace as dataclass_replace
        if is_dataclass(eval_config):
            treatment_config = dataclass_replace(
                eval_config,
                submission_dir=TREATMENT_DIR,
                results_dir=RESULTS_DIR / "public-prompt",
            )
        elif hasattr(eval_config, "model_copy"):
            treatment_config = eval_config.model_copy(update={
                "submission_dir": TREATMENT_DIR,
                "results_dir": RESULTS_DIR / "public-prompt",
            })
        else:
            raise RuntimeError("unknown EvalConfig data model; refuse GPU comparison")
        if (Path(treatment_config.submission_dir) != TREATMENT_DIR or
            Path(treatment_config.results_dir) != RESULTS_DIR / "public-prompt"):
            raise RuntimeError("treatment Evaluator path isolation failed")
        treatment_evaluator = Evaluator(treatment_config)
        evaluators = {"v2_5min": evaluator, "public_prompt_5min": treatment_evaluator}

'''
    text = replace_one(text, '        evaluator = Evaluator(eval_config)\n',
                       evaluator_bootstrap, "paired evaluator")

    loop = '''        records: list[dict[str, object]] = []
        for index, task_id in enumerate(holdout_ids, 1):
            task_order = (["v2_5min", "public_prompt_5min"] if index % 2
                          else ["public_prompt_5min", "v2_5min"])
            for arm in task_order:
                evaluator_for_arm = evaluators[arm]
                print("PRIVATE_PAIRED_31B_TASK=" + json.dumps({
                    "arm": arm, "task": task_id, "index": index,
                }, sort_keys=True), flush=True)
                try:
                    result = run_maybe_async(evaluator_for_arm.evaluate_task(
                        task=tasks_by_id[task_id], task_index=index,
                        total_tasks=len(holdout_ids)))
                    patch = (result.agent_patch or "").strip()
                    row = {
                        "arm": arm, "instance_id": task_id, "status": "completed",
                        "resolved": bool(result.resolved),
                        "test_exit_code": result.test_exit_code,
                        "patch_chars": len(patch), "has_patch": bool(patch),
                        "tool_calls": result.tool_calls,
                        "duration_seconds": result.duration_seconds,
                        "error_type": None,
                    }
                except BaseException as exc:
                    row = _error_record(task_id, exc)
                    # The private diagnostic JSON holds raw exception details;
                    # stdout and public GitHub receive only sanitized classes.
                    row.pop("error", None)
                    row["arm"] = arm
                    print("PRIVATE_PAIRED_31B_TASK_EXCEPTION=" + type(exc).__name__,
                          flush=True)
                records.append(row)
                print("PRIVATE_PAIRED_31B_SAFE_METRIC=" +
                      json.dumps(row, sort_keys=True), flush=True)
        if len(records) != 6:
            raise RuntimeError("missing trial record: no selective task omission")
        score_by_arm = {}
        for arm in ("v2_5min", "public_prompt_5min"):
            scored = [x for x in records if x["arm"] == arm]
            if len(scored) != 3:
                raise RuntimeError("unbalanced arms")
            score_by_arm[arm] = {
                "evaluated": len(scored),
                "resolved": sum(x.get("resolved") is True for x in scored),
                "patched": sum(x.get("has_patch") is True for x in scored),
                "errors": sum(x.get("status") != "completed" for x in scored),
            }
        output = {
            "version": "public-prompt-v2-paired-clean-v1",
            "model": MODEL_NAME, "status": "completed",
            "selected_public_dev_ids": holdout_ids,
            "total_evaluations": len(records),
            "score_by_arm": score_by_arm, "results": records,
        }
        SUMMARY_PATH.write_text(json.dumps(output, indent=2, sort_keys=True),
                                encoding="utf-8")
        print("PRIVATE_PAIRED_31B_SAFE_SUMMARY=" +
              json.dumps({k: v for k, v in output.items() if k != "results"},
                         sort_keys=True), flush=True)
'''
    text = replace_section(text,
                           '        records: list[dict[str, object]] = []\n',
                           '    finally:\n',
                           loop, "paired task loop")
    text = replace_one(text,
        '        "status": "error",\n',
        '        "status": "error",\n',
        "retain private failure writer") if False else text

    compile(text, KERNEL_FILE, "exec")
    if "__SUBMISSION_PAYLOAD_B64__" in text or "__VERIFIER_LORA_HOLDOUT_MANIFEST_JSON__" in text:
        raise ValueError("unrendered template placeholders")
    if text.count("PAIRED_PROMPT_FROZEN_SELECTED_PUBLIC_DEV_IDS") != 1:
        raise ValueError("selection not pinned")
    if "treatment_evaluator = Evaluator(treatment_config)" not in text:
        raise ValueError("missing isolated competitor evaluator")
    if "competition_submit_code" in text:
        raise ValueError("unexpected official competition submit entry")
    return text


def render(repo: Path, source_zip: bytes, public_ipynb: Path, out: Path,
           kernel_ref: str) -> dict:
    if not re.fullmatch(r"kolihhan/[a-z0-9-]{10,100}", kernel_ref):
        raise ValueError("invalid one-time private kernel reference")
    if out.exists() and any(out.iterdir()):
        raise FileExistsError("refuse to overwrite private output")
    plan = json.loads((repo / MANIFEST_PATH).read_text())
    source = render_runtime(
        (repo / TEMPLATE_PATH).read_text(),
        source_zip, notebook_bundle(public_ipynb), plan)
    out.mkdir(parents=True, exist_ok=True)
    (out / KERNEL_FILE).write_text(source)
    metadata = {
        "id": kernel_ref, "title": kernel_ref.split("/", 1)[1],
        "code_file": KERNEL_FILE, "language": "python", "kernel_type": "script",
        "is_private": True, "enable_gpu": True, "enable_tpu": False,
        "enable_internet": False, "machine_shape": "NvidiaL4",
        "docker_image": "gcr.io/kaggle-private-byod/python@sha256:37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461",
        "dataset_sources": ["metric/gemma-4-developer-agent-wheelhouse"],
        "competition_sources": ["gemma-4-developer-agent"],
        "kernel_sources": [], "model_sources": [MODEL_SOURCE],
    }
    (out / "kernel-metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    report = {
        "status": "private_render_only", "manifest_sha256": digest(
            (repo / MANIFEST_PATH).read_bytes()),
        "reference_sha256": digest(source_zip),
        "public_prompt_sha256": EXPECTED_PUBLIC_PROMPT_SHA,
        "competitor_zip_sha256": PROMPT_ZIP_SHA,
        "task_evaluations": 6,
        "no_gpu_yet": True, "competition_submission_created": False,
    }
    print("PUBLIC_PROMPT_PAIRED_CPU_RENDER=" + json.dumps(report, sort_keys=True),
          flush=True)
    return report


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--repo", type=Path, default=Path("."))
    p.add_argument("--source-zip", type=Path, required=True)
    p.add_argument("--public-ipynb", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--kernel-ref", required=True)
    opt = p.parse_args()
    render(opt.repo.resolve(), opt.source_zip.read_bytes(),
           opt.public_ipynb, opt.out.resolve(), opt.kernel_ref)


if __name__ == "__main__":
    main()
