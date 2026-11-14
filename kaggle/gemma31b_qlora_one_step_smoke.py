"""Exact 31B QAT -> PEFT LoRA one-step PRIVATE Kaggle GPU smoke.

Synthetic text only; no real issue, benchmark task or reference patch.
This is not a training candidate, official score, or validation of transfer.
Fail closed on CPU/disk offload, absent GPU, inability to backward/save.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import time
import importlib.metadata
import subprocess
import sys

MODEL=Path("/kaggle/input/models/google/gemma-4/transformers/"
           "gemma-4-31b-it-qat-q4_0-unquantized/2")
DEST=Path("/kaggle/working/gemma31b-smoke-adapter")
REPORT=Path("/kaggle/working/gemma31b-lora-smoke-result.json")
SAMPLE=("User: Fix a tiny Python function: f() returns 0, expected 1. "
        "Respond with a unified diff.\nAssistant: diff --git a/bug.py b/bug.py\n"
        "@@ -1,2 +1,2 @@\n def f():\n-    return 0\n+    return 1\n")
TRAINING={"r":4,"lora_alpha":8,"target_modules":["q_proj","v_proj"],
          "training_steps":1,"max_tokens":96,"lr":2e-5}


def device_map_summary(model)->dict:
    raw=getattr(model,"hf_device_map",None)
    if not isinstance(raw,dict) or not raw:
        raise RuntimeError("missing_sharded_device_map")
    devices=set()
    for dest in raw.values():
        if isinstance(dest,int):
            devices.add(dest)
        elif isinstance(dest,str) and dest.startswith("cuda:") and dest[5:].isdigit():
            devices.add(int(dest[5:]))
        elif isinstance(dest,str) and dest.isdigit():
            devices.add(int(dest))
        else:
            raise RuntimeError("offload_or_unknown_device")
    if not devices:
        raise RuntimeError("no_gpu_in_device_map")
    return {"device_count":len(devices),"module_count":len(raw),
            "gpu_indices":sorted(devices),"cpu_disk_offload":False}


def ensure_peft_dependency_compatible()->str:
    try:
        version=importlib.metadata.version("torchao")
    except importlib.metadata.PackageNotFoundError:
        return "torchao_absent"
    parts=version.split(".")
    if len(parts)<2 or not all(x.isdigit() for x in parts[:2]):
        raise RuntimeError("torchao_version_unknown")
    if tuple(map(int,parts[:2]))<(0,16):
        subprocess.run([sys.executable,"-m","pip","uninstall","-y","torchao"],
                       capture_output=True,text=True,check=True,timeout=90)
        return "removed_old_torchao"
    return "torchao_compatible"


def main()->dict:
    stage="START"
    report={"model_source":"google/gemma-4-31b-it-qat-q4_0-unquantized/2",
            "training_objective":"ONE_STEP_SYNTHETIC_SMOKE_ONLY",
            "checkpoint":"QAT-unquantized",
            "scored_inference_model":"gemma-4-31b-it-qat-w4a16-ct",
            "scored_adapter_load_test":False,
            "real_task_training_rows":0,
            "official_submission":False,
            "training_config":TRAINING}
    try:
        stage="MODEL_MOUNT"
        if not (MODEL/"config.json").is_file():
            raise RuntimeError("model_mount_missing")
        stage="IMPORTS"
        compat=ensure_peft_dependency_compatible()
        import torch
        from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
        from transformers import AutoModelForCausalLM,AutoProcessor,BitsAndBytesConfig
        report["torchao_action"]=compat
        gpu_count=torch.cuda.device_count()
        report["visible_cuda_devices"]=gpu_count
        if gpu_count<2:
            raise RuntimeError("insufficient_l4_devices")
        stage="PROCESSOR"
        processor=AutoProcessor.from_pretrained(str(MODEL),local_files_only=True)
        tokenizer=getattr(processor,"tokenizer",None)
        if tokenizer is None:
            raise RuntimeError("no_tokenizer")
        stage="MODEL_LOAD_4BIT"
        dtype=torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
        quant=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type="nf4",
                                 bnb_4bit_use_double_quant=True,
                                 bnb_4bit_compute_dtype=dtype,
                                 bnb_4bit_quant_storage=dtype)
        model=AutoModelForCausalLM.from_pretrained(
            str(MODEL),local_files_only=True,quantization_config=quant,
            dtype=dtype,low_cpu_mem_usage=True,device_map="auto",
            max_memory={i:"20GiB" for i in range(gpu_count)})
        report["model_class"]=model.__class__.__name__
        report["placement"]=device_map_summary(model)
        stage="PEFT"
        model.config.use_cache=False
        model=prepare_model_for_kbit_training(model,use_gradient_checkpointing=True)
        lora=LoraConfig(r=TRAINING["r"],lora_alpha=TRAINING["lora_alpha"],
                        lora_dropout=0.0,bias="none",
                        target_modules=TRAINING["target_modules"],task_type="CAUSAL_LM")
        model=get_peft_model(model,lora)
        model.train()
        if hasattr(model,"enable_input_require_grads"):
            model.enable_input_require_grads()
        trainable=[p for p in model.parameters() if p.requires_grad]
        report["trainable_parameter_count"]=sum(p.numel() for p in trainable)
        if not trainable:
            raise RuntimeError("zero_trainable_parameters")
        stage="SINGLE_FORWARD_BACKWARD"
        data=tokenizer(SAMPLE,return_tensors="pt",max_length=TRAINING["max_tokens"],
                       truncation=True,add_special_tokens=True)
        first=next(p.device for p in model.parameters() if p.device.type=="cuda")
        data={k:v.to(first) for k,v in data.items()}
        result=model(**data,labels=data["input_ids"].clone(),use_cache=False)
        loss=result.loss
        if not bool(torch.isfinite(loss).item()):
            raise RuntimeError("nonfinite_loss")
        report["finite_loss"]=True
        report["token_count"]=int(data["input_ids"].shape[1])
        loss.backward()
        grad_count=sum(int(p.grad is not None) for p in trainable)
        report["trainable_tensors_with_gradient"]=grad_count
        if grad_count==0:
            raise RuntimeError("missing_lora_gradients")
        optim=torch.optim.AdamW(trainable,lr=TRAINING["lr"])
        optim.step()
        optim.zero_grad(set_to_none=True)
        stage="SAVE_ADAPTER"
        DEST.mkdir(parents=True,exist_ok=True)
        model.save_pretrained(str(DEST),safe_serialization=True)
        names={p.name for p in DEST.iterdir() if p.is_file()}
        if not {"adapter_config.json","adapter_model.safetensors"}.issubset(names):
            raise RuntimeError("missing_PEFT_output_files")
        if names.intersection({"model.safetensors","pytorch_model.bin","config.json"}):
            raise RuntimeError("full_model_artifact_unexpected")
        cfg=json.loads((DEST/"adapter_config.json").read_text())
        if int(cfg.get("r",-1))!=TRAINING["r"]:
            raise RuntimeError("saved_adapter_wrong_rank")
        report["adapter_bytes"]=(DEST/"adapter_model.safetensors").stat().st_size
        report["adapter_config_validated"]=True
        report["status"]="SYNTHETIC_ONE_STEP_ADAPTER_SAVED"
        report["real_training_example_count"]=0
        report["scored_31b_adapter_loading_proven"]=False
        return report
    except Exception as exc:
        report["status"]="SMOKE_FAILED"
        report["failure_phase"]=stage
        report["failure_type"]=type(exc).__name__
        return report


if __name__=="__main__":
    answer=main()
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text(json.dumps(answer,sort_keys=True,indent=2),encoding="utf-8")
    print("GEMMA_31B_REAL_LORA_SMOKE="+json.dumps(answer,sort_keys=True),flush=True)
    if answer["status"]!="SYNTHETIC_ONE_STEP_ADAPTER_SAVED":
        raise SystemExit(1)
