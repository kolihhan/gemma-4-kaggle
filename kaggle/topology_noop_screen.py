"""No-op eligibility screen for the topology A/B denominator.

A task is eligible only when the untouched workspace fails its official
verification gate. This runtime invokes no model and writes no task text,
reference patch, or test output to artifacts.
"""
from __future__ import annotations

import asyncio
import glob
import importlib
import json
import shutil
import subprocess
import sys
import time
import traceback
from pathlib import Path

DATA_DIR = Path('/kaggle/input/competitions/gemma-4-developer-agent')
WHEELHOUSE_DIR = Path('/kaggle/input/datasets/metric/gemma-4-developer-agent-wheelhouse')
WORKING_DIR = Path('/kaggle/working')
RESULT_PATH = WORKING_DIR / 'topology_noop_screen.json'

TASKS = [
    ('rich_3061', 'Textualize/rich'),
    ('rich_3067', 'Textualize/rich'),
    ('rich_3934', 'Textualize/rich'),
    ('rich_3942', 'Textualize/rich'),
    ('fastapi_13920', 'fastapi/fastapi'),
    ('fastapi_14077', 'fastapi/fastapi'),
    ('fastapi_14463', 'fastapi/fastapi'),
    ('fastapi_14851', 'fastapi/fastapi'),
    ('fastapi_14986', 'fastapi/fastapi'),
    ('rich_3105', 'Textualize/rich'),
    ('rich_4079', 'Textualize/rich'),
    ('rich_3777', 'Textualize/rich'),
    ('rich_3052', 'Textualize/rich'),
    ('fastapi_5077', 'fastapi/fastapi'),
    ('fastapi_9425', 'fastapi/fastapi'),
    ('fastapi_14873', 'fastapi/fastapi'),
    ('fastapi_9555', 'fastapi/fastapi'),
    ('fastapi_15280', 'fastapi/fastapi'),
    ('fastapi_14448', 'fastapi/fastapi'),
]


def install_official_wheelhouse() -> None:
    if not WHEELHOUSE_DIR.is_dir():
        raise FileNotFoundError(f'missing official wheelhouse: {WHEELHOUSE_DIR}')
    for pattern in (
        '/usr/local/lib/python*/dist-packages/*cutlass*.pth',
        '/usr/local/lib/python*/site-packages/*cutlass*.pth',
    ):
        for pth in glob.glob(pattern):
            try:
                Path(pth).unlink()
            except OSError:
                pass
    fixed = Path('/tmp/gemma4-scorer-wheelhouse')
    fixed.mkdir(parents=True, exist_ok=True)
    for wheel in WHEELHOUSE_DIR.glob('*.whl'):
        if 'cutlass' in wheel.name.lower():
            continue
        name = wheel.name.replace('cu128', '+cu128') if 'cu128' in wheel.name and '+' not in wheel.name else wheel.name
        target = fixed / name
        if not target.exists():
            try:
                target.symlink_to(wheel)
            except OSError:
                shutil.copyfile(wheel, target)
    wheels = sorted(str(p) for p in fixed.glob('*.whl'))
    if not wheels:
        raise RuntimeError('official scorer wheelhouse is empty')
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', '--no-deps', '--force-reinstall', *wheels], check=True)
    importlib.invalidate_caches()


def error_record(instance_id: str, repo: str, exc: BaseException) -> dict[str, object]:
    return {
        'instance_id': instance_id,
        'repo': repo,
        'status': 'error',
        'control': 'noop',
        'resolved': None,
        'test_exit_code': None,
        'error_type': type(exc).__name__,
        'error': str(exc),
    }


