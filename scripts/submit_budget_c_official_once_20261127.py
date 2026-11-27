"""One-shot owner-requested official Gemma 31B C budget trial.

Exploratory 4/6 vs 3/6 on reused tasks; failed promotion gate. This is an owner-requested official trial, not a promoted Champion.
CLI modes intentionally separate build, bytes check and final submit.
Never retry an ambiguous official response or overwrite a Kaggle notebook.
"""
from __future__ import annotations
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import time
import zipfile

from scripts.build_behavioral_probe_timeout_safe_20261123 import _source_files,_pack
from scripts.budget_factorial_20261127 import arm_files
from scripts.submit_v2_toolcap60_official_once import (
    COMPETITION,authenticated_submissions,
)

KERNEL="kolihhan/gemma4-budget-c-submit-20261127"
MARKER="gemma31-budget-c-5min60-1024-20261127"
CANDIDATE_SHA="103070674849434a7e7ce93e74d4829996427097f2018a69d1dee0c1bda5df3f"
CHAMPION_SHA="ff08c10240a38e151a2ea1d0478e999ee5d2f437d2dad5571d912cf12859922b"
ACTIVE={"PENDING","RUNNING","SCORING","QUEUED","EVALUATING"}

def sha(b):
    return hashlib.sha256(b).hexdigest()

def verified_bytes(source:bytes)->bytes:
    arms=arm_files(_source_files(source))
    control,candidate=_pack(arms["champion"]),_pack(arms["C"])
    if sha(control)!=CHAMPION_SHA or sha(candidate)!=CANDIDATE_SHA:
        raise RuntimeError("unexpected frozen exact code bundle")
    with zipfile.ZipFile(io.BytesIO(control)) as a,zipfile.ZipFile(io.BytesIO(candidate)) as b:
        if a.testzip() is not None or b.testzip() is not None:
            raise RuntimeError("corrupt ZIP")
        members={"agent.yaml","eval_config.yaml","configs/sampling.yaml","prompts/system.md"}
        if set(a.namelist())!=members or set(b.namelist())!=members:
            raise RuntimeError("wrong ZIP membership")
        if any(a.read(name)!=b.read(name) for name in members-{"configs/sampling.yaml"}):
            raise RuntimeError("unexpected change beyond sampling")
    return candidate

def build_notebook(source:Path,out:Path)->dict:
    import nbformat
    if out.exists():raise FileExistsError("one-shot notebook overwrite prohibited")
    blob=verified_bytes(source.read_bytes())
    encoded=base64.b64encode(blob).decode("ascii")
    cell=("import base64,hashlib\nfrom pathlib import Path\n"
          +"payload=base64.b64decode("+repr(encoded)+",validate=True)\n"
          +"assert hashlib.sha256(payload).hexdigest()=="+repr(CANDIDATE_SHA)+"\n"
          +"Path('/kaggle/working/submission.zip').write_bytes(payload)\n"
          +"print('BUDGET_C_REMOTE_SHA256="+CANDIDATE_SHA+"')\n")
    nb=nbformat.v4.new_notebook(cells=[
       nbformat.v4.new_markdown_cell(
           "# 31B C budget trial — 5min / 60 calls / 1024 thinking\n\n"
           "Original Champion score 0.18 derived from the Apache-2.0 "
           "Budget-Fit V2 by lynnsakurai. Only the thinking budget is reduced from 4096 to 1024. "
           "This CPU notebook materializes an exact, validated ZIP; it does "
           "not run the model, train, evaluate, or submit."),
       nbformat.v4.new_code_cell(cell)])
    nb.metadata["kernelspec"]={"display_name":"Python 3","language":"python","name":"python3"}
    nbformat.validate(nb)
    out.mkdir()
    (out/"budget_c.ipynb").write_text(nbformat.writes(nb))
    meta={"id":KERNEL,"title":KERNEL.split("/")[1],
          "code_file":"budget_c.ipynb","language":"python",
          "kernel_type":"notebook","is_private":True,
          "enable_gpu":False,"enable_tpu":False,"enable_internet":False,
          "competition_sources":[COMPETITION],
          "dataset_sources":[],"kernel_sources":[],"model_sources":[]}
    (out/"kernel-metadata.json").write_text(json.dumps(meta,sort_keys=True,indent=2)+"\n")
    return {"sha256":CANDIDATE_SHA,"kernel":KERNEL,
            "source_champion_sha256":CHAMPION_SHA,
            "private_cpu_only":True,"official_submit":False}

