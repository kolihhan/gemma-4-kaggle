"""Deterministic no-inference control for source-first Gemma 31B candidate."""
import hashlib
import io
import unittest
from unittest.mock import patch
import zipfile

from scripts import build_source_first_localization_v1 as candidate
from scripts import build_v2_toolcap_submission as parent
from scripts.build_toolcap60_timeout_recovery import files_for_candidate as scored

V2={
    "agent.yaml": """agent_class: LlmAgent
name: swe_coder
model: gemma-4-31b-it-qat-w4a16-ct
instruction: !include prompts/system.md
tools:
  - run_command
  - read_file
  - edit_file
  - write_file
  - get_status
  - submit_patch
  - get_code_neighbors
  - search_similar_code
  - get_code_subgraph
generate_content_config: !include configs/sampling.yaml
""",
    "prompts/system.md": "Frozen base policy; use graph tools selectively",
    "configs/sampling.yaml": "temperature: 0.2\nthinking_budget: 4096\n",
    "eval_config.yaml": "evaluation:\n  max_time_minutes: 8\n  max_tool_calls: 28\n  max_turns: 80\n",
}


class SourceFirstPackage(unittest.TestCase):
    def setUp(self):
        patched=patch.object(parent,"validate_source_zip",return_value=dict(V2))
        patched.start()
        self.addCleanup(patched.stop)

    def test_only_one_mutated_member(self):
        orig=scored(b"pinned")
        new=candidate.files_for_candidate(b"pinned")
        self.assertEqual(set(orig),set(new))
        self.assertEqual({k for k in orig if orig[k]!=new[k]},{"prompts/system.md"})
        self.assertTrue(new["prompts/system.md"].startswith(orig["prompts/system.md"]))
        self.assertEqual(new["agent.yaml"],orig["agent.yaml"])
        self.assertEqual(new["configs/sampling.yaml"],orig["configs/sampling.yaml"])
        self.assertEqual(new["eval_config.yaml"],orig["eval_config.yaml"])

    def test_exact_model_and_task_budget(self):
        files=candidate.files_for_candidate(b"pinned")
        self.assertEqual(files["agent.yaml"].count("model: gemma-4-31b-it-qat-w4a16-ct"),1)
        for term in ("max_time_minutes: 5","max_tool_calls: 60","max_turns: 80"):
            self.assertIn(term,files["eval_config.yaml"])

    def test_source_first_and_graph_fallback_are_bounded(self):
        instructions=candidate.files_for_candidate(b"pinned")["prompts/system.md"]
        for word in ("The FIRST objective","exclude tests","at most ONE broader",
                     "async functions","Do NOT call a graph tool","submit_patch",
                     "STOP","--glob '!**/tests/**'"):
            self.assertIn(word,instructions)
        self.assertNotIn("Conditional one-hop implementation localization",instructions)

    def test_deterministic_integrity(self):
        a=candidate.build(b"pinned")
        b=candidate.build(b"pinned")
        self.assertEqual(hashlib.sha256(a).hexdigest(),hashlib.sha256(b).hexdigest())
        with zipfile.ZipFile(io.BytesIO(a)) as z:
            self.assertIsNone(z.testzip())
            self.assertEqual(set(z.namelist()),set(V2))
            self.assertIn(b"Source-first, no test-file distraction",z.read("prompts/system.md"))

    def test_fail_closed_model_and_tool_drift(self):
        changes=(
            ("model: gemma-4-31b-it-qat-w4a16-ct","model: gemma-4-12b-it","agent.yaml"),
            ("  - run_command\n","","agent.yaml"),
            ("max_time_minutes: 8","max_time_minutes: 7","eval_config.yaml"),
        )
        for before,after,key in changes:
            drift=dict(V2)
            drift[key]=drift[key].replace(before,after)
            with self.subTest(key=key),patch.object(parent,"validate_source_zip",return_value=drift):
                with self.assertRaises(ValueError):
                    candidate.files_for_candidate(b"pinned")


if __name__=="__main__":
    unittest.main()
