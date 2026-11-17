"""Grade both arms on private native tests after patch generation has finished."""

from collections import Counter
from hashlib import sha256
from importlib.metadata import version
import logging
from math import comb
from random import Random
import tempfile


ARMS = ("control", "retrieval")
WHEEL_SHA = "9ad876581f3acde8ec3c369858f0834e2b9f41a3cffce3ca42f09cb090aea9d3"


def unique_file(name):
    files = list(Path("/kaggle/input").rglob(name))
    if len(files) != 1:
        raise RuntimeError(f"Missing or ambiguous private input: {name}")
    return files[0]


def solver_results():
    rows = {}
    archive_sha = None
    for start, stop in ((0, 16), (16, 31)):
        path = unique_file(f"solver-results-{start}.json")
        data = json.loads(path.read_text())
        if (data["membership_sha256"], data["offset"], data["stop"], data["model"],
                data["control_archive_sha256"]) != (
            PLAN["membership_sha256"], start, stop, MODEL_NAME, PLAN["control_archive_sha256"],
        ):
            raise ValueError("Solver identity or range mismatch")
        if archive_sha and archive_sha != data["retrieval_archive_sha256"]:
            raise ValueError("Treatment archive drift between solver shards")
        archive_sha = data["retrieval_archive_sha256"]
        expected = {(case["instance_id"], arm) for case in CASES[start:stop] for arm in ARMS}
        actual = {(row["instance_id"], row["arm"]) for row in data["rows"]}
        if actual != expected or len(data["rows"]) != len(expected):
            raise ValueError("Missing or repeated frozen arm recordings")
        for row in data["rows"]:
            instance, arm = row["instance_id"], row["arm"]
            patch_file = path.parent / f"{instance}.{arm}.patch"
            patch = patch_file.read_bytes() if patch_file.is_file() else b""
            if sha256(patch).hexdigest() != row["patch_sha256"]:
                raise ValueError("Solver patch artifact digest mismatch")
            rows[instance, arm] = row, patch.decode()
    return rows, archive_sha


async def grade(work, rows, linked):
    from adk_submission import ModelRegistry
    from swegemma.config import EvalConfig
    from swegemma.deduplication import resolve_task_snapshot_paths
    from swegemma.evaluate import Evaluator
    from swegemma.harness.verification import verify_task
    from swegemma.models import Task, load_tasks

    click_root = linked.parent
    click_manifest = json.loads(linked.read_text())
    if click_manifest["cohort_sha256"] != CLICK_LOCK:
        raise ValueError("Click test fixtures changed")
    click_rows = {f"external_click_{row['pr']}": row for row in click_manifest["cases"]}
    official_rows = {row.instance_id: row for row in load_tasks(DATA_DIR / "tasks.jsonl")}
    for directory in ("results", "submission", "dependencies"):
        (work / directory).mkdir()
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-q", "--no-index", "--find-links", str(click_root / "wheels"),
         "--target", str(work / "dependencies"), "flit-core==3.12.0", "colorama==0.4.6"],
        check=True, capture_output=True, timeout=150,
    )
    sys.path.insert(0, str(work / "dependencies"))
    config = EvalConfig(
        tasks_path=DATA_DIR / "tasks.jsonl", snapshots_dir=DATA_DIR / "snapshots",
        results_dir=work / "results", submission_dir=work / "submission", models=ModelRegistry(),
        sandbox="subprocess", wheels_dir=DATA_DIR / "wheels", timeout_seconds=300,
        verification_timeout_seconds=240, display_mode="quiet",
    )
    click_config = EvalConfig(
        tasks_path=work / "tasks.jsonl", snapshots_dir=click_root,
        results_dir=work / "results", submission_dir=work / "submission", models=ModelRegistry(),
        sandbox="subprocess", wheels_dir=DATA_DIR / "wheels", timeout_seconds=300,
        verification_timeout_seconds=180, display_mode="quiet",
    )
    native = Evaluator(config)
    click = Evaluator(click_config)
    slots = asyncio.Semaphore(4)

    async def score_case(case):
        async with slots:
            instance = case["instance_id"]
            if case["source"] == "original_upstream_issue":
                record = click_rows[instance]
                files = {kind: click_root / Path(info["filename"]).name for kind, info in record["files"].items()}
                for kind in ("snapshot", "tests"):
                    if sha256(files[kind].read_bytes()).hexdigest() != record["files"][kind]["sha256"]:
                        raise ValueError("Click fixture checksum mismatch")
                if record["base"] != case["base_commit"] or record["files"]["snapshot"]["sha256"] != case["solver_snapshot_sha256"]:
                    raise ValueError("Click fixture is not part of the frozen cohort")
                task = Task(instance_id=instance, repo=case["repo"], base_commit=record["base"],
                            problem_statement="", test_patch=files["tests"].read_text())
                snapshot, base, delta = files["snapshot"], None, None
                evaluator = click
            else:
                task = native._hydrate_task_from_secret(official_rows[instance])
                snapshot, base, delta = resolve_task_snapshot_paths(config.snapshots_dir, instance, task.repo)
                evaluator = native
            if task.repo != case["repo"] or not (task.test_patch.strip() or task.FAIL_TO_PASS or task.PASS_TO_PASS):
                raise ValueError("Missing native test specification")
            results = []
            for arm in ARMS:
                observed, patch = rows[instance, arm]
                result = await verify_task(
                    evaluator.docker, evaluator.config, task, snapshot, base_snapshot_path=base, patch_path=delta,
                    agent_patch=patch, trace=None, start_time=time.perf_counter(),
                )
                results.append({**observed, "repo": task.repo, "resolved": bool(result.resolved),
                                "verifier_exit": result.test_exit_code,
                                "verifier_error": bool(result.error), "grade_seconds": round(result.duration_seconds, 2)})
            print("GEMMA31_VERIFIED_A_PAIR", flush=True)
            return results

    pairs = await asyncio.gather(*(score_case(case) for case in CASES))
    return pairs


