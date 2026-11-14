"""Pure tests for private F2P source serializer; no real source text."""
import tempfile
from pathlib import Path
from unittest import TestCase,main
from unittest.mock import patch
from scripts.build_private_f2p_patch_sft import (
    forbidden_content, assemble, write_private, TRAIN_COUNT, VALIDATION_COUNT,
)

class PrivateSourceSerializerTests(TestCase):
    def test_rejects_non_patch_and_huge_examples(self):
        self.assertIsNotNone(forbidden_content("test","I made the fix"))
        self.assertIsNotNone(forbidden_content("bug","diff --git a/a b/a\n"))
        self.assertIsNotNone(forbidden_content("x"*46000,"valid"))
        self.assertIsNone(forbidden_content("Small issue",
             "diff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py\n"
             "@@ -1 +1 @@\n-0\n+1\n"))

    def test_repo_split_and_no_gold_no_tool_trajectory_serialization(self):
        # 19 mutually different source repos gives the known deterministic
        # expected 16/3 split, without relying on task names from public HF.
        rows=[]
        scale={}
        for i in range(19):
            task=f"synthetic_task_{i}"
            row={"instance_id":task,"source":{"repo":f"owner/repo{i}","license":"MIT"},
                 "cohort":"original","index":i,
                 "model_patch":("diff --git a/a.py b/a.py\n"
                                "--- a/a.py\n+++ b/a.py\n"
                                "@@ -1 +1 @@\n-return 0\n+return 1\n")}
            rows.append(row)
            scale[task]={"user":"owner","repo":f"repo{i}",
                         "problem_statement":"Fix the bug in simple function"}
        with patch("scripts.build_private_f2p_patch_sft.selected_sources",return_value=rows),\
             patch("scripts.build_private_f2p_patch_sft.get_scale_match",return_value=scale):
            with tempfile.TemporaryDirectory() as temp:
                metadata=write_private(Path(temp))
                self.assertEqual(metadata["train_rows"],TRAIN_COUNT)
                self.assertEqual(metadata["holdout_rows"],VALIDATION_COUNT)
                import json
                train=[json.loads(x) for x in (Path(temp)/"train.jsonl").read_text().splitlines()]
                held=[json.loads(x) for x in (Path(temp)/"holdout.jsonl").read_text().splitlines()]
                self.assertFalse({x["repo_hash"] for x in train} & {x["repo_hash"] for x in held})
                for row in train+held:
                    self.assertEqual(set(row),{
                        "id_hash","repo_hash","source_cohort","source_case_index",
                        "prompt","completion","supervision_kind",
                        "source_F2P_proven_pass","gold_patch_present","tool_trace_present"})
                    self.assertNotIn("reference_patch",row)
                    self.assertFalse(row["gold_patch_present"])
                    self.assertFalse(row["tool_trace_present"])
                with self.assertRaises(FileExistsError):
                    write_private(Path(temp))

if __name__=="__main__":
    main()
