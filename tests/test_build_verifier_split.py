import copy
import json
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from scripts.build_verifier_split import (
    DEFAULT_EXCLUDED_IDS,
    DEFAULT_HOLDOUT_QUOTA,
    build_split,
    load_jsonl,
    replace_confounded_holdout,
)


DIAGNOSTIC_IDS = {
    "rich_3278",
    "rich_2725",
    "rich_3930",
    "httpx_3672",
    "fastapi_14361",
    "fastapi_14266",
    "fastapi_14609",
    "requests_6592",
    "requests_7502",
    "requests_6757",
}

ROUND1_CONFOUNDED_IDS = {
    "rich_3064",
    "rich_4070",
    "fastapi_14297",
    "fastapi_14583",
    "fastapi_14371",
    "fastapi_15030",
    "requests_6629",
    "requests_7505",
}


def patch_with_changed_lines(lines: int) -> str:
    if lines <= 0:
        return ""
    body = "\n".join(f"+line_{i}" for i in range(lines))
    return f"diff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py\n@@ -0,0 +1,{lines} @@\n{body}\n"


class VerifierSplitTests(unittest.TestCase):
    def test_split_is_independent_of_input_order(self):
        tasks = [
            {"instance_id": f"fastapi_{i}", "repo": "fastapi/fastapi", "patch": patch_with_changed_lines(i + 1)}
            for i in range(8)
        ] + [
            {"instance_id": f"rich_{i}", "repo": "Textualize/rich", "patch": patch_with_changed_lines((i + 1) * 12)}
            for i in range(6)
        ]
        quota = {"fastapi/fastapi": 3, "Textualize/rich": 2}

        forward = build_split(tasks, quota, set())
        reverse = build_split(list(reversed(tasks)), quota, set())

        self.assertEqual(forward, reverse)

    def test_excluded_and_httpx_never_enter_train_or_holdout(self):
        tasks = [
            {"instance_id": "seen", "repo": "fastapi/fastapi", "patch": patch_with_changed_lines(2)},
            {"instance_id": "fastapi_a", "repo": "fastapi/fastapi", "patch": patch_with_changed_lines(5)},
            {"instance_id": "fastapi_b", "repo": "fastapi/fastapi", "patch": patch_with_changed_lines(40)},
            {"instance_id": "httpx_1", "repo": "encode/httpx", "patch": patch_with_changed_lines(2)},
        ]

        split = build_split(tasks, {"fastapi/fastapi": 1}, {"seen"})
        train_ids = {item["instance_id"] for item in split["train"]}
        holdout_ids = {item["instance_id"] for item in split["holdout"]}
        excluded_ids = {item["instance_id"] for item in split["excluded"]}

        self.assertNotIn("seen", train_ids | holdout_ids)
        self.assertNotIn("httpx_1", train_ids | holdout_ids)
        self.assertEqual(excluded_ids, {"seen", "httpx_1"})

    def test_holdout_spreads_across_patch_size_buckets(self):
        tasks = [
            {"instance_id": "r_small", "repo": "Textualize/rich", "patch": patch_with_changed_lines(2)},
            {"instance_id": "r_medium", "repo": "Textualize/rich", "patch": patch_with_changed_lines(20)},
            {"instance_id": "r_large", "repo": "Textualize/rich", "patch": patch_with_changed_lines(50)},
            {"instance_id": "r_xlarge", "repo": "Textualize/rich", "patch": patch_with_changed_lines(100)},
            {"instance_id": "r_small2", "repo": "Textualize/rich", "patch": patch_with_changed_lines(3)},
        ]

        split = build_split(tasks, {"Textualize/rich": 4}, set())
        buckets = {item["patch_bucket"] for item in split["holdout"]}

        self.assertEqual(buckets, {"1-10", "11-30", "31-80", "81+"})

    def test_replacement_preserves_repo_bucket_and_never_reenters_training(self):
        split = {
            "version": "verifier-lora-v0",
            "selection": {"method": "bucket-round-robin-sha256"},
            "holdout": [
                {"instance_id": "keep", "repo": "repo/a", "patch_bucket": "1-10"},
                {"instance_id": "bad", "repo": "repo/a", "patch_bucket": "11-30"},
            ],
            "train": [
                {"instance_id": "candidate_z", "repo": "repo/a", "patch_bucket": "11-30"},
                {"instance_id": "candidate_a", "repo": "repo/a", "patch_bucket": "11-30"},
                {"instance_id": "wrong_bucket", "repo": "repo/a", "patch_bucket": "31-80"},
                {"instance_id": "wrong_repo", "repo": "repo/b", "patch_bucket": "11-30"},
            ],
            "excluded": [],
            "counts": {"total_input": 6, "train": 4, "holdout": 2, "excluded": 0, "holdout_by_repo": {"repo/a": 2}},
        }

        replaced = replace_confounded_holdout(split, {"bad"})
        reversed_train = copy.deepcopy(split)
        reversed_train["train"].reverse()
        replaced_reversed = replace_confounded_holdout(reversed_train, {"bad"})

        self.assertEqual(replaced, replaced_reversed)
        holdout = {item["instance_id"]: item for item in replaced["holdout"]}
        self.assertIn("keep", holdout)
        self.assertNotIn("bad", holdout)
        replacement_ids = set(holdout) - {"keep"}
        self.assertEqual(len(replacement_ids), 1)
        replacement = holdout[replacement_ids.pop()]
        self.assertEqual((replacement["repo"], replacement["patch_bucket"]), ("repo/a", "11-30"))

        train_ids = {item["instance_id"] for item in replaced["train"]}
        excluded = {item["instance_id"]: item for item in replaced["excluded"]}
        self.assertNotIn("bad", train_ids)
        self.assertEqual(excluded["bad"]["reason"], "gold_control_confounded")
        self.assertEqual(replaced["counts"]["holdout"], 2)
        self.assertEqual(replaced["counts"]["train"], 3)
        self.assertEqual(replaced["counts"]["excluded"], 1)

    def test_replacement_fails_loudly_without_same_repo_bucket_candidate(self):
        split = {
            "version": "verifier-lora-v0",
            "selection": {},
            "holdout": [{"instance_id": "bad", "repo": "repo/a", "patch_bucket": "81+"}],
            "train": [{"instance_id": "other", "repo": "repo/a", "patch_bucket": "1-10"}],
            "excluded": [],
            "counts": {"total_input": 2, "train": 1, "holdout": 1, "excluded": 0, "holdout_by_repo": {"repo/a": 1}},
        }

        with self.assertRaisesRegex(ValueError, "same repo/bucket"):
            replace_confounded_holdout(split, {"bad"})

    def test_round1_real_replacement_contract(self):
        split = json.loads(Path("docs/evaluation/verifier-lora-split-v0.json").read_text(encoding="utf-8"))
        before_slots = Counter((item["repo"], item["patch_bucket"]) for item in split["holdout"])

        replaced = replace_confounded_holdout(split, ROUND1_CONFOUNDED_IDS)

        holdout_ids = {item["instance_id"] for item in replaced["holdout"]}
        train_ids = {item["instance_id"] for item in replaced["train"]}
        excluded_ids = {item["instance_id"] for item in replaced["excluded"]}
        after_slots = Counter((item["repo"], item["patch_bucket"]) for item in replaced["holdout"])
        self.assertEqual(len(holdout_ids), 12)
        self.assertTrue(ROUND1_CONFOUNDED_IDS.isdisjoint(holdout_ids | train_ids))
        self.assertTrue(ROUND1_CONFOUNDED_IDS.issubset(excluded_ids))
        self.assertEqual(before_slots, after_slots)
        self.assertEqual(replaced["counts"]["train"], 99)
        self.assertEqual(replaced["counts"]["holdout"], 12)
        self.assertEqual(replaced["counts"]["excluded"], 18)

    def test_real_corpus_contract(self):
        tasks = load_jsonl(Path("tasks.jsonl"))
        split = build_split(tasks, DEFAULT_HOLDOUT_QUOTA, DEFAULT_EXCLUDED_IDS)

        holdout_ids = {item["instance_id"] for item in split["holdout"]}
        train_ids = {item["instance_id"] for item in split["train"]}
        self.assertEqual(len(split["holdout"]), 12)
        self.assertTrue(DIAGNOSTIC_IDS.isdisjoint(holdout_ids))
        self.assertNotIn("httpx_3672", train_ids | holdout_ids)
        self.assertEqual(split["counts"]["holdout_by_repo"], DEFAULT_HOLDOUT_QUOTA)
        self.assertEqual(split["version"], "verifier-lora-v0")

        # The manifest must remain JSON serializable for durable repo storage.
        json.dumps(split, sort_keys=True)

    def test_cli_runs_from_repo_root_and_writes_manifest(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "split.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    "scripts/build_verifier_split.py",
                    "tasks.jsonl",
                    "--output",
                    str(output),
                ],
                cwd=Path(__file__).resolve().parents[1],
                text=True,
                capture_output=True,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["version"], "verifier-lora-v0")
            self.assertEqual(payload["counts"]["holdout"], 12)


if __name__ == "__main__":
    unittest.main()
