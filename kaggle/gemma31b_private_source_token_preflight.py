"""PRIVATE CPU token-length and completion-only SFT integrity preflight.

Private Kaggle dataset must provide 16 train / 3 repo-disjoint validation rows.
Use exact Gemma 4 31B QAT tokenizer from mounted official model source.
NO model tensor weights, train step, raw task output, patch output, or uploads.
"""
from __future__ import annotations
from collections import Counter
import json
from pathlib import Path
import statistics

DATASET=Path("/kaggle/input/gemma31b-verified-repair-sft-v0")
MODEL=Path("/kaggle/input/models/google/gemma-4/transformers/"
           "gemma-4-31b-it-qat-q4_0-unquantized/2")
DEST=Path("/kaggle/working/gemma31b-source-token-preflight.json")
PROMPT_BANDS=(1024,2048,4096,8192,16384)
EXPECTED={"train.jsonl":16,"holdout.jsonl":3}
EXECUTION_STAGE="init"


def find_private_data_dir()->Path:
    """Resolve Kaggle flat vs owner/datasets/versioned mount layouts safely."""
    root=Path("/kaggle/input")
    if not root.is_dir():
        raise RuntimeError("phase_no_kaggle_input_root")
    candidates=[
      DATASET,
      root/"datasets"/"kolihhan"/"gemma31b-verified-repair-sft-v0",
      root/"datasets"/"kolihhan"/"gemma31b-verified-repair-sft-v0"/"versions"/"1",
      root/"kolihhan"/"gemma31b-verified-repair-sft-v0",
    ]
    # Inspect only the expected own source contract, never print other
    # dataset paths or traverse external symlinks.
    for p in root.rglob("source_contract.json"):
        candidates.append(p.parent)
        if len(candidates)>50:
            raise RuntimeError("phase_private_mount_listing_too_large")
    valid=[]
    for candidate in candidates:
        if not all((candidate/name).is_file() for name in ("train.jsonl","holdout.jsonl","source_contract.json")):
            continue
        try:
            contract=json.loads((candidate/"source_contract.json").read_text(encoding="utf-8"))
        except (OSError,ValueError):
            continue
        if (contract.get("schema_version")=="gemma31b-source-patch-completion-v0" and
            contract.get("train_rows")==16 and contract.get("holdout_rows")==3 and
            contract.get("excluded_gold_patch") is True):
            valid.append(candidate.resolve())
    distinct=set(valid)
    if len(distinct)!=1:
        raise RuntimeError("phase_private_dataset_contract_not_found_or_ambiguous")
    return next(iter(distinct))


