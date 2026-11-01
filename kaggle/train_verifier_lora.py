"""One-shot verifier-only LoRA v0 trainer for Gemma 4 E4B.

This script is intentionally narrow: it consumes the frozen deterministic
training-only verifier trajectories, requires gold-pass coverage for all six
Task-4 targets plus at least one approved base-fail safe-stop example, renders
them through the local Gemma 4 chat template, refuses truncation, and trains
one rank-8 adapter. It does not read blind evaluation data and does not perform
a hyperparameter sweep.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


SFT_JSONL_B64 = "__VERIFIER_SFT_JSONL_B64__"
MODEL_PATH = Path(
    "/kaggle/input/models/google/gemma-4/transformers/"
    "gemma-4-e4b-it-qat-q4_0-unquantized/2"
)
OUTPUT_ROOT = Path("/kaggle/working/verifier-lora-v0")
ADAPTER_DIR = OUTPUT_ROOT / "adapter"
REPORT_PATH = OUTPUT_ROOT / "training_report.json"

EXPECTED_TASK_IDS = [
    "fastapi_14479",
    "requests_6644",
    "rich_3718",
    "rich_3882",
    "rich_3953",
    "rich_4006",
]
FORBIDDEN_KEYS = {
    "reference_patch",
    "reference_solution",
    "gold_patch",
    "solution_patch",
    "test_patch",
}
TRAINING_CONFIG = {
    "r": 8,
    "lora_alpha": 16,
    "lora_dropout": 0.05,
    "learning_rate": 1e-4,
    "num_train_epochs": 3,
    "seed": 42,
    "max_length": 4096,
    "target_modules": [
        "q_proj",
        "k_proj",
        "v_proj",
        "o_proj",
        "gate_proj",
        "up_proj",
        "down_proj",
    ],
}


def _walk_forbidden(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key) in FORBIDDEN_KEYS:
                raise ValueError(f"forbidden solution field at {path}.{key}")
            _walk_forbidden(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _walk_forbidden(child, f"{path}[{index}]")


def load_sft_rows(payload: str) -> list[dict[str, Any]]:
    """Parse and strictly validate the frozen paired Task-4 dataset."""
    if not isinstance(payload, str) or not payload.strip():
        raise ValueError("SFT payload is empty")

    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(payload.splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid SFT JSONL line {line_number}: {exc}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"SFT row {line_number} must be an object")
        _walk_forbidden(row)
        rows.append(row)

    if not rows:
        raise ValueError("SFT dataset has no rows")

    expected_tasks = set(EXPECTED_TASK_IDS)
    seen_examples: set[str] = set()
    gold_tasks: set[str] = set()
    safe_stop_count = 0

    for row in rows:
        task_id = row.get("instance_id")
        example_id = row.get("example_id")
        if not isinstance(task_id, str) or task_id not in expected_tasks:
            raise ValueError(f"unexpected SFT task ID: {task_id!r}")
        if not isinstance(example_id, str) or not example_id:
            raise ValueError(f"{task_id}: missing example_id")
        if example_id in seen_examples:
            raise ValueError(f"duplicate SFT example_id: {example_id}")
        seen_examples.add(example_id)

        label = row.get("label")
        source = row.get("source")
        if label == "verified_submit":
            expected_example_id = f"{task_id}:gold-pass"
            if example_id != expected_example_id:
                raise ValueError(
                    f"{task_id}: verified_submit must use example_id {expected_example_id!r}"
                )
            if source != "gold_patch_targeted_test":
                raise ValueError(f"{task_id}: unexpected positive source {source!r}")
            if task_id in gold_tasks:
                raise ValueError(f"{task_id}: duplicate gold-pass supervision")
            gold_tasks.add(task_id)
        elif label == "safe_stop":
            expected_example_id = f"{task_id}:base-fail"
            if example_id != expected_example_id:
                raise ValueError(
                    f"{task_id}: safe_stop must use example_id {expected_example_id!r}"
                )
            if source != "base_targeted_failure":
                raise ValueError(f"{task_id}: unexpected safe-stop source {source!r}")
            safe_stop_count += 1
        else:
            raise ValueError(f"{task_id}: unexpected label {label!r}")

        messages = row.get("messages")
        tools = row.get("tools")
        if not isinstance(messages, list) or not messages:
            raise ValueError(f"{example_id}: messages missing/empty")
        if not isinstance(tools, list) or not tools:
            raise ValueError(f"{example_id}: tools missing/empty")
        roles = [message.get("role") for message in messages if isinstance(message, dict)]
        if "system" not in roles or "assistant" not in roles or "tool" not in roles:
            raise ValueError(f"{example_id}: incomplete verifier trajectory roles: {roles}")

    if gold_tasks != expected_tasks:
        missing = [task_id for task_id in EXPECTED_TASK_IDS if task_id not in gold_tasks]
        extra = sorted(gold_tasks - expected_tasks)
        raise ValueError(
            f"SFT dataset must contain one gold-pass for every frozen target; "
            f"missing={missing} extra={extra}"
        )
    if safe_stop_count < 1:
        raise ValueError("SFT dataset must contain at least one approved safe_stop example")

    return rows


def _render_chat(processor: Any, row: dict[str, Any]) -> str:
    try:
        text = processor.apply_chat_template(
            row["messages"],
            tools=row.get("tools"),
            tokenize=False,
            add_generation_prompt=False,
        )
    except TypeError as exc:
        raise ValueError(
            f"{row.get('example_id', row.get('instance_id'))}: "
            "Gemma 4 chat template rejected tool-calling trajectory"
        ) from exc
    if not isinstance(text, str) or not text.strip():
        raise ValueError(
            f"{row.get('example_id', row.get('instance_id'))}: rendered chat is empty"
        )
    return text


def _tokenize_for_length(processor: Any, text: str) -> list[int]:
    tokenizer = getattr(processor, "tokenizer", processor)
    encoded = tokenizer(text, add_special_tokens=False)
    ids = encoded.get("input_ids") if isinstance(encoded, dict) else getattr(encoded, "input_ids", None)
    if not isinstance(ids, list):
        raise ValueError("processor/tokenizer did not return a flat input_ids list")
    return ids


def preflight_token_lengths(
    processor: Any,
    rows: list[dict[str, Any]],
    *,
    max_length: int,
) -> dict[str, int]:
    """Render/tokenize all examples and abort rather than silently truncate."""
    lengths: dict[str, int] = {}
    for row in rows:
        key = str(row.get("example_id") or row.get("instance_id") or "")
        if not key:
            raise ValueError("training row has no example identifier")
        if key in lengths:
            raise ValueError(f"duplicate example identifier in length preflight: {key}")
        text = _render_chat(processor, row)
        length = len(_tokenize_for_length(processor, text))
        lengths[key] = length
        if length > max_length:
            raise ValueError(
                f"{key}: {length} tokens would truncate at max_length={max_length}"
            )
    return lengths


def render_training_texts(processor: Any, rows: list[dict[str, Any]]) -> list[str]:
    return [_render_chat(processor, row) for row in rows]


def validate_lora_target_modules(model: Any, targets: list[str]) -> list[str]:
    """Ensure suffix targets exist only inside the text decoder namespace."""
    target_set = set(targets)
    matches = [
        name
        for name, _ in model.named_modules()
        if name.rsplit(".", 1)[-1] in target_set
    ]
    if not matches:
        raise ValueError("no LoRA target modules found")
    outside = [name for name in matches if not name.startswith("model.layers.")]
    if outside:
        raise ValueError(f"LoRA target matched outside model.layers: {outside[:10]}")
    missing = [target for target in targets if not any(name.endswith(f".{target}") for name in matches)]
    if missing:
        raise ValueError(f"LoRA target modules missing from decoder: {missing}")
    return matches


def _decode_embedded_dataset() -> str:
    import base64

    if SFT_JSONL_B64 == "__VERIFIER_SFT_JSONL_B64__":
        raise RuntimeError("SFT dataset placeholder was not rendered")
    try:
        return base64.b64decode(SFT_JSONL_B64.encode("ascii"), validate=True).decode("utf-8")
    except Exception as exc:
        raise RuntimeError("invalid embedded SFT dataset") from exc


def _package_versions() -> dict[str, str]:
    import importlib.metadata

    result = {}
    for package in ("torch", "transformers", "peft", "trl", "datasets", "accelerate"):
        try:
            result[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            result[package] = "missing"
    return result


def main() -> None:
    import torch
    from datasets import Dataset
    from peft import LoraConfig
    from transformers import AutoModelForCausalLM, AutoProcessor, set_seed
    from trl import SFTConfig, SFTTrainer

    if not MODEL_PATH.is_dir():
        raise FileNotFoundError(f"unquantized E4B model mount not found: {MODEL_PATH}")
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    ADAPTER_DIR.mkdir(parents=True, exist_ok=True)

    raw_payload = _decode_embedded_dataset()
    rows = load_sft_rows(raw_payload)
    dataset_sha256 = hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()
    set_seed(TRAINING_CONFIG["seed"])

    processor = AutoProcessor.from_pretrained(str(MODEL_PATH), local_files_only=True)
    tokenizer = getattr(processor, "tokenizer", None)
    if tokenizer is None:
        raise RuntimeError("Gemma 4 processor has no tokenizer")
    if tokenizer.pad_token_id is None:
        if tokenizer.eos_token_id is None:
            raise RuntimeError("Gemma 4 tokenizer has neither pad nor eos token")
        tokenizer.pad_token = tokenizer.eos_token

    token_lengths = preflight_token_lengths(
        processor,
        rows,
        max_length=TRAINING_CONFIG["max_length"],
    )
    texts = render_training_texts(processor, rows)
    example_ids = [str(row["example_id"]) for row in rows]
    instance_ids = [str(row["instance_id"]) for row in rows]
    labels = [str(row["label"]) for row in rows]
    train_dataset = Dataset.from_dict(
        {
            "example_id": example_ids,
            "instance_id": instance_ids,
            "label": labels,
            "text": texts,
        }
    )

    dtype = torch.bfloat16 if torch.cuda.is_available() and torch.cuda.is_bf16_supported() else torch.float16
    model = AutoModelForCausalLM.from_pretrained(
        str(MODEL_PATH),
        local_files_only=True,
        dtype=dtype,
        low_cpu_mem_usage=True,
        device_map="auto",
    )
    if model.__class__.__name__ != "Gemma4ForCausalLM":
        raise RuntimeError(f"expected Gemma4ForCausalLM, got {model.__class__.__name__}")
    model.config.use_cache = False
    model.gradient_checkpointing_enable()
    matched_modules = validate_lora_target_modules(model, TRAINING_CONFIG["target_modules"])

    peft_config = LoraConfig(
        r=TRAINING_CONFIG["r"],
        lora_alpha=TRAINING_CONFIG["lora_alpha"],
        lora_dropout=TRAINING_CONFIG["lora_dropout"],
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=TRAINING_CONFIG["target_modules"],
    )
    training_args = SFTConfig(
        output_dir=str(OUTPUT_ROOT / "trainer"),
        dataset_text_field="text",
        max_length=TRAINING_CONFIG["max_length"],
        learning_rate=TRAINING_CONFIG["learning_rate"],
        num_train_epochs=TRAINING_CONFIG["num_train_epochs"],
        per_device_train_batch_size=1,
        gradient_accumulation_steps=1,
        gradient_checkpointing=True,
        bf16=dtype == torch.bfloat16,
        fp16=dtype == torch.float16,
        logging_steps=1,
        save_strategy="no",
        report_to="none",
        seed=TRAINING_CONFIG["seed"],
        data_seed=TRAINING_CONFIG["seed"],
        packing=False,
    )
    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        processing_class=tokenizer,
        peft_config=peft_config,
    )

    trainable_params = sum(p.numel() for p in trainer.model.parameters() if p.requires_grad)
    total_params = sum(p.numel() for p in trainer.model.parameters())
    if trainable_params <= 0 or trainable_params >= total_params:
        raise RuntimeError(
            f"unexpected trainable parameter count: trainable={trainable_params} total={total_params}"
        )

    result = trainer.train()
    trainer.model.save_pretrained(str(ADAPTER_DIR), safe_serialization=True)

    required = {"adapter_config.json", "adapter_model.safetensors"}
    actual_files = {path.name for path in ADAPTER_DIR.iterdir() if path.is_file()}
    missing = sorted(required - actual_files)
    if missing:
        raise RuntimeError(f"adapter output missing required files: {missing}")
    forbidden_full_model = {
        "model.safetensors",
        "pytorch_model.bin",
        "config.json",
    } & actual_files
    if forbidden_full_model:
        raise RuntimeError(f"full-model artifacts leaked into adapter dir: {sorted(forbidden_full_model)}")

    adapter_config = json.loads((ADAPTER_DIR / "adapter_config.json").read_text(encoding="utf-8"))
    if int(adapter_config.get("r", -1)) != TRAINING_CONFIG["r"]:
        raise RuntimeError(f"saved adapter rank mismatch: {adapter_config.get('r')}")

    report = {
        "version": "verifier-lora-v0-training",
        "status": "completed",
        "model_path": str(MODEL_PATH),
        "model_class": model.__class__.__name__,
        "dataset_sha256": dataset_sha256,
        "required_gold_task_ids": EXPECTED_TASK_IDS,
        "example_ids": example_ids,
        "instance_ids": instance_ids,
        "label_counts": dict(Counter(labels)),
        "token_lengths": token_lengths,
        "max_observed_tokens": max(token_lengths.values()),
        "training_config": TRAINING_CONFIG,
        "matched_target_module_count": len(matched_modules),
        "matched_target_module_sample": matched_modules[:20],
        "trainable_params": trainable_params,
        "total_params": total_params,
        "trainable_fraction": trainable_params / total_params,
        "train_metrics": dict(result.metrics),
        "adapter_files": sorted(actual_files),
        "package_versions": _package_versions(),
        "visible_gpus": torch.cuda.device_count() if torch.cuda.is_available() else 0,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print("VERIFIER_LORA_TRAINING_REPORT", json.dumps(report, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
