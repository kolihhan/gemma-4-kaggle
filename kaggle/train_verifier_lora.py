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
from collections.abc import Mapping
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
    "logit_chunk_tokens": 256,
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


def ensure_peft_torchao_compat(*, version_lookup=None, runner=None) -> dict[str, str]:
    """Remove only a known-incompatible torchao before importing PEFT."""
    import importlib.metadata
    import subprocess
    import sys

    if version_lookup is None:
        version_lookup = importlib.metadata.version
    if runner is None:
        runner = subprocess.run

    try:
        version = str(version_lookup("torchao"))
    except importlib.metadata.PackageNotFoundError:
        return {"torchao_version": "missing", "action": "none"}

    pieces = version.split(".")
    if len(pieces) < 2:
        raise RuntimeError(f"cannot parse installed torchao version: {version!r}")
    try:
        major = int(pieces[0])
        minor = int(pieces[1])
    except ValueError as exc:
        raise RuntimeError(f"cannot parse installed torchao version: {version!r}") from exc

    if (major, minor) >= (0, 16):
        return {"torchao_version": version, "action": "none"}

    runner(
        [sys.executable, "-m", "pip", "uninstall", "-y", "torchao"],
        check=True,
        text=True,
        capture_output=True,
    )
    return {"torchao_version": version, "action": "uninstalled_incompatible"}


def build_two_gpu_load_kwargs(torch_module, *, dtype) -> dict[str, Any]:
    device_count = int(torch_module.cuda.device_count())
    if device_count != 2:
        raise RuntimeError(f'verifier LoRA v0 requires exactly 2 CUDA GPUs; found {device_count}')

    # Accelerate's generic "balanced" placement leaves the frozen E4B checkpoint
    # badly skewed on 2x L4 because the 5.25 GiB per-layer embedding block is an
    # indivisible module. Keep the observed stable module boundaries, but place
    # that block on GPU 0 so static weights are roughly 7.5 / 7.3 GiB instead of
    # 2.3 / 12.5 GiB. This preserves both GPUs and forbids CPU/disk offload.
    device_map = {
        'model.vision_tower': 0,
        'model.language_model.embed_tokens': 0,
        'model.language_model.embed_tokens_per_layer': 0,
        'model.audio_tower': 1,
        'model.embed_vision': 1,
        'model.embed_audio': 1,
        'model.language_model.per_layer_projection_norm': 0,
        'model.language_model.per_layer_model_projection': 0,
    }
    for layer_index in range(42):
        device_map[f'model.language_model.layers.{layer_index}'] = 0 if layer_index <= 3 else 1
    device_map.update(
        {
            'model.language_model.norm': 1,
            'model.language_model.rotary_emb': 1,
            'lm_head': 0,
        }
    )
    return {
        'dtype': dtype,
        'low_cpu_mem_usage': True,
        'device_map': device_map,
    }


def validate_two_gpu_device_map(model) -> dict[str, Any]:
    device_map = getattr(model, 'hf_device_map', None)
    if not isinstance(device_map, Mapping) or not device_map:
        raise RuntimeError('model is missing a non-empty hf_device_map')

    accelerator_devices = set()
    offloaded_devices = set()
    for destination in device_map.values():
        normalized = destination
        if isinstance(destination, str):
            normalized = destination.strip().lower()
            if normalized.startswith('cuda:'):
                normalized = int(normalized.split(':', 1)[1])
            elif normalized.isdigit():
                normalized = int(normalized)
        elif getattr(destination, 'type', None) == 'cuda':
            normalized = int(destination.index)

        if normalized in {'cpu', 'disk'}:
            offloaded_devices.add(str(normalized))
        elif isinstance(normalized, int):
            accelerator_devices.add(normalized)
        else:
            raise RuntimeError(f'unexpected device-map destination: {destination!r}')

    if offloaded_devices:
        raise RuntimeError(f'CPU/disk offload is forbidden for verifier LoRA v0: {sorted(offloaded_devices)}')
    if accelerator_devices != {0, 1}:
        raise RuntimeError(f'model must span both GPU 0 and GPU 1; got {sorted(accelerator_devices)}')
    return {
        'accelerator_devices': sorted(accelerator_devices),
        'offloaded_devices': sorted(offloaded_devices),
        'module_count': len(device_map),
    }


def validate_trainer_model_parallel(trainer) -> None:
    if not bool(getattr(trainer, 'is_model_parallel', False)):
        raise RuntimeError('Trainer did not recognize the two-GPU model-parallel placement')
    if bool(getattr(trainer, 'place_model_on_device', True)):
        raise RuntimeError('Trainer must not move the model after model-parallel loading')


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