def receipt(rows):
    matches=[r for r in rows if r.get("description")==MARKER]
    if len(matches)>1:raise RuntimeError("multiple exact receipts; abort")
    return {k:matches[0].get(k) for k in
            ("ref","date","status","publicScore","description")} if matches else None

def submit_exact_once(remote_zip:Path):
    from kaggle.api.kaggle_api_extended import KaggleApi
    api=KaggleApi()
    api.authenticate()
    blob=remote_zip.read_bytes()
    if sha(blob)!=CANDIDATE_SHA:
        raise RuntimeError("remote Kaggle CPU Notebook bytes differ")
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        if z.testzip():raise RuntimeError("remote ZIP corrupt")
    existing=receipt(authenticated_submissions())
    if existing:
        print("OFFICIAL_ALREADY_SUBMITTED="+json.dumps(existing,default=str),flush=True)
        return
    quota=api.competition_get_submission_limits(COMPETITION)
    rows=authenticated_submissions()
    if receipt(rows):
        print("OFFICIAL_ALREADY_SUBMITTED_AFTER_RECHECK",flush=True)
        return
    active=[{k:r.get(k) for k in ("ref","status")} for r in rows
            if str(r.get("status","")).split(".")[-1].upper() in ACTIVE]
    print("OFFICIAL_PRE_SUBMIT_GATE="+json.dumps({
      "allowed":quota.num_allowed_now,
      "limited_by_total":quota.limited_by_total,
      "active_count":len(active),"remote_sha256":CANDIDATE_SHA
    }),flush=True)
    if quota.num_allowed_now < 1 or quota.limited_by_total or active:
        raise RuntimeError("no legal Kaggle slot or active prior submission")
    print("OFFICIAL_ONE_SUBMIT_ATTEMPT="+MARKER,flush=True)
    try:
        api.competition_submit_code(
          file_name="submission.zip",message=MARKER,competition=COMPETITION,
          kernel=KERNEL,kernel_version=1,quiet=True)
    except BaseException as exc:
        response=getattr(exc,"response",None)
        status=getattr(response,"status_code",None)
        msg=str(getattr(response,"text","") or getattr(exc,"body","") or exc)
        categories={
           "pending":bool(re.search(r"pending|in.progress|already.*submission",msg,re.I)),
           "quota":bool(re.search(r"limit|quota|too many",msg,re.I)),
           "bad_request":bool(re.search(r"invalid|bad request",msg,re.I)),
           "permission":bool(re.search(r"forbidden|unauthorized|permission",msg,re.I))
        }
        print("OFFICIAL_SDK_EXCEPTION_SAFE="+json.dumps({
          "class":type(exc).__name__,"http":status,"categories":categories
        }),flush=True)
    # Ambiguous API return is NEVER authorization for a second attempt.
    for attempt in range(12):
        row=receipt(authenticated_submissions())
        if row:
            print("OFFICIAL_NEW_AUTHENTICATED_RECEIPT="+json.dumps(row,default=str),flush=True)
            return
        time.sleep(10)
    raise RuntimeError("UNKNOWN_OFFICIAL_RECEIPT_NO_AUTO_RETRY")

def main():
    p=argparse.ArgumentParser()
    sp=p.add_subparsers(dest="mode",required=True)
    build=sp.add_parser("build")
    build.add_argument("--source",type=Path,required=True)
    build.add_argument("--out",type=Path,required=True)
    do=sp.add_parser("submit")
    do.add_argument("--remote-zip",type=Path,required=True)
    args=p.parse_args()
    if args.mode=="build":
        print("BUDGET_C_CPU_NOTEBOOK="+json.dumps(build_notebook(args.source,args.out),sort_keys=True),flush=True)
    else:
        submit_exact_once(args.remote_zip)
if __name__=="__main__":main()
