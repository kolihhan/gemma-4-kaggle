"""Private CPU gold/no-op controls on the frozen official development cohort.

The one-shot launcher embeds the established wheelhouse setup and the frozen
metadata. Kaggle mounts the original tasks and snapshots at runtime.
"""

from collections import Counter, defaultdict
from hashlib import sha256
from importlib.metadata import version
import logging
import tempfile


async def run_sweep(workspace: Path) -> list[dict]:
    from adk_submission import ModelRegistry
    from swegemma.config import EvalConfig
    from swegemma.deduplication import resolve_task_snapshot_paths
    from swegemma.evaluate import Evaluator
    from swegemma.harness.verification import verify_task
    from swegemma.models import load_tasks

    tasks_path = DATA_DIR / "tasks.jsonl"
    snapshots = DATA_DIR / "snapshots"
    selected_ids = {row["instance_id"] for row in COHORT["cases"]}
    selected = {x.instance_id: x for x in load_tasks(tasks_path) if x.instance_id in selected_ids}
    if len(selected_ids) != 42 or set(selected) != selected_ids:
        raise RuntimeError("Frozen task membership mismatch")
    if any(selected[row["instance_id"]].repo != row["repo"] for row in COHORT["cases"]):
        raise RuntimeError("Frozen repository membership mismatch")
    submission = workspace / "empty-submission"
    submission.mkdir()
    results = workspace / "private-results"
    results.mkdir()
    config = EvalConfig(
        tasks_path=tasks_path, snapshots_dir=snapshots, results_dir=results,
        submission_dir=submission, models=ModelRegistry(), sandbox="subprocess",
        wheels_dir=DATA_DIR / "wheels", timeout_seconds=300,
        verification_timeout_seconds=240, verbose=False,
    )
    evaluator = Evaluator(config)
    slots = asyncio.Semaphore(4)

    async def screen(row: dict) -> dict:
        task_id = row["instance_id"]
        async with slots:
            try:
                task = evaluator._hydrate_task_from_secret(selected[task_id])
                if task.instance_id != task_id or task.repo != row["repo"]:
                    raise ValueError("Hydrated task mismatch")
                if not isinstance(task.patch, str) or not task.patch.strip() or not (
                    (task.test_patch or "").strip() or task.FAIL_TO_PASS or task.PASS_TO_PASS or task.test_files
                ):
                    raise ValueError("Missing reference patch or test specification")
                snapshot, base_snapshot, patch_path = resolve_task_snapshot_paths(snapshots, task_id, task.repo)

                async def control(candidate: str) -> dict:
                    result = await verify_task(
                        evaluator.docker, config, task, snapshot, base_snapshot_path=base_snapshot,
                        patch_path=patch_path, agent_patch=candidate, trace=None, start_time=time.perf_counter(),
                    )
                    return {"pass": bool(result.resolved), "exit": result.test_exit_code}

                gold = await control(task.patch)
                if gold != {"pass": True, "exit": 0}:
                    result = {**row, "gold": gold, "noop": None, "status": "reference_failed"}
                else:
                    noop = await control("")
                    status = "eligible" if noop == {"pass": False, "exit": 1} else "noop_inconclusive"
                    result = {**row, "gold": gold, "noop": noop, "status": status}
            except Exception as error:
                result = {**row, "status": "error", "error_type": type(error).__name__}
            return result

    return await asyncio.gather(*(screen(row) for row in COHORT["cases"]))


def run_main() -> None:
    logging.disable(logging.CRITICAL)
    wheel = WHEELHOUSE_DIR / "swegemma-0.2.11-py3-none-any.whl"
    if sha256(wheel.read_bytes()).hexdigest() != "9ad876581f3acde8ec3c369858f0834e2b9f41a3cffce3ca42f09cb090aea9d3":
        raise RuntimeError("Unrecognized official SWE-Gemma verifier wheel")
    install_wheelhouse()
    if version("swegemma") != "0.2.11":
        raise RuntimeError("Installed SWE-Gemma version mismatch")
    with tempfile.TemporaryDirectory(prefix="gemma42-native-") as temporary:
        rows = asyncio.run(run_sweep(Path(temporary)))
    transitions = defaultdict(Counter)
    by_repository = defaultdict(Counter)
    for row in rows:
        transitions[row["prior_control"]][row["status"]] += 1
        by_repository[row["repo"]][row["status"]] += 1
    report = {
        "case_count": len(rows), "cohort_sha256": COHORT_SHA, "verifier": "swegemma-0.2.11",
        "no_model_inference": True, "no_official_submission": True,
        "transitions": transitions, "by_repository": by_repository,
        "strict_eligible": sum(row["status"] == "eligible" for row in rows),
    }
    (WORKING_DIR / "gemma-official-dev42-controls.json").write_text(json.dumps({"report": report, "rows": rows}, sort_keys=True))


if __name__ == "__main__":
    # The launcher inserts the metadata and the pinned install_wheelhouse helper.
    run_main()
