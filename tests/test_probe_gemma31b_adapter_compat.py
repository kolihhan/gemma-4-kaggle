import unittest
from unittest.mock import patch
from scripts.probe_gemma31b_adapter_compat import text_arch,audit,get_small_json


class AdapterStaticContractTests(unittest.TestCase):
    def test_text_arch_resolves_nested_language_model(self):
        result=text_arch({"text_config":{"hidden_size":4096,"num_hidden_layers":42}})
        self.assertEqual(result["hidden_size"],4096)
        self.assertEqual(result["num_hidden_layers"],42)

    def test_only_whitelisted_models_and_config_names(self):
        with self.assertRaisesRegex(ValueError,"unapproved"):
            get_small_json("attacker/nonmodel","config.json")
        with self.assertRaisesRegex(ValueError,"unapproved"):
            get_small_json("google/gemma-4-31B-it-qat-w4a16-ct","model.safetensors")

    def test_compatible_shapes_not_inference_adapter_load(self):
        serving={"text_config":{"hidden_size":4096,"num_hidden_layers":42},
                 "quantization_config":{"format":"compressed-tensors"}}
        train={"text_config":{"hidden_size":4096,"num_hidden_layers":42}}
        example={"peft_type":"LORA","task_type":"CAUSAL_LM","r":16,
                 "lora_alpha":16,"base_model_name_or_path":"google/gemma-4-31B-it-qat-w4a16-ct",
                 "target_modules":["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"]}
        with patch("scripts.probe_gemma31b_adapter_compat.get_small_json",
                   side_effect=[serving,train,example]):
            result=audit()
        self.assertTrue(result["text_dimensions_equal"])
        self.assertFalse(result["adapter_load_test_executed"])
        self.assertFalse(result["model_weights_loaded"])
        self.assertTrue(result["example_targets_subset_of_guide"])


if __name__=="__main__":
    unittest.main()