def tokenize_training_texts(tokenizer: Any, texts: list[str]) -> list[dict[str, list[int]]]:
    """Tokenize full SFT transcripts without truncation and copy inputs to LM labels."""
    examples: list[dict[str, list[int]]] = []
    for index, text in enumerate(texts):
        encoded = tokenizer(text, add_special_tokens=False, truncation=False)
        input_ids = encoded.get("input_ids") if isinstance(encoded, Mapping) else None
        attention_mask = encoded.get("attention_mask") if isinstance(encoded, Mapping) else None
        if not isinstance(input_ids, list) or not input_ids:
            raise ValueError(f"training example {index}: tokenizer returned invalid input_ids")
        if attention_mask is None:
            attention_mask = [1] * len(input_ids)
        if not isinstance(attention_mask, list) or len(attention_mask) != len(input_ids):
            raise ValueError(f"training example {index}: invalid attention_mask")
        examples.append(
            {
                "input_ids": input_ids,
                "attention_mask": attention_mask,
                "labels": list(input_ids),
            }
        )
    return examples


def full_sequence_chunk_ranges(sequence_length: int, chunk_tokens: int) -> list[tuple[int, int]]:
    """Partition every shifted next-token position into bounded contiguous chunks."""
    if sequence_length < 2:
        raise ValueError("sequence_length must be at least 2")
    if chunk_tokens <= 0:
        raise ValueError("chunk_tokens must be positive")
    shifted_length = sequence_length - 1
    return [
        (start, min(start + chunk_tokens, shifted_length))
        for start in range(0, shifted_length, chunk_tokens)
    ]


def chunked_full_sequence_causal_lm_loss(
    hidden_states: Any,
    labels: Any,
    lm_head: Any,
    *,
    chunk_tokens: int,
    final_logit_softcapping: float | None = None,
):
    """Compute the exact full-sequence causal-LM mean loss with bounded vocab logits."""
    import torch
    import torch.nn.functional as F
    from torch.utils.checkpoint import checkpoint

    if getattr(hidden_states, "ndim", None) != 3:
        raise ValueError("hidden_states must have shape [batch, sequence, hidden]")
    if getattr(labels, "ndim", None) != 2:
        raise ValueError("labels must have shape [batch, sequence]")
    if tuple(hidden_states.shape[:2]) != tuple(labels.shape):
        raise ValueError(
            f"hidden_states/labels shape mismatch: "
            f"hidden={tuple(hidden_states.shape)} labels={tuple(labels.shape)}"
        )

    ranges = full_sequence_chunk_ranges(int(hidden_states.shape[1]), chunk_tokens)
    shifted_hidden = hidden_states[:, :-1, :]
    shifted_labels = labels[:, 1:]
    supervised_tokens = int((shifted_labels != -100).sum().item())
    if supervised_tokens <= 0:
        raise ValueError("full-sequence causal LM loss has no supervised tokens")

    if final_logit_softcapping is not None and float(final_logit_softcapping) <= 0:
        raise ValueError("final_logit_softcapping must be positive when set")

    def chunk_loss(chunk_hidden, chunk_labels):
        logits = lm_head(chunk_hidden).float()
        if final_logit_softcapping is not None:
            cap = float(final_logit_softcapping)
            logits = torch.tanh(logits / cap) * cap
        targets = chunk_labels.to(logits.device)
        return F.cross_entropy(
            logits.reshape(-1, logits.shape[-1]),
            targets.reshape(-1),
            ignore_index=-100,
            reduction="sum",
        )

    total_loss = None
    for start, end in ranges:
        hidden_chunk = shifted_hidden[:, start:end, :]
        label_chunk = shifted_labels[:, start:end]
        if hidden_chunk.requires_grad:
            piece = checkpoint(
                chunk_loss,
                hidden_chunk,
                label_chunk,
                use_reentrant=False,
            )
        else:
            piece = chunk_loss(hidden_chunk, label_chunk)
        total_loss = piece if total_loss is None else total_loss + piece

    return total_loss / supervised_tokens


def resolve_chunked_loss_components(model: Any) -> tuple[Any, Any, Any, float | None]:
    """Resolve the injected Gemma 4 base model, backbone, LM head, and exact logit softcap."""
    base_model = model.get_base_model() if hasattr(model, "get_base_model") else model
    backbone = getattr(base_model, "model", None)
    lm_head = getattr(base_model, "lm_head", None)
    config = getattr(base_model, "config", None)
    if backbone is None or lm_head is None or config is None:
        raise RuntimeError("trainer could not resolve Gemma 4 backbone/lm_head/config")

    text_config = config.get_text_config() if hasattr(config, "get_text_config") else config
    softcap = getattr(text_config, "final_logit_softcapping", None)
    return base_model, backbone, lm_head, softcap


