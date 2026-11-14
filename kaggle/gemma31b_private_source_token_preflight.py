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


def load_rows(name:str)->list[dict]:
    if name not in EXPECTED:
        raise ValueError("unsupported split")
    f=DATASET/name
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


def lengths(tokenizer, rows:list[dict])->list[dict]:
    stats=[]
    for row in rows:
        prefix=tokenizer.apply_chat_template(
            [{"role":"user","content":row["prompt"]}],
            tokenize=True,add_generation_prompt=True)
        if not isinstance(prefix,list) or not prefix:
            raise ValueError("chat_template_prompt_failed")
        target=tokenizer.encode(row["completion"],add_special_tokens=False)
        if not isinstance(target,list) or not target:
            raise ValueError("diff_target_empty")
        stop=tokenizer.eos_token_id
        if stop is None:
            raise ValueError("missing_eos")
        source_len=len(prefix)
        completion_len=len(target)+1
        total=source_len+completion_len
        if completion_len<5 or total<=completion_len:
            raise ValueError("masked_completion_length_invalid")
        stats.append({"source_tokens":source_len,"completion_tokens":completion_len,
                      "total_tokens":total,"repo_hash":row["repo_hash"]})
    return stats


def run()->dict:
    try:
        train=load_rows("train.jsonl")
        held=load_rows("holdout.jsonl")
    except FileNotFoundError:
        raise RuntimeError("phase_private_dataset_mount_missing") from None
    if len({r["id_hash"] for r in train+held})!=19:
        raise ValueError("task_ids_overlap")
    if {r["repo_hash"] for r in train} & {r["repo_hash"] for r in held}:
        raise ValueError("train_holdout_repository_overlap")
    if not (MODEL/"config.json").is_file():
        raise RuntimeError("phase_exact_model_source_mount_missing")
    from transformers import AutoProcessor
    try:
        processor=AutoProcessor.from_pretrained(str(MODEL),local_files_only=True)
    except (OSError,FileNotFoundError,ValueError):
        raise RuntimeError("phase_tokenizer_processor_load_failure") from None
    tokenizer=getattr(processor,"tokenizer",None)
    if tokenizer is None:
        raise ValueError("official_tokenizer_unavailable")
    out={}
    for name,records in (("train",train),("holdout",held)):
        data=lengths(tokenizer,records)
        totals=[x["total_tokens"] for x in data]
        out[name]={
          "n":len(data),"max_tokens":max(totals),
          "median_tokens":round(statistics.median(totals),1),
          "max_completion_tokens":max(x["completion_tokens"] for x in data),
          "max_prompt_tokens":max(x["source_tokens"] for x in data),
          "fits_budget":{str(b):sum(x<=b for x in totals) for b in PROMPT_BANDS},
          "completion_nonempty":all(x["completion_tokens"]>=5 for x in data),
        }
    return {
      "status":"PRIVATE_31B_QAT_TOKENIZER_COMPLETION_ONLY_PREFLIGHT_OK",
      "data_source":"kolihhan/gemma31b-verified-repair-sft-v0",
      "model_tokenizer":"Gemma 4 31B QAT unquantized v2",
      "split_reports":out,
      "repository_overlap":0,
      "completion_only_masking_not_yet_run":True,
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
                "safe_stage":str(err) if str(err).startswith("phase_") else "schema_or_unknown",
                "raw_dataset_or_model_path_logged":False}
        DEST.write_text(json.dumps(report,sort_keys=True),encoding="utf-8")
        print("GEMMA_PRIVATE_SOURCE_TOKEN_PREFLIGHT="+json.dumps(report,sort_keys=True),flush=True)
        raise SystemExit(1) from None
