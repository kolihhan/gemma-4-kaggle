import unittest


class VerifierLoraMultiGpuPlacementTests(unittest.TestCase):
    def test_build_load_kwargs_requires_exact_two_gpus_and_balances_model(self):
        from kaggle.train_verifier_lora import build_two_gpu_load_kwargs

        class FakeCuda:
            @staticmethod
            def device_count():
                return 2

        class FakeTorch:
            cuda = FakeCuda()

        kwargs = build_two_gpu_load_kwargs(FakeTorch, dtype="fp16")
        device_map = kwargs["device_map"]
        self.assertEqual(kwargs["dtype"], "fp16")
        self.assertTrue(kwargs["low_cpu_mem_usage"])
        self.assertIsInstance(device_map, dict)
        self.assertEqual(device_map["model.language_model.embed_tokens_per_layer"], 0)
        self.assertEqual(device_map["model.language_model.embed_tokens"], 0)
        self.assertEqual(device_map["model.language_model.layers.3"], 0)
        self.assertEqual(device_map["model.language_model.layers.4"], 1)
        self.assertEqual(device_map["model.language_model.layers.41"], 1)
        self.assertEqual(device_map["model.vision_tower"], 0)
        self.assertEqual(device_map["model.audio_tower"], 1)
        self.assertEqual(set(device_map.values()), {0, 1})
        self.assertNotIn("max_memory", kwargs)

        class OneGpuCuda:
            @staticmethod
            def device_count():
                return 1

        class OneGpuTorch:
            cuda = OneGpuCuda()

        with self.assertRaisesRegex(RuntimeError, "exactly 2 CUDA GPUs"):
            build_two_gpu_load_kwargs(OneGpuTorch, dtype="fp16")

    def test_validate_two_gpu_device_map_rejects_cpu_disk_or_single_gpu(self):
        from kaggle.train_verifier_lora import validate_two_gpu_device_map

        class Good:
            hf_device_map = {
                "model.language_model.embed_tokens": 0,
                "model.language_model.layers.0": 0,
                "model.language_model.layers.1": 1,
                "lm_head": 1,
            }

        summary = validate_two_gpu_device_map(Good())
        self.assertEqual(summary["accelerator_devices"], [0, 1])
        self.assertEqual(summary["offloaded_devices"], [])

        class CpuOffload:
            hf_device_map = {"a": 0, "b": 1, "c": "cpu"}

        with self.assertRaisesRegex(RuntimeError, "CPU/disk offload"):
            validate_two_gpu_device_map(CpuOffload())

        class SingleGpu:
            hf_device_map = {"a": 0, "b": 0}

        with self.assertRaisesRegex(RuntimeError, "both GPU 0 and GPU 1"):
            validate_two_gpu_device_map(SingleGpu())

    def test_validate_trainer_model_parallel_contract(self):
        from kaggle.train_verifier_lora import validate_trainer_model_parallel

        class GoodTrainer:
            is_model_parallel = True
            place_model_on_device = False

        validate_trainer_model_parallel(GoodTrainer())

        class BadTrainer:
            is_model_parallel = False
            place_model_on_device = True

        with self.assertRaisesRegex(RuntimeError, "model-parallel"):
            validate_trainer_model_parallel(BadTrainer())


if __name__ == "__main__":
    unittest.main()
