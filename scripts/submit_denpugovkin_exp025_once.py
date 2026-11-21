"""One-shot submission of exp025 from public notebook, without executing untrusted notebook code."""
import ast, base64, csv, hashlib, io, json, subprocess, time, zipfile
from pathlib import Path
from kaggle.api.kaggle_api_extended import KaggleApi

COMP = "gemma-4-developer-agent"
SOURCE = "denpugovkin/gemma-4-repair-lab-compare-before-you-submit"
KERNEL = "kolihhan/gemma4-denpugovkin-exp025-20261121"
MARKER = "denpugovkin-exp025-patchsmith-40calls-20261121"
ROOT = Path("/tmp/denpugovkin-exp025-one-shot")
MEMBERS = {"LICENSE.txt","NOTICE.txt","agent.yaml","configs/sampling.yaml",
           "eval_config.yaml","prompts/system.md"}

def cmd(args, timeout=180):
    return subprocess.run(args,capture_output=True,text=True,check=True,timeout=timeout).stdout

def ledger():
    return list(csv.DictReader(io.StringIO(cmd(
        ["kaggle","competitions","submissions",COMP,"-v"],120).lstrip("\ufeff"))))

def receipt(rows):
    hits=[r for r in rows if r.get("description")==MARKER]
    if len(hits)>1: raise RuntimeError("DUPLICATE_RECEIPT_MANUAL_REVIEW")
    if not hits: return None
    return {k:hits[0].get(k) for k in
            ("ref","status","date","publicScore","privateScore","description")}

def quota(api):
    old=ledger()
    found=receipt(old)
    if found:
        print("ALREADY_SUBMITTED="+json.dumps(found,sort_keys=True),flush=True)
        return False
    lim=api.competition_get_submission_limits(COMP)
    active=[r.get("ref") for r in old if
            (r.get("status") or "").upper().split(".")[-1] in
            {"PENDING","RUNNING","QUEUED","SCORING","EVALUATING"}]
    print("LIVE_QUOTA="+json.dumps({"allowed":lim.num_allowed_now,
          "today":lim.num_today,"total_limit":lim.limited_by_total,
          "active":active}),flush=True)
    if lim.num_allowed_now<1 or lim.limited_by_total or active:
        raise RuntimeError("QUOTA_UNAVAILABLE_OR_ACTIVE_SUBMISSION")
    return True

def literal(nb,name):
    found=[]
    for cell in nb["cells"]:
        if cell.get("cell_type")!="code": continue
        src="".join(cell["source"])
        try: nodes=ast.parse(src).body
        except SyntaxError: continue
        for node in nodes:
            if isinstance(node,ast.Assign) and any(
              isinstance(x,ast.Name) and x.id==name for x in node.targets):
                found.append(ast.literal_eval(node.value))
    if len(found)!=1: raise RuntimeError(f"EXPECTED_ONE_{name}_FOUND_{len(found)}")
    return found[0]