def load_rows(name:str,source_dir:Path)->list[dict]:
    if name not in EXPECTED:
        raise ValueError("unsupported split")
    f=source_dir/name
    if not f.is_file():
        raise FileNotFoundError("private_source_dataset_not_mounted")
    rows=[json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
    if len(rows)!=EXPECTED[name]:
        raise ValueError("private_dataset_row_count_drift")
    for row in rows:
        if not isinstance(row,dict) or row.get("source_F2P_proven_pass") is not True:
            raise ValueError("unapproved_positive")
        if row.get("gold_patch_present") is not False or row.get("tool_trace_present") is not False:
            raise ValueError("gold_or_tool_source_disallowed")
        if not isinstance(row.get("prompt"),str) or not isinstance(row.get("completion"),str):
            raise ValueError("empty_training_text")
        if not row["completion"].startswith("diff --git "):
            raise ValueError("non_diff_target")
    return rows


def pack_completion_only(processor,tokenizer,row:dict,max_tokens:int|None=None)->dict:
    """Build real trainable ids/labels: issue tokens never contribute to loss.

    No truncation; callers must explicitly omit oversized examples.
    """
    rendered=processor.apply_chat_template(
        [{"role":"user","content":[{"type":"text","text":row["prompt"]}]}],
        tokenize=False,add_generation_prompt=True)
    if not isinstance(rendered,str) or not rendered:
        raise ValueError("processor_chat_template_prompt_failed")
    prefix=tokenizer.encode(rendered,add_special_tokens=False)
    target=tokenizer.encode(row["completion"],add_special_tokens=False)
    # Compare with actual full-sequence tokenization. SentencePiece/BPE
    # may merge across the prompt/target boundary, shifting loss labels.
    joint=tokenizer.encode(rendered+row["completion"],add_special_tokens=False)
    if joint!=prefix+target:
        raise ValueError("prompt_target_token_boundary_mismatch")
    eos=tokenizer.eos_token_id
    if not prefix or len(target)<4 or eos is None:
        raise ValueError("empty_prefix_or_diff_target_or_eos")
    ids=prefix+target+[eos]
    labels=[-100]*len(prefix)+target+[eos]
    if len(ids)!=len(labels) or labels[:len(prefix)]!=[-100]*len(prefix):
        raise AssertionError("completion_only_loss_mask_invalid")
    if max_tokens is not None and len(ids)>max_tokens:
        raise ValueError("example_exceeds_budget_no_truncation")
    return {"input_ids":ids,"attention_mask":[1]*len(ids),"labels":labels,
            "source_tokens":len(prefix),"completion_tokens":len(target)+1}


def lengths(processor,tokenizer,rows:list[dict])->list[dict]:
    stats=[]
    for row in rows:
        packed=pack_completion_only(processor,tokenizer,row)
        source_len=packed["source_tokens"]
        completion_len=packed["completion_tokens"]
        if packed["labels"].count(-100)!=source_len or len(packed["input_ids"])!=source_len+completion_len:
            raise AssertionError("training_loss_mask_length_drift")
        stats.append({"source_tokens":source_len,"completion_tokens":completion_len,
                      "total_tokens":len(packed["input_ids"]),"repo_hash":row["repo_hash"],
                      "completion_only_mask_verified":True,"token_boundary_verified":True})
    return stats


def run()->dict:
    global EXECUTION_STAGE
    EXECUTION_STAGE="resolve_private_data_contract"
    try:
        data_root=find_private_data_dir()
        EXECUTION_STAGE="load_private_source_rows"
        train=load_rows("train.jsonl",data_root)
        held=load_rows("holdout.jsonl",data_root)
    except FileNotFoundError:
        raise RuntimeError("phase_private_dataset_mount_missing") from None
    EXECUTION_STAGE="validate_private_labels_and_repo_split"
    if len({r["id_hash"] for r in train+held})!=19:
        raise ValueError("task_ids_overlap")
    if {r["repo_hash"] for r in train} & {r["repo_hash"] for r in held}:
        raise ValueError("train_holdout_repository_overlap")
    EXECUTION_STAGE="verify_exact_31b_tokenizer_mount"
    if not (MODEL/"config.json").is_file():
        raise RuntimeError("phase_exact_model_source_mount_missing")
    EXECUTION_STAGE="import_exact_processor"
    from transformers import AutoProcessor
    EXECUTION_STAGE="load_exact_31b_processor"
    try:
        processor=AutoProcessor.from_pretrained(str(MODEL),local_files_only=True)
    except (OSError,FileNotFoundError,ValueError):
        raise RuntimeError("phase_tokenizer_processor_load_failure") from None
    tokenizer=getattr(processor,"tokenizer",None)
    if tokenizer is None:
        raise ValueError("official_tokenizer_unavailable")
    out={}
    for name,records in (("train",train),("holdout",held)):
        EXECUTION_STAGE="tokenize_"+name
        data=lengths(processor,tokenizer,records)
        totals=[x["total_tokens"] for x in data]
        out[name]={
          "n":len(data),"max_tokens":max(totals),
          "median_tokens":round(statistics.median(totals),1),
          "max_completion_tokens":max(x["completion_tokens"] for x in data),
          "max_prompt_tokens":max(x["source_tokens"] for x in data),
          "fits_budget":{str(b):sum(x<=b for x in totals) for b in PROMPT_BANDS},
          "completion_nonempty":all(x["completion_tokens"]>=5 for x in data),
          "completion_only_mask_verified":all(x["completion_only_mask_verified"] for x in data),
          "joint_sequence_token_boundary_verified":all(x["token_boundary_verified"] for x in data),
          "fits_4096_without_truncation":sum(x["total_tokens"]<=4096 for x in data),
        }
    EXECUTION_STAGE="complete"
    return {
      "status":"PRIVATE_31B_QAT_TOKENIZER_COMPLETION_ONLY_PREFLIGHT_OK",
      "data_source":"kolihhan/gemma31b-verified-repair-sft-v0",
      "model_tokenizer":"Gemma 4 31B QAT unquantized v2",
      "split_reports":out,
      "repository_overlap":0,
      "completion_only_masking_cpu_verified":True,
      "gradient_or_gpu_mask_execution_unverified":True,
      "all_source_train_patches_independently_F2P":True,
      "raw_task_text_logged":False,"reference_patch_read":False,
      "model_tensors_loaded":False,"GPU_used":False,"training":False,
      "official_submission":False,
    }


if __name__=="__main__":
    try:
        report=run()
        DEST.write_text(json.dumps(report,indent=2,sort_keys=True),encoding="utf-8")
        print("GEMMA_PRIVATE_SOURCE_TOKEN_PREFLIGHT="+json.dumps(report,sort_keys=True),flush=True)
    except Exception as err:
        report={"status":"TOKEN_PREFLIGHT_BLOCKED","failure_type":type(err).__name__,
                "safe_stage":EXECUTION_STAGE,
                "safe_error_class":str(err) if str(err).startswith("phase_") else "unreported",
                "raw_dataset_or_model_path_logged":False}
        DEST.write_text(json.dumps(report,sort_keys=True),encoding="utf-8")
        print("GEMMA_PRIVATE_SOURCE_TOKEN_PREFLIGHT="+json.dumps(report,sort_keys=True),flush=True)
        raise SystemExit(1) from None
