"""Manual one-shot score-first candidate; never execute external notebooks.

Independent implementation of concise search/edit/check/submit policy, motivated
by public 40-call fast-path approach. Derives native config from the pinned
Apache-2.0 Budget-Fit source; preserves original model, sampling, tools and
command/scorer timeout. Four-minute task cap is a risk reduction, not proof
of full hidden-batch time safety.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
from pathlib import Path
import subprocess
import time
import zipfile
from urllib.parse import urlsplit

from scripts.build_toolcap60_timeout_recovery import (
    build as build_champion, files_for_candidate as champion_files,
)
from scripts.submit_v2_toolcap60_official_once import (
    authenticated_submissions, compile_without_inference, COMPETITION,
)

SOURCE = "lynnsakurai/gemma-4-budget-fit-agent-w-bounded-rescue/2"
CHAMPION_SHA = "ff08c10240a38e151a2ea1d0478e999ee5d2f437d2dad5571d912cf12859922b"
KERNEL = "kolihhan/gemma4-fastpath40-4min-20261124"
MARKER = "gemma31-fastpath40-4min-score-first-20261124"
ROOT = Path("/tmp/gemma-score-first-fastpath-20261124")

PROMPT = """You are a software engineer repairing the reported issue in /workspace.
The resulting Git patch is the answer. Prioritize the requested behavior, not
exhaustive analysis. Follow the issue's exact public API, error messages, and
existing project conventions.

1. Find the implementation using the most distinctive identifier, error text,
   or traceback location. Use a bounded git grep search and small read_file
   ranges. Read the immediate caller or relevant test only if needed to decide
   what change is correct. Avoid broad repository scans and redundant graph
   searches.
2. Once the likely cause is supported by source evidence, make the smallest
   complete source change. Do not wait for exhaustive certainty. Use edit_file
   with an exact unique old_string and a short replacement. If it fails, reread
   that region and use a smaller unique match. Keep the patch focused on the
   requested behavior.
3. Inspect the diff. If a relevant focused test or inexpensive executable
   check is available, run it with an explicit short shell timeout; never run
   the entire suite. Fix an actionable defect once if time permits. Missing
   dependencies or unrelated pre-existing failures are not reasons to undo a
   sound source fix. Do not modify evaluation infrastructure, existing tests
   just to pass, or leave scratch files in the repository.
4. Call submit_patch promptly once the change is ready; end the turn without
   further analysis. Use get_status when unsure of the time remaining. If time
   is short, finish the existing source change and submit rather than explore.

