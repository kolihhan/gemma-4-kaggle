import unittest

from scripts.analyze_tasks import choose_sample, diff_stats, summarize_tasks


class DiffStatsTests(unittest.TestCase):
    def test_counts_files_and_changed_lines(self):
        patch = """diff --git a/a.py b/a.py
--- a/a.py
+++ b/a.py
@@ -1,2 +1,3 @@
-old
+new
+extra
 keep
diff --git a/b.py b/b.py
--- a/b.py
+++ b/b.py
@@ -1 +1 @@
-x
+y
"""
        self.assertEqual(
            diff_stats(patch),
            {"files": 2, "additions": 3, "deletions": 2, "lines": 5},
        )


class SummaryTests(unittest.TestCase):
    def setUp(self):
        self.tasks = [
            {
                "instance_id": "fastapi_1",
                "repo": "fastapi/fastapi",
                "hints_text": "hint",
                "problem_statement": "short issue",
                "patch": "diff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py\n@@ -1 +1 @@\n-x\n+y\n",
                "test_patch": "",
                "created_at": "2026-01-01T00:00:00Z",
            },
            {
                "instance_id": "fastapi_2",
                "repo": "fastapi/fastapi",
                "hints_text": "",
                "problem_statement": "a somewhat longer issue",
                "patch": "diff --git a/b.py b/b.py\n--- a/b.py\n+++ b/b.py\n@@ -1 +1,3 @@\n-x\n+y\n+z\n+w\n",
                "test_patch": "",
                "created_at": "2026-02-01T00:00:00Z",
            },
            {
                "instance_id": "httpx_1",
                "repo": "encode/httpx",
                "hints_text": None,
                "problem_statement": "issue",
                "patch": "",
                "test_patch": "",
                "created_at": "2026-03-01T00:00:00Z",
            },
        ]

    def test_summary_has_counts_and_patch_buckets(self):
        summary = summarize_tasks(self.tasks)
        self.assertEqual(summary["task_count"], 3)
        self.assertEqual(summary["repos"], {"fastapi/fastapi": 2, "encode/httpx": 1})
        self.assertEqual(summary["tasks_with_hints"], 1)
        self.assertEqual(summary["solution_patch_lines"]["0"], 1)
        self.assertEqual(summary["solution_patch_lines"]["1-10"], 2)
        self.assertEqual(summary["created_at"]["min"], "2026-01-01T00:00:00Z")
        self.assertEqual(summary["created_at"]["max"], "2026-03-01T00:00:00Z")

    def test_sample_is_deterministic_and_keeps_repo_coverage(self):
        sample = choose_sample(self.tasks, per_repo=2)
        self.assertEqual([item["instance_id"] for item in sample], ["httpx_1", "fastapi_1", "fastapi_2"])


if __name__ == "__main__":
    unittest.main()
