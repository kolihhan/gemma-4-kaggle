"""Create a private solver input bundle for the frozen 31-case comparison."""

from hashlib import sha256
import logging
import tempfile


def checksum(path: Path) -> str:
    checksum = sha256()
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            checksum.update(block)
    return checksum.hexdigest()


def build() -> dict:
    from swegemma.deduplication import (
        extract_tar_archive,
        pack_tar_archive,
        reconstruct_snapshot,
        resolve_task_snapshot_paths,
    )
    from swegemma.models import load_tasks

    destination = WORKING_DIR / "gemma31-solver-inputs"
    snapshots = destination / "snapshots"
    snapshots.mkdir(parents=True)
    wheels = destination / "wheels"
    wheels.mkdir()
    linked = list(Path("/kaggle/input").rglob("linked-click-control-bundle.json"))
    if len(linked) != 1:
        raise RuntimeError("Missing exact private Click archive source")
    click_directory = linked[0].parent
    click = json.loads(linked[0].read_text())
    if click["cohort_sha256"] != LOCK["click_control_cohort_sha256"]:
        raise ValueError("Click source membership mismatch")
    click_rows = {f"external_click_{row['pr']}": row for row in click["cases"]}
    official_rows = {task.instance_id: task for task in load_tasks(DATA_DIR / "tasks.jsonl")}
    tasks = []
    hashes = {}
    for entry in LOCK["cases"]:
        task_id = entry["instance_id"]
        target = snapshots / f"{task_id}.tgz"
        task = {"instance_id": task_id, "repo": entry["repo"]}
        if entry["source"] == "official_development":
            row = official_rows[task_id]
            if row.repo != entry["repo"] or not row.problem_statement.strip():
                raise ValueError("Frozen official source metadata mismatch")
            task.update(base_commit=row.base_commit, problem_statement=row.problem_statement)
            original, base, patch = resolve_task_snapshot_paths(DATA_DIR / "snapshots", task_id, row.repo)
            with tempfile.TemporaryDirectory(prefix="gemma31-source-") as tmp:
                working = Path(tmp) / "workspace"
                working.mkdir()
                if base is not None:
                    if not reconstruct_snapshot(base, patch, working):
                        raise RuntimeError("Official before-fix workspace did not reconstruct")
                else:
                    extract_tar_archive(original, working)
                for git in sorted(working.rglob(".git"), key=lambda item: -len(item.parts)):
                    if git.is_symlink() or git.is_file():
                        git.unlink()
                    elif git.is_dir():
                        shutil.rmtree(git)
                pack_tar_archive(working, target)
        elif entry["source"] == "original_upstream_issue":
            row = click_rows[task_id]
            before = row["files"]["snapshot"]
            archive = click_directory / Path(before["filename"]).name
            if row["base"] != entry["base_commit"] or checksum(archive) != before["sha256"]:
                raise ValueError("Click source fixture mismatch")
            if before["sha256"] != entry["solver_snapshot_sha256"]:
                raise ValueError("Click archive changed since the freeze")
            statement = CLICK_STATEMENTS[task_id]
            if sha256(statement.encode()).hexdigest() != entry["problem_statement_sha256"]:
                raise ValueError("Click issue body changed since the freeze")
            task.update(base_commit=entry["base_commit"], problem_statement=statement)
            shutil.copyfile(archive, target)
        else:
            raise ValueError("Unknown source type")
        hashes[target.name] = checksum(target)
        tasks.append(task)
    if len(tasks) != 31 or set(CLICK_STATEMENTS) != set(click_rows):
        raise ValueError("Incomplete locked cohort")
    # Public package binaries support editable installs and ordinary workspace
    # tests. No benchmark tests, solutions or per-issue archive patches are copied.
    for source in (DATA_DIR / "wheels", click_directory / "wheels"):
        for wheel in sorted(source.glob("*.whl")):
            target = wheels / wheel.name
            if target.exists() and checksum(target) != checksum(wheel):
                raise ValueError("Conflicting offline wheel versions")
            if not target.exists():
                shutil.copyfile(wheel, target)
            hashes[f"wheels/{wheel.name}"] = checksum(target)
    tasks_path = destination / "tasks.jsonl"
    tasks_path.write_text("".join(json.dumps(task, sort_keys=True) + "\n" for task in tasks))
    hashes["tasks.jsonl"] = checksum(tasks_path)
    report = {"case_count": len(tasks), "lock_sha256": LOCK_SHA, "files": hashes}
    (destination / "gemma31-solver-bundle.json").write_text(json.dumps(report, sort_keys=True))
    return {"case_count": len(tasks), "source_snapshots": len(tasks),
            "dependency_wheels": len(list(wheels.glob("*.whl"))),
            "solver_manifest_sha256": checksum(destination / "gemma31-solver-bundle.json")}


if __name__ == "__main__":
    logging.disable(logging.CRITICAL)
    try:
        install_wheelhouse()
        report = json.dumps(build(), sort_keys=True)
        (WORKING_DIR / "gemma31-solver-report.json").write_text(report)
        print("GEMMA31_SOLVER_INPUTS=" + report, flush=True)
    except Exception as error:
        raise RuntimeError("SOLVER_INPUT_PREP_" + type(error).__name__) from None
