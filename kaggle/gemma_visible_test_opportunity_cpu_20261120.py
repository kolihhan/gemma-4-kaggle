"""Gemma 4 official PRIVATE CPU-only repository-visible test opportunity gate.

Retrospective gold-patch touched paths are used ONLY inside this evaluator to
estimate an upper-bound test discovery opportunity. Never include gold patch
contents, changed paths, problem statements, hidden tests, or model output in
logs/artifacts or future solver prompt. Not a solver A/B and not proof of
test availability on blind issues.
"""
from __future__ import annotations

import glob, importlib, json, re, shutil, subprocess, sys, zipfile, tarfile
from pathlib import Path
from collections import Counter

DATA=Path("/kaggle/input/competitions/gemma-4-developer-agent")
WHEELS=Path("/kaggle/input/datasets/metric/gemma-4-developer-agent-wheelhouse")
WORK=Path("/kaggle/working")
OUT=WORK/"gemma_visible_test_opportunity_safe.json"
CASES={
    "fastapi_14458":"fastapi/fastapi",
    "fastapi_15589":"fastapi/fastapi",
    "rich_3894":"Textualize/rich",
    "rich_3905":"Textualize/rich",
}

def install_wheels():
    if not WHEELS.is_dir():raise RuntimeError("OFFICIAL_WHEELHOUSE_MISSING")
    for pattern in ("/usr/local/lib/python*/dist-packages/*cutlass*.pth",
                    "/usr/local/lib/python*/site-packages/*cutlass*.pth"):
        for p in glob.glob(pattern):
            try:Path(p).unlink()
            except OSError:pass
    fixed=Path("/tmp/gemma-native-visible-test-wheels")
    fixed.mkdir(parents=True,exist_ok=True)
    for wheel in WHEELS.glob("*.whl"):
        if "cutlass" in wheel.name.lower():continue
        name=wheel.name.replace("cu128","+cu128") if "cu128" in wheel.name and "+" not in wheel.name else wheel.name
        dest=fixed/name
        if not dest.exists():
            try:dest.symlink_to(wheel)
            except OSError:shutil.copyfile(wheel,dest)
    wheels=sorted(map(str,fixed.glob("*.whl")))
    if not wheels:raise RuntimeError("EMPTY_WHEELHOUSE")
    subprocess.run([sys.executable,"-m","pip","install","-q","--no-deps","--force-reinstall",*wheels],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=240)
    importlib.invalidate_caches()

def source_paths(snapshot):
    """Read paths only; do not extract untrusted archive members."""
    p=Path(snapshot)
    if p.is_dir():
        values=[x.relative_to(p).as_posix() for x in p.rglob("*") if x.is_file()]
        return set(values),"directory"
    if p.is_file() and zipfile.is_zipfile(p):
        with zipfile.ZipFile(p) as z: return set(x.filename for x in z.infolist() if not x.is_dir()),"zip"
    if p.is_file() and tarfile.is_tarfile(p):
        with tarfile.open(p) as t:return set(x.name for x in t.getmembers() if x.isfile()),"tar"
    return set(),"unsupported_snapshot_format"

def touched_source_paths(patch):
    # Confidential gold patch is used only as an isolated retrospective
    # evaluator label; this function returns paths to the private process.
    result=[]
    for line in str(patch).splitlines():
        if not line.startswith("diff --git a/"):continue
        if " b/" not in line:continue
        left=line[len("diff --git a/"):].split(" b/",1)[0].strip()
        if not left or left.startswith("/") or ".." in Path(left).parts:continue
        if left.endswith(".py") and not Path(left).name.startswith("test_"):
            result.append(left)
    return sorted(set(result))

def candidate_names(path):
    p=Path(path)
    n=p.stem
    return {"test_"+n+".py",n+"_test.py","tests/test_"+n+".py"}

def path_matches(all_paths,touched):
    repo_tests=[s for s in all_paths if
        (Path(s).name.startswith("test_") and s.endswith(".py"))
        or s.endswith("_test.py")]
    answers=[]
    for file in touched:
        suffixes=candidate_names(file)
        matched={t for t in repo_tests if Path(t).name in {Path(s).name for s in suffixes}}
        answers.append(len(matched))
    return {"repository_test_python_files":len(repo_tests),
            "source_py_file_count_from_gold_patch":len(touched),
            "touched_files_with_any_basename_test":sum(bool(n) for n in answers),
            "distinct_maybe_relevant_test_paths":sum(answers),
            "any_test_path_in_original_repo":bool(repo_tests)}

