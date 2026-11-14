"""One frozen Scale-SWE independent container test: baseline FAIL then model PASS.

Source: first of eight NVIDIA v2.0/sweagent accepted success cases.
Only Nvidia MODEL patch is applied. Gold fix is never read. The official
Scale-SWE image is executed with no network, low memory, no new privileges.
Runs <= 3 source-defined F2P test selectors, separately before/after repair.
Prints only pytest exit codes, JUnit counts and aggregate verdict.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
from tempfile import TemporaryDirectory
from xml.etree import ElementTree as ET

from scripts.check_scale_swe_model_patch_apply import fetch_nvidia_fixed_eight, get_scale_match

MAX_TESTS=3


def invoke(args:list[str], *, stdin:str|None=None, timeout:int=150)->tuple[int,str]:
    try:
        p=subprocess.run(args,input=stdin,stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,text=True,timeout=timeout,
                         check=False,env={**os.environ,"GIT_TERMINAL_PROMPT":"0"})
    except (OSError,subprocess.TimeoutExpired):
        return (124,"")
    return (p.returncode,p.stdout)


def workdir_sane(workdir:object)->bool:
    if not isinstance(workdir,str) or not workdir.startswith("/workspace/"):
        return False
    if len(workdir)>200 or any(p in (".","..","") for p in workdir[1:].split("/")):
        return False
    return True


def test_selectors(meta:dict)->list[str]:
    synthetic=meta.get("f2p_script")
    if isinstance(synthetic,str) and synthetic.strip():
        return ["test_fail_to_pass.py"]
    target=meta.get("FAIL_TO_PASS")
    try:
        names=json.loads(target) if isinstance(target,str) else target
    except ValueError:
        return []
    if not isinstance(names,list) or not names:
        return []
    chosen=[]
    for name in names[:MAX_TESTS]:
        if not isinstance(name,str) or len(name)>175:
            return []
        if not re.fullmatch(r"[A-Za-z0-9_./\[\]:-]+",name) or ".." in name or name.startswith("/"):
            return []
        if ".py" not in name:
            return []
        chosen.append(name)
    return chosen


def junit_counts(container:str,location:str)->dict|None:
    code,xml=invoke(["docker","exec",container,"cat",location],timeout=20)
    if code!=0 or not xml:
        return None
    try:
        root=ET.fromstring(xml)
    except ET.ParseError:
        return None
    suites=list(root.iter("testsuite"))
    if not suites:
        return None
    return {
        name:sum(int(s.get(name,0)) for s in suites)
        for name in ("tests","failures","errors","skipped")
    }


def run_test(container:str,workdir:str,which:str,selectors:list[str])->dict:
    outfile="/tmp/gemma_scale_"+which+".xml"
    cmd=["docker","exec","--workdir",workdir,container,
         "python","-m","pytest","-q","-x","--disable-warnings",
         "--junitxml="+outfile,*selectors]
    exitcode,_=invoke(cmd,timeout=140)
    return {"exit_code":exitcode,"junit":junit_counts(container,outfile)}


def fetch_gold_for_control_only(instance_id:str)->str:
    """Read upstream Scale-SWE gold patch ONLY for isolated benchmark integrity.

    Not a training target, model context or inference hint; never print it.
    """
    from scripts.join_scale_swe_parquet_eight import validate_catalog, may_contain
    import fsspec
    import pyarrow.parquet as pq
    matches=[]
    for uri in validate_catalog():
        with fsspec.open(uri,mode="rb",block_size=1<<16,
                         cache_type="none",timeout=40) as handle:
            pf=pq.ParquetFile(handle)
            for rg in range(pf.metadata.num_row_groups):
                group=pf.metadata.row_group(rg)
                ix=next((i for i in range(group.num_columns)
                         if group.column(i).path_in_schema=="instance_id"),None)
                if ix is not None and not may_contain(group.column(ix).statistics,{instance_id}):
                    continue
                ids=pf.read_row_group(rg,columns=["instance_id"])["instance_id"].to_pylist()
                positions=[i for i,val in enumerate(ids) if val==instance_id]
                if not positions:
                    continue
                col=pf.read_row_group(rg,columns=["patch"])["patch"]
                matches.extend(col[i].as_py() for i in positions)
    if len(matches)!=1 or not isinstance(matches[0],str) or not matches[0].startswith("diff --git "):
        raise ValueError("unique official reference fix unavailable")
    return matches[0]


def image_size_gate(image:str)->str:
    """Reject unknown or over-budget image manifests BEFORE any Docker pull."""
    code, body=invoke(["docker","manifest","inspect",image],timeout=80)
    if code!=0:
        return "image_manifest_unavailable"
    try:
        obj=json.loads(body)
    except ValueError:
        return "image_manifest_invalid"
    layers=obj.get("layers") if isinstance(obj,dict) else None
    if not isinstance(layers,list) or not layers:
        return "image_layers_unknown"
    size=[x.get("size") for x in layers if isinstance(x,dict)]
    if len(size)!=len(layers) or not all(isinstance(v,int) and v>0 for v in size):
        return "image_layers_unknown"
    if sum(size)>1_500_000_000:
        return "image_above_1p5GB_cap"
    return "image_under_1p5GB_cap"


def run(case_index:int=0, gold_control:bool=False)->dict:
    if case_index not in range(8):
        raise ValueError("only original eight task IDs are allowed")
    selected=fetch_nvidia_fixed_eight()
    source=get_scale_match(selected)
    fixed_id=list(selected)[case_index]
    meta=source[fixed_id]
    model_patch=(fetch_gold_for_control_only(fixed_id) if gold_control
                 else selected[fixed_id]["model_patch"])
    image=meta.get("image_url")
    workdir=meta.get("workdir")
    if not isinstance(image,str) or not re.fullmatch(r"aweaiteam/scaleswe:[A-Za-z0-9_.-]{5,180}",image):
        return {"status":"untrusted_image"}
    if not workdir_sane(workdir):
        return {"status":"invalid_source_workdir"}
    targets=test_selectors(meta)
    if not targets:
        return {"status":"unsupported_test_selector"}
    manifest=image_size_gate(image)
    if manifest!="image_under_1p5GB_cap":
        return {"status":manifest, "frozen_case_index":case_index}

    pull,_=invoke(["docker","pull","--quiet",image],timeout=410)
    if pull!=0:
        return {"status":"source_docker_pull_failed"}
    container="gemma_scale_replay_case"+str(case_index)
    cmd=["docker","create","--name",container,
         "--network","none","--memory","5g","--cpus","2",
         "--pids-limit","256","--cap-drop","ALL",
         "--security-opt","no-new-privileges",
         "--tmpfs","/tmp:rw,size=512m",
         image,"sleep","720"]
    status,_=invoke(cmd,timeout=45)
    if status!=0:
        return {"status":"isolated_container_create_failed"}
    try:
        start,_=invoke(["docker","start",container],timeout=35)
        if start!=0:
            return {"status":"isolated_container_start_failed"}
        reset,_=invoke(["docker","exec","-w",workdir,container,
                        "git","reset","--hard",meta["parent_commit"]],timeout=70)
        if reset!=0:
            return {"status":"source_base_reset_failed"}
        f2p_patch=meta.get("f2p_patch")
        synthetic=meta.get("f2p_script")
        if isinstance(synthetic,str) and synthetic.strip():
            # Source synthetic test saved only inside ephemeral runner/container.
            with TemporaryDirectory(prefix="scale_f2p_") as root:
                testfile=Path(root)/"test_fail_to_pass.py"
                testfile.write_text(synthetic,encoding="utf-8")
                ret,_=invoke(["docker","cp",str(testfile),
                              container+":"+workdir+"/test_fail_to_pass.py"],timeout=35)
            if ret!=0:
                return {"status":"synthetic_test_install_failed"}
        elif isinstance(f2p_patch,str) and f2p_patch.strip():
            ret,_=invoke(["docker","exec","-i","-w",workdir,
                          container,"git","apply","-"],stdin=f2p_patch,timeout=50)
            if ret!=0:
                return {"status":"f2p_test_patch_apply_failed"}
        else:
            return {"status":"missing_f2p_test"}
        before=run_test(container,workdir,"baseline",targets)
        if before["junit"] is None:
            return {"status":"baseline_junit_unavailable",
                    "baseline_exit_code":before["exit_code"]}
        ret,_=invoke(["docker","exec","-i","-w",workdir,
                      container,"git","apply","--check","-"],stdin=model_patch,timeout=55)
        if ret!=0:
            return {"status":"model_patch_not_applicable_after_f2p_test_install",
                    "baseline":before}
        ret,_=invoke(["docker","exec","-i","-w",workdir,
                      container,"git","apply","-"],stdin=model_patch,timeout=55)
        if ret!=0:
            return {"status":"model_patch_apply_failed","baseline":before}
        after=run_test(container,workdir,"patched",targets)
        base=before["junit"]
        fixed=after["junit"]
        valid=(before["exit_code"]==1 and base["failures"]>=1 and base["errors"]==0
               and after["exit_code"]==0 and fixed is not None and
               fixed["tests"]>=1 and fixed["failures"]==0 and fixed["errors"]==0)
        return {"status":("F2P_BASELINE_FAIL_GOLD_PASS" if gold_control
                          else "F2P_BASELINE_FAIL_MODEL_PASS") if valid
                else ("F2P_GOLD_CONTROL_NOT_CONFIRMED" if gold_control
                      else "F2P_NOT_INDEPENDENTLY_CONFIRMED"),
                "patch_source":"upstream_gold_integrity_control_ONLY" if gold_control else "nvidia_model",
                "frozen_case_index":case_index,
                "test_origin":"source_synthetic_f2p_script" if isinstance(synthetic,str) and synthetic.strip() else "source_developer_f2p_patch",
                "num_selected_test_ids":len(targets),
                "before":before,"after":after,
                "test_environment":"same_isolated_offline_container_before_after",
                "no_gold_patch_used":not gold_control,
                "gold_patch_used_for_training_or_model_context":False,
                "training_started":False,"official_submission":False}
    finally:
        invoke(["docker","rm","-f",container],timeout=30)


if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--case-index",type=int,choices=list(range(8)),default=0)
    parser.add_argument("--gold-control",action="store_true")
    options=parser.parse_args()
    try:
        out=run(options.case_index, options.gold_control)
        print("GEMMA_SCALE_FIRST_CONTAINER_F2P="+json.dumps(out,sort_keys=True),flush=True)
    except Exception as e:
        print("GEMMA_SCALE_FIRST_CONTAINER_F2P_BLOCKED="+json.dumps({
            "error_class":type(e).__name__,
            "source_contents_or_secrets_logged":False}),flush=True)
        raise SystemExit(1) from None
