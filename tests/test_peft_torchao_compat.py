import importlib.metadata
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
TRAINER_SOURCE = ROOT / "kaggle" / "train_verifier_lora.py"


class PeftTorchaoCompatTests(unittest.TestCase):
    def test_old_torchao_is_removed_before_peft_import(self):
        from kaggle.train_verifier_lora import ensure_peft_torchao_compat

        calls = []

        def version_lookup(name):
            self.assertEqual(name, "torchao")
            return "0.10.0"

        def runner(args, **kwargs):
            calls.append((args, kwargs))

            class Result:
                stdout = "removed"

            return Result()

        result = ensure_peft_torchao_compat(version_lookup=version_lookup, runner=runner)
        self.assertEqual(result, {"torchao_version": "0.10.0", "action": "uninstalled_incompatible"})
        self.assertEqual(len(calls), 1)
        args, kwargs = calls[0]
        self.assertEqual(args[-5:], ["-m", "pip", "uninstall", "-y", "torchao"])
        self.assertTrue(kwargs["check"])
        self.assertTrue(kwargs["text"])
        self.assertTrue(kwargs["capture_output"])

        source = TRAINER_SOURCE.read_text(encoding="utf-8")
        self.assertLess(source.index("ensure_peft_torchao_compat()"), source.index("from peft import"))

    def test_absent_or_supported_torchao_is_a_noop(self):
        from kaggle.train_verifier_lora import ensure_peft_torchao_compat

        def must_not_run(*args, **kwargs):
            raise AssertionError("runner should not be called")

        def absent(_name):
            raise importlib.metadata.PackageNotFoundError("torchao")

        self.assertEqual(
            ensure_peft_torchao_compat(version_lookup=absent, runner=must_not_run),
            {"torchao_version": "missing", "action": "none"},
        )
        self.assertEqual(
            ensure_peft_torchao_compat(version_lookup=lambda _name: "0.16.1", runner=must_not_run),
            {"torchao_version": "0.16.1", "action": "none"},
        )


if __name__ == "__main__":
    unittest.main()
