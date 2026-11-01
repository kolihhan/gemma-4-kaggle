import json
import unittest


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
        self.assertEqual(
            TRAINING_CONFIG["target_modules"],
            ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        )
        self.assertNotIn("sweep", TRAINING_CONFIG)
        self.assertNotIn("grid", TRAINING_CONFIG)

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

    def test_text_only_lora_target_guard_uses_language_model_decoder(self):
        from kaggle.train_verifier_lora import validate_lora_target_modules

        class FakeModel:
            def named_modules(self):
                return iter(
                    [
                        ("model.language_model.layers.0.self_attn.q_proj", object()),
                        ("model.language_model.layers.0.self_attn.k_proj", object()),
                        ("model.language_model.layers.0.self_attn.v_proj", object()),
                        ("model.language_model.layers.0.self_attn.o_proj", object()),
                        ("model.language_model.layers.0.mlp.gate_proj", object()),
                        ("model.language_model.layers.0.mlp.up_proj", object()),
                        ("model.language_model.layers.0.mlp.down_proj", object()),
                    ]
                )

        matches = validate_lora_target_modules(FakeModel(), ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"])
        self.assertEqual(len(matches), 7)

        class BadModel(FakeModel):
            def named_modules(self):
                return iter(list(super().named_modules()) + [("model.vision_tower.layers.0.q_proj", object())])

        with self.assertRaisesRegex(ValueError, "outside model.language_model.layers"):
            validate_lora_target_modules(BadModel(), ["q_proj"])


if __name__ == "__main__":
    unittest.main()
