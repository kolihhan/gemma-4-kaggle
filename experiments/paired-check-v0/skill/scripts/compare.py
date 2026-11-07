"""Run an agent-selected Python check in disposable repository snapshots."""

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tarfile
import tempfile
import time


COMPARISON_MODE = "paired"
BASELINE_TAG = "refs/tags/_swegemma_baseline"
MAX_SNAPSHOT_BYTES = 64 * 1024 * 1024


def git(workspace, *arguments):
    return subprocess.check_output(
        ["git", "-C", str(workspace), *arguments], stderr=subprocess.PIPE, timeout=6
    )


def files(workspace):
    paths = git(workspace, "ls-files", "--cached", "--others", "--exclude-standard", "-z")
    return sorted(set(Path(os.fsdecode(p)) for p in paths.split(b"\0") if p))


def fingerprint(workspace, paths):
    digest = hashlib.sha256()
    total = 0
    for relative in paths:
        path = workspace / relative
        digest.update(os.fsencode(relative) + b"\0")
        if path.is_symlink():
            digest.update(os.fsencode(os.readlink(path)))
        elif path.is_file():
            total += path.stat().st_size
            if total > MAX_SNAPSHOT_BYTES:
                raise ValueError("snapshot_size_limit")
            digest.update(path.read_bytes())
        elif not path.exists():
            digest.update(b"deleted")
        else:
            raise ValueError("unsupported_repository_entry")
    return digest.hexdigest()


def copy_current(workspace, destination, paths):
    for relative in paths:
        source = workspace / relative
        target = destination / relative
        if source.is_symlink():
            link = os.readlink(source)
            if Path(link).is_absolute() or not source.resolve().is_relative_to(workspace):
                raise ValueError("external_source_symlink")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.symlink_to(link)
        elif source.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)


def copy_build_metadata(workspace, destinations):
    ignored = git(workspace, "ls-files", "--others", "--ignored", "--exclude-standard", "-z")
    for raw in ignored.split(b"\0"):
        if not raw:
            continue
        relative = Path(os.fsdecode(raw))
        metadata = relative.name == "_version.py" or any(
            p.endswith((".egg-info", ".dist-info")) for p in relative.parts
        )
        source = workspace / relative
        if not metadata or source.is_symlink() or not source.is_file():
            continue
        if any(p in {".venv", "venv", ".tox", "__pycache__"} for p in relative.parts):
            continue
        if source.stat().st_size > 100_000:
            continue
        for destination in destinations:
            target = destination / relative
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)


def clip(text, limit=600):
    if len(text) <= limit:
        return text
    half = limit // 2
    return text[:half] + "\n[output shortened]\n" + text[-half:]


def worker(code_path, report_path, workspace):
    current = Path.cwd().resolve()
    original = Path(workspace).resolve()
    external = []
    for path in sys.path:
        resolved = Path(path or ".").resolve()
        if not resolved.is_relative_to(original):
            external.append(path)
    sys.path[:] = [str(current / "src"), str(current), *external]
    try:
        code = Path(code_path).read_text()
        exec(compile(code, "<agent-selected-check>", "exec"), {"__name__": "__main__"})
    finally:
        imports, conflicts = [], []
        for name, module in list(sys.modules.items()):
            filename = getattr(module, "__file__", None)
            if not filename:
                continue
            resolved = Path(filename).resolve()
            if resolved.is_relative_to(original):
                conflicts.append(name)
            elif resolved.is_relative_to(current):
                imports.append(name)
        Path(report_path).write_text(json.dumps({
            "source_imports": sorted(imports)[:4],
            "origin_conflicts": sorted(conflicts)[:4],
        }))


def run_check(code_path, snapshot, workspace, timeout, label, temporary):
    report = temporary / (label + ".json")
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONHASHSEED="0")
    environment["PYTHONPATH"] = os.pathsep.join((str(snapshot / "src"), str(snapshot)))
    arguments = [sys.executable, str(Path(__file__).resolve()), "--worker",
                 str(code_path), str(report), str(workspace)]
    start = time.monotonic()
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        process = subprocess.Popen(
            arguments, cwd=snapshot, env=environment,
            stdout=stdout, stderr=stderr, start_new_session=True,
        )
        timed_out = False
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
        finally:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
        stdout.seek(0)
        stderr.seek(0)
        out = stdout.read(64_000).decode(errors="replace")
        err = stderr.read(64_000).decode(errors="replace")
    provenance = json.loads(report.read_text()) if report.exists() else {
        "source_imports": [], "origin_conflicts": [],
    }
    return {
        "label": label, "return_code": process.returncode,
        "stdout": clip(out), "stderr": clip(err), "timed_out": timed_out,
        "elapsed_seconds": round(time.monotonic() - start, 3), **provenance,
    }


def compare(code, workspace, timeout=10, mode=COMPARISON_MODE):
    workspace = Path(workspace).resolve()
    if mode not in {"paired", "repeat"} or not 0 < timeout <= 20:
        return {"status": "skipped", "reason": "invalid_options"}
    if not code.strip() or len(code) > 12_000:
        return {"status": "skipped", "reason": "invalid_check_size"}
    try:
        baseline = git(workspace, "rev-parse", BASELINE_TAG + "^{commit}").decode().strip()
    except (subprocess.SubprocessError, OSError):
        return {"status": "skipped", "reason": "baseline_tag_unavailable"}
    try:
        paths = files(workspace)
        before = fingerprint(workspace, paths)
        with tempfile.TemporaryDirectory(prefix="paired-check-") as directory:
            temporary = Path(directory)
            base, current = temporary / "base", temporary / "current"
            base.mkdir()
            current.mkdir()
            archive = git(workspace, "archive", baseline)
            if len(archive) > MAX_SNAPSHOT_BYTES:
                raise ValueError("snapshot_size_limit")
            with tarfile.open(fileobj=io.BytesIO(archive)) as tree:
                tree.extractall(base, filter="data")
            copy_current(workspace, current, paths)
            copy_build_metadata(workspace, (base, current))
            if files(workspace) != paths or fingerprint(workspace, paths) != before:
                raise ValueError("workspace_changed_while_copying")
            code_path = temporary / "agent_check.txt"
            code_path.write_text(code)
            first = base
            labels = ("baseline", "current")
            if mode == "repeat":
                first = temporary / "current_repeat"
                shutil.copytree(current, first, symlinks=True)
                labels = ("current_1", "current_2")
            runs = [
                run_check(code_path, first, workspace, timeout, labels[0], temporary),
                run_check(code_path, current, workspace, timeout, labels[1], temporary),
            ]
            unchanged = files(workspace) == paths and fingerprint(workspace, paths) == before
            verified = unchanged and all(
                r["source_imports"] and not r["origin_conflicts"] and not r["timed_out"]
                for r in runs
            )
            return {
                "status": "compared" if verified else "inconclusive",
                "baseline_commit": baseline, "workspace_unchanged": unchanged,
                "runs": runs,
            }
    except (OSError, ValueError, tarfile.TarError, subprocess.SubprocessError) as error:
        return {"status": "skipped", "reason": str(error)[:180]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", default="/workspace")
    parser.add_argument("--code")
    parser.add_argument("--timeout", type=float, default=10)
    parser.add_argument("--worker", nargs=3, help=argparse.SUPPRESS)
    arguments = parser.parse_args()
    if arguments.worker:
        worker(*arguments.worker)
    elif arguments.code is None:
        parser.error("--code is required")
    else:
        print(json.dumps(compare(arguments.code, arguments.workspace, arguments.timeout)))


if __name__ == "__main__":
    main()
