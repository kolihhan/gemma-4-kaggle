"""CPU-only tests for the non-executing public Notebook research auditor."""
import json
import tempfile
import unittest
from pathlib import Path

from scripts.audit_evgen_notebook_20261123 import analyze, read_notebook


class NotebookAuditTests(unittest.TestCase):
    def test_section_boundary_and_keyword_counts(self):
        cells = [
            ("markdown", "# Introduction\nOld experiments.\n"),
            ("markdown", "## 11. What I Want to Investigate Next\n150 lines per read_file; second attempt 0/10.\n"),
            ("code", "print('code is not executed')\n"),
            ("markdown", "## 12. Conclusion\nA separate budget discussion."),
        ]
        report = analyze(cells, "fake.ipynb")
        self.assertTrue(report["section11_found"])
        self.assertEqual(report["section11_topic_hits"]["150_line_limit"], 1)
        self.assertEqual(report["section11_topic_hits"]["zero_of_ten"], 1)
        self.assertEqual(report["section11_topic_hits"]["read_file"], 1)
        self.assertEqual(report["section11_topic_hits"]["budget"], 0)
        self.assertFalse(report["is_notebook_v41_proven"])
        self.assertTrue(report["no_notebook_execution"])

    def test_downloaded_notebook_source_is_read_without_execution(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d, "public.ipynb")
            path.write_text(json.dumps({
                "cells": [{"cell_type": "markdown", "source": ["## 11. What I Want to Investigate Next\n", "Try verification."]},
                          {"cell_type": "code", "source": "raise RuntimeError('must never execute')"}],
            }))
            cells, name = read_notebook(Path(d))
            self.assertEqual(name, "public.ipynb")
            self.assertEqual(len(cells), 2)
            self.assertTrue(analyze(cells, name)["section11_found"])

    def test_fail_closed_on_multiple_notebooks(self):
        with tempfile.TemporaryDirectory() as d:
            for name in ("a.ipynb", "b.ipynb"):
                Path(d, name).write_text('{"cells": []}')
            with self.assertRaisesRegex(ValueError, "ambiguous"):
                read_notebook(Path(d))


if __name__ == "__main__":
    unittest.main()
