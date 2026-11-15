"""Synthetic no-GPU unit contracts for 31B LoRA smoke."""
import unittest
from types import SimpleNamespace
import inspect
from unittest.mock import patch
import importlib.metadata
from kaggle.gemma31b_qlora_one_step_smoke import device_map_summary,TRAINING,main,require_4bit_dependencies

class QLoraSmokeTests(unittest.TestCase):
    def test_no_cpu_offload_is_falsifiable(self):
        m=SimpleNamespace(hf_device_map={"model.embed":0,"model.layers.0":1,
                                         "model.layers.1":"cuda:2"})
        x=device_map_summary(m)
        self.assertEqual(x["gpu_indices"],[0,1,2])
        self.assertFalse(x["cpu_disk_offload"])
        for bad in [
            {"model.embed":"cpu","model.layers.0":1},
            {"model.embed":"disk","model.layers.0":0},
            {},
        ]:
            with self.assertRaises(RuntimeError):
                device_map_summary(SimpleNamespace(hf_device_map=bad))

    def test_4bit_dependency_fail_fast(self):
        versions={"bitsandbytes":"0.50.0","accelerate":"1.15.0"}
        with patch("kaggle.gemma31b_qlora_one_step_smoke.importlib.metadata.version",
                   side_effect=lambda name:versions[name]):
            self.assertEqual(require_4bit_dependencies(),versions)
        def missing(name):
            if name=="bitsandbytes":
                raise importlib.metadata.PackageNotFoundError(name)
            return versions[name]
        with patch("kaggle.gemma31b_qlora_one_step_smoke.importlib.metadata.version",
                   side_effect=missing):
            with self.assertRaisesRegex(RuntimeError,"missing_4bit_dependency_bitsandbytes"):
                require_4bit_dependencies()

    def test_exact_multimodal_model_load_class(self):
        source=inspect.getsource(main)
        self.assertIn("Gemma4ForConditionalGeneration.from_pretrained(",source)
        self.assertNotIn("AutoModelForCausalLM",source)

    def test_one_step_and_lora_scope_bounded(self):
        self.assertEqual(TRAINING["training_steps"],1)
        self.assertLessEqual(TRAINING["max_tokens"],128)
        self.assertTrue(set(TRAINING["target_modules"]).issubset({"q_proj","v_proj"}))
        self.assertLessEqual(TRAINING["r"],8)

if __name__=="__main__":
    unittest.main()
