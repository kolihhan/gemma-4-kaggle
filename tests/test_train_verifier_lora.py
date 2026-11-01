import base64
import json
import unittest


EXPECTED_IDS = [
    "fastapi_14479",
    "rich_3718",
    "rich_3882",
    "rich_3953",
    "rich_4006",
]


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

    def test_dataset_loader_rejects_leakage_duplicates_and_unexpected_ids(self):
        from kaggle.train_verifier_lora import load_sft_rows

        good = [
            {
                "instance_id": task_id,
                "label": "verified_submit",
                "source": "gold_patch_targeted_test",
                "messages": [{"role": "system", "content": "x"}],
                "tools": [{"type": "function", "function": {"name": "run_command"}}],
            }
            for task_id in EXPECTED_IDS
        ]
        payload = "\n".join(json.dumps(row) for row in good) + "\n"
        rows = load_sft_rows(payload)
        self.assertEqual([row["instance_id"] for row in rows], EXPECTED_IDS)

        bad_cases = []
        duplicate = good + [dict(good[0])]
        bad_cases.append("\n".join(json.dumps(row) for row in duplicate))
        wrong_id = [dict(row) for row in good]
        wrong_id[0]["instance_id"] = "rich_3105"
        bad_cases.append("\n".join(json.dumps(row) for row in wrong_id))
        leaked = [dict(row) for row in good]
        leaked[0] = dict(leaked[0], reference_patch="secret")
        bad_cases.append("\n".join(json.dumps(row) for row in leaked))
        wrong_label = [dict(row) for row in good]
        wrong_label[0]["label"] = "maybe"
        bad_cases.append("\n".join(json.dumps(row) for row in wrong_label))

        for payload in bad_cases:
            with self.subTest(payload=payload[:120]):
                with self.assertRaises(ValueError):
                    load_sft_rows(payload)

    def test_length_preflight_refuses_truncation(self):
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
                "messages": [{"role": "system", "content": "abcd"}],
                "tools": [{"type": "function", "function": {"name": "run_command"}}],
            }
        ]
        lengths = preflight_token_lengths(FakeProcessor(), rows, max_length=4)
        self.assertEqual(lengths, {"short": 4})

        rows[0]["messages"][0]["content"] = "abcde"
        with self.assertRaisesRegex(ValueError, "would truncate"):
            preflight_token_lengths(FakeProcessor(), rows, max_length=4)

    def test_text_only_lora_target_guard_rejects_non_decoder_modules(self):
        from kaggle.train_verifier_lora import validate_lora_target_modules

        class FakeModel:
            def named_modules(self):
                return iter(
                    [
                        ("model.layers.0.self_attn.q_proj", object()),
                        ("model.layers.0.self_attn.k_proj", object()),
                        ("model.layers.0.self_attn.v_proj", object()),
                        ("model.layers.0.self_attn.o_proj", object()),
                        ("model.layers.0.mlp.gate_proj", object()),
                        ("model.layers.0.mlp.up_proj", object()),
                        ("model.layers.0.mlp.down_proj", object()),
                    ]
                )

        matches = validate_lora_target_modules(FakeModel(), ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"])
        self.assertEqual(len(matches), 7)

        class BadModel(FakeModel):
            def named_modules(self):
                return iter(list(super().named_modules()) + [("vision_tower.layers.0.q_proj", object())])

        with self.assertRaisesRegex(ValueError, "outside model.layers"):
            validate_lora_target_modules(BadModel(), ["q_proj"])


if __name__ == "__main__":
    unittest.main()
