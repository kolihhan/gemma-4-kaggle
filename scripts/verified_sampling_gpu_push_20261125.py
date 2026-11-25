"""Verified single GPU registration, fail closed on ambiguous push.

Reuse existing, verified terminal v1 kernel as a new version of the exact
sampling-v2 repair. No automatic retry, no official submission.
"""
from __future__ import annotations
import argparse
import inspect
import json
import re
import subprocess
import time
from pathlib import Path
from urllib.parse import urlsplit

def validate_receipt(response, expected):
    if getattr(response,"error",None):
        raise RuntimeError("Kaggle returned a push error")
    versions=[getattr(response,k,None) for k in ("version_number","versionNumber")]
    versions=[v for v in versions if v is not None]
    if not versions or any(type(v) is not int or v<2 for v in versions) or len(set(versions))!=1:
        raise RuntimeError("new version receipt absent or invalid; do not retry")
    ref=getattr(response,"ref",None)
    url=getattr(response,"url",None)
    if ref not in (None,expected,"/code/"+expected):
        raise RuntimeError("receipt ref mismatch")
    if url:
        u=urlsplit(url)
        if u.scheme!="https" or u.netloc not in {"www.kaggle.com","kaggle.com"} or u.path.rstrip("/")!="/code/"+expected:
            raise RuntimeError("receipt URL mismatch")
    if not ref and not url:
        raise RuntimeError("receipt has no verified identity")
    return expected+"/"+str(versions[0])

def status(ref):
    p=subprocess.run(["kaggle","kernels","status",ref],capture_output=True,text=True,timeout=30)
    raw=p.stdout+p.stderr
    matches=set(re.findall(r"KernelWorkerStatus\.([A-Z_]+)",raw))
    if p.returncode==0 and len(matches)==1:
        return matches.pop()
    if re.search(r"not found|404",raw,re.I):return "NOT_FOUND"
    if re.search(r"forbidden|permission|401|403",raw,re.I):return "AUTH_ERROR"
    return "QUERY_ERROR"

def selftest():
    from types import SimpleNamespace as R
    ref="kolihhan/gemma4-sampling-regime-paired-20261124-v1"
    assert validate_receipt(R(version_number=2,ref=ref,error=None),ref)==ref+"/2"
    for bad in [R(version_number=1,ref=ref),R(version_number=2,ref=ref,error="failure"),R(version_number=None,ref=ref),R(version_number=2,ref="wrong/ref"),R(version_number=2)]:
        try:validate_receipt(bad,ref)
        except RuntimeError:pass
        else:raise AssertionError("accepted invalid registration receipt")
    print("REGISTRATION_RECEIPT_FIXTURES_PASS",flush=True)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--directory",type=Path,required=True)
    p.add_argument("--receipt",type=Path,required=True)
    a=p.parse_args()
    selftest()
    ref="kolihhan/gemma4-sampling-regime-paired-20261124-v1"
    missing="kolihhan/gemma4-sampling-regime-paired-20261124-v2"
    s1,s2=status(ref),status(missing)
    print("KAGGLE_PRE_PUSH_STATES="+json.dumps({"existing_v1":s1,"missing_v2":s2}),flush=True)
    if s1!="ERROR" or s2!="NOT_FOUND":
        raise RuntimeError("not safe to reuse terminal kernel; no push")
    m=a.directory/"kernel-metadata.json"
    d=json.loads(m.read_text())
    if d.get("id")!=missing or not d.get("is_private") or not d.get("enable_gpu") or d.get("enable_internet"):
        raise RuntimeError("unexpected rendered metadata")
    d["id"]=ref;d["title"]=ref.split("/")[1]
    m.write_text(json.dumps(d,indent=2))
    from kaggle.api.kaggle_api_extended import KaggleApi
    api=KaggleApi();api.authenticate()
    params=inspect.signature(api.kernels_push).parameters
    if "accelerator" not in params or "timeout" not in params:
        raise RuntimeError("SDK cannot explicitly pin GPU/runtime")
    print("KAGGLE_ONE_PUSH_ATTEMPT",flush=True)
    resp=api.kernels_push(str(a.directory),accelerator="NvidiaL4",timeout="9000")
    pinned=validate_receipt(resp,ref)
    print("KAGGLE_VERSION_RECEIPT="+pinned,flush=True)
    # Persist the receipt immediately even if visibility verification fails.
    a.receipt.write_text(pinned+"\n")
    deadline=time.monotonic()+120
    while time.monotonic()<deadline:
        st=status(pinned)
        print("KAGGLE_REGISTRATION_CHECK="+st,flush=True)
        if st in {"QUEUED","RUNNING","COMPLETE","ERROR","FAILED","CANCELLED"}:
            print("KAGGLE_REGISTERED_VERSION="+pinned,flush=True)
            return
        if st=="AUTH_ERROR":break
        time.sleep(10)
    raise RuntimeError("registration unconfirmed; no long poll, no retry")

if __name__=="__main__":main()
