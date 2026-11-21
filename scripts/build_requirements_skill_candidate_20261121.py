"""Create one 31B Skill candidate from a SHA-verified scored Champion source.

This only packages code: no 31B model call, official Kaggle score, or grader PASS.
The scorer source ZIP is required privately and is NOT included in this repo.
"""
from __future__ import annotations

from hashlib import sha256
from io import BytesIO
from pathlib import Path
import zipfile

CHAMPION_SHA256 = 'ff08c10240a38e151a2ea1d0478e999ee5d2f437d2dad5571d912cf12859922b'
MODEL = 'gemma-4-31b-it-qat-w4a16-ct'
SKILL = 'skills/requirements-evidence'
SOURCE = Path(__file__).with_name('requirements_evidence_20261121.py')
STAMP = (2026, 11, 21, 0, 0, 0)
EXPECTED = {'agent.yaml','prompts/system.md','configs/sampling.yaml','eval_config.yaml'}

SKILL_DOC = """---
name: requirements-evidence
description: Read existing sandbox-local Python tests and source docstrings for expected behavior when an issue is underspecified. No network, private tests, or reference patches.
---
Use the read-only script scripts/requirements_evidence.py with --query "short issue phrase".
Inspect returned code yourself before editing. NO_MATCH is not proof of absence;
TRUNCATED means incomplete coverage. One call at most, skip when issue is clear.
"""
PROMPT_DELTA = """
## Optional local requirements evidence
When the task's behavioral requirement is ambiguous, you MAY call the
requirements-evidence skill's scripts/requirements_evidence.py ONCE via the
native run_skill_script tool with a short --query phrase. The script gives
bounded existing test assertions, code docstrings and path/line references;
it does not retrieve external issue bodies or reference patches. Treat the
result as fallible candidates and inspect surrounding source. NO_MATCH and
TRUNCATED are not evidence that a behavior is impossible. If the issue is
already clear, skip this lookup. Budget and final submit_patch policy unchanged.
"""

def files_for_candidate(control: dict[str,str]) -> dict[str,str]:
    if set(control) != EXPECTED: raise ValueError('expected scored four-file base')
    a = control['agent.yaml']
    if a.count('model: '+MODEL) != 1 or a.count('\ntools:\n') != 1:
        raise ValueError('wrong model or missing canonical tool stanza')
    if 'skills:' in a or not all(k in a for k in ('run_command','submit_patch')):
        raise ValueError('unexpected existing skills or missing tools')
    ev = control['eval_config.yaml']
    if any(ev.count(k)!=1 for k in ('max_time_minutes: 5','max_tool_calls: 60','max_turns: 80')):
        raise ValueError('budget not pinned to 0.18 Champion')
    if not SOURCE.is_file(): raise FileNotFoundError(SOURCE)
    out = dict(control)
    out['agent.yaml'] = a.replace('\ntools:\n', f'\nskills:\n  - {SKILL}\ntools:\n', 1)
    out['prompts/system.md'] = control['prompts/system.md'].rstrip() + '\n' + PROMPT_DELTA
    out[f'{SKILL}/SKILL.md'] = SKILL_DOC
    out[f'{SKILL}/scripts/requirements_evidence.py'] = SOURCE.read_text(encoding='utf-8')
    if out['configs/sampling.yaml'] != control['configs/sampling.yaml'] or out['eval_config.yaml'] != ev:
        raise AssertionError('sampling/budget drift')
    return out

def build_candidate(source_zip: bytes) -> tuple[bytes,dict]:
    from scripts.build_toolcap60_timeout_recovery import (
        build as original_champion_build,
        files_for_candidate as original_champion_files,
    )
    champion = original_champion_build(source_zip)
    actual = sha256(champion).hexdigest()
    if actual != CHAMPION_SHA256:
        raise ValueError(f'scored champion mismatch ({actual}), STOP')
    files = files_for_candidate(original_champion_files(source_zip))
    with BytesIO() as stream:
        with zipfile.ZipFile(stream,'w') as archive:
            for path,body in sorted(files.items()):
                if path.startswith('/') or '..' in Path(path).parts: raise ValueError('bad path')
                zi=zipfile.ZipInfo(path,date_time=STAMP)
                zi.compress_type=zipfile.ZIP_DEFLATED
                zi.external_attr=0o100644 << 16
                archive.writestr(zi,body.encode('utf-8'))
        result=stream.getvalue()
    with zipfile.ZipFile(BytesIO(result)) as archive:
        if archive.testzip() is not None or set(archive.namelist()) != set(files):
            raise ValueError('invalid candidate ZIP')
    return result,{'champion_sha256':actual,'candidate_sha256':sha256(result).hexdigest(),
                   'model':MODEL,'scored':False,'graded_resolves':None}
