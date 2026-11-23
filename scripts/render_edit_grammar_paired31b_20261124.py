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

from scripts.build_gemma_edit_grammar_20261124 import (
    files_for_pair, build_pair, CHAMPION_SHA256
)
from scripts.prepare_public_budgetfit_v2 import EXPECTED_ZIP_SHA256

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
from scripts.render_contract_impact_31b_pilot import replace_one, replace_section

MODEL = "gemma-4-31b-it-qat-w4a16-ct"
KERNEL_FILE = "paired_edit_grammar31b_5min_runtime.py"
MANIFEST_PATH = "experiments/edit-grammar-paired-20261124/manifest.json"
TEMPLATE_PATH = "kaggle/verifier_baseline_runtime.py"
CONTROL_ZIP_SHA = "ff08c10240a38e151a2ea1d0478e999ee5d2f437d2dad5571d912cf12859922b"
CANDIDATE_ZIP_SHA = "dda74a68742c6cd1592917bdd1d00cf35de44979094de5bb0ae19adf38f45b38"
MODEL_SOURCE = f"google/gemma-4/Other/{MODEL}/2"


def validate_manifest(plan: dict) -> None:
    if plan.get("version") != "edit-grammar-31b-5min-paired-v1":
        raise ValueError("manifest version drift")
    if plan.get("model") != MODEL:
        raise ValueError("model drift")
    if plan.get("source_zip_sha256") != EXPECTED_ZIP_SHA256 or plan.get("champion_zip_sha256") != CHAMPION_SHA256:
        raise ValueError("source provenance drift")
    if (plan.get("control_zip_sha256") != CONTROL_ZIP_SHA or
        plan.get("candidate_zip_sha256") != CANDIDATE_ZIP_SHA):
        raise ValueError("candidate SHA drift")
    spec = plan.get("shared_budget", {})
    if {key: spec.get(key) for key in ("max_time_minutes","max_tool_calls","max_turns","timeout_seconds")} != {
            "max_time_minutes":5,"max_tool_calls":60,"max_turns":80,"timeout_seconds":300}:
        raise ValueError("unmatched 4min/60call budget")
    exp = plan.get("experiment", {})
    if (exp.get("arms") != ["champion_5min","edit_grammar_5min"] or
        exp.get("tasks") != 8 or exp.get("model_task_evaluations") != 16):
        raise ValueError("wrong paired sample")
    sel = plan.get("selection", {})
    if sel.get("counts_by_repo") != {"fastapi_":3,"rich_":3,"requests_":2}:
        raise ValueError("task strata drift")
    if not re.fullmatch(r"[\w-]{20,100}", sel.get("salt", "")):
        raise ValueError("missing preregistered salt")
    excluded = sel.get("exclude_instance_ids", [])
    if not isinstance(excluded,list) or len(excluded)!=len(set(excluded)):
        raise ValueError("invalid exclusion list")


def payload(files: dict[str, str]) -> str:
    return base64.b64encode(json.dumps(files, sort_keys=True,
        separators=(",", ":")).encode("utf-8")).decode("ascii")


