# Appended only to the official wheelhouse installer; private diagnostic runtime.
import re
from collections import Counter
CASES = __PRIVATE_CASES__
OUT = WORKING_DIR / "control_phase_sentinel_safe.json"


def classify(v):
    # Signals, not inferred internal stages. Never export raw error/output.
    code = getattr(v, "test_exit_code", None)
    code = code if type(code) is int else None
    err = str(getattr(v, "error", "") or "")
    out = str(getattr(v, "test_output", "") or "")
    s = err + "\n" + out
    signals = []
    patterns = {
        "collection_error": r"ERROR collecting|Interrupted: \d+ errors? during collection",
        "missing_dependency": r"ModuleNotFoundError|No module named|ImportError",
        "timeout_mention": r"TimeoutExpired|timed out|TimeoutExceeded",
        "patch_apply_error_mention": r"patch does not apply|patch failed:|corrupt patch|error:.*patch",
        "no_tests_collected": r"collected 0 items|no tests ran",
        "assertion_marker": r"AssertionError|assert .*==",
        "pytest_failed_summary": r"\b[1-9]\d* failed\b",
        "pytest_error_summary": r"\b[1-9]\d* errors?\b",
        "pytest_passed_summary": r"\b[1-9]\d* passed\b",
    }
    for label, pattern in patterns.items():
        if re.search(pattern, s, re.I):
            signals.append(label)
    return {"resolved": bool(v.resolved), "test_exit_code": code,
            "error_present": bool(err), "test_output_present": bool(out),
            "signals": sorted(signals), "classification": "observed_signals_only"}


async def execute():
    from swegemma.config import EvalConfig
    from swegemma.models import load_tasks
    from swegemma.evaluate import Evaluator
    from swegemma.deduplication import resolve_task_snapshot_paths
    from swegemma.harness.verification import verify_task
    from adk_submission import ModelRegistry
    wanted = {t for _, t in CASES}
    original = {t.instance_id: t for t in load_tasks(DATA_DIR / "tasks.jsonl") if t.instance_id in wanted}
    assert set(original) == wanted and len(wanted) == 4
    results = WORKING_DIR / "sentinel-results"
    empty = WORKING_DIR / "sentinel-empty"
    results.mkdir(exist_ok=True); empty.mkdir(exist_ok=True)
    cfg = EvalConfig(tasks_path=DATA_DIR/"tasks.jsonl",snapshots_dir=DATA_DIR/"snapshots",results_dir=results,
        submission_dir=empty,models=ModelRegistry(),sandbox="subprocess",wheels_dir=DATA_DIR/"wheels",
        timeout_seconds=240,verification_timeout_seconds=180,verbose=False)
    ev = Evaluator(cfg)
    rows = []
    for label, tid in CASES:
        row = {"stratum": label, "controls": {}}
        stage = "hydrate"
        try:
            task = ev._hydrate_task_from_secret(original[tid])
            assert task.instance_id == tid and task.patch and task.patch.strip()
            stage = "resolve_snapshot"
            snapshot, base, patch_path = resolve_task_snapshot_paths(DATA_DIR/"snapshots",task.instance_id,task.repo)
            for name, patch in (("gold",task.patch),("noop","")):
                stage = "verify_" + name
                try:
                    v = await verify_task(ev.docker, ev.config, task, snapshot,
                        base_snapshot_path=base,patch_path=patch_path,agent_patch=patch,
                        agent_error=None,trace=None,start_time=time.perf_counter())
                    row["controls"][name] = classify(v)
                except Exception as e:
                    row["controls"][name] = {"exception_type": type(e).__name__, "observed_boundary":stage}
        except Exception as e:
            row["setup_exception"] = {"type":type(e).__name__, "observed_boundary":stage}
        rows.append(row)
    return {"rows":rows,"tasks":len(rows),"controls_returned":sum(len(r["controls"]) for r in rows),
            "gpu":False,"model_inference":False,"competition_submission":False,"private_content_exported":False,
            "limitation":"coarse verifier result signals; no inferred phase from missing output"}


if __name__ == "__main__":
    try:
        install_official_wheelhouse()
        result = asyncio.run(execute())
        OUT.write_text(json.dumps(result,sort_keys=True))
        print("SENTINEL_SAFE="+json.dumps(result,sort_keys=True),flush=True)
    except Exception as e:
        print("SENTINEL_BLOCKED="+type(e).__name__,flush=True)
        raise RuntimeError("private sentinel blocked") from None
