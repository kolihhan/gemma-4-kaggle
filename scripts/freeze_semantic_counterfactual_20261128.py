"""Offline paired request construction for a diagnostic ONLY.

Input must be an actual captured OpenAI-compatible pre-edit request, not a
reconstructed narrative. This does not provide a model server, instrument the
official scorer, or prove that an injected packet is legal at competition time.
No networking, model invocation, or grading. Keep captured requests private.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

MODEL="gemma-4-31b-it-qat-w4a16-ct"
MAX_EVIDENCE_BYTES=4096
HEADER="Diagnostic observation at the frozen pre-edit checkpoint (not a solution):\n"

def canonical(obj):
    return json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode()

def digest(obj):
    return hashlib.sha256(canonical(obj)).hexdigest()

def freeze(request, evidence, case):
    if request.get("model","").removeprefix("openai/")!=MODEL:
        raise ValueError("not pinned 31B model")
    if not isinstance(request.get("messages"),list) or not request["messages"]:
        raise ValueError("missing captured message prefix")
    if not isinstance(request.get("tools"),list) or not request["tools"]:
        raise ValueError("missing captured tool schema")
    if request.get("stream"):
        raise ValueError("require non-streaming diagnostic request")
    if case.get("stage")!="pre_edit" or case.get("strict_eligible") is not True:
        raise ValueError("case not qualified")
    if case.get("checkpoint_verified") is not True:
        raise ValueError("capture and no-mutation checkpoint must be verified independently")
    if set(evidence)!={"source","observation","provenance_sha256"}:
        raise ValueError("unsupported evidence fields")
    if evidence["source"]!="issue_visible_base_execution":
        raise ValueError("unapproved evidence provenance")
    h=evidence["provenance_sha256"]
    if not isinstance(h,str) or len(h)!=64 or any(c not in "0123456789abcdef" for c in h):
        raise ValueError("missing execution provenance hash")
    observation=evidence["observation"]
    if not isinstance(observation,str) or not observation.strip() or len(observation.encode())>MAX_EVIDENCE_BYTES:
        raise ValueError("invalid observation")
    control=copy.deepcopy(request)
    treatment=copy.deepcopy(request)
    control["messages"].append({"role":"user","content":HEADER+"No additional observation supplied."})
    treatment["messages"].append({"role":"user","content":HEADER+observation})
    assert control["messages"][:-1]==treatment["messages"][:-1]==request["messages"]
    assert {k:v for k,v in control.items() if k!="messages"}=={k:v for k,v in treatment.items() if k!="messages"}
    return {"control":control,"treatment":treatment,
            "manifest":{"prefix_sha256":digest(request),"case_sha256":digest(case),
                        "evidence_sha256":digest(evidence),"control_sha256":digest(control),
                        "treatment_sha256":digest(treatment),
                        "only_changed_field":"messages[-1].content",
                        "context_lengths_equal":None,"model_inference":False,
                        "official_submission":False,"diagnostic_only":True}}

def smoke():
    r={"model":MODEL,"messages":[{"role":"user","content":"fixture"}],"tools":[{"type":"function","function":{"name":"read_file"}}],"temperature":0.2}
    e={"source":"issue_visible_base_execution","observation":"fixture output","provenance_sha256":"a"*64}
    c={"stage":"pre_edit","strict_eligible":True,"checkpoint_verified":True}
    out=freeze(r,e,c)
    assert len(r["messages"])==1 and out["control"]["messages"][0]==r["messages"][0]
    assert out["manifest"]["control_sha256"]!=out["manifest"]["treatment_sha256"]
    assert freeze(r,e,c)==out
    for bad in (dict(c,strict_eligible=False),dict(c,checkpoint_verified=False),dict(c,stage="post_edit")):
        try:freeze(r,e,bad)
        except ValueError:pass
        else:raise AssertionError("invalid checkpoint accepted")
    for bad in (dict(e,source="reference_patch"),dict(e,observation="x"*4097),dict(e,answer="hidden")):
        try:freeze(r,bad,c)
        except ValueError:pass
        else:raise AssertionError("invalid evidence accepted")
    print("SEMANTIC_PAIR_SMOKE=PASS")

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--smoke",action="store_true")
    p.add_argument("--request",type=Path);p.add_argument("--evidence",type=Path);p.add_argument("--case",type=Path);p.add_argument("--out",type=Path)
    a=p.parse_args()
    if a.smoke:smoke()
    else:
        if not all((a.request,a.evidence,a.case,a.out)):p.error("all four paths required")
        out=freeze(*(json.loads(x.read_text()) for x in (a.request,a.evidence,a.case)))
        # Private local directory only. No printing raw request data.
        a.out.mkdir(parents=True,exist_ok=False)
        for k,v in out.items():
            dest=a.out/(k+".json")
            with dest.open("x",encoding="utf-8") as f:json.dump(v,f,ensure_ascii=False,indent=2)
            dest.chmod(0o600)
        print(json.dumps(out["manifest"],sort_keys=True))
