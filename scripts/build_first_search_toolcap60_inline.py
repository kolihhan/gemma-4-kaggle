"""Opt-in tool-native first search for pinned Gemma 4 Toolcap60.

No custom tools: executed via the competition's existing run_command. This
module cannot assert that the actual model has executed the tool. Champion
ZIP is checked fail-closed when packaging the real candidate.
"""
from __future__ import annotations
import hashlib
import io
import re
import shlex
import zipfile

CHAMPION_SHA256 = 'ff08c10240a38e151a2ea1d0478e999ee5d2f437d2dad5571d912cf12859922b'
MODEL='gemma-4-31b-it-qat-w4a16-ct'
STAMP=(2026, 11, 21, 0, 0, 0)

INLINE_SCRIPT = r'''import os, re, ast, json, time
from pathlib import Path
start=time.monotonic()
query=os.environ.get('SWE_QUERY','')
words=lambda s: set(x.lower() for x in re.findall(r'[A-Za-z]{3,}', s.replace('_',' ')))
need=words(query)
root=Path('.').resolve()
allowed=['fastapi','rich','requests','src/fastapi','src/rich','src/requests']
skip={'tests','test','testing','fixtures','fixture','private','hidden','grader','docs','examples','benchmarks','__pycache__'}
matched=[]
scanned=0
truncated=False
for sub in allowed:
    base=root/sub
    if not base.is_dir() or base.is_symlink():continue
    for directory,dirs,files in os.walk(base,followlinks=False):
        dirs[:]=sorted(x for x in dirs if not x.startswith('.') and x.lower() not in skip and not (Path(directory)/x).is_symlink())
        for name in sorted(files):
            if not name.endswith('.py') or name.startswith(('test_','.')) or name.endswith('_test.py'):continue
            path=Path(directory)/name
            if path.is_symlink():continue
            rel=path.relative_to(root)
            if any(x.lower() in skip or x.startswith('.') for x in rel.parts):continue
            if scanned>=300 or time.monotonic()-start>3.0:
                truncated=True;break
            try:
                if path.stat().st_size>100000:continue
                src=path.read_text(encoding='utf-8')
                tree=ast.parse(src)
            except (OSError, UnicodeError, SyntaxError):continue
            scanned+=1
            lines=src.splitlines()
            for node in ast.walk(tree):
                if not isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):continue
                same=len(need & words(node.name))
                pathhit=len(need & words(str(rel)))
                doc=len(need & words(ast.get_docstring(node) or ''))
                score=5*same+2*pathhit+doc
                if score<=0:continue
                snippet='\n'.join(lines[node.lineno-1:min(len(lines),node.lineno+7)])[:450]
                matched.append((score,str(rel),node.lineno,{'path':str(rel),'line':node.lineno,'symbol':node.name,'score':score,'snippet':snippet}))
        if truncated:break
    if truncated:break
if truncated:
    print('FIRST_SEARCH_STATUS=TRUNCATED; USE ORIGINAL SEARCH; NO PARTIAL EVIDENCE')
elif not matched:
    print('FIRST_SEARCH_STATUS=NO_MATCH; USE ORIGINAL SEARCH')
else:
    matched.sort(key=lambda x:(-x[0],x[1],x[2]))
    print('FIRST_SEARCH_STATUS=MATCH; production-only evidence follows')
    print(json.dumps([x[-1] for x in matched[:3]],ensure_ascii=True))
'''

def make_command(query: str) -> str:
    if not re.fullmatch(r'[A-Za-z0-9_ ]{3,80}',query):
        raise ValueError('identifier-only query required')
    return f'SWE_QUERY={shlex.quote(query)} python - <<\'PY\'\n{INLINE_SCRIPT}PY\n'

def candidate_files(control:dict[str,str]) -> dict[str,str]:
    expected={'agent.yaml','prompts/system.md','configs/sampling.yaml','eval_config.yaml'}
    if set(control)!=expected:raise ValueError('expected scored four-file package only')
    agent=control['agent.yaml']
    spec=control['eval_config.yaml']
    if agent.count('model: '+MODEL)!=1 or 'run_command' not in agent or 'submit_patch' not in agent:
        raise ValueError('wrong model/tools')
    if any(spec.count(k)!=1 for k in ('max_time_minutes: 5','max_tool_calls: 60','max_turns: 80')):
        raise ValueError('changed champion budget')
    if 'FIRST_SEARCH_STATUS' in control['prompts/system.md']:
        raise ValueError('already injected')
    policy='''

## ONE optional deterministic first-search (supported native run_command)
If the issue concerns Python production code in fastapi/rich/requests, and has
one clear API/function identifier, spend at most ONE run_command on the exact
self-contained scanner below. Replace only REPLACE_QUERY_TOKEN with at most 3
space-separated ASCII identifier words (letters/digits/underscore only).
This scanner is **not** available as a repository script; run the inline code.
The tool prints up to 3 code snippets, or TRUNCATED/NO_MATCH. TRUNCATED means
coverage is INCOMPLETE, **never** trust it as no matching file: immediately
return to the original targeted search. NO_MATCH is not proof of absence.
Inspect the function and surrounding code before editing; do not copy text
from skipped/test/hidden directories. This is guidance, not a new tool.
The normal safety rules, time/call budget, and submit_patch remain unchanged.

~~~sh
'''+make_command('REPLACE_QUERY_TOKEN')+'''~~~
'''
    out=dict(control)
    out['prompts/system.md']=control['prompts/system.md'].rstrip()+'\n'+policy
    assert {k for k in out if out[k]!=control[k]}=={'prompts/system.md'}
    return out

def build_from_source_zip(source_zip:bytes) -> bytes:
    from scripts.build_toolcap60_timeout_recovery import build as build_control
    from scripts.build_toolcap60_timeout_recovery import files_for_candidate
    baseline=build_control(source_zip)
    if hashlib.sha256(baseline).hexdigest()!=CHAMPION_SHA256:
        raise ValueError('baseline archive != exact scored 0.18 Champion; STOP')
    files=candidate_files(files_for_candidate(source_zip))
    with io.BytesIO() as sink:
        with zipfile.ZipFile(sink,'w') as archive:
            for name,content in sorted(files.items()):
                item=zipfile.ZipInfo(name,date_time=STAMP)
                item.compress_type=zipfile.ZIP_DEFLATED
                item.external_attr=0o100644<<16
                archive.writestr(item,content.encode())
        candidate=sink.getvalue()
    with zipfile.ZipFile(io.BytesIO(candidate)) as z:
        if z.testzip() is not None or set(z.namelist())!=set(files):
            raise ValueError('invalid derived candidate')
    return candidate
