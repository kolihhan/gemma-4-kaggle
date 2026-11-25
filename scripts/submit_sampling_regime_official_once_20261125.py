"""Owner-authorized, one-shot official sampling-regime trial.

Rank-2 public v19/v24 files differ only in sampling; 0.18 vs 0.24 is a
single official score per version, not proof of causality. Keep our exact
scored 5min Champion prompt, model, tools, limits and change only sampling.
No private GPU or model training. No blind retry, no duplicate submit.
"""
from __future__ import annotations
import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import time
from urllib.parse import urlsplit
import zipfile
import io

from scripts.render_sampling_regime31b_20261124 import make_pair
from scripts.submit_v2_toolcap60_official_once import (
    authenticated_submissions, compile_without_inference, COMPETITION,
)

SOURCE="lynnsakurai/gemma-4-budget-fit-agent-w-bounded-rescue/2"
KERNEL="kolihhan/gemma4-sampling60-5min-20261125"
MARKER="gemma31-sampling1-topk64-5min60-20261125"
CHAMPION_SHA="ff08c10240a38e151a2ea1d0478e999ee5d2f437d2dad5571d912cf12859922b"
CANDIDATE_SHA="6183b58d06209f5a2a0b399b57cfcaa766129ad3615d633ba2e2c9bc2b7fd50a"
ROOT=Path("/tmp/gemma-sampling-official-20261125")
ACTIVE={"PENDING","RUNNING","QUEUED","SCORING","EVALUATING"}

def sha(x):return hashlib.sha256(x).hexdigest()

def receipt(rows):
    match=[r for r in rows if r.get("description")==MARKER]
    if len(match)>1:raise RuntimeError("duplicate marker; stop")
    return {k:match[0].get(k) for k in ("ref","status","date","publicScore","description")} if match else None

def slot(api):
    rows=authenticated_submissions()
    if (old:=receipt(rows)):
        print("SAMPLING_EXISTING_RECEIPT="+json.dumps(old),flush=True)
        return False
    q=api.competition_get_submission_limits(COMPETITION)
    active=[]
    for r in rows:
        state=str(r.get("status") or "").upper().split(".")[-1]
        if state not in ACTIVE:continue
        dt=datetime.fromisoformat(r["date"].replace("Z","+00:00"))
        if dt.tzinfo is None:dt=dt.replace(tzinfo=timezone.utc)
        age=(datetime.now(timezone.utc)-dt).total_seconds()/3600
        active.append({"ref":str(r.get("ref")),"status":state,"age_hours":round(age,2)})
    print("SAMPLING_OFFICIAL_SLOT="+json.dumps({"allowed":q.num_allowed_now,"limited_by_total":q.limited_by_total,"active":active}),flush=True)
    if q.num_allowed_now<1 or q.limited_by_total:raise RuntimeError("Kaggle official submission allowance unavailable")
    # Explicit owner authorization for a distinct candidate. Only the known
    # stale FastPath receipt may coexist, and only when the platform itself
    # reports a legal unused slot. Do not interpret PENDING as failed.
    if any(r["ref"]!="58808118" or r["status"]!="PENDING" or r["age_hours"]<24 for r in active):
        raise RuntimeError("unexpected active submission; no parallel submit")
    return True

