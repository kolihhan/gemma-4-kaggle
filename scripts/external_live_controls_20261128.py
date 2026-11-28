"""External benchmark calibration only. No model, Kaggle credential or submission."""
import hashlib
import json
import re
import subprocess
import tempfile
import time
from pathlib import Path

from datasets import load_dataset
from huggingface_hub import HfApi, hf_hub_download
from swebench.harness.test_spec.test_spec import make_test_spec
from swebench.harness.grading import get_eval_report, get_logs_eval

DATASET = "SWE-bench-Live/SWE-bench-Live"
UPSTREAM = "40cc8d4bf39d7e0955874b74dd31d0faf5606419"
SEED = "gemma-external-control-pilot-20261128-v1"
EXCLUDED = {"fastapi/fastapi", "tiangolo/fastapi", "textualize/rich", "psf/requests", "encode/httpx"}


def cmd(args, timeout=90):
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)


def as_list(v):
    return json.loads(v) if isinstance(v, str) else list(v or [])


def select():
    # Resolve and pin one dataset revision before selection.
    revision = HfApi().dataset_info(DATASET).sha
    assert re.fullmatch(r"[0-9a-f]{40}", revision)
    import urllib.request
    url = f"https://raw.githubusercontent.com/lspecian/gemma4-moving-failures/{UPSTREAM}/experiments/unseen100_ids.txt"
    with urllib.request.urlopen(url, timeout=30) as r:
        old = r.read(100000).decode().splitlines()
    assert len(old) == len(set(old)) == 99
    banned = EXCLUDED | {re.sub(r"-\d+.*$", "", x).replace("__", "/", 1).lower() for x in old}
    pool = []
    ds = load_dataset(DATASET, split="test", revision=revision)
    for row in ds:
        date = str(row.get("created_at") or "")
        repo = row["repo"].lower()
        statement = row.get("problem_statement") or ""
        f2p, p2p = as_list(row.get("FAIL_TO_PASS")), as_list(row.get("PASS_TO_PASS"))
        diff = row.get("difficulty") or {}
        # Small resource-bounded diagnostic cohort, not representative leaderboard.
        if (date < "2025-02-01" or repo in banned or len(statement.strip()) < 150
            or row.get("log_parser") != "pytest" or not 1 <= len(f2p) <= 10
            or not 1 <= len(p2p) <= 300 or not row.get("patch") or not row.get("test_patch")
            or not 1 <= int(diff.get("lines") or 0) <= 100):
            continue
        pool.append(row)
    ranked = sorted(pool, key=lambda x: hashlib.sha256((SEED+"|"+x["instance_id"]).encode()).hexdigest())
    chosen = []
    for row in ranked:
        if row["repo"].lower() not in {r["repo"].lower() for r in chosen}:
            chosen.append(row)
        if len(chosen) == 2:
            break
    assert len(chosen) == 2
    print("EXTERNAL_FROZEN="+json.dumps({"dataset":DATASET,"revision":revision,"pool":len(pool),"selected":[r["instance_id"] for r in chosen],
          "base_commits":[r["base_commit"] for r in chosen],"exclude_repositories":len(banned),"seed":SEED}),flush=True)
    return chosen


