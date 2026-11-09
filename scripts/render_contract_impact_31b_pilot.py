#!/usr/bin/env python3
"""Render an inference-capable, paired, private 31B Kaggle pilot.

A read-only/same-model evaluation of the frozen V2 control against the
Contract & Impact architecture. NOT a competition submission.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path
import re

from scripts.build_contract_impact_candidate import payload
from scripts.prepare_public_budgetfit_v2 import validate_source_zip

MODEL = "gemma-4-31b-it-qat-w4a16-ct"
MANIFEST_PATH = "experiments/architecture-contract-impact-v0/31b-pilot-manifest.json"
TEMPLATE_PATH = "kaggle/verifier_baseline_runtime.py"
KERNEL_FILE = "contract_impact_paired_31b_runtime.py"
MODEL_SOURCE = f"google/gemma-4/Other/{MODEL}/2"
ARMS = ("baseline_v2", "contract_impact")


def replace_one(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise ValueError(f"{label}: expected exactly one occurrence, got {count}")
    return source.replace(old, new, 1)


def replace_section(source: str, start: str, end: str, new: str, label: str) -> str:
    if source.count(start) != 1 or source.count(end) != 1:
        raise ValueError(f"{label}: exact boundaries changed")
    before, remaining = source.split(start, 1)
    _, after = remaining.split(end, 1)
    return before + new + "\n\n" + end + after


def validate_manifest(manifest: dict) -> None:
    if manifest.get("version") != "contract-impact-31b-paired-pilot-v1":
        raise ValueError("preregistered manifest version drift")
    if manifest.get("repositories") != ["fastapi", "rich"]:
        raise ValueError("repository sample changed")
    if manifest.get("per_repo") != 2:
        raise ValueError("sample size changed")
    if manifest.get("max_pilot_evaluations") != 8:
        raise ValueError("evaluation count changed")
    if manifest.get("arms") != list(ARMS):
        raise ValueError("unexpected arms")
    if not re.fullmatch(r"[a-zA-Z0-9-]{12,120}", manifest.get("salt", "")):
        raise ValueError("salt not frozen")
    exclude = manifest.get("exclude_instance_ids")
    if not isinstance(exclude, list) or len(exclude) != len(set(exclude)):
        raise ValueError("invalid exclusion manifest")


def render_runtime(template: str, source_zip: bytes, manifest: dict) -> str:
    validate_manifest(manifest)
    control = validate_source_zip(source_zip)
    treatment = payload(source_zip)
    for name in ("configs/sampling.yaml", "eval_config.yaml"):
        if control[name] != treatment[name]:
            raise ValueError("sampling/eval budget confounded between arms")
    if "skills/contract-impact/scripts/contract.py" not in treatment:
        raise ValueError("no executable Skill in treatment")

    encoded = base64.b64encode(json.dumps({
        ARMS[0]: control, ARMS[1]: treatment,
    }, sort_keys=True, separators=(",", ":")).encode("utf-8")).decode("ascii")
    text = replace_one(template, '"__SUBMISSION_PAYLOAD_B64__"', repr(encoded),
                       "source package marker")
    text = replace_one(text, 'HOLDOUT_MANIFEST_JSON = "__VERIFIER_LORA_HOLDOUT_MANIFEST_JSON__"',
                       "HOLDOUT_MANIFEST_JSON = " + repr(json.dumps(manifest, sort_keys=True)),
                       "fixed pilot manifest")
    text = replace_one(text, 'MODEL_NAME = "gemma-4-e4b-it-qat-w4a16-ct"',
                       f'MODEL_NAME = "{MODEL}"', "31B model")
    text = replace_one(text, 'AGENT_DIR = WORKING_DIR / "submission"',
                       'AGENT_DIR = WORKING_DIR / "submission-v2"\n'
                       'TREATMENT_DIR = WORKING_DIR / "submission-contract-impact"', "arm dirs")
    text = replace_one(text, 'RESULTS_DIR = WORKING_DIR / "verifier-baseline-results"',
                       'RESULTS_DIR = WORKING_DIR / "contract-impact-private-results"', "results dir")
    text = replace_one(text, 'SUMMARY_PATH = WORKING_DIR / "verifier_baseline_results.json"',
                       'SUMMARY_PATH = WORKING_DIR / "contract_impact_paired_31b_results.json"', "summary file")

    materialize = '''def materialize_submission() -> None:
    raw = base64.b64decode(SUBMISSION_PAYLOAD_B64.encode("ascii")).decode("utf-8")
    arms = json.loads(raw)
    if set(arms) != {"baseline_v2", "contract_impact"}:
        raise ValueError("paired payload arms drift")
    for arm, root in (("baseline_v2", AGENT_DIR),
                      ("contract_impact", TREATMENT_DIR)):
        files = arms[arm]
        if not isinstance(files, dict) or "agent.yaml" not in files:
            raise ValueError("invalid paired submission payload")
        if root.exists():
            shutil.rmtree(root)
        root.mkdir(parents=True)
        real_root = root.resolve()
        for relative, content in sorted(files.items()):
            target = (root / relative).resolve()
            if real_root not in target.parents:
                raise ValueError("unsafe submission path")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
'''
    text = replace_section(text, "def materialize_submission() -> None:",
                           "def load_holdout_ids()", materialize, "package materialization")

    selector = '''def load_holdout_ids(public_tasks) -> list[str]:
    import hashlib
    plan = json.loads(HOLDOUT_MANIFEST_JSON)
    if plan["version"] != "contract-impact-31b-paired-pilot-v1":
        raise ValueError("unexpected pilot manifest")
    ignored = set(plan["exclude_instance_ids"])
    ids = []
    for repo in plan["repositories"]:
        prefix = repo + "_"
        pool = sorted({task.instance_id for task in public_tasks
                       if task.instance_id.startswith(prefix)
                       and task.instance_id not in ignored})
        ranked = sorted(pool, key=lambda key: (
            hashlib.sha256((plan["salt"] + "|" + key).encode()).hexdigest(),
            key))
        count = int(plan["per_repo"])
        if len(ranked) < count:
            raise ValueError("not enough eligible tasks for " + repo)
        ids.extend(ranked[:count])
    if len(ids) != 4 or len(set(ids)) != 4:
        raise ValueError("pilot denominator not 4 distinct tasks")
    print("PREREGISTERED_TASK_IDS", json.dumps(ids), flush=True)
    return ids
'''
    text = replace_section(text, "def load_holdout_ids() -> list[str]:",
                           "def run_maybe_async(", selector, "task selector")
    text = replace_one(text, "    holdout_ids = load_holdout_ids()\n", "",
                       "delay selector until data hydrated")

    validator = '''    limits, generation_constraints = build_submission_limits()
    for arm_root in (AGENT_DIR, TREATMENT_DIR):
        validate_directory(arm_root, limits=limits)
        declared_models = discover_declared_models(arm_root)
        if declared_models != {MODEL_NAME}:
            raise RuntimeError("wrong model declaration: " + str(arm_root))
        arm_adapters = discover_adapters(
            str(arm_root), adapter_extensions=ALLOWED_ADAPTER_EXTENSIONS)
        if getattr(arm_adapters, "adapters", None):
            raise ValueError("LoRA/adapters forbidden in paired pilot")
    adapters = discover_adapters(
        str(AGENT_DIR), adapter_extensions=ALLOWED_ADAPTER_EXTENSIONS)
    for shared in ("configs/sampling.yaml", "eval_config.yaml"):
        if (AGENT_DIR / shared).read_bytes() != (TREATMENT_DIR / shared).read_bytes():
            raise ValueError("arm budget or sampling drift")
'''
    text = replace_section(text, "    limits, generation_constraints = build_submission_limits()",
                           "    model_path = Path(", validator, "paired model validation")
    text = replace_one(text, 'E4B model weights not found:', "31B model weights not found:",
                       "weight error scope")
    text = replace_one(text,
                       '    public_tasks = load_tasks(tasks_path)\n'
                       '    tasks_by_id = {task.instance_id: task for task in public_tasks if task.instance_id in set(holdout_ids)}',
                       '    public_tasks = load_tasks(tasks_path)\n'
                       '    holdout_ids = load_holdout_ids(public_tasks)\n'
                       '    tasks_by_id = {task.instance_id: task for task in public_tasks if task.instance_id in set(holdout_ids)}',
                       "hydrated holdout selection")

    text = replace_one(text, "        eval_config = EvalConfig(",
                       "        eval_kwargs = dict(", "shared evaluator kwargs")
    text = replace_one(text, "        evaluator = Evaluator(eval_config)",
                       '        base_kwargs = dict(eval_kwargs)\n'
                       '        base_kwargs["results_dir"] = RESULTS_DIR / "baseline_v2"\n'
                       '        alternative_kwargs = dict(eval_kwargs)\n'
                       '        alternative_kwargs["results_dir"] = RESULTS_DIR / "contract_impact"\n'
                       '        alternative_kwargs["submission_dir"] = TREATMENT_DIR\n'
                       '        evaluators = {\n'
                       '            "baseline_v2": Evaluator(EvalConfig(**base_kwargs)),\n'
                       '            "contract_impact": Evaluator(EvalConfig(**alternative_kwargs)),\n'
                       '        }', "paired evaluators")

    evaluation = '''        records: list[dict[str, object]] = []
        for index, task_id in enumerate(holdout_ids, 1):
            order = ("baseline_v2", "contract_impact") if index % 2 else (
                "contract_impact", "baseline_v2")
            for arm in order:
                print(f"[{index:02d}/{len(holdout_ids):02d}] {arm} {task_id}",
                      flush=True)
                try:
                    result = run_maybe_async(
                        evaluators[arm].evaluate_task(
                            task=tasks_by_id[task_id],
                            task_index=index,
                            total_tasks=len(holdout_ids),
                        )
                    )
                    candidate = (result.agent_patch or "").strip()
                    record = {
                        "instance_id": task_id,
                        "arm": arm,
                        "status": "completed",
                        "resolved": bool(result.resolved),
                        "test_exit_code": result.test_exit_code,
                        "patch_chars": len(candidate),
                        "has_patch": bool(candidate),
                        "tool_calls": result.tool_calls,
                        "duration_seconds": result.duration_seconds,
                    }
                except BaseException as exc:
                    record = _error_record(task_id, exc)
                    record["arm"] = arm
                    print(f"PILOT_TASK_ERROR {arm} {task_id} {type(exc).__name__}",
                          flush=True)
                records.append(record)
                # Only safe, derived task-level metrics, no patches/solutions/traces.
                print("PAIRED_TASK_METRIC", json.dumps(record, sort_keys=True), flush=True)
                SUMMARY_PATH.write_text(
                    json.dumps({"version": "contract-impact-31b-paired-pilot-v1",
                                "status": "partial", "records": records,
                                "requested": len(holdout_ids) * 2},
                               indent=2, sort_keys=True), encoding="utf-8")

        totals = {}
        for arm in ("baseline_v2", "contract_impact"):
            arm_records = [r for r in records if r["arm"] == arm]
            totals[arm] = {
                "requested": len(holdout_ids),
                "completed": sum(r["status"] == "completed" for r in arm_records),
                "resolved": sum(r.get("resolved") is True for r in arm_records),
                "seconds": round(sum(float(r.get("duration_seconds") or 0.0)
                                     for r in arm_records), 3),
            }
        output = {
            "version": "contract-impact-31b-paired-pilot-v1",
            "model": MODEL_NAME,
            "status": "completed",
            "requested": len(holdout_ids) * 2,
            "instance_ids": holdout_ids,
            "arms": totals,
            "records": records,
            "visible_gpus": gpu_count,
            "tensor_parallel_size": tp_size,
            "limitations": "single paired 4-task exploratory public-development pilot; "
                           "not independent proof of hidden transfer",
        }
        SUMMARY_PATH.write_text(json.dumps(output, indent=2, sort_keys=True),
                                encoding="utf-8")
        print("PAIRED_PILOT_SUMMARY", json.dumps(
            {k: v for k, v in output.items() if k != "records"}, sort_keys=True), flush=True)
'''
    text = replace_section(text, "        records: list[dict[str, object]] = []",
                           "    finally:", evaluation, "paired task loop")
    text = replace_one(text, '"version": "verifier-lora-v0",\n                "model": MODEL_NAME,\n                "status": "error"',
                       '"version": "contract-impact-31b-paired-pilot-v1",\n'
                       '                "model": MODEL_NAME,\n                "status": "error"',
                       "top-level failure schema")
    compile(text, KERNEL_FILE, "exec")
    if ("Evaluator(EvalConfig(**base_kwargs))" not in text
            or "Evaluator(EvalConfig(**alternative_kwargs))" not in text):
        raise ValueError("paired evaluators missing from runtime")
    if '"__SUBMISSION_PAYLOAD_B64__"' in text or '"__VERIFIER_LORA_HOLDOUT_MANIFEST_JSON__"' in text:
        raise ValueError("unrendered placeholder")
    return text


def render(repo: Path, source_zip: bytes, output: Path, kernel_ref: str) -> dict:
    if not re.fullmatch(r"kolihhan/[a-z0-9-]+", kernel_ref):
        raise ValueError("unexpected private kernel ref")
    if output.exists() and any(output.iterdir()):
        raise FileExistsError("refuse overwrite of an existing kernel directory")
    manifest = json.loads((repo / MANIFEST_PATH).read_text())
    template = (repo / TEMPLATE_PATH).read_text()
    runtime = render_runtime(template, source_zip, manifest)
    output.mkdir(parents=True, exist_ok=True)
    (output / KERNEL_FILE).write_text(runtime)
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
    (output / "kernel-metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    summary = {
        "kernel_ref": kernel_ref,
        "status": "private_paired_pilot_rendered",
        "source_zip_sha256": hashlib.sha256(source_zip).hexdigest(),
        "runtime_sha256": hashlib.sha256(runtime.encode()).hexdigest(),
        "manifest_sha256": hashlib.sha256(
            (repo / MANIFEST_PATH).read_bytes()).hexdigest(),
        "official_submission_created": False,
        "model_inference_executed_by_renderer": False,
    }
    print("PAIRED_PILOT_RENDER", json.dumps(summary, sort_keys=True))
    return summary


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, default=Path("."))
    ap.add_argument("--source-zip", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--kernel-ref", required=True)
    args = ap.parse_args()
    render(args.repo.resolve(), args.source_zip.read_bytes(),
           args.out.resolve(), args.kernel_ref)


if __name__ == "__main__":
    main()