class CausalLmCollator:
    """Right-pad causal-LM examples; ignore padding tokens in the loss."""

    def __init__(self, tokenizer: Any):
        if tokenizer.pad_token_id is None:
            raise ValueError("tokenizer pad_token_id is required")
        self.pad_token_id = int(tokenizer.pad_token_id)

    def __call__(self, features: list[dict[str, list[int]]]) -> dict[str, Any]:
        import torch

        if not features:
            raise ValueError("cannot collate an empty batch")
        max_length = max(len(feature["input_ids"]) for feature in features)
        input_ids: list[list[int]] = []
        attention_mask: list[list[int]] = []
        labels: list[list[int]] = []
        for feature in features:
            ids = list(feature["input_ids"])
            mask = list(feature["attention_mask"])
            target = list(feature["labels"])
            if not (len(ids) == len(mask) == len(target)):
                raise ValueError("causal LM feature lengths do not match")
            padding = max_length - len(ids)
            input_ids.append(ids + [self.pad_token_id] * padding)
            attention_mask.append(mask + [0] * padding)
            labels.append(target + [-100] * padding)
        return {
            "input_ids": torch.tensor(input_ids, dtype=torch.long),
            "attention_mask": torch.tensor(attention_mask, dtype=torch.long),
            "labels": torch.tensor(labels, dtype=torch.long),
        }


def validate_model_class(model: Any) -> None:
    """Require the official multimodal Gemma 4 wrapper used by this checkpoint."""
    name = model.__class__.__name__
    if name != "Gemma4ForConditionalGeneration":
        raise ValueError(
            f"expected Gemma4ForConditionalGeneration for the E4B checkpoint, got {name}"
        )


def validate_lora_target_modules(model: Any, targets: list[str]) -> list[str]:
    """Select exact text-decoder modules while ignoring same-named multimodal tower layers."""
    target_set = set(targets)
    decoder_prefix = "model.language_model.layers."
    matches = [
        name
        for name, _ in model.named_modules()
        if name.startswith(decoder_prefix) and name.rsplit(".", 1)[-1] in target_set
    ]
    if not matches:
        raise ValueError("no LoRA target modules found in model.language_model.layers")
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
    for package in ("torch", "transformers", "peft", "datasets", "accelerate"):
        try:
            result[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            result[package] = "missing"
    return result


def main() -> None:
    ensure_peft_torchao_compat()

    import torch
    from datasets import Dataset
    from transformers import (
        AutoModelForCausalLM,
        AutoProcessor,
        Trainer,
        TrainingArguments,
        set_seed,
    )
    from peft import LoraConfig, get_peft_model

    class FullSequenceTrainer(Trainer):
        """Preserve full causal-LM supervision while chunking only the vocab projection."""

        def compute_loss(
            self,
            model,
            inputs,
            return_outputs=False,
            num_items_in_batch=None,
        ):
            model_inputs = dict(inputs)
            labels = model_inputs.pop("labels")
            _, backbone, lm_head, softcap = resolve_chunked_loss_components(model)
            outputs = backbone(
                **model_inputs,
                use_cache=False,
                return_dict=True,
            )
            hidden_states = outputs.last_hidden_state
            loss = chunked_full_sequence_causal_lm_loss(
                hidden_states,
                labels,
                lm_head,
                chunk_tokens=TRAINING_CONFIG["logit_chunk_tokens"],
                final_logit_softcapping=softcap,
            )
            return (loss, outputs) if return_outputs else loss

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
    tokenizer.padding_side = "right"

    token_lengths = preflight_token_lengths(
        processor,
        rows,
        max_length=TRAINING_CONFIG["max_length"],
    )
    texts = render_training_texts(processor, rows)
    tokenized_examples = tokenize_training_texts(tokenizer, texts)
    example_ids = [str(row["example_id"]) for row in rows]
    instance_ids = [str(row["instance_id"]) for row in rows]
    labels = [str(row["label"]) for row in rows]
    train_dataset = Dataset.from_list(tokenized_examples)

    if not torch.cuda.is_available():
        raise RuntimeError("verifier LoRA training requires a visible CUDA GPU")
    dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    load_kwargs = build_two_gpu_load_kwargs(torch, dtype=dtype)
    model = AutoModelForCausalLM.from_pretrained(
        str(MODEL_PATH),
        local_files_only=True,
        **load_kwargs,
    )
    validate_model_class(model)
    device_map_summary = validate_two_gpu_device_map(model)
    base_model_class = model.__class__.__name__
    model.config.use_cache = False
    model.gradient_checkpointing_enable()
    matched_modules = validate_lora_target_modules(model, TRAINING_CONFIG["target_modules"])

    peft_config = LoraConfig(
        r=TRAINING_CONFIG["r"],
        lora_alpha=TRAINING_CONFIG["lora_alpha"],
        lora_dropout=TRAINING_CONFIG["lora_dropout"],
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=matched_modules,
    )
    model = get_peft_model(model, peft_config)
    device_map_summary = validate_two_gpu_device_map(model)
    if hasattr(model, "enable_input_require_grads"):
        model.enable_input_require_grads()

    training_args = TrainingArguments(
        output_dir=str(OUTPUT_ROOT / "trainer"),
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
        remove_unused_columns=False,
    )
    trainer = FullSequenceTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        data_collator=CausalLmCollator(tokenizer),
    )
    validate_trainer_model_parallel(trainer)

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
        "model_class": base_model_class,
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
        "visible_gpus": torch.cuda.device_count(),
        "device_map_summary": device_map_summary,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print("VERIFIER_LORA_TRAINING_REPORT", json.dumps(report, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
