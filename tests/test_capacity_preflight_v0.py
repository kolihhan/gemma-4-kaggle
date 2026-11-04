"""CPU-only integrity tests for the capacity boundary gate."""
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "capacity_preflight", ROOT / "scripts" / "capacity_preflight_v0.py"
)
capacity = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(capacity)


class CapacityPreflightV0Tests(unittest.TestCase):
    def test_pair_changes_only_root_model_declaration(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = capacity.prepare_model_pair(ROOT, Path(tmp))
            assert set(result) == {"e4b", "31b"}
            paths = sorted(
                p.relative_to(ROOT / "submission").as_posix()
                for p in (ROOT / "submission").rglob("*") if p.is_file()
            )
            for name, model in (
                ("e4b", "gemma-4-e4b-it-qat-w4a16-ct"),
                ("31b", "gemma-4-31b-it-qat-w4a16-ct"),
            ):
                base = Path(tmp) / name
                self.assertEqual(
                    sorted(p.relative_to(base).as_posix() for p in base.rglob("*") if p.is_file()),
                    paths,
                )
                self.assertIn(f"model: {model}", (base / "agent.yaml").read_text())
                self.assertEqual((base / "agent.yaml").read_text().count("model:"), 1)
                for p in paths:
                    if p != "agent.yaml":
                        self.assertEqual(
                            (base / p).read_bytes(),
                            (ROOT / "submission" / p).read_bytes(),
                        )
            self.assertEqual(
                (Path(tmp) / "e4b" / "agent.yaml").read_bytes(),
                (ROOT / "submission" / "agent.yaml").read_bytes(),
            )
            self.assertEqual(result["e4b"]["model"], "gemma-4-e4b-it-qat-w4a16-ct")

    def test_tampered_frozen_control_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            shutil.copytree(ROOT / "submission", repo / "submission")
            (repo / "scripts").mkdir()
            shutil.copy2(ROOT / "scripts" / "render_reliability_v1_kernel.py",
                         repo / "scripts" / "render_reliability_v1_kernel.py")
            agent = repo / "submission" / "agent.yaml"
            agent.write_text(agent.read_text() + "\n# drift\n")
            with self.assertRaisesRegex(ValueError, "hash"):
                capacity.prepare_model_pair(repo, Path(tmp) / "out")

    def test_metadata_only_selection_disjoint_from_known_exposures(self):
        manifest = capacity.build_feasibility_manifest(ROOT)
        selected = manifest["feasibility_ids"]
        reserve = manifest["confirmation_reserve_ids"]
        self.assertEqual(len(selected), 4)
        self.assertEqual(len(reserve), 12)
        self.assertEqual(len(set(selected + reserve)), 16)
        self.assertEqual(manifest["status"], "PREFROZEN_METADATA_ONLY_NOT_PROMOTION")
        self.assertFalse(manifest["contains_task_text"])
        self.assertEqual(manifest["feasibility_by_repo"], {"Textualize/rich": 2, "fastapi/fastapi": 2})
        self.assertTrue(manifest["selection_digest_sha256"])
        split = json.loads(
            (ROOT / "docs/evaluation/verifier-lora-split-v0.json").read_text()
        )
        excluded = {x["instance_id"] for x in split["excluded"] + split["holdout"]}
        for p in (
            "docs/evaluation/verifier-lora-train-subset-v0.json",
            "docs/evaluation/verifier-lora-blind-reservation-v0.json",
        ):
            excluded.update(
                x["instance_id"] for x in json.loads((ROOT / p).read_text())["tasks"]
            )
        excluded.update(
            x["instance_id"] for x in json.loads(
                (ROOT / "docs/evaluation/topology-ab-manifest-v1.json").read_text()
            )["holdout"]
        )
        self.assertFalse(set(selected + reserve) & excluded)

    def test_missing_provenance_is_a_hard_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            shutil.copytree(ROOT / "docs/evaluation", repo / "docs/evaluation")
            (repo / "docs/evaluation/verifier-lora-blind-reservation-v0.json").unlink()
            with self.assertRaises(FileNotFoundError):
                capacity.build_feasibility_manifest(repo)

    def test_no_task_data_or_reference_patch_in_model_pair(self):
        with tempfile.TemporaryDirectory() as tmp:
            capacity.prepare_model_pair(ROOT, Path(tmp))
            for output in ("e4b", "31b"):
                files = {
                    p.name for p in (Path(tmp) / output).rglob("*") if p.is_file()
                }
                self.assertNotIn("tasks.jsonl", files)
                self.assertNotIn("test_patch", files)


if __name__ == "__main__":
    unittest.main()