def main():
    from kaggle.api.kaggle_api_extended import KaggleApi
    import nbformat
    api=KaggleApi();api.authenticate()
    if not slot(api):return
    ROOT.mkdir()
    src=ROOT/"source";src.mkdir()
    subprocess.run(["kaggle","kernels","output",SOURCE,"-p",str(src),"-o"],check=True,stdout=subprocess.DEVNULL,timeout=180)
    c,t,czip,candidate,old,new=make_pair((src/"submission.zip").read_bytes())
    if sha(czip)!=CHAMPION_SHA or sha(candidate)!=CANDIDATE_SHA:
        raise RuntimeError("exact frozen package SHA mismatch")
    if {k for k in c if c[k]!=t[k]}!={"configs/sampling.yaml"}:
        raise RuntimeError("non-sampling change")
    compile_without_inference(candidate)
    print("SAMPLING_OFFICIAL_CANDIDATE="+json.dumps({"sha256":sha(candidate),"control_sha256":sha(czip),"old_sampling":old,"new_sampling":new,"only_changed":"configs/sampling.yaml","minutes":5,"calls":60,"private_gpu":False,"new_training":False,"gain_not_proven":True,"prior_scored_budget":True}),flush=True)
    dest=ROOT/"kernel";dest.mkdir()
    data=base64.b64encode(candidate).decode("ascii")
    cell="import base64, hashlib\nfrom pathlib import Path\n"+f"payload=base64.b64decode({data!r},validate=True)\nassert hashlib.sha256(payload).hexdigest()=={CANDIDATE_SHA!r}\nPath('/kaggle/working/submission.zip').write_bytes(payload)\n"
    nb=nbformat.v4.new_notebook(cells=[
        nbformat.v4.new_markdown_cell("# Sampling-only trial\n\nDerived from our 0.18 Champion (lynnsakurai Budget-Fit v2, Apache-2.0). Research motivation: muhammedidris28/gemma4-agent-runs v19/v24; no copied third-party prompt or training. This notebook packages a CPU-validated submission; it does not perform inference."),
        nbformat.v4.new_code_cell(cell)])
    nb.metadata["kernelspec"]={"display_name":"Python 3","language":"python","name":"python3"}
    nbformat.validate(nb)
    (dest/"sampling.ipynb").write_text(nbformat.writes(nb))
    (dest/"kernel-metadata.json").write_text(json.dumps({"id":KERNEL,"title":KERNEL.split("/")[-1],"code_file":"sampling.ipynb","language":"python","kernel_type":"notebook","is_private":True,"enable_gpu":False,"enable_tpu":False,"enable_internet":False,"competition_sources":[COMPETITION],"dataset_sources":[],"kernel_sources":[],"model_sources":[]}))
    if not slot(api):return
    # Same verified SDK path as the successful FastPath CPU builder.
    push=api.kernels_push(str(dest),timeout="600")
    vs=[v for v in (getattr(push,"version_number",None),getattr(push,"versionNumber",None)) if v is not None]
    ref=getattr(push,"ref",None);url=getattr(push,"url",None)
    if getattr(push,"error",None) or not vs or any(type(v) is not int or v<1 for v in vs) or len(set(vs))!=1:
        raise RuntimeError("CPU kernel receipt invalid; no submit")
    if ref not in (None,KERNEL,"/code/"+KERNEL):raise RuntimeError("CPU kernel ref mismatch")
    if url:
        u=urlsplit(url)
        if u.scheme!="https" or u.netloc not in {"www.kaggle.com","kaggle.com"} or u.path.rstrip("/")!="/code/"+KERNEL:
            raise RuntimeError("CPU kernel URL mismatch")
    if not ref and not url:raise RuntimeError("missing CPU kernel identity")
    version=vs[0];pinned=f"{KERNEL}/{version}"
    print("SAMPLING_CPU_KERNEL_RECEIPT="+pinned,flush=True)
    errors=0
    deadline=time.monotonic()+600
    while time.monotonic()<deadline:
        p=subprocess.run(["kaggle","kernels","status",pinned],capture_output=True,text=True,timeout=40)
        if p.returncode:
            errors+=1
            if errors>=3:raise RuntimeError("CPU kernel status unavailable; stop")
        else:
            errors=0
            raw=p.stdout+p.stderr
            if "KernelWorkerStatus.COMPLETE" in raw:break
            if any(s in raw for s in ("KernelWorkerStatus.ERROR","KernelWorkerStatus.FAILED","KernelWorkerStatus.CANCELLED")):
                raise RuntimeError("CPU kernel terminal failure")
        time.sleep(10)
    else:raise RuntimeError("CPU packaging not complete; no submission")
    out=ROOT/"remote";out.mkdir()
    subprocess.run(["kaggle","kernels","output",pinned,"-p",str(out),"-o"],check=True,stdout=subprocess.DEVNULL,timeout=120)
    if (out/"submission.zip").read_bytes()!=candidate:raise RuntimeError("remote candidate mismatch")
    print("SAMPLING_REMOTE_SHA_VERIFIED="+CANDIDATE_SHA,flush=True)
    if not slot(api):return
    print("SAMPLING_OFFICIAL_SUBMIT_ATTEMPT="+pinned,flush=True)
    try:
        r=api.competition_submit_code(file_name="submission.zip",message=MARKER,competition=COMPETITION,kernel=KERNEL,kernel_version=version,quiet=True)
        print("SAMPLING_OFFICIAL_RESPONSE_TYPE="+type(r).__name__,flush=True)
    except Exception as e:
        print("SAMPLING_OFFICIAL_EXCEPTION_TYPE="+type(e).__name__,flush=True)
    for _ in range(12):
        r=receipt(authenticated_submissions())
        if r:
            print("SAMPLING_AUTHENTICATED_RECEIPT="+json.dumps(r,sort_keys=True),flush=True)
            return
        time.sleep(10)
    raise RuntimeError("official receipt unknown; do not retry")

if __name__=="__main__":main()
