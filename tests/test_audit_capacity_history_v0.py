"""Regressions for historical capacity-candidate exposure scanning."""
import importlib.util
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "capacity_history", ROOT / "scripts" / "audit_capacity_history_v0.py"
)
history = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(history)


def run(repo: Path, *args: str, env: dict | None = None) -> str:
    cp = subprocess.run(
        ["git", "-C", str(repo), *args],
        env=env, check=True, capture_output=True, text=True
    )
    return cp.stdout.strip()


class CapacityHistoricalExposureTests(unittest.TestCase):
    def make_repo(self, folder: Path) -> Path:
        repo = folder / "repo"
        repo.mkdir()
        run(repo, "init")
        run(repo, "config", "user.name", "Unit Test")
        run(repo, "config", "user.email", "unit@example.org")
        (repo / "docs" / "evaluation").mkdir(parents=True)
        (repo / "docs" / "research").mkdir(parents=True)
        return repo

    def commit(self, repo: Path, date: str, label: str) -> None:
        run(repo, "add", ".")
        env = dict(os.environ, GIT_AUTHOR_DATE=date, GIT_COMMITTER_DATE=date)
        run(repo, "commit", "-m", label, env=env)

    def test_historical_inspection_not_hidden_by_later_deletion(self):
        with tempfile.TemporaryDirectory() as d:
            repo = self.make_repo(Path(d))
            (repo / "docs" / "research" / "old.md").write_text(
                "Previously inspected rich_999999 and fastapi_999999.\n"
            )
            self.commit(repo, "2026-11-01T01:00:00+0000", "old")
            (repo / "docs" / "research" / "old.md").unlink()
            (repo / "docs" / "research" / "new.md").write_text("no id\n")
            self.commit(repo, "2026-11-02T01:00:00+0000", "delete")
            result = history.scan_history(repo, ["rich_999999", "fastapi_999999"])
            self.assertEqual(set(result["historical_exposed_ids"]), {
                "rich_999999", "fastapi_999999"
            })
            self.assertTrue(result["historical_mentions"])
            self.assertFalse(result["certifies_blind"])

    def test_frozen_metadata_only_not_a_manual_exposure(self):
        with tempfile.TemporaryDirectory() as d:
            repo = self.make_repo(Path(d))
            (repo / "docs" / "evaluation" / "verifier-lora-split-v0.json").write_text(
                '{"train":["rich_999999"]}\n'
            )
            self.commit(repo, "2026-11-01T01:00:00+0000", "metadata")
            result = history.scan_history(repo, ["rich_999999"])
            self.assertEqual(result["historical_exposed_ids"], [])
            self.assertGreater(result["checked_revisions"], 0)

    def test_after_cutoff_not_classified_as_historical(self):
        with tempfile.TemporaryDirectory() as d:
            repo = self.make_repo(Path(d))
            (repo / "docs" / "research" / "base.md").write_text("initial\n")
            self.commit(repo, "2026-11-01T01:00:00+0000", "base")
            (repo / "docs" / "research" / "new.md").write_text("rich_999999\n")
            self.commit(repo, "2026-11-04T06:30:00+0000", "late")
            result = history.scan_history(repo, ["rich_999999"])
            self.assertEqual(result["historical_exposed_ids"], [])

    def test_shallow_clone_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            repo = self.make_repo(Path(d))
            (repo / "docs" / "research" / "base.md").write_text("base\n")
            self.commit(repo, "2026-11-01T01:00:00+0000", "base")
            (repo / ".git" / "shallow").write_text(run(repo, "rev-parse", "HEAD") + "\n")
            with self.assertRaisesRegex(ValueError, "shallow"):
                history.scan_history(repo, ["rich_999999"])


if __name__ == "__main__":
    unittest.main()