async def run_screen() -> dict[str, object]:
    from adk_submission import ModelRegistry
    from swegemma.config import EvalConfig
    from swegemma.deduplication import resolve_task_snapshot_paths
    from swegemma.evaluate import Evaluator
    from swegemma.harness.verification import verify_task
    from swegemma.models import load_tasks

    ids = [task_id for task_id, _ in TASKS]
    if len(ids) != 19 or len(set(ids)) != 19:
        raise RuntimeError('topology screen must contain exactly 19 unique tasks')

    tasks_path = DATA_DIR / 'tasks.jsonl'
    snapshots_dir = DATA_DIR / 'snapshots'
    results_dir = WORKING_DIR / 'topology-noop-results'
    empty_submission = WORKING_DIR / 'topology-noop-empty-submission'
    results_dir.mkdir(parents=True, exist_ok=True)
    empty_submission.mkdir(parents=True, exist_ok=True)

    public = load_tasks(tasks_path)
    by_id = {task.instance_id: task for task in public if task.instance_id in set(ids)}
    missing = sorted(set(ids) - set(by_id))
    if missing:
        raise RuntimeError(f'missing tasks: {missing}')

    config = EvalConfig(
        tasks_path=tasks_path,
        snapshots_dir=snapshots_dir,
        results_dir=results_dir,
        submission_dir=empty_submission,
        models=ModelRegistry(),
        sandbox='subprocess',
        wheels_dir=DATA_DIR / 'wheels',
        timeout_seconds=300,
        verification_timeout_seconds=300,
        verbose=False,
    )
    evaluator = Evaluator(config)

    records: list[dict[str, object]] = []
    for index, (instance_id, expected_repo) in enumerate(TASKS, 1):
        print(f'[{index:02d}/19] noop {instance_id}', flush=True)
        try:
            task = evaluator._hydrate_task_from_secret(by_id[instance_id])
            if task.instance_id != instance_id or task.repo != expected_repo:
                raise RuntimeError(f'hydrated metadata mismatch for {instance_id}: {task.repo!r}')
            has_test_spec = bool(
                (task.test_patch and task.test_patch.strip())
                or getattr(task, 'FAIL_TO_PASS', ())
                or getattr(task, 'PASS_TO_PASS', ())
                or getattr(task, 'test_files', None)
            )
            if not has_test_spec:
                raise RuntimeError('verification test specification unavailable')
            snapshot_path, base_snapshot_path, patch_path = resolve_task_snapshot_paths(
                snapshots_dir, task.instance_id, task.repo
            )
            started = time.perf_counter()
            verification = await verify_task(
                evaluator.docker,
                evaluator.config,
                task,
                snapshot_path,
                base_snapshot_path=base_snapshot_path,
                patch_path=patch_path,
                agent_patch='',
                agent_error=None,
                trace=None,
                start_time=started,
            )
            record = {
                'instance_id': instance_id,
                'repo': expected_repo,
                'status': 'completed',
                'control': 'noop',
                'resolved': bool(verification.resolved),
                'test_exit_code': verification.test_exit_code,
                'duration_seconds': verification.duration_seconds,
                'error': verification.error,
            }
        except BaseException as exc:
            record = error_record(instance_id, expected_repo, exc)
            print(f'noop error {instance_id}: {type(exc).__name__}: {exc}', flush=True)
        records.append(record)
        print('NOOP_RESULT', json.dumps(record, sort_keys=True), flush=True)

    eligible = sorted(
        str(r['instance_id']) for r in records
        if r.get('status') == 'completed'
        and r.get('resolved') is False
        and isinstance(r.get('test_exit_code'), int)
        and int(r['test_exit_code']) != 0
    )
    noop_pass = sorted(
        str(r['instance_id']) for r in records
        if r.get('status') == 'completed'
        and r.get('resolved') is True
        and r.get('test_exit_code') == 0
    )
    ambiguous = sorted(set(ids) - set(eligible) - set(noop_pass))
    return {
        'version': 'topology-ab-noop-screen-v1',
        'status': 'completed',
        'control': 'noop',
        'requested': 19,
        'completed': sum(r.get('status') == 'completed' for r in records),
        'eligible_instance_ids': eligible,
        'noop_passing_instance_ids': noop_pass,
        'ambiguous_instance_ids': ambiguous,
        'results': records,
    }


def main() -> None:
    WORKING_DIR.mkdir(parents=True, exist_ok=True)
    install_official_wheelhouse()
    result = asyncio.run(run_screen())
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding='utf-8')
    print('TOPOLOGY_NOOP_SUMMARY', json.dumps({k:v for k,v in result.items() if k!='results'}, sort_keys=True), flush=True)


if __name__ == '__main__':
    try:
        main()
    except BaseException as exc:
        RESULT_PATH.write_text(json.dumps({
            'version': 'topology-ab-noop-screen-v1',
            'status': 'error',
            'error_type': type(exc).__name__,
            'error': str(exc),
            'traceback': traceback.format_exc(),
        }, indent=2, sort_keys=True), encoding='utf-8')
        raise
