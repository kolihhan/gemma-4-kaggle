"""Private CPU-only evaluation-integrity screen on three already-tested Gemma 31B tasks.

Uses the installed OFFICIAL SWE-Gemma verifier and exact public development
snapshots. No model, GPU, internet, hidden task or official competition submit.
Only exports safe feature flags and gold/noop outcomes; never reference patches,
raw task statements, grader text, commands, or trace contents.
"""
from __future__ import annotations

import asyncio
import glob
import importlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

DATA_DIR = Path("/kaggle/input/competitions/gemma-4-developer-agent")
WHEELHOUSE_DIR = Path("/kaggle/input/datasets/metric/gemma-4-developer-agent-wheelhouse")
WORKING_DIR = Path("/kaggle/working")
OUTPUT = WORKING_DIR / "paired_three_task_integrity_cpu.json"
TASKS = (
    ("fastapi_14487", "fastapi/fastapi"),
    ("rich_3782", "Textualize/rich"),
    ("requests_7427", "psf/requests"),
)


def features(statement: object, hints: object) -> dict[str, object]:
    """Do not retain or display original issue text or linked URL."""
    raw = statement if isinstance(statement, str) else ""
    hint = hints if isinstance(hints, str) else ""
    urls = re.findall(r"https?://[^\s)\]>]+", raw)
    without_links = re.sub(r"https?://[^\s)\]>]+", " ", raw)
    words = re.findall(r"[A-Za-z0-9_]+", without_links)
    return {
        "statement_chars": len(raw),
        "hint_chars": len(hint),
        "has_external_url": bool(urls),
        "short_link_pointer_risk": bool(urls and len(raw) < 300 and len(words) <= 20),
        "not_a_spec_sufficiency_verdict": True,
    }


def classify(noop: dict, gold: dict) -> str:
    if noop.get("status") != "completed" or gold.get("status") != "completed":
        return "evaluation_error"
    if gold.get("resolved") is True and noop.get("resolved") is False:
        return "informative_gold_pass_noop_fail"
    if gold.get("resolved") is True and noop.get("resolved") is True:
        return "unhelpful_noop_already_passes"
    if gold.get("resolved") is False and noop.get("resolved") is False:
        return "confounded_gold_fails"
    return "confounded_other"


def install_wheelhouse() -> None:
    if not WHEELHOUSE_DIR.is_dir():
        raise RuntimeError("missing official wheelhouse")
    for pattern in (
        "/usr/local/lib/python*/dist-packages/*cutlass*.pth",
        "/usr/local/lib/python*/site-packages/*cutlass*.pth",
    ):
        for pth in glob.glob(pattern):
            try:
                Path(pth).unlink()
            except OSError:
                pass
    fixed = Path("/tmp/gemma4-scorer-wheelhouse")
    fixed.mkdir(parents=True, exist_ok=True)
    for wheel in WHEELHOUSE_DIR.glob("*.whl"):
        if "cutlass" in wheel.name.lower():
            continue
        name = (wheel.name.replace("cu128", "+cu128")
                if "cu128" in wheel.name and "+" not in wheel.name else wheel.name)
        dest = fixed / name
        if not dest.exists():
            try:
                dest.symlink_to(wheel)
            except OSError:
                shutil.copyfile(wheel, dest)
    wheels = sorted(str(p) for p in fixed.glob("*.whl"))
    if not wheels:
        raise RuntimeError("empty official wheelhouse")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-q", "--no-deps",
         "--force-reinstall", *wheels],
        check=True, capture_output=True, timeout=240,
    )
    importlib.invalidate_caches()