Budget: 40 tool calls, 4 minutes, 80 turns. Prefer an early evidence-based
source edit and a focused check over a long search or repeated verification.
Never fabricate evidence, access hidden tests or use the network.
"""


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build(source: bytes) -> bytes:
    if sha(build_champion(source)) != CHAMPION_SHA:
        raise ValueError("frozen Champion SHA mismatch")
    base = champion_files(source)
    cfg = base["eval_config.yaml"]
    for token in ("max_time_minutes: 5", "max_tool_calls: 60", "max_turns: 80", "timeout_seconds: 240"):
        if cfg.count(token) != 1:
            raise ValueError("unexpected Champion config")
    files = dict(base)
    files["eval_config.yaml"] = cfg.replace("max_time_minutes: 5","max_time_minutes: 4",1).replace(
        "max_tool_calls: 60","max_tool_calls: 40",1)
    files["prompts/system.md"] = PROMPT
    assert {k for k in files if files[k] != base[k]} == {"eval_config.yaml","prompts/system.md"}
    buf = io.BytesIO()
    with zipfile.ZipFile(buf,"w") as z:
        for name,body in sorted(files.items()):
            info = zipfile.ZipInfo(name,date_time=(2026,11,24,0,0,0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            z.writestr(info,body.encode())
    data=buf.getvalue()
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        assert z.testzip() is None and set(z.namelist())==set(base)
        assert z.read("agent.yaml").decode()==base["agent.yaml"]
        assert z.read("configs/sampling.yaml").decode()==base["configs/sampling.yaml"]
    return data


def receipt(rows):
    found=[r for r in rows if r.get("description")==MARKER]
    if len(found)>1:
        raise RuntimeError("duplicate receipt: stop")
    if not found:return None
    return {k:found[0].get(k) for k in ("ref","status","publicScore","date","description")}


def slot(api):
    rows=authenticated_submissions()
    existing=receipt(rows)
    if existing:
        print("FASTPATH_EXISTING_RECEIPT="+json.dumps(existing),flush=True)
        return False
    active=[r.get("ref") for r in rows if str(r.get("status")).upper().split(".")[-1] in
            {"PENDING","RUNNING","QUEUED","SCORING","EVALUATING"}]
    limits=api.competition_get_submission_limits(COMPETITION)
    print("FASTPATH_SLOT="+json.dumps({"allowed":limits.num_allowed_now,"active":active,
                                       "limited_by_total":limits.limited_by_total}),flush=True)
    if limits.num_allowed_now<1 or active or limits.limited_by_total:
        raise RuntimeError("no legal slot")
    return True


def main():
    from kaggle.api.kaggle_api_extended import KaggleApi
    import nbformat
    api=KaggleApi();api.authenticate()
    if not slot(api):return
    ROOT.mkdir()
    origin=ROOT/"source";origin.mkdir()
    subprocess.run(["kaggle","kernels","output",SOURCE,"-p",str(origin),"-o"],
                   stdout=subprocess.DEVNULL,check=True,timeout=180)
    candidate=build((origin/"submission.zip").read_bytes())
    compile_without_inference(candidate)
    expected=sha(candidate)
    print("FASTPATH_CANDIDATE_SHA="+expected,flush=True)
    print("FASTPATH_RUNTIME_SCENARIO="+json.dumps({
        "agent_minutes":4,"calls":40,"startup_seconds_assumed":1800,
        "setup_plus_overrun_seconds_per_task_assumed":45,"tasks_assumed":120,
        "estimated_seconds":120*(240+45)+1800,
        "not_a_hidden_runtime_guarantee":True
    }),flush=True)
    dest=ROOT/"kernel";dest.mkdir()
    encoded=base64.b64encode(candidate).decode("ascii")
    cell=("import hashlib,base64\nfrom pathlib import Path\n"
          f"data=base64.b64decode({encoded!r},validate=True)\n"
          f"assert hashlib.sha256(data).hexdigest()=={expected!r}\n"
          "Path('/kaggle/working/submission.zip').write_bytes(data)\n"
          "print('FASTPATH_ARCHIVE_VERIFIED')\n")
    nb=nbformat.v4.new_notebook(cells=[
        nbformat.v4.new_markdown_cell(
            "# FastPath 40/4\n\nIndependent concise repair strategy. Native configuration derived "
            "from lynnsakurai Budget-Fit v2 (Apache-2.0). Public inspiration: "
            "bliverrigpdoge LB 0.22 3 tweaks 40 tool calls; not an exact reproduction "
            "or a claimed score. Four minute budget reduces but does not eliminate timeout risk."),
        nbformat.v4.new_code_cell(cell)])
    nb.metadata["kernelspec"]={"display_name":"Python 3","language":"python","name":"python3"}
    nbformat.validate(nb)
    (dest/"fastpath.ipynb").write_text(nbformat.writes(nb))
    (dest/"kernel-metadata.json").write_text(json.dumps({
        "id":KERNEL,"title":KERNEL.split("/")[-1],"code_file":"fastpath.ipynb",
        "language":"python","kernel_type":"notebook","is_private":True,
        "enable_gpu":False,"enable_tpu":False,"enable_internet":False,
        "competition_sources":[COMPETITION],"dataset_sources":[],
        "kernel_sources":[],"model_sources":[]},sort_keys=True))
    if not slot(api):return
    push=api.kernels_push(str(dest),timeout="600")
    versions=[v for v in (getattr(push,"version_number",None),getattr(push,"versionNumber",None)) if v is not None]
    ref=getattr(push,"ref",None)
    url=getattr(push,"url",None)
    if getattr(push,"error",None) or not versions or any(type(v) is not int or v<1 for v in versions) or len(set(versions))!=1:
        raise RuntimeError("kernel version not verified")
    if ref not in (None,KERNEL,"/code/"+KERNEL):
        raise RuntimeError("kernel ref mismatch")
    if url:
        parsed=urlsplit(url)
        if parsed.scheme!="https" or parsed.netloc not in {"www.kaggle.com","kaggle.com"} or parsed.path.rstrip("/")!="/code/"+KERNEL:
            raise RuntimeError("kernel URL mismatch")
    if not ref and not url:
        raise RuntimeError("kernel identity not verified")
    version=versions[0];pinned=f"{KERNEL}/{version}"
    print("FASTPATH_CPU_BUILDER="+pinned,flush=True)
    for _ in range(75):
        p=subprocess.run(["kaggle","kernels","status",pinned],capture_output=True,text=True,timeout=60,check=True)
        if "KernelWorkerStatus.COMPLETE" in p.stdout:break
        if any(t in p.stdout for t in ("KernelWorkerStatus.ERROR","KernelWorkerStatus.FAILED","KernelWorkerStatus.CANCELLED")):
            raise RuntimeError("CPU builder failed")
        time.sleep(10)
    else:raise RuntimeError("CPU builder not complete")
    out=ROOT/"remote";out.mkdir()
    subprocess.run(["kaggle","kernels","output",pinned,"-p",str(out),"-o"],
                   check=True,stdout=subprocess.DEVNULL,timeout=180)
    if (out/"submission.zip").read_bytes()!=candidate:
        raise RuntimeError("remote candidate differs")
    print("FASTPATH_REMOTE_SHA_VERIFIED="+expected,flush=True)
    if not slot(api):return
    print("FASTPATH_ONE_OFFICIAL_SUBMIT_STARTED="+pinned,flush=True)
    try:
        resp=api.competition_submit_code(file_name="submission.zip",message=MARKER,
             competition=COMPETITION,kernel=KERNEL,kernel_version=version,quiet=True)
        print("FASTPATH_API_RESPONSE_TYPE="+type(resp).__name__,flush=True)
    except Exception as e:
        print("FASTPATH_API_EXCEPTION_TYPE="+type(e).__name__,flush=True)
    # Ambiguous API response is NOT a retry authorization.
    for _ in range(18):
        r=receipt(authenticated_submissions())
        if r:
            print("FASTPATH_AUTHENTICATED_RECEIPT="+json.dumps(r,sort_keys=True),flush=True)
            return
        time.sleep(10)
    raise RuntimeError("submission receipt unknown; do not retry")


if __name__=="__main__":
    main()
