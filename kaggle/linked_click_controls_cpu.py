"""Build pinned Click snapshots and run private offline reference controls."""

from collections import Counter
import gzip
from hashlib import sha256
from io import BytesIO
import logging
import tarfile
import tempfile


BUNDLE_NAME = "linked-click-control-bundle.json"
SOURCE_WHEELS = ("flit-core==3.12.0", "colorama==0.4.6")


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def git(source: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(source), *args], timeout=45)


def source_snapshot(source: Path, base: str) -> bytes:
    archive = BytesIO(git(source, "archive", base))
    with tarfile.open(fileobj=archive, mode="a") as tar:
        paths = set(tar.getnames())
        if "src/click/__init__.py" not in paths or "click" in paths:
            raise RuntimeError("Unexpected Click source layout")
        # The scorer places /workspace first. Expose the original src package
        # there so an installed Click cannot shadow the checkout.
        link = tarfile.TarInfo("click")
        link.type = tarfile.SYMTYPE
        link.linkname = "src/click"
        link.mode = 0o777
        tar.addfile(link)
    return gzip.compress(archive.getvalue(), mtime=0)


def build_snapshots() -> None:
    bundle = WORKING_DIR / "linked-click-input"
    wheels = bundle / "wheels"
    wheels.mkdir(parents=True)
    subprocess.run(
        [sys.executable, "-m", "pip", "download", "-q", "--only-binary=:all:", "--dest", str(wheels), *SOURCE_WHEELS],
        check=True, capture_output=True, timeout=240,
    )
    records = []
    with tempfile.TemporaryDirectory(prefix="click-source-") as directory:
        source = Path(directory) / "click"
        subprocess.run(
            ["git", "clone", "--shallow-since=2026-04-02", "https://github.com/pallets/click.git", str(source)],
            check=True, capture_output=True, timeout=200,
        )
        for row in COHORT["cases"]:
            head = git(source, "rev-list", "--parents", "-n", "1", row["fix"]).decode().split()
            if len(head) < 2 or head[1] != row["base"]:
                raise RuntimeError("Frozen base mismatch")
            git(source, "cat-file", "-e", f"{row['base']}:LICENSE.txt")
            key = f"click_{row['pr']}"
            files = {part: bundle / f"{key}.{suffix}" for part, suffix in (
                ("snapshot", "tar.gz"), ("gold", "gold.patch"), ("tests", "test.patch"),
            )}
            files["snapshot"].write_bytes(source_snapshot(source, row["base"]))
            for part, paths in (("gold", row["production"]), ("tests", row["tests"])):
                patch = git(source, "diff", "--binary", "--no-renames", row["base"], row["fix"], "--", *paths)
                if not patch.startswith(b"diff --git"):
                    raise RuntimeError("Missing frozen patch")
                files[part].write_bytes(patch)
            records.append({"pr": row["pr"], "base": row["base"], "fix": row["fix"],
                            "files": {k: {"filename": f.name, "sha256": digest(f)} for k, f in files.items()}})
    (bundle / BUNDLE_NAME).write_text(json.dumps({"cohort_sha256": LOCK, "cases": records}, sort_keys=True))


async def verify_snapshots(bundle: Path, workspace: Path, records: list[dict]) -> list[dict]:
    from adk_submission import ModelRegistry
    from swegemma.config import EvalConfig
    from swegemma.harness.verification import verify_task
    from swegemma.models import Task
    from swegemma.sandbox.subprocess import SubprocessManager

    config = EvalConfig(
        tasks_path=workspace / "tasks.jsonl", snapshots_dir=bundle, results_dir=workspace / "results",
        submission_dir=workspace / "submission", models=ModelRegistry(), sandbox="subprocess",
        wheels_dir=DATA_DIR / "wheels", timeout_seconds=300, verification_timeout_seconds=180,
        display_mode="quiet",
    )
    (workspace / "results").mkdir()
    (workspace / "submission").mkdir()
    slots = asyncio.Semaphore(4)

    async def evaluate(record: dict) -> dict:
        async with slots:
            row = {k: record[k] for k in ("pr", "base", "fix")}
            try:
                files = {label: bundle / Path(item["filename"]).name for label, item in record["files"].items()}
                if any(digest(file) != record["files"][label]["sha256"] for label, file in files.items()):
                    raise RuntimeError("Snapshot or patch digest mismatch")
                task = Task(instance_id=f"external_click_{row['pr']}", repo="pallets/click",
                            base_commit=row["base"], problem_statement="", test_patch=files["tests"].read_text())
                sandbox = SubprocessManager(timeout_seconds=180)
                for control, patch in (("gold", files["gold"].read_text()), ("noop", "")):
                    grade = await verify_task(sandbox, config, task, files["snapshot"],
                                              agent_patch=patch, start_time=time.perf_counter())
                    row[control] = {"pass": bool(grade.resolved), "exit": grade.test_exit_code}
                if row["gold"] != {"pass": True, "exit": 0}:
                    row["status"] = "reference_failed"
                elif row["noop"] != {"pass": False, "exit": 1}:
                    row["status"] = "noop_inconclusive"
                else:
                    row["status"] = "eligible"
            except Exception as error:
                row.update(status="error", error_type=type(error).__name__)
            return row

    return await asyncio.gather(*(evaluate(row) for row in records))


def verify_main() -> None:
    matches = list(Path("/kaggle/input").rglob(BUNDLE_NAME))
    if len(matches) != 1:
        raise RuntimeError("Exact private control bundle required")
    bundle = matches[0].parent
    packed = json.loads(matches[0].read_text())
    records = packed["cases"]
    key = lambda x: (x["pr"], x["base"], x["fix"])
    if packed["cohort_sha256"] != LOCK or [key(x) for x in records] != [key(x) for x in COHORT["cases"]]:
        raise RuntimeError("Frozen case membership mismatch")
    wheel = WHEELHOUSE_DIR / "swegemma-0.2.11-py3-none-any.whl"
    if digest(wheel) != "9ad876581f3acde8ec3c369858f0834e2b9f41a3cffce3ca42f09cb090aea9d3":
        raise RuntimeError("Unrecognized official verifier wheel")
    install_wheelhouse()
    with tempfile.TemporaryDirectory(prefix="click-native-") as temporary:
        workspace = Path(temporary)
        dependencies = workspace / "site-packages"
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q", "--no-index", "--find-links", str(bundle / "wheels"),
             "--target", str(dependencies), *SOURCE_WHEELS],
            check=True, capture_output=True, timeout=150,
        )
        sys.path.insert(0, str(dependencies))
        rows = asyncio.run(verify_snapshots(bundle, workspace, records))
    (WORKING_DIR / "gemma-click-native-controls.json").write_text(json.dumps({
        "cohort_sha256": LOCK, "count": len(rows), "counts": Counter(row["status"] for row in rows),
        "verifier": "swegemma-0.2.11", "rows": rows,
    }, sort_keys=True))


if __name__ == "__main__":
    logging.disable(logging.CRITICAL)
    try:
        if STAGE == "build":
            build_snapshots()
        else:
            verify_main()
    except Exception as error:
        raise RuntimeError(f"LINKED_CLICK_{STAGE.upper()}_{type(error).__name__}") from None
