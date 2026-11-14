"""Compare a runnable pre-edit reproduction against the scored 31B champion."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

from scripts.build_public_prompt_only_control_20261111 import make_zip
from scripts.build_toolcap60_timeout_recovery import build, files_for_candidate
from scripts.render_earlyedit_v2_paired_31b import IMAGE
from scripts.render_patch_checkpoint_31b import CHAMPION_SHA
from scripts.render_public_prompt_vs_v2_paired_31b import render_pair
from scripts.render_v2_toolcap_31b_pilot import MODEL, MODEL_SOURCE, TEMPLATE_PATH, replace_one, replace_section

ROOT = Path(__file__).resolve().parents[1]
TASKS = ("fastapi_15800", "rich_3518", "rich_4075", "fastapi_14492")
ARMS = ("champion", "repro_first")
VERSION = "gemma-31b-repro-first-20261114"
RESULT = "repro_first_summary.json"
REPRO_RULE = (
    "- If the issue supplies a runnable example or names a focused existing test for the "
    "behavior, try it once before editing. Use a single `run_command` with `timeout 20` "
    "and no new files. The example should fail for the exact behavior the issue asks "
    "you to fix. If it is unavailable or blocked by setup, proceed with the source edit. "
    "If it fails as expected, keep that command and run it unchanged after the edit "
    "as your focused verification.\n"
)


def arm_files(source_zip: bytes) -> tuple[dict[str, str], dict[str, str]]:
    if hashlib.sha256(build(source_zip)).hexdigest() != CHAMPION_SHA:
        raise ValueError("scored 0.180 champion source drift")
    control = files_for_candidate(source_zip)
    treatment = dict(control)
    heading = "### 2. Edit by call 10, absolutely by call 12\n\n"
    treatment["prompts/system.md"] = replace_one(
        control["prompts/system.md"], heading, heading + REPRO_RULE, "pre-edit reproduction"
    )
    return control, treatment


INTEGRITY = '''async def grade_integrity(evaluator, task):
    import time
    from swegemma.deduplication import resolve_task_snapshot_paths
    from swegemma.harness.verification import verify_task

    truth = evaluator._hydrate_task_from_secret(task)
    if not isinstance(truth.patch, str) or not truth.patch.strip():
        raise RuntimeError("missing gold reference")
    snapshot, base, delta = resolve_task_snapshot_paths(
        evaluator.config.snapshots_dir, truth.instance_id, truth.repo)
    outcomes = []
    for candidate in ("", truth.patch):
        checked = await verify_task(evaluator.docker, evaluator.config, truth, snapshot,
                                    base_snapshot_path=base, patch_path=delta,
                                    agent_patch=candidate, start_time=time.perf_counter())
        outcomes.append((bool(checked.resolved), checked.test_exit_code))
    return outcomes == [(False, 1), (True, 0)]


def observed_checks(trace):
    if not trace:
        return None
    before, after = set(), set()
    edited = False
    for event in trace.entries:
        if event.event_type != "tool_call":
            continue
        if event.tool_name in ("edit_file", "write_file"):
            edited = True
        if event.tool_name == "run_command":
            command = (event.tool_args or {}).get("command", "")
            if isinstance(command, str) and (
                "pytest" in command or "unittest" in command or "assert " in command
            ):
                (after if edited else before).add(command.strip())
    return {"pre_edit_checks": len(before), "identical_pre_post_checks": len(before & after)}
'''


def render(repo: Path, source_zip: bytes, out: Path, kernel_ref: str) -> None:
    if not re.fullmatch(r"kolihhan/gemma4-repro-first-[0-9]+", kernel_ref):
        raise ValueError("invalid private kernel identity")
    control, treatment = arm_files(source_zip)
    archive = make_zip(treatment)
    treatment_sha = hashlib.sha256(archive).hexdigest()
    runtime = render_pair((repo / TEMPLATE_PATH).read_text(), control, treatment, {
        "version": VERSION, "arms": ARMS, "tasks": TASKS,
        "control_zip_sha256": CHAMPION_SHA, "treatment_zip_sha256": treatment_sha,
    })
    runtime = replace_section(runtime, "def load_holdout_ids(public_tasks) -> list[str]:",
                              "def run_maybe_async(", f"def load_holdout_ids(public_tasks):\n"
                              f"    return {TASKS!r}\n\n\n" + INTEGRITY, "frozen tasks and trace metrics")
    runtime = replace_one(runtime, "            task_order = (", (
        "            if not run_maybe_async(grade_integrity(evaluator, tasks_by_id[task_id])):\n"
        "                raise RuntimeError('task gold/no-op integrity check failed: ' + task_id)\n"
        "            task_order = ("
    ), "current verifier controls")
    runtime = replace_one(runtime, '"error_type": None,\n', (
        '"error_type": None, "checks": observed_checks(result.trace),\n'
    ), "check uptake")
    runtime = replace_one(runtime, "if len(records) != 6:", f"if len(records) != {2 * len(TASKS)}:",
                          "paired denominator")
    runtime = replace_one(runtime, "if len(scored) != 3:", f"if len(scored) != {len(TASKS)}:",
                          "arm denominator")
    runtime = replace_one(runtime, "if gpu_count < 1:", "if gpu_count != 4:", "verified L4x4 shape")
    runtime = replace_one(runtime, "Kaggle baseline kernel has no visible GPU",
                          "this matched test requires four GPU devices", "GPU shape failure")
    runtime = replace_one(runtime, '                "traceback": traceback.format_exc(),\n', "", "safe failure")
    runtime = replace_one(runtime, '                "error": str(exc),\n', "", "safe failure message")
    runtime = replace_one(runtime, "        write_failure(exc)\n        raise",
                          "        write_failure(exc)\n        raise RuntimeError(type(exc).__name__) from None",
                          "safe exception")
    runtime = (runtime.replace('"v2_5min"', repr(ARMS[0]))
               .replace('"public_prompt_5min"', repr(ARMS[1]))
               .replace("paired_prompt_v2_31b_results.json", RESULT)
               .replace('"public-prompt-v2-paired-clean-v1"', repr(VERSION)))
    runtime = replace_one(runtime, '            "model": MODEL_NAME, "status": "completed",\n',
                          '            "model": MODEL_NAME, "status": "completed",\n'
                          f'            "treatment_zip_sha256": {treatment_sha!r},\n', "result provenance")
    compile(runtime, "repro_first.py", "exec")
    out.mkdir(parents=True, exist_ok=False)
    (out / "repro_first.py").write_text(runtime)
    (out / "kernel-metadata.json").write_text(json.dumps({
        "id": kernel_ref, "title": kernel_ref.split("/", 1)[1], "code_file": "repro_first.py",
        "language": "python", "kernel_type": "script", "is_private": True,
        "enable_gpu": True, "enable_tpu": False, "enable_internet": False,
        "machine_shape": "NvidiaL4", "docker_image": IMAGE,
        "competition_sources": ["gemma-4-developer-agent"],
        "dataset_sources": ["metric/gemma-4-developer-agent-wheelhouse"],
        "model_sources": [MODEL_SOURCE], "kernel_sources": [],
    }, indent=2) + "\n")
    print("REPRO_FIRST_RENDER=" + json.dumps({
        "control_zip_sha256": CHAMPION_SHA, "treatment_zip_sha256": treatment_sha,
        "model": MODEL, "tasks": TASKS, "budget": "5min/60/80", "arms": ARMS,
    }), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-zip", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--kernel-ref", required=True)
    args = parser.parse_args()
    render(ROOT, args.source_zip.read_bytes(), args.out, args.kernel_ref)
