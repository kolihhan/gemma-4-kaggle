import json
from collections import UserDict
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
TRAINER_SOURCE = ROOT / "kaggle" / "train_verifier_lora.py"

EXPECTED_TASK_IDS = [
    "fastapi_14479",
    "requests_6644",
    "rich_3718",
    "rich_3882",
    "rich_3953",
    "rich_4006",
]


def sft_row(task_id, label):
    if label == "verified_submit":
        example_id = f"{task_id}:gold-pass"
        source = "gold_patch_targeted_test"
    elif label == "safe_stop":
        example_id = f"{task_id}:base-fail"
        source = "base_targeted_failure"
    else:
        example_id = f"{task_id}:bad"
        source = "bad"
    return {
        "instance_id": task_id,
        "example_id": example_id,
        "label": label,
        "source": source,
        "messages": [
            {"role": "system", "content": "verify"},
            {"role": "assistant", "content": "run test"},
            {"role": "tool", "content": "evidence"},
        ],
        "tools": [{"type": "function", "function": {"name": "run_command"}}],
    }


class VerifierLoraTrainingContractTests(unittest.TestCase):
    def test_frozen_v0_config(self):
        from kaggle.train_verifier_lora import TRAINING_CONFIG

        self.assertEqual(TRAINING_CONFIG["r"], 8)
        self.assertEqual(TRAINING_CONFIG["lora_alpha"], 16)
        self.assertEqual(TRAINING_CONFIG["lora_dropout"], 0.05)
        self.assertEqual(TRAINING_CONFIG["learning_rate"], 1e-4)
        self.assertEqual(TRAINING_CONFIG["num_train_epochs"], 3)
        self.assertEqual(TRAINING_CONFIG["seed"], 42)
        self.assertEqual(TRAINING_CONFIG["max_length"], 4096)
        self.assertEqual(TRAINING_CONFIG["loss_window_tokens"], 256)
        self.assertEqual(
            TRAINING_CONFIG["target_modules"],
            ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        )
        self.assertNotIn("sweep", TRAINING_CONFIG)
        self.assertNotIn("grid", TRAINING_CONFIG)

    def test_two_gpu_load_kwargs_move_large_per_layer_embeddings_to_gpu0(self):
        from kaggle.train_verifier_lora import build_two_gpu_load_kwargs

        class FakeCuda:
            @staticmethod
            def device_count():
                return 2

        class FakeTorch:
            cuda = FakeCuda()

        dtype = object()
        kwargs = build_two_gpu_load_kwargs(FakeTorch, dtype=dtype)
        device_map = kwargs["device_map"]

        self.assertIs(kwargs["dtype"], dtype)
        self.assertTrue(kwargs["low_cpu_mem_usage"])
        self.assertIsInstance(device_map, dict)
        self.assertEqual(device_map["model.language_model.embed_tokens_per_layer"], 0)
        self.assertEqual(device_map["model.language_model.embed_tokens"], 0)
        self.assertEqual(device_map["model.language_model.layers.0"], 0)
        self.assertEqual(device_map["model.language_model.layers.3"], 0)
        self.assertEqual(device_map["model.language_model.layers.4"], 1)
        self.assertEqual(device_map["model.language_model.layers.41"], 1)
        self.assertEqual(device_map["model.audio_tower"], 1)
        self.assertEqual(device_map["model.vision_tower"], 0)
        self.assertEqual({value for value in device_map.values()}, {0, 1})
        self.assertNotIn("max_memory", kwargs)

    def test_kaggle_runtime_uses_native_transformers_trainer_not_trl(self):
        source = TRAINER_SOURCE.read_text(encoding="utf-8")
        self.assertNotIn("from trl", source)
        self.assertNotIn("SFTTrainer", source)
        self.assertNotIn("SFTConfig", source)
        self.assertIn("Trainer", source)
        self.assertIn("TrainingArguments", source)
        self.assertIn("get_peft_model", source)
        self.assertIn("CausalLmCollator", source)

    def test_final_window_loss_keeps_full_context_but_bounds_vocab_logits(self):
        from kaggle.train_verifier_lora import final_window_loss_slice

        self.assertEqual(final_window_loss_slice(3134, 256), (256, 2878))
        self.assertEqual(final_window_loss_slice(64, 256), (64, 0))
        with self.assertRaisesRegex(ValueError, "sequence_length"):
            final_window_loss_slice(0, 256)
        with self.assertRaisesRegex(ValueError, "loss_window_tokens"):
            final_window_loss_slice(64, 0)

        source = TRAINER_SOURCE.read_text(encoding="utf-8")
        self.assertIn("class FinalWindowTrainer", source)
        self.assertIn("logits_to_keep=keep_tokens", source)

    def test_tokenize_training_texts_accepts_mapping_batch_encoding(self):
        from kaggle.train_verifier_lora import tokenize_training_texts

        class FakeTokenizer:
            def __call__(self, text, add_special_tokens=False, truncation=False):
                return UserDict(
                    {
                        "input_ids": [11, 12, 13],
                        "attention_mask": [1, 1, 1],
                    }
                )

        examples = tokenize_training_texts(FakeTokenizer(), ["hello"])
        self.assertEqual(
            examples,
            [
                {
                    "input_ids": [11, 12, 13],
                    "attention_mask": [1, 1, 1],
                    "labels": [11, 12, 13],
                }
            ],
        )

    def test_dataset_loader_accepts_gold_coverage_plus_safe_stop_subset(self):
        from kaggle.train_verifier_lora import load_sft_rows

        good = []
        for task_id in EXPECTED_TASK_IDS:
            if task_id in {"requests_6644", "rich_3953"}:
                good.append(sft_row(task_id, "safe_stop"))
            good.append(sft_row(task_id, "verified_submit"))
        payload = "\n".join(json.dumps(row) for row in good) + "\n"
        rows = load_sft_rows(payload)
        self.assertEqual([row["example_id"] for row in rows], [row["example_id"] for row in good])
        self.assertEqual(
            {row["instance_id"] for row in rows if row["label"] == "verified_submit"},
            set(EXPECTED_TASK_IDS),
        )
        self.assertIn("safe_stop", {row["label"] for row in rows})

    def test_dataset_loader_rejects_leakage_duplicates_missing_gold_and_bad_labels(self):
        from kaggle.train_verifier_lora import load_sft_rows

        good = [sft_row(task_id, "verified_submit") for task_id in EXPECTED_TASK_IDS]
        good.insert(1, sft_row("requests_6644", "safe_stop"))

        bad_cases = []
        duplicate = good + [dict(good[0])]
        bad_cases.append("\n".join(json.dumps(row) for row in duplicate))

        wrong_id = [dict(row) for row in good]
        wrong_id[0]["instance_id"] = "rich_3105"
        bad_cases.append("\n".join(json.dumps(row) for row in wrong_id))

        leaked = [dict(row) for row in good]
        leaked[0] = dict(leaked[0], reference_patch="secret")
        bad_cases.append("\n".join(json.dumps(row) for row in leaked))

        missing_gold = [row for row in good if row["example_id"] != "rich_4006:gold-pass"]
        bad_cases.append("\n".join(json.dumps(row) for row in missing_gold))

        no_negative = [sft_row(task_id, "verified_submit") for task_id in EXPECTED_TASK_IDS]
        bad_cases.append("\n".join(json.dumps(row) for row in no_negative))

        wrong_label = [dict(row) for row in good]
        wrong_label[0]["label"] = "maybe"
        bad_cases.append("\n".join(json.dumps(row) for row in wrong_label))

        wrong_example_id = [dict(row) for row in good]
        wrong_example_id[0]["example_id"] = "fastapi_14479:base-fail"
        bad_cases.append("\n".join(json.dumps(row) for row in wrong_example_id))

        for payload in bad_cases:
            with self.subTest(payload=payload[:120]):
                with self.assertRaises(ValueError):
                    load_sft_rows(payload)

    def test_length_preflight_refuses_truncation_and_keys_by_example(self):
        from kaggle.train_verifier_lora import preflight_token_lengths

        class FakeProcessor:
            def apply_chat_template(self, messages, tools=None, tokenize=False, add_generation_prompt=False):
                self.last_tools = tools
                return messages[0]["content"]

            def __call__(self, text, add_special_tokens=False):
                return {"input_ids": list(range(len(text)))}

        rows = [
            {
                "instance_id": "short",
                "example_id": "short:gold-pass",
                "messages": [{"role": "system", "content": "abcd"}],
                "tools": [{"type": "function", "function": {"name": "run_command"}}],
            }
        ]
        lengths = preflight_token_lengths(FakeProcessor(), rows, max_length=4)
        self.assertEqual(lengths, {"short:gold-pass": 4})

        rows[0]["messages"][0]["content"] = "abcde"
        with self.assertRaisesRegex(ValueError, "would truncate"):
            preflight_token_lengths(FakeProcessor(), rows, max_length=4)

    def test_expected_hf_model_class_is_multimodal_wrapper(self):
        from kaggle.train_verifier_lora import validate_model_class

        class GoodModel:
            pass

        GoodModel.__name__ = "Gemma4ForConditionalGeneration"
        validate_model_class(GoodModel())

        class BadModel:
            pass

        BadModel.__name__ = "Gemma4ForCausalLM"
        with self.assertRaisesRegex(ValueError, "Gemma4ForConditionalGeneration"):
            validate_model_class(BadModel())

    def test_text_only_lora_target_selection_filters_multimodal_towers(self):
        from kaggle.train_verifier_lora import validate_lora_target_modules

        decoder_names = [
            "model.language_model.layers.0.self_attn.q_proj",
            "model.language_model.layers.0.self_attn.k_proj",
            "model.language_model.layers.0.self_attn.v_proj",
            "model.language_model.layers.0.self_attn.o_proj",
            "model.language_model.layers.0.mlp.gate_proj",
            "model.language_model.layers.0.mlp.up_proj",
            "model.language_model.layers.0.mlp.down_proj",
        ]

        class FakeModel:
            def named_modules(self):
                return iter(
                    [(name, object()) for name in decoder_names]
                    + [
                        ("model.vision_tower.layers.0.q_proj", object()),
                        ("model.audio_tower.layers.0.gate_proj", object()),
                    ]
                )

        matches = validate_lora_target_modules(
            FakeModel(),
            ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        )
        self.assertEqual(matches, decoder_names)
        self.assertTrue(all(name.startswith("model.language_model.layers.") for name in matches))

    def test_text_decoder_target_selection_fails_if_any_requested_projection_is_missing(self):
        from kaggle.train_verifier_lora import validate_lora_target_modules

        class MissingModel:
            def named_modules(self):
                return iter([("model.language_model.layers.0.self_attn.q_proj", object())])

        with self.assertRaisesRegex(ValueError, "missing from decoder"):
            validate_lora_target_modules(MissingModel(), ["q_proj", "k_proj"])


if __name__ == "__main__":
    unittest.main()