def render_runtime(template: str, source_zip: bytes, plan: dict) -> str:
    validate_manifest(plan)
    if digest(source_zip) != EXPECTED_ZIP_SHA256:
        raise ValueError("original source checksum mismatch")
    control, treatment = files_for_pair(source_zip)
    control_zip, candidate_zip = build_pair(source_zip)
    if digest(control_zip) != CONTROL_ZIP_SHA or digest(candidate_zip) != CANDIDATE_ZIP_SHA:
        raise ValueError("paired package checksum mismatch")
    if set(control) != set(treatment):
        raise ValueError("tool set changed")
    if [name for name in control if control[name] != treatment[name]] != ["prompts/system.md"]:
        raise ValueError("experiment must only change prompt")
    if any(x not in control["eval_config.yaml"] for x in ("max_time_minutes: 5","max_tool_calls: 60","max_turns: 80")):
        raise ValueError("mismatched budgets")

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
        'AGENT_DIR = WORKING_DIR / "paired-champion-5min"', "V2 dir")
    text = replace_one(text,
        'RESULTS_DIR = WORKING_DIR / "verifier-baseline-results"',
        'RESULTS_DIR = WORKING_DIR / "paired-edit-grammar-private-results"', "results dir")
    text = replace_one(text,
        'SUMMARY_PATH = WORKING_DIR / "verifier_baseline_results.json"',
        'SUMMARY_PATH = WORKING_DIR / "paired_edit_grammar31b_5min_results.json"', "summary file")
    text = replace_one(text, "E4B model weights not found:", "31B model weights not found:", "weights label")

    # Both payloads generated only from SHA-pinned source, parsed public
    # Notebook literal cells. Do not execute any downloaded notebook cells.
    inject = (
        "\nTREATMENT_DIR = WORKING_DIR / 'paired-edit-grammar-5min'\n"
        "TREATMENT_PAYLOAD_B64 = " + repr(payload(treatment)) + "\n"
    )
    text = replace_one(text,
        'SUMMARY_PATH = WORKING_DIR / "paired_edit_grammar31b_5min_results.json"',
        'SUMMARY_PATH = WORKING_DIR / "paired_edit_grammar31b_5min_results.json"' + inject,
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
    if plan["version"] != "edit-grammar-31b-5min-paired-v1":
        raise ValueError("selection version drift")
    sel = plan["selection"]
    excluded = set(sel["exclude_instance_ids"])
    ids = {task.instance_id for task in public_tasks}
    chosen = []
    for prefix, count in sel["counts_by_repo"].items():
        candidates = sorted(x for x in ids if x.startswith(prefix) and x not in excluded)
        if len(candidates) < count:
            raise ValueError("not enough untouched tasks in " + prefix)
        ranked = sorted(candidates, key=lambda item: (
            hashlib.sha256((sel["salt"] + "|" + item).encode()).hexdigest(), item))
        chosen.extend(ranked[:count])
    if len(chosen) != 8 or len(set(chosen)) != 8:
        raise RuntimeError("paired selection invalid")
    print("EDIT_GRAMMAR_FROZEN_SELECTED_PUBLIC_DEV_IDS=" + json.dumps(chosen),
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
        evaluators = {"champion_5min": evaluator, "edit_grammar_5min": treatment_evaluator}

'''
    text = replace_one(text, '        evaluator = Evaluator(eval_config)\n',
                       evaluator_bootstrap, "paired evaluator")

    loop = '''        records: list[dict[str, object]] = []
        for index, task_id in enumerate(holdout_ids, 1):
            task_order = (["champion_5min", "edit_grammar_5min"] if index % 2
                          else ["edit_grammar_5min", "champion_5min"])
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
        if len(records) != 16:
            raise RuntimeError("missing trial record: no selective task omission")
        score_by_arm = {}
        for arm in ("champion_5min", "edit_grammar_5min"):
            scored = [x for x in records if x["arm"] == arm]
            if len(scored) != 8:
                raise RuntimeError("unbalanced arms")
            score_by_arm[arm] = {
                "evaluated": len(scored),
                "resolved": sum(x.get("resolved") is True for x in scored),
                "patched": sum(x.get("has_patch") is True for x in scored),
                "errors": sum(x.get("status") != "completed" for x in scored),
            }
        output = {
            "version": "edit-grammar-31b-5min-paired-v1",
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
    if text.count("EDIT_GRAMMAR_FROZEN_SELECTED_PUBLIC_DEV_IDS") != 1:
        raise ValueError("selection not pinned")
    if "treatment_evaluator = Evaluator(treatment_config)" not in text:
        raise ValueError("missing isolated competitor evaluator")
    if "competition_submit_code" in text:
        raise ValueError("unexpected official competition submit entry")
    return text


def render(repo: Path, source_zip: bytes, out: Path,
           kernel_ref: str) -> dict:
    if not re.fullmatch(r"kolihhan/[a-z0-9-]{10,100}", kernel_ref):
        raise ValueError("invalid one-time private kernel reference")
    if out.exists() and any(out.iterdir()):
        raise FileExistsError("refuse to overwrite private output")
    plan = json.loads((repo / MANIFEST_PATH).read_text())
    source = render_runtime(
        (repo / TEMPLATE_PATH).read_text(),
        source_zip, plan)
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
        "control_zip_sha256": CONTROL_ZIP_SHA,
        "candidate_zip_sha256": CANDIDATE_ZIP_SHA,
        "task_evaluations": 16,
        "no_gpu_yet": True, "competition_submission_created": False,
    }
    print("PUBLIC_PROMPT_PAIRED_CPU_RENDER=" + json.dumps(report, sort_keys=True),
          flush=True)
    return report


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
