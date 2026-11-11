"""Matched 12B vs 31B code-agent capacity experiment (configuration only).

Source is EXACT SHA-pinned attributed public V2. No model training, imports,
or GPU use. 5-minute agent clock, 28 tools, same prompt and sampling across arms.
The one and only cross-arm difference is the declared allowed Gemma 4 model.
This builds candidates; it does not prove model capacity or issue-resolution gains.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path
import zipfile
from scripts.prepare_public_budgetfit_v2 import validate_source_zip, EXPECTED_ZIP_SHA256

BASE_MODEL = "gemma-4-31b-it-qat-w4a16-ct"
SMALL_MODEL = "gemma-4-12b-it-qat-w4a16-ct"
STAMP = (2026, 11, 12, 0, 0, 0)
ARMS = {"v2_31b": BASE_MODEL, "v2_12b": SMALL_MODEL}


def _sha(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def candidate_files(source_zip: bytes) -> dict[str, dict[str, str]]:
    original = validate_source_zip(source_zip)
    assert _sha(source_zip) == EXPECTED_ZIP_SHA256
    if original["eval_config.yaml"].count("max_time_minutes: 8") != 1:
        raise ValueError("unrecognized base budget")
    five = dict(original)
    five["eval_config.yaml"] = original["eval_config.yaml"].replace(
        "max_time_minutes: 8", "max_time_minutes: 5", 1
    )
    if "max_tool_calls: 28" not in five["eval_config.yaml"]:
        raise ValueError("tools count drift")
    if "max_turns: 80" not in five["eval_config.yaml"]:
        raise ValueError("turn count drift")
    if five["agent.yaml"].count("model: " + BASE_MODEL) != 1:
        raise ValueError("model declaration drift")
    smaller = dict(five)
    smaller["agent.yaml"] = five["agent.yaml"].replace(
        "model: " + BASE_MODEL, "model: " + SMALL_MODEL, 1
    )
    if set(smaller) != set(five) or any(smaller[k] != five[k] for k in five if k != "agent.yaml"):
        raise ValueError("uncontrolled arm drift")
    if smaller["agent.yaml"].replace("model: "+SMALL_MODEL,"model: "+BASE_MODEL) != five["agent.yaml"]:
        raise ValueError("unexpected non-model change")
    if "gemma-4-31b" in smaller["agent.yaml"]:
        raise ValueError("residual 31B reference in smaller model config")
    return {"v2_31b":five,"v2_12b":smaller}


def archive(files: dict[str, str]) -> bytes:
    buf=io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name,content in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=STAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644<<16
            z.writestr(info,content.encode("utf-8"))
    blob=buf.getvalue()
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        if z.testzip() is not None or set(z.namelist())!=set(files):
            raise ValueError("bad ZIP")
    return blob


def build(source_zip: bytes) -> dict[str, bytes]:
    return {arm:archive(files) for arm,files in candidate_files(source_zip).items()}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-zip",type=Path,required=True)
    p.add_argument("--out-dir",type=Path,required=True)
    a=p.parse_args()
    if a.out_dir.exists() and any(a.out_dir.iterdir()):
        raise FileExistsError("refuse overwriting controls")
    blobs=build(a.source_zip.read_bytes())
    a.out_dir.mkdir(parents=True,exist_ok=True)
    report={}
    for name,blob in blobs.items():
        path=a.out_dir/(name+".zip")
        path.write_bytes(blob)
        report[name]={"model":ARMS[name],"sha256":_sha(blob),"zip_bytes":len(blob)}
    print("CAPACITY_12B_31B_CPU_ONLY="+json.dumps({
        "source_notebook":"lynnsakurai/gemma-4-budget-fit-agent-w-bounded-rescue/2",
        "source_sha256":EXPECTED_ZIP_SHA256,
        "budgets":"5m/28calls/80turns",
        "same_prompt_tools_sampling":True,
        "actual_model_scoring":False,
        "training":False,"gpu":False,"official_submission":False,
        "candidates":report,
    },sort_keys=True))


if __name__=="__main__":
    main()
