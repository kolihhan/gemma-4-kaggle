"""Stage the exact scored-0.18 + real public 31B coder LoRA as a PRIVATE CPU Kaggle notebook.

This never runs a Gemma model, uses GPU, or submits to the competition.
The notebook mounts the original public adapter kernel and reconstructs only
the SHA-pinned candidate in /kaggle/working/submission.zip. No model bytes
or competition task data are committed to GitHub.
"""
from __future__ import annotations
import base64
import hashlib
import io
import json
from pathlib import Path
import zipfile

from scripts.gemma31_uploaded_coder_adapter_one_variable_cpu import package

SOURCE_KERNEL="ayush04barai/lora-step-2"
KERNEL="kolihhan/gemma31-018-coder-lora-cpu-nov19"
CODE_FILE="build_candidate_cpu.py"
STAMP=(2026,11,19,0,0,0)

def render(scored_zip:bytes, adapter_dir:Path, target:Path)->dict:
    if target.exists() and any(target.iterdir()):
        raise FileExistsError("REFUSE_EXISTING_PRIVATE_BUILDER")
    archive,report=package(scored_zip,adapter_dir)
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        data={name:z.read(name) for name in z.namelist()}
    names=sorted(data)
    cfg_names=sorted(n for n in names if not n.startswith("adapters/"))
    if len(cfg_names)!=4 or len(names)!=6:
        raise RuntimeError("CANDIDATE_NOT_EXPECTED_SIX_FILE_BUNDLE")
    cfg_source={n:base64.b64encode(data[n]).decode("ascii") for n in cfg_names}
    hashes={n:hashlib.sha256(data[n]).hexdigest() for n in names}
    code=(
        "import base64,hashlib,io,zipfile\n"
        "from pathlib import Path\n"
        "SOURCE=Path('/kaggle/input/notebooks/ayush04barai/lora-step-2/trained_adapter/main_lora')\n"
        f"CONFIG_B64={repr(cfg_source)}\n"
        f"FILE_HASHES={repr(hashes)}\n"
        f"EXPECTED_ARCHIVE_SHA={repr(report['candidate_zip_sha256'])}\n"
        "data={n:base64.b64decode(v,validate=True) for n,v in CONFIG_B64.items()}\n"
        "for n in ('adapter_config.json','adapter_model.safetensors'):\n"
        "    path=SOURCE/n\n"
        "    if not path.is_file(): raise FileNotFoundError('MISSING_PINNED_PUBLIC_ADAPTER:'+n)\n"
        "    data['adapters/main_lora/'+n]=path.read_bytes()\n"
        "assert set(data)==set(FILE_HASHES)\n"
        "for n,v in data.items():\n"
        "    if hashlib.sha256(v).hexdigest()!=FILE_HASHES[n]:\n"
        "        raise ValueError('ADAPTER_OR_CONFIG_SOURCE_CHANGED:'+n)\n"
        "buf=io.BytesIO()\n"
        "with zipfile.ZipFile(buf,'w') as z:\n"
        "    for n,v in sorted(data.items()):\n"
        "        info=zipfile.ZipInfo(n,date_time=(2026,11,19,0,0,0))\n"
        "        info.compress_type=zipfile.ZIP_DEFLATED\n"
        "        info.external_attr=0o100644<<16\n"
        "        z.writestr(info,v)\n"
        "bundle=buf.getvalue()\n"
        "if hashlib.sha256(bundle).hexdigest()!=EXPECTED_ARCHIVE_SHA:\n"
        "    raise ValueError('SCORING_ARCHIVE_BYTE_HASH_DRIFT')\n"
        "with zipfile.ZipFile(io.BytesIO(bundle)) as z:\n"
        "    assert z.testzip() is None and set(z.namelist())==set(FILE_HASHES)\n"
        "out=Path('/kaggle/working/submission.zip')\n"
        "out.write_bytes(bundle)\n"
        "print('GEMMA_31B_REAL_CODER_LORA_PRIVATE_CPU_BUILDER_SHA256='+EXPECTED_ARCHIVE_SHA,flush=True)\n"
        "print('GEMMA_GPU_INFERENCE_AND_COMPETITION_SUBMISSION=FALSE',flush=True)\n"
    )
    compile(code,CODE_FILE,"exec")
    target.mkdir(parents=True,exist_ok=False)
    (target/CODE_FILE).write_text(code,encoding="utf8")
    meta={
        "id":KERNEL,
        "title":KERNEL.split("/",1)[1],
        "code_file":CODE_FILE,
        "language":"python",
        "kernel_type":"script",
        "is_private":True,
        "enable_gpu":False,
        "enable_tpu":False,
        "enable_internet":False,
        "competition_sources":["gemma-4-developer-agent"],
        "dataset_sources":[],
        "kernel_sources":[SOURCE_KERNEL],
        "model_sources":[],
    }
    (target/"kernel-metadata.json").write_text(json.dumps(meta,indent=2,sort_keys=True)+"\n")
    return {
        "kernel":KERNEL,
        "candidate_zip_sha256":report["candidate_zip_sha256"],
        "adapter_weights_sha256":report["weights_sha256"],
        "config_file_count":4,
        "adapter_file_count":2,
        "private":True,
        "cpu_only":True,
        "official_submission":False,
        "source_attribution":SOURCE_KERNEL,
        "adapter_license_independently_verified":False,
        "model_impact_unmeasured":True,
    }
