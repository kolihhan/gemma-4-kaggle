"""Verify that the V4 submission uses the exact Notebook version Kaggle created.

No network, competition submission, GPU, or real archive involved.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch

from scripts import submit_solver_v4_cgr_once as target


class KernelVersionContractTests(unittest.TestCase):
    def test_valid_server_version_and_fail_closed_errors(self):
        valid = types.SimpleNamespace(ref=target.KERNEL, version_number=7)
        self.assertEqual(target.verified_kernel_version(valid), 7)
        official_cli_response = types.SimpleNamespace(
            url="https://www.kaggle.com/code/" + target.KERNEL,
            versionNumber=7,
            error="",
        )
        self.assertEqual(target.verified_kernel_version(official_cli_response), 7)
        both = types.SimpleNamespace(
            ref=target.KERNEL,
            version_number=7,
            versionNumber=7,
        )
        self.assertEqual(target.verified_kernel_version(both), 7)
        for bad in (
            types.SimpleNamespace(ref=target.KERNEL, version_number=0),
            types.SimpleNamespace(ref=target.KERNEL, version_number=None),
            types.SimpleNamespace(ref=target.KERNEL, version_number=True),
            types.SimpleNamespace(ref=target.KERNEL, version_number=7,
                                  versionNumber=8),
            types.SimpleNamespace(ref=target.KERNEL, versionNumber="7"),
            object(),
        ):
            with self.subTest(bad=repr(bad)):
                with self.assertRaisesRegex(RuntimeError, "VERSION_UNCONFIRMED"):
                    target.verified_kernel_version(bad)
        for bad in (
            types.SimpleNamespace(ref="somebody/other", versionNumber=7),
            types.SimpleNamespace(
                url="https://www.kaggle.com/code/somebody/other",
                versionNumber=7,
            ),
            types.SimpleNamespace(
                url="https://www.kaggle.com.evil.invalid/code/" + target.KERNEL,
                versionNumber=7,
            ),
            types.SimpleNamespace(versionNumber=7),
        ):
            with self.subTest(bad=repr(bad)):
                with self.assertRaisesRegex(RuntimeError, "IDENTITY_UNCONFIRMED"):
                    target.verified_kernel_version(bad)
        error = types.SimpleNamespace(ref=target.KERNEL, versionNumber=7,
                                      error="insufficient notebook quota")
        with self.assertRaisesRegex(RuntimeError, "VERSION_UNCONFIRMED"):
            target.verified_kernel_version(error)

    def test_exact_pushed_version_used_for_status_output_and_submit(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            archive = b"deterministic unit-test-only bytes"
            (root / "submission.zip").write_bytes(archive)
            digest = hashlib.sha256(archive).hexdigest()
            (root / "candidate.sha256").write_text(digest)
            (root / "kernel").mkdir()

            api = Mock()
            api.kernels_push.return_value = types.SimpleNamespace(
                url="https://www.kaggle.com/code/" + target.KERNEL,
                versionNumber=7, error="",
            )
            api.competition_submit_code.return_value = {"ok": True}
            extended = types.ModuleType("kaggle.api.kaggle_api_extended")
            extended.KaggleApi = lambda: api
            fake_modules = {
                "kaggle": types.ModuleType("kaggle"),
                "kaggle.api": types.ModuleType("kaggle.api"),
                "kaggle.api.kaggle_api_extended": extended,
            }
            download_refs = []

            def download_output(argv, **kwargs):
                self.assertEqual(argv[:3], ["kaggle", "kernels", "output"])
                download_refs.append(argv[3])
                destination = Path(argv[argv.index("-p") + 1])
                (destination / "submission.zip").write_bytes(archive)
                return subprocess.CompletedProcess(argv, 0)

            receipt = {
                "description": target.MARKER,
                "ref": "test-code-submission-receipt",
                "status": "SubmissionStatus.PENDING",
            }

            with (
                patch.dict(sys.modules, fake_modules),
                patch.object(target, "ROOT", root),
                patch.object(target, "EXPECTED_SHA", digest),
                patch.object(target, "check_slot", side_effect=[True, True]) as gate,
                patch.object(target, "authenticated_submissions", return_value=[receipt]),
                patch.object(target, "cmd", return_value="KernelWorkerStatus.COMPLETE") as cli,
                patch.object(target.subprocess, "run", side_effect=download_output),
            ):
                target.submit()

            self.assertEqual(gate.call_count, 2)
            api.authenticate.assert_called_once()
            api.kernels_push.assert_called_once_with(str(root / "kernel"))
            self.assertEqual(download_refs, [target.KERNEL + "/7"])
            self.assertEqual(cli.call_args.args[0][:4], [
                "kaggle", "kernels", "status", target.KERNEL + "/7"
            ])
            self.assertEqual(
                api.competition_submit_code.call_args.kwargs["kernel_version"], 7
            )

    def test_push_without_confirmed_version_never_calls_submission(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            archive = b"unit-test bytes"
            digest = hashlib.sha256(archive).hexdigest()
            (root / "submission.zip").write_bytes(archive)
            (root / "candidate.sha256").write_text(digest)
            (root / "kernel").mkdir()
            api = Mock()
            api.kernels_push.return_value = types.SimpleNamespace(
                ref=target.KERNEL, version_number=None,
            )
            extended = types.ModuleType("kaggle.api.kaggle_api_extended")
            extended.KaggleApi = lambda: api
            with (
                patch.dict(sys.modules, {
                    "kaggle": types.ModuleType("kaggle"),
                    "kaggle.api": types.ModuleType("kaggle.api"),
                    "kaggle.api.kaggle_api_extended": extended,
                }),
                patch.object(target, "ROOT", root),
                patch.object(target, "EXPECTED_SHA", digest),
                patch.object(target, "check_slot", return_value=True),
            ):
                with self.assertRaisesRegex(RuntimeError, "VERSION_UNCONFIRMED"):
                    target.submit()
            api.competition_submit_code.assert_not_called()


if __name__ == "__main__":
    unittest.main()
