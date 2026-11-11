"""Reproduce a PUBLIC Kaggle prompt-only alternative without executing notebook code.

Unmodified competitor bundle is NOT a new scored result. Two variants:
  * original8: exact public four-file contents (8-minute cap)
  * matched5: change only time cap to 5 minutes to match user's V2 5m
Public source: bliverrigpdoge/lb-0-22-4-config-files-no-training.
Notebooks are pulled from Kaggle externally; their code isn't stored here.
"""
from __future__ import annotations
import argparse
import ast
import hashlib
import io
import json
from pathlib import Path
import zipfile

from scripts.prepare_public_budgetfit_v2 import (
    EXPECTED_ZIP_SHA256,
    EXPECTED_MEMBERS,
    validate_source_zip,
)

PUBLIC_REF="bliverrigpdoge/lb-0-22-4-config-files-no-training"
EXPECTED_PUBLIC_PROMPT_SHA="475cc9b7fcc0dc295532f5cb5e1928f26a491f501837ad08b1c79bdbe1a3eaa4"
EXPECTED_V2_PROMPT_SHA=EXPECTED_MEMBERS["prompts/system.md"]
STAMP=(2026,11,11,0,0,0)


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def notebook_bundle(notebook_path: Path) -> dict[str,str]:
    """Only parse literal dicts; NEVER execute third-party notebook source."""
    raw=json.loads(notebook_path.read_text(encoding="utf-8"))
    found=[]
    for cell in raw.get("cells",[]):
        if cell.get("cell_type")!="code":
            continue
        source=cell.get("source","")
        if isinstance(source,list):
            source="".join(source)
        if not isinstance(source,str):
            continue
        try:
            tree=ast.parse(source)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node,ast.Dict):
                continue
            try:
                value=ast.literal_eval(node)
            except (ValueError,TypeError,OverflowError,RecursionError):
                continue
            if (isinstance(value,dict) and
                set(value)==set(EXPECTED_MEMBERS) and
                all(isinstance(k,str) and isinstance(v,str)
                    for k,v in value.items())):
                found.append(value)
    if len(found)!=1:
        raise ValueError("public notebook has no unique four-file literal bundle")
    result=found[0]
    if digest(result["prompts/system.md"].encode())!=EXPECTED_PUBLIC_PROMPT_SHA:
        raise ValueError("public Notebook prompt changed; source must be re-audited")
    return result


def candidate_files(source_zip: bytes, public: dict[str,str], *,
                    minutes: int) -> dict[str,str]:
    baseline=validate_source_zip(source_zip)
    if minutes not in (5,8):
        raise ValueError("time budget variant must be 5 or 8")
    if set(public)!=set(baseline):
        raise ValueError("public four-file structure drift")
    for name in baseline:
        if name!="prompts/system.md" and public[name]!=baseline[name]:
            raise ValueError("public Notebook changed another file: "+name)
    if digest(baseline["prompts/system.md"].encode())!=EXPECTED_V2_PROMPT_SHA:
        raise ValueError("reference prompt drift")
    if digest(public["prompts/system.md"].encode())!=EXPECTED_PUBLIC_PROMPT_SHA:
        raise ValueError("external prompt digest drift")
    cfg=public["eval_config.yaml"]
    if cfg.count("max_time_minutes: 8")!=1:
        raise ValueError("cannot identify exact original 8-minute cap")
    if cfg.count("max_tool_calls: 28")!=1 or cfg.count("max_turns: 80")!=1:
        raise ValueError("unexpected original tool or turn budget")
    result=dict(public)
    if minutes==5:
        result["eval_config.yaml"]=cfg.replace(
            "max_time_minutes: 8","max_time_minutes: 5",1)
    # Prove the treatment changes no model, tools, sampling, or other config.
    if any(result[k]!=baseline[k] for k in baseline
           if k not in ("prompts/system.md","eval_config.yaml")):
        raise ValueError("uncontrolled model/tool/sampling drift")
    return result


def make_zip(files: dict[str,str]) -> bytes:
    out=io.BytesIO()
    with zipfile.ZipFile(out,"w") as z:
        for name,text in sorted(files.items()):
            info=zipfile.ZipInfo(name,date_time=STAMP)
            info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=0o100644<<16
            z.writestr(info,text.encode())
    data=out.getvalue()
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        if z.testzip() is not None or set(z.namelist())!=set(files):
            raise ValueError("invalid candidate zip")
    return data


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-zip",type=Path,required=True)
    p.add_argument("--public-ipynb",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--minutes",type=int,choices=(5,8),required=True)
    args=p.parse_args()
    if args.out.exists():
        raise FileExistsError("refuse to overwrite frozen candidate")
    source=args.source_zip.read_bytes()
    if digest(source)!=EXPECTED_ZIP_SHA256:
        raise ValueError("not exact pinned Budget-Fit V2")
    files=candidate_files(source,notebook_bundle(args.public_ipynb),
                          minutes=args.minutes)
    output=make_zip(files)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_bytes(output)
    print("PUBLIC_PROMPT_ONLY_BUILD="+json.dumps({
        "public_source":PUBLIC_REF,
        "public_prompt_sha256":EXPECTED_PUBLIC_PROMPT_SHA,
        "base_zip_sha256":digest(source),
        "minutes":args.minutes,
        "tool_calls":28,
        "turns":80,
        "candidate_sha256":digest(output),
        "same_baseline_model_tools_sampling":True,
        "no_gpu_no_training_no_competition_submission":True,
        "independently_scored":False,
    },sort_keys=True))


if __name__=="__main__":
    main()
