"""CPU-only dependency diagnosis for a *previously failed* Gemma4 31B 4bit load.

Never loads model weights, uses CUDA, trains, handles private data, or submits.
This is image-environment comparison, NOT a GPU model load proof.
"""
import importlib.metadata as md
import json
import sys
from pathlib import Path

OUT=Path("/kaggle/working/gemma31b-4bit-dependencies-safe.json")
PACKAGES=("transformers","torch","peft","accelerate","bitsandbytes","torchao","safetensors","triton")
result={"kind":"KAGGLE_PRIVATE_CPU_IMAGE_ONLY",
        "versions":{},"bitsandbytes_config_constructible":False,
        "gemma4_class_available":False,
        "gpu_model_load_proven":False,"training":False,
        "new_gpu":False,"official_submission":False}
try:
    for name in PACKAGES:
        try:result["versions"][name]=md.version(name)
        except md.PackageNotFoundError:result["versions"][name]="NOT_INSTALLED"
    stage="TRANSFORMERS_IMPORT"
    from transformers import Gemma4ForConditionalGeneration,BitsAndBytesConfig
    result["gemma4_class_available"]=True
    stage="BITSANDBYTES_CONFIG_INSTANTIATION"
    import torch
    x=BitsAndBytesConfig(load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_quant_storage=torch.bfloat16)
    result["bitsandbytes_config_constructible"]=bool(x.load_in_4bit)
    result["status"]="CPU_DEPENDENCY_PREFLIGHT_COMPLETE"
except BaseException as error:
    result["status"]="CPU_DEPENDENCY_PREFLIGHT_FAILED"
    result["failure_phase"]=stage
    result["exception_type"]=type(error).__name__
    # Use only known dependency tokens; no raw exception message or paths.
    message=str(error).lower()
    result["suspected_package_tokens"]=[
        name for name in PACKAGES if name in message]
OUT.write_text(json.dumps(result,indent=2,sort_keys=True),encoding="utf-8")
print("GEMMA31B_CPU_DEPENDENCY_SAFE="+json.dumps(result,sort_keys=True),flush=True)
sys.exit(0 if result["status"]=="CPU_DEPENDENCY_PREFLIGHT_COMPLETE" else 1)
