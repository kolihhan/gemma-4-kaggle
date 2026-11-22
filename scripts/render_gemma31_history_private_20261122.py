"""Render an unscored, private 2-issue 31B Candidate History diagnostic.

The scored 0.18 control archive, task manifest, model, 5min/60call budget
and exact Kaggle wheelhouse remain fixed. No official competition submission.
"""
from __future__ import annotations
import argparse
import base64
from hashlib import sha256
import json
from pathlib import Path

from scripts.build_gemma31_existing_tests import build
from scripts.render_gemma31_pair import IMAGE,MODEL,DATASET,SOLVER_INPUTS

REF = "kolihhan/gemma31-candidate-history-2issues-20261122-v1"
OFFSET, STOP = 11, 13
C0_SHA="ff08c10240a38e151a2ea1d0478e999ee5d2f437d2dad5571d912cf12859922b"

def make(source_zip:bytes, out:Path):
    plan=json.loads(Path("experiments/solver-v3/gemma31-existing-test-retrieval-20261117.json").read_text())
    original=Path("docs/evaluation/gemma-31-matched-validation-membership-2026-11-17.json").read_bytes()
    if sha256(original).hexdigest()!=plan["membership_sha256"]:
        raise ValueError("Frozen issue membership mismatch")
    cases=json.loads(original)["cases"]
    if len(cases)!=31 or [x["instance_id"] for x in cases[OFFSET:STOP]]!=["rich_3506","fastapi_15588"]:
        raise ValueError("Frozen diagnostic tasks changed")
    control,treatment=build(source_zip)
    if sha256(control).hexdigest()!=C0_SHA:raise ValueError("0.18 champion archive mismatch")
    prefix=Path("kaggle/verifier_baseline_runtime.py").read_text().split("\ndef materialize_submission",1)[0]
    body=Path("kaggle/gemma31_pair_solver.py").read_text()
    a="        order = tuple(config) if (OFFSET + index) % 2 == 0 else tuple(reversed(config))"
    b="        order = ('control',)  # Historical 0.18 Champion only: no treatment, no ensemble."
    if body.count(a)!=1:raise ValueError("Original solver loop drift")
    body=body.replace(a,b)
    a="    from swegemma.harness.agent_runner import run_agent_sandbox"
    b="    from scripts.gemma_candidate_history_live31 import run_with_history as run_agent_sandbox"
    if body.count(a)!=1:raise ValueError("Original official runner import drift")
    body=body.replace(a,b)
    a="            patch, error, trace = await run_agent_sandbox(sandbox, config[arm], task, snapshot)"
    b="            patch, error, trace = await run_agent_sandbox(sandbox, config[arm], task, snapshot, history_directory=directory / f'{instance}.history')"
    if body.count(a)!=1:raise ValueError("Original agent call drift")
    body=body.replace(a,b)
    # The unchanged reference scorer is not bundled: this private solver sees no gold/test patches.
    modules={}
    for name in ("scripts/candidate_history.py","scripts/gemma_candidate_history_live31.py"):
        blob=Path(name).read_bytes()
        compile(blob.decode(),name,"exec")
        modules[name]=base64.b64encode(blob).decode()
    prep=[
        "from pathlib import Path",
        "import base64,sys",
        "MODULE_ROOT=Path('/kaggle/working/gemma31-history-observer-private')",
        "MODULE_ROOT.mkdir(parents=True,exist_ok=True)",
        "(MODULE_ROOT/'scripts').mkdir(exist_ok=True)",
        "(MODULE_ROOT/'scripts'/'__init__.py').write_text('')",
    ]
    for name,b64 in modules.items():
        prep.append(f"(MODULE_ROOT/{name!r}).write_bytes(base64.b64decode({b64!r}))")
    prep.append("sys.path.insert(0,str(MODULE_ROOT))")
    assets={"PLAN":plan,"MODEL_NAME":MODEL,"CASES":[{"instance_id":c["instance_id"],"repo":c["repo"]} for c in cases],
            "OFFSET":OFFSET,"STOP":STOP,"ARM_ZIPS":{"control":base64.b64encode(control).decode(),
            "retrieval":base64.b64encode(treatment).decode()}}
    code="\n".join([prefix,*(f"{k} = {v!r}" for k,v in assets.items()),*prep,body])
    compile(code,"experiment.py","exec")
    out.mkdir(parents=True,exist_ok=False)
    (out/"experiment.py").write_text(code)
    meta={"id":REF,"title":REF.split("/")[-1],"code_file":"experiment.py",
          "language":"python","kernel_type":"script","is_private":True,
          "enable_gpu":True,"enable_tpu":False,"enable_internet":False,
          "machine_shape":"NvidiaL4","docker_image":IMAGE,
          "dataset_sources":[DATASET],"kernel_sources":[SOLVER_INPUTS],
          "competition_sources":[],"model_sources":[f"google/gemma-4/Other/{MODEL}/2"]}
    (out/"kernel-metadata.json").write_text(json.dumps(meta,sort_keys=True,indent=2))
    print("GEMMA_HISTORY_FROZEN_ISSUES=2")
    print("GEMMA_HISTORY_EXACT_CONTROL_SHA256="+sha256(control).hexdigest())
    print("GEMMA_HISTORY_MODEL="+MODEL)
    print("GEMMA_HISTORY_BUDGET_5MIN_60CALLS=TRUE")
    print("GEMMA_HISTORY_PRIVATE_DIAGNOSTIC_NO_OFFICIAL_SUBMISSION=TRUE")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--source-zip",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    make(args.source_zip.read_bytes(),args.out)