def smoke():
    assert touched_source_paths("diff --git a/pkg/a.py b/pkg/a.py\n@@ -1 +1 @@\n-a\n+b")==["pkg/a.py"]
    assert path_matches({"pkg/a.py","tests/test_a.py"},["pkg/a.py"])["touched_files_with_any_basename_test"]==1
    print("GEMMA_VISIBLE_TEST_OPPORTUNITY_SELFTEST=PASS",flush=True)

def main():
    install_wheels()
    from adk_submission import ModelRegistry
    from swegemma.config import EvalConfig
    from swegemma.deduplication import resolve_task_snapshot_paths
    from swegemma.evaluate import Evaluator
    from swegemma.models import load_tasks

    visible={x.instance_id:x for x in load_tasks(DATA/"tasks.jsonl") if x.instance_id in CASES}
    if set(visible)!=set(CASES):raise RuntimeError("FROZEN_FOUR_PUBLIC_DEV_TASKS_MISSING")
    (WORK/"gemma-visible-test-empty").mkdir(parents=True,exist_ok=True)
    (WORK/"gemma-visible-test-results").mkdir(parents=True,exist_ok=True)
    config=EvalConfig(
        tasks_path=DATA/"tasks.jsonl",snapshots_dir=DATA/"snapshots",
        results_dir=WORK/"gemma-visible-test-results",
        submission_dir=WORK/"gemma-visible-test-empty",
        models=ModelRegistry(),sandbox="subprocess",wheels_dir=DATA/"wheels",
        timeout_seconds=300,verification_timeout_seconds=200,verbose=False)
    evaluator=Evaluator(config)
    safe=[]
    for i,(task_id,expected_repo) in enumerate(CASES.items(),1):
        # Hydrated task's confidential patch is not disclosed; used only to
        # locate retrospectively touched SOURCE files, an oracle upper bound.
        row={"task_ordinal":i,"repo_family":"FastAPI" if "fastapi" in expected_repo else "Rich"}
        try:
            task=evaluator._hydrate_task_from_secret(visible[task_id])
            if task.instance_id!=task_id or task.repo!=expected_repo:
                raise RuntimeError("HYDRATED_TASK_MISMATCH")
            path,base,patch_path=resolve_task_snapshot_paths(
                DATA/"snapshots",task.instance_id,task.repo)
            paths,kind=source_paths(path)
            row.update(path_matches(paths,touched_source_paths(task.patch)))
            row["snapshot_kind"]=kind
            row["snapshot_path_readable"]=bool(paths)
            row["status"]="METADATA_COMPLETE" if paths else "SNAPSHOT_PATHS_UNAVAILABLE"
        except BaseException as exc:
            row["status"]="UNKNOWN_"+type(exc).__name__
        safe.append(row)
        print("GEMMA_VISIBLE_TEST_SAFE_TASK="+json.dumps(row,sort_keys=True),flush=True)
    result={
      "study":"real_official_public_dev_cpu_visible_repository_test_upperbound_v0",
      "tasks":4,"oracle_gold_used_ONLY_for_retrospective_path_membership":True,
      "zero_agent_inference":True,"zero_model_gpu":True,"zero_competition_submission":True,
      "no_private_task_text_patch_path_or_hidden_test_exported":True,
      "note":"Discovered filenames are not proof of executable/relevant model-visible tests. Gold touched paths must never be supplied to a model.",
      "rows":safe}
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("GEMMA_VISIBLE_TEST_CPU_AGGREGATE="+json.dumps({
        "tasks":len(safe),
        "complete":sum(r["status"]=="METADATA_COMPLETE" for r in safe),
        "any_filename_matched":sum(bool(r.get("touched_files_with_any_basename_test")) for r in safe),
        "all_rows":safe,"no_gpu":True,"no_submit":True
    },sort_keys=True),flush=True)

if __name__=="__main__":
    try:
        smoke();main()
    except BaseException as e:
        print("GEMMA_VISIBLE_TEST_CPU_BLOCKER="+type(e).__name__,flush=True)
        raise RuntimeError("PRIVATE_CPU_VISIBLE_TEST_GATE_FAILED") from None