def control(row, spec, image_id, kind):
    started = time.monotonic()
    result = {"control":kind,"status":"BLOCKED"}
    container = None
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp)
        try:
            # No host mount, network, credential injection, GPU or privileged mode.
            c = cmd(["docker","create","--network","none","--cap-drop","ALL","--security-opt","no-new-privileges",
                     "--pids-limit","256","--memory","5g","--cpus","2","--entrypoint","/bin/bash",
                     image_id,"-c","sleep infinity"])
            if c.returncode:
                result["phase"]="container_create";return result
            container = c.stdout.strip()
            if cmd(["docker","start",container]).returncode:
                result["phase"]="container_start";return result
            head = cmd(["docker","exec","-w","/testbed",container,"git","rev-parse","HEAD"])
            if head.returncode or head.stdout.strip() != row["base_commit"]:
                result["phase"]="base_commit_mismatch";return result
            if kind == "gold":
                patch = p/"patch.diff"
                patch.write_text(row["patch"].rstrip("\n")+"\n")
                if cmd(["docker","cp",str(patch),container+":/tmp/control.diff"]).returncode:
                    result["phase"]="patch_copy";return result
                applied = cmd(["docker","exec","-w","/testbed",container,"git","apply","--recount","/tmp/control.diff"])
                if applied.returncode:
                    result["phase"]="gold_patch_apply";return result
            e = p/"eval.sh"; e.write_text(spec.eval_script)
            if cmd(["docker","cp",str(e),container+":/tmp/control-eval.sh"]).returncode:
                result["phase"]="test_script_copy";return result
            log = p/"test.log"
            with log.open("w") as f:
                proc=subprocess.run(["docker","exec",container,"/bin/bash","/tmp/control-eval.sh"],stdout=f,stderr=subprocess.STDOUT,timeout=600)
            result["script_exit"]=proc.returncode
            if log.stat().st_size > 20_000_000:
                result["phase"]="log_too_large";return result
            status, found = get_logs_eval(spec,str(log))
            if not found or not status:
                result["phase"]="test_output_missing_or_invalid";return result
            targets = as_list(row["FAIL_TO_PASS"])
            counts = {k:sum(str(status.get(t,"MISSING")).upper()==k for t in targets) for k in ("PASSED","FAILED","MISSING","ERROR","SKIPPED")}
            result["f2p_observed"]=counts
            report = get_eval_report(spec,{"instance_id":row["instance_id"],"model_patch":row["patch"] if kind=="gold" else "","model_name_or_path":"control"},str(log),True)[row["instance_id"]]
            result["upstream_resolved"]=bool(report["resolved"])
            # Require actual observed target failures for noop, full observed target passes and
            # upstream regression gate for gold. Missing/collection issues cannot qualify.
            if all(str(status.get(t,"")).upper()=="PASSED" for t in targets) and report["resolved"]:
                result["status"]="PASS"
            elif counts["FAILED"]>0:
                result["status"]="FAIL"
            else:
                result["phase"]="targets_not_discriminating"
            return result
        except subprocess.TimeoutExpired:
            result["phase"]="timeout";return result
        except Exception as exc:
            result["phase"]="exception_"+type(exc).__name__;return result
        finally:
            if container:
                cmd(["docker","rm","-f",container])
            result["seconds"]=round(time.monotonic()-started,2)


def main():
    rows = select()
    records=[]
    for row in rows:
        spec=make_test_spec(row,namespace="starryzhang")
        result={"instance_id":row["instance_id"],"image":spec.instance_image_key}
        try:
            pull=cmd(["docker","pull",spec.instance_image_key],timeout=300)
            if pull.returncode:
                result["status"]="IMAGE_PULL_BLOCKED"
            else:
                info=cmd(["docker","image","inspect",spec.instance_image_key,"--format","{{.Id}}"])
                if info.returncode or not re.fullmatch(r"sha256:[0-9a-f]{64}",info.stdout.strip()):
                    raise ValueError("image digest unavailable")
                image=info.stdout.strip()
                result["image_id"]=image
                result["gold"]=control(row,spec,image,"gold")
                result["noop"]=control(row,spec,image,"noop")
                result["qualified"]=result["gold"]["status"]=="PASS" and result["noop"]["status"]=="FAIL"
        except Exception as exc:
            result["status"]="BLOCKED_"+type(exc).__name__
        finally:
            cmd(["docker","image","rm",spec.instance_image_key],timeout=120)
        records.append(result)
        print("EXTERNAL_CONTROL="+json.dumps(result,sort_keys=True),flush=True)
    print("EXTERNAL_SUMMARY="+json.dumps({"tasks":len(records),"qualified":sum(bool(r.get("qualified")) for r in records),"gpu":False,"model_inference":False,"kaggle_submission":False,"official_equivalence":False}),flush=True)


if __name__ == "__main__":
    main()
