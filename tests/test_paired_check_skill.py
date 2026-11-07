"""Exercise the agent-selected check through the source snapshot runner."""

import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "experiments/paired-check-v0/skill/scripts/compare.py"


class PairedCheckTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.repo = Path(self.temporary.name) / "repo"
        self.repo.mkdir()
        self.git("init", "-q")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "user.name", "Fixture")
        (self.repo / "samplepkg.py").write_text("value = 'before'\n")
        self.git("add", ".")
        self.git("commit", "-qm", "fixture base")
        self.git("tag", "_swegemma_baseline")
        spec = importlib.util.spec_from_file_location("paired_check", SCRIPT)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def git(self, *arguments):
        return subprocess.check_output(
            ["git", "-C", str(self.repo), *arguments], text=True
        )

    def invoke(self, code="import samplepkg; print(samplepkg.value)", mode="paired"):
        return self.module.compare(code, self.repo, timeout=2, mode=mode)

    def test_printed_behavior_can_change_with_identical_exit_codes(self):
        (self.repo / "samplepkg.py").write_text("value = 'after'\n")
        before = self.git("diff", "--binary", "_swegemma_baseline")
        result = self.invoke()
        self.assertEqual(result["status"], "compared")
        self.assertEqual([r["return_code"] for r in result["runs"]], [0, 0])
        self.assertEqual([r["stdout"].strip() for r in result["runs"]], ["before", "after"])
        self.assertEqual(self.git("diff", "--binary", "_swegemma_baseline"), before)

    def test_repeat_control_runs_the_same_edited_source_twice(self):
        (self.repo / "samplepkg.py").write_text("value = 'after'\n")
        result = self.invoke(mode="repeat")
        self.assertEqual([r["label"] for r in result["runs"]], ["current_1", "current_2"])
        self.assertEqual([r["stdout"].strip() for r in result["runs"]], ["after", "after"])

    def test_baseline_tag_survives_an_agent_commit(self):
        (self.repo / "samplepkg.py").write_text("value = 'committed edit'\n")
        self.git("add", ".")
        self.git("commit", "-qm", "agent edit")
        self.assertEqual(self.invoke()["runs"][0]["stdout"].strip(), "before")

    def test_staged_edits_are_visible(self):
        (self.repo / "samplepkg.py").write_text("value = 'staged'\n")
        self.git("add", ".")
        self.assertEqual(self.invoke()["runs"][1]["stdout"].strip(), "staged")

    def test_untracked_source_is_only_in_the_current_snapshot(self):
        (self.repo / "extra.py").write_text("value = 42\n")
        result = self.invoke("import samplepkg, extra; print(extra.value)")
        self.assertNotEqual(result["runs"][0]["return_code"], 0)
        self.assertEqual(result["runs"][1]["stdout"].strip(), "42")
        self.assertEqual((self.repo / "extra.py").read_text(), "value = 42\n")

    def test_deleted_source_is_absent_in_the_current_snapshot(self):
        (self.repo / "samplepkg.py").unlink()
        result = self.invoke()
        self.assertEqual(result["runs"][0]["stdout"].strip(), "before")
        self.assertNotEqual(result["runs"][1]["return_code"], 0)
        self.assertFalse((self.repo / "samplepkg.py").exists())

    def test_probe_mutation_stays_in_the_disposable_snapshot(self):
        result = self.invoke(
            "import samplepkg; from pathlib import Path; "
            "Path('samplepkg.py').write_text('corrupted = True'); print(samplepkg.value)"
        )
        self.assertEqual(result["status"], "compared")
        self.assertEqual((self.repo / "samplepkg.py").read_text(), "value = 'before'\n")

    def test_missing_baseline_fails_without_running_code(self):
        self.git("tag", "-d", "_swegemma_baseline")
        result = self.invoke("raise RuntimeError('must not run')")
        self.assertEqual(result["status"], "skipped")
        self.assertEqual(result["reason"], "baseline_tag_unavailable")

    def test_import_from_the_parent_checkout_is_rejected(self):
        result = self.invoke(
            "import sys; sys.path.insert(0, " + repr(str(self.repo))
            + "); import samplepkg; print(samplepkg.value)"
        )
        self.assertEqual(result["status"], "inconclusive")
        self.assertTrue(any(r["origin_conflicts"] for r in result["runs"]))

    def test_source_free_output_does_not_claim_repository_verification(self):
        result = self.invoke("print('looks fine')")
        self.assertEqual(result["status"], "inconclusive")
        self.assertTrue(all(not r["source_imports"] for r in result["runs"]))

    def test_assertion_failure_is_returned_as_an_observation(self):
        (self.repo / "samplepkg.py").write_text("value = 'after'\n")
        result = self.invoke("import samplepkg; assert samplepkg.value == 'after'")
        self.assertEqual(result["status"], "compared")
        self.assertEqual([r["return_code"] for r in result["runs"]], [1, 0])

    def test_cli_returns_one_json_object(self):
        result = subprocess.run(
            [self.module.sys.executable, str(SCRIPT), "--workspace", str(self.repo),
             "--code", "import samplepkg; print(samplepkg.value)"],
            capture_output=True, text=True, check=True,
        )
        self.assertEqual(json.loads(result.stdout)["status"], "compared")

    def test_hanging_check_times_out_without_claiming_a_comparison(self):
        result = self.module.compare(
            "import samplepkg, time; time.sleep(30)", self.repo, timeout=0.1,
        )
        self.assertEqual(result["status"], "inconclusive")
        self.assertTrue(all(r["timed_out"] for r in result["runs"]))
        self.assertTrue(result["workspace_unchanged"])

    def test_src_layout_uses_the_snapshot_and_preserves_build_metadata(self):
        package = self.repo / "src/sourcepkg"
        package.mkdir(parents=True)
        (package / "__init__.py").write_text("from ._version import value\n")
        (self.repo / ".gitignore").write_text("_version.py\n")
        self.git("add", ".")
        self.git("commit", "-qm", "src package fixture")
        self.git("tag", "-f", "_swegemma_baseline")
        (package / "_version.py").write_text("value = 'generated'\n")
        result = self.invoke("import sourcepkg; print(sourcepkg.value)")
        self.assertEqual(result["status"], "compared")
        self.assertEqual([r["stdout"].strip() for r in result["runs"]], ["generated", "generated"])


if __name__ == "__main__":
    unittest.main()