def report(pairs):
    rng = Random(20261117)
    n = len(pairs)
    differences = [int(candidate["resolved"]) - int(control["resolved"]) for control, candidate in pairs]
    resamples = sorted(sum(rng.choices(differences, k=n)) / n for _ in range(40_000))
    rescues, regressions = differences.count(1), differences.count(-1)
    discordant = rescues + regressions
    mcnemar = min(1.0, 2 * sum(comb(discordant, x) for x in range(min(rescues, regressions) + 1)) / 2**discordant)
    by_repo = {}
    for control, candidate in pairs:
        repo = by_repo.setdefault(control["repo"], Counter())
        repo["n"] += 1
        repo["rescues"] += candidate["resolved"] and not control["resolved"]
        repo["regressions"] += control["resolved"] and not candidate["resolved"]
    by_arm = {}
    for arm_index, arm in enumerate(ARMS):
        cases = [pair[arm_index] for pair in pairs]
        by_arm[arm] = {
            "resolved": sum(item["resolved"] for item in cases),
            "seconds": round(sum(item["seconds"] for item in cases), 2),
            "grade_seconds": round(sum(item["grade_seconds"] for item in cases), 2),
            "total_calls": sum(item["tool_calls"] for item in cases),
            "retrieval_calls": sum(item["retrieval_calls"] for item in cases),
            "retrieval_with_matches": sum(item["retrieval_with_matches"] for item in cases),
            "model_responses": sum(item["model_response"] for item in cases),
            "solver_errors": dict(Counter(item["error"] for item in cases if item["error"])),
            "verifier_exit": dict(Counter(item["verifier_exit"] for item in cases)),
            "verifier_errors": sum(item["verifier_error"] for item in cases),
        }
    interval = [resamples[999], resamples[38_999]]
    uptake_on_rescue = sum(delta == 1 and c["retrieval_with_matches"] > 0 for delta, (_, c) in zip(differences, pairs))
    valid = all(x["model_response"] and x["error"] != "agent_error" and x["verifier_exit"] in (0, 1)
                for pair in pairs for x in pair)
    return {"n": n, "rescues": rescues, "regressions": regressions, "arms": by_arm,
            "paired_delta": sum(differences) / n, "paired_ci95": interval, "mcnemar_two_sided": mcnemar,
            "by_repo": by_repo, "retrieval_with_matches_on_rescues": uptake_on_rescue,
            "all_model_runs_and_grades_valid": valid,
            "paired_validation_pass": n == 31 and valid and interval[0] > 0 and uptake_on_rescue > 0}


def main():
    logging.disable(logging.CRITICAL)
    if sha256((WHEELHOUSE_DIR / "swegemma-0.2.11-py3-none-any.whl").read_bytes()).hexdigest() != WHEEL_SHA:
        raise ValueError("Verifier epoch mismatch")
    install_wheelhouse()
    if version("swegemma") != "0.2.11":
        raise ValueError("Wrong SWE-Gemma verifier")
    rows, archive_sha = solver_results()
    with tempfile.TemporaryDirectory(prefix="gemma31-pair-grade-") as work:
        pairs = asyncio.run(grade(Path(work), rows, unique_file("linked-click-control-bundle.json")))
    results = report(pairs)
    results.update(membership_sha256=PLAN["membership_sha256"], verifier="swegemma-0.2.11",
                   control_archive_sha256=PLAN["control_archive_sha256"], retrieval_archive_sha256=archive_sha)
    (WORKING_DIR / "gemma31-paired-results.json").write_text(json.dumps({"report": results, "pairs": pairs}, sort_keys=True))
    print("GEMMA31_PAIRED_NATIVE_RESULTS=" + json.dumps(results, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
