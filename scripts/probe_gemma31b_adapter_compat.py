"""Gemma 4 31B train/inference/adapter STATIC compatibility audit (CPU only).

Fetch small JSON configs only; no tensor weights or model inference.
Never use third-party adapter on competition tasks, and do not claim an
adapter would load merely because architecture dimensions match.
"""
from __future__ import annotations

import json
import re
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError

BASE="google/gemma-4-31B-it-qat-w4a16-ct"
TRAIN="google/gemma-4-31B-it-qat-q4_0-unquantized"
EXAMPLE="eexian/gemma4-31b-w4-weighted-reasoning-lora"
SAFE={(BASE,"config.json"),(TRAIN,"config.json"),(EXAMPLE,"adapter_config.json")}


def get_small_json(repo:str,name:str,cap:int=200_000)->dict:
    if (repo,name) not in SAFE:
        raise ValueError("unapproved metadata URL")
    url=f"https://huggingface.co/{repo}/resolve/main/{name}"
    req=Request(url,headers={"User-Agent":"Gemma4AdapterContractResearch/1.0"})
    with urlopen(req,timeout=35) as h:
        body=h.read(cap+1)
    if len(body)>cap:
        raise ValueError("unexpected config size")
    obj=json.loads(body)
    if not isinstance(obj,dict):
        raise ValueError("unexpected JSON document")
    return obj


def text_arch(cfg:dict)->dict:
    model=cfg.get("text_config",cfg)
    if not isinstance(model,dict):
        raise ValueError("model text_config unavailable")
    keys=("model_type","hidden_size","intermediate_size","num_hidden_layers",
          "num_attention_heads","num_key_value_heads","head_dim","vocab_size",
          "sliding_window_pattern","attention_bias","max_position_embeddings")
    return {k:model.get(k) for k in keys}


def audit()->dict:
    try:
        serving=get_small_json(BASE,"config.json")
    except Exception:
        raise ValueError("phase_serving_public_config") from None
    try:
        training=get_small_json(TRAIN,"config.json")
    except Exception:
        raise ValueError("phase_training_public_config") from None
    try:
        adapter=get_small_json(EXAMPLE,"adapter_config.json")
    except Exception:
        raise ValueError("phase_public_adapter_config") from None
    try:
        st=text_arch(serving)
        tr=text_arch(training)
    except (ValueError, TypeError):
        raise ValueError("phase_text_arch_parser") from None
    mismatches=[key for key in st if st[key] != tr[key]]
    active=adapter.get("target_modules")
    if isinstance(active,list):
        target_policy="explicit_list"
        targets=sorted(x for x in active if isinstance(x,str) and
                       re.fullmatch(r"[a-z][a-z0-9_]{0,40}",x))
    elif isinstance(active,str):
        target_policy="named_regex_or_all_linear"
        targets=[]
    elif active is None:
        target_policy="PEFT_default_target_modules"
        targets=[]
    else:
        raise ValueError("unsupported PEFT target-module schema")
    # This is comparison to public trainer-guide targets, NOT actual
    # model parameter existence or PEFT runtime loading.
    expected={"q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"}
    return {
        "inference_model":BASE,"train_model":TRAIN,
        "public_example_adapter":EXAMPLE,
        "inference_architecture":serving.get("architectures"),
        "training_architecture":training.get("architectures"),
        "text_dimension_mismatch_keys":mismatches,
        "text_dimensions_equal":not bool(mismatches),
        "serving_quantization_type":str(serving.get("quantization_config",{}).get("format",
               serving.get("quantization_config",{}).get("quant_method","unknown"))),
        "train_has_quantization_config":bool(training.get("quantization_config")),
        "example_peft_type":adapter.get("peft_type"),
        "example_task_type":adapter.get("task_type"),
        "example_rank":adapter.get("r"),
        "example_lora_alpha":adapter.get("lora_alpha"),
        "example_base_model":adapter.get("base_model_name_or_path"),
        "example_target_policy":target_policy,
        "example_targets":targets,
        "example_targets_subset_of_guide":set(targets).issubset(expected),
        "actual_safetensors_read":False,
        "model_weights_loaded":False,
        "adapter_load_test_executed":False,
        "training_performed":False,
        "inference_improvement_measured":False,
    }


if __name__=="__main__":
    try:
        print("GEMMA_31B_LORA_CONFIG_CONTRACT="+json.dumps(audit(),sort_keys=True),flush=True)
    except Exception as exc:
        print("GEMMA_31B_LORA_CONFIG_BLOCKED="+json.dumps({
           "error_type":type(exc).__name__,
           "error_phase":str(exc) if str(exc).startswith("phase_") else "schema_validation",
           "raw_error_url_or_auth_logged":False}),flush=True)
        raise SystemExit(1) from None