def package():
    d=ROOT/"source"; d.mkdir(parents=True,exist_ok=True)
    cmd(["kaggle","kernels","pull",SOURCE,"-p",str(d),"--metadata"])
    nbfiles=list(d.glob("*.ipynb"))
    if len(nbfiles)!=1: raise RuntimeError("NOTEBOOK_NOT_UNIQUE")
    raw=nbfiles[0].read_bytes()
    nb=json.loads(raw)
    meta=json.loads((d/"kernel-metadata.json").read_text())
    if meta.get("id")!=SOURCE or COMP not in meta.get("competition_sources",[]):
        raise RuntimeError("SOURCE_MISMATCH")
    candidate=literal(nb,"CANDIDATE_FILES")
    control=literal(nb,"CONTROL_FILES")
    if set(candidate)!=MEMBERS or set(control)!=MEMBERS:
        raise RuntimeError("CHANGED_FILE_SET")
    if not all(isinstance(v,str) for v in candidate.values()):
        raise RuntimeError("NON_TEXT_MEMBER")
    if any(candidate[k]!=control[k] for k in MEMBERS-{"eval_config.yaml"}):
        raise RuntimeError("UNEXPECTED_RUNTIME_DIFFERENCES")
    if candidate["eval_config.yaml"]!=control["eval_config.yaml"].replace(
       "max_tool_calls: 28","max_tool_calls: 40",1):
        raise RuntimeError("NOT_EXPECTED_EXP025_40_CALLS")
    if "model: gemma-4-31b-it-qat-w4a16-ct" not in candidate["agent.yaml"]:
        raise RuntimeError("MODEL_MISMATCH")
    if "max_time_minutes: 8" not in candidate["eval_config.yaml"]:
        raise RuntimeError("TIME_MISMATCH")
    if "Patchsmith" not in candidate["NOTICE.txt"]:
        raise RuntimeError("MISSING_ATTRIBUTION")
    out=io.BytesIO()
    with zipfile.ZipFile(out,"w") as z:
        for k in sorted(candidate):
            info=zipfile.ZipInfo(k,date_time=(1980,1,1,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=0o100644<<16
            z.writestr(info,candidate[k].encode())
    buf=out.getvalue()
    with zipfile.ZipFile(io.BytesIO(buf)) as z:
        if z.testzip()!=None or set(z.namelist())!=MEMBERS:
            raise RuntimeError("BAD_ZIP")
        if any(z.read(k).decode()!=v for k,v in candidate.items()):
            raise RuntimeError("ZIP_CHANGED_FILE_BYTES")
    (ROOT/"submission.zip").write_bytes(buf)
    print("SOURCE_SHA256="+hashlib.sha256(raw).hexdigest(),flush=True)
    print("CANDIDATE_SHA256="+hashlib.sha256(buf).hexdigest(),flush=True)
    print("CANDIDATE_MEMBERS="+str(sorted(MEMBERS)),flush=True)
    return buf

def builder(payload):
    import nbformat
    sha=hashlib.sha256(payload).hexdigest()
    b64=base64.b64encode(payload).decode()
    script=("import base64, hashlib\nfrom pathlib import Path\n"
            f"data=base64.b64decode({b64!r},validate=True)\n"
            f"assert hashlib.sha256(data).hexdigest()=={sha!r}\n"
            "Path('/kaggle/working/submission.zip').write_bytes(data)\n"
            f"print('EXP025_REMOTE_SHA={sha}')\n")
    nb=nbformat.v4.new_notebook(cells=[
        nbformat.v4.new_markdown_cell(
          "# Den Pugovkin exp025 Patchsmith candidate\n\n"
          "Original notebook: https://www.kaggle.com/code/denpugovkin/gemma-4-repair-lab-compare-before-you-submit\n\n"
          "Upstream authors credited in bundled LICENSE.txt and NOTICE.txt. "
          "CPU-only private reproducibility builder; no training/inference."),
        nbformat.v4.new_code_cell(script)])
    nb.metadata["kernelspec"]={"display_name":"Python 3","language":"python","name":"python3"}
    nbformat.validate(nb)
    p=ROOT/"builder";p.mkdir()
    (p/"builder.ipynb").write_text(nbformat.writes(nb))
    (p/"kernel-metadata.json").write_text(json.dumps({
      "id":KERNEL,"title":"Den Pugovkin exp025 Patchsmith 40call candidate",
      "code_file":"builder.ipynb","language":"python","kernel_type":"notebook",
      "is_private":True,"enable_gpu":False,"enable_tpu":False,"enable_internet":False,
      "competition_sources":[COMP],"dataset_sources":[],"kernel_sources":[],
      "model_sources":[]},indent=2))
    return p

def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    api=KaggleApi();api.authenticate()
    if not quota(api):return
    payload=package()
    pushed=api.kernels_push(str(builder(payload)),timeout="600")
    versions=[getattr(pushed,k,None) for k in ("version_number","versionNumber")]
    versions=[v for v in versions if v is not None]
    if getattr(pushed,"error",None) or not versions or any(
        type(v)!=int or v<1 or v!=versions[0] for v in versions):
        raise RuntimeError("KERNEL_VERSION_UNCONFIRMED")
    version=versions[0]
    if getattr(pushed,"ref",None) not in (KERNEL,"/code/"+KERNEL):
        raise RuntimeError("KERNEL_REF_UNCONFIRMED")
    pinned=f"{KERNEL}/{version}"
    print("PRIVATE_BUILDER_PINNED="+pinned,flush=True)
    for _ in range(60):
        status=cmd(["kaggle","kernels","status",pinned],60)
        if "KernelWorkerStatus.COMPLETE" in status:break
        if any(x in status for x in
          ("KernelWorkerStatus.ERROR","KernelWorkerStatus.FAILED","KernelWorkerStatus.CANCELLED")):
            raise RuntimeError("PRIVATE_BUILDER_FAILED")
        time.sleep(10)
    else:raise RuntimeError("PRIVATE_BUILDER_TIMEOUT")
    remote=ROOT/"remote";remote.mkdir()
    cmd(["kaggle","kernels","output",pinned,"-p",str(remote),"-o"],180)
    if (remote/"submission.zip").read_bytes()!=payload:
        raise RuntimeError("REMOTE_ZIP_BYTES_DIFFER")
    print("EXACT_REMOTE_ZIP_VERIFIED="+hashlib.sha256(payload).hexdigest(),flush=True)
    if not quota(api):return
    print("OFFICIAL_SUBMIT_STARTED="+pinned,flush=True)
    try:
        response=api.competition_submit_code(
          file_name="submission.zip",message=MARKER,competition=COMP,
          kernel=KERNEL,kernel_version=version,quiet=True)
        print("SUBMIT_API_RESPONSE="+json.dumps(
          response.to_dict() if hasattr(response,"to_dict") else str(response),
          default=str,sort_keys=True),flush=True)
    except Exception as ex:
        print("SUBMIT_CLIENT_EXCEPTION="+type(ex).__name__,flush=True)
    for _ in range(15):
        entry=receipt(ledger())
        if entry and entry.get("ref"):
            print("OFFICIAL_RECEIPT="+json.dumps(entry,sort_keys=True),flush=True)
            return
        time.sleep(10)
    raise RuntimeError("RECEIPT_UNCONFIRMED_DO_NOT_RETRY")

if __name__=="__main__":
    main()