async def evaluate_controls() -> dict:
    from adk_submission import ModelRegistry
    from swegemma.config import EvalConfig
    from swegemma.deduplication import resolve_task_snapshot_paths
    from swegemma.evaluate import Evaluator
    from swegemma.harness.verification import verify_task
    from swegemma.models import load_tasks

    tasks_path = DATA_DIR / "tasks.jsonl"
    snapshots = DATA_DIR / "snapshots"
    public = load_tasks(tasks_path)
    selected = {x.instance_id: x for x in public if x.instance_id in {t[0] for t in TASKS}}
    if set(selected) != {x[0] for x in TASKS}:
        raise RuntimeError("exact preregistered three tasks not found")

    empty_submission = WORKING_DIR / "three-task-empty-submission"
    results_dir = WORKING_DIR / "three-task-integrity-verifier"
    empty_submission.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)
    config = EvalConfig(
        tasks_path=tasks_path,
        snapshots_dir=snapshots,
        results_dir=results_dir,
        submission_dir=empty_submission,
        models=ModelRegistry(),
        sandbox="subprocess",
        wheels_dir=DATA_DIR / "wheels",
        timeout_seconds=300,
        verification_timeout_seconds=240,
        verbose=False,
    )
    evaluator = Evaluator(config)
    rows = []
    for task_id, expected_repo in TASKS:
        visible = selected[task_id]
        f = features(getattr(visible, "problem_statement", ""),
                     getattr(visible, "hints_text", ""))
        controls: dict[str, dict] = {}
        for control in ("noop", "gold"):
            try:
                task = evaluator._hydrate_task_from_secret(visible)
                if task.instance_id != task_id or task.repo != expected_repo:
                    raise RuntimeError("hydrated task metadata mismatch")
                patch = "" if control == "noop" else task.patch
                if control == "gold" and not isinstance(patch, str):
                    raise RuntimeError("no reference patch")
                if not ((getattr(task, "test_patch", "") or "").strip()
                        or getattr(task, "FAIL_TO_PASS", ())
                        or getattr(task, "PASS_TO_PASS", ())
                        or getattr(task, "test_files", None)):
                    raise RuntimeError("no test specification")
                snapshot_path, base_snapshot_path, patch_path = resolve_task_snapshot_paths(
                    snapshots, task.instance_id, task.repo
                )
                started = time.perf_counter()
                result = await verify_task(
                    evaluator.docker, evaluator.config, task, snapshot_path,
                    base_snapshot_path=base_snapshot_path, patch_path=patch_path,
                    agent_patch=patch, agent_error=None, trace=None, start_time=started,
                )
                controls[control] = {
                    "status": "completed",
                    "resolved": bool(result.resolved),
                    "test_exit_code": result.test_exit_code,
                    "duration_seconds": round(result.duration_seconds or 0, 2),
                    "error_type": None,
                }
            except BaseException as exc:
                controls[control] = {
                    "status": "error",
                    "resolved": None,
                    "test_exit_code": None,
                    "duration_seconds": None,
                    "error_type": type(exc).__name__,
                }
            print("SAFE_INTEGRITY_CONTROL=" + json.dumps({
                "instance_id": task_id, "control": control,
                **controls[control],
            }, sort_keys=True), flush=True)
        rows.append({
            "instance_id": task_id,
            "repo": expected_repo,
            "input_features": f,
            "noop": controls["noop"],
            "gold": controls["gold"],
            "integrity_category": classify(controls["noop"], controls["gold"]),
        })
    return {
        "version": "gemma4-paired-31b-three-task-integrity-v1",
        "requested": len(TASKS), "results": rows,
        "original_31b_paired_run": 43057377220,
        "public_development_only": True,
        "no_model_inference": True, "no_gpu": True,
        "no_official_submission": True,
        "no_raw_issue_patch_or_grader_output_export": True,
        "limits": (
            "Gold/noop is a local verifier check, not proof of hidden-task quality. "
            "A title/URL heuristic is not a human judgment of full task sufficiency. "
            "A bundled wheel can shadow source without being detected by this control."
        ),
    }


def main() -> None:
    WORKING_DIR.mkdir(parents=True, exist_ok=True)
    install_wheelhouse()
    outcome = asyncio.run(evaluate_controls())
    OUTPUT.write_text(json.dumps(outcome, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("SAFE_INTEGRITY_SUMMARY=" + json.dumps({
        "version": outcome["version"],
        "categories": {r["instance_id"]: r["integrity_category"] for r in outcome["results"]},
        "no_model_inference": True,
        "no_official_submission": True,
    }, sort_keys=True), flush=True)


if __name__ == "__main__":
    try:
        main()
    except BaseException as exc:
        OUTPUT.write_text(json.dumps({
            "version": "gemma4-paired-31b-three-task-integrity-v1",
            "status": "error",
            "error_type": type(exc).__name__,
            "no_raw_issue_patch_or_grader_output_export": True,
        }, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        raise RuntimeError("INTEGRITY_CPU_RUN_FAILED_" + type(exc).__name__) from None
