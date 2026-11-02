#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path

EXPECTED_SHA256 = {
    'agent.yaml': '3e7b6878a07e01a6015c5949faaac6323460a01c246bcc1364ffbb9fb724a708',
    'eval_config.yaml': 'fb71231c07834b8fdc9b5e4d08c4d91b4bd6f4061b19a14dfc0bb98dff966412',
    'configs/sampling.yaml': '3dab0b2506dae34ce92fef7b380d6073729104b23fe2cf66d44ac1d2f213aa6a',
    'prompts/system.md': '8b0326e707778ad36722b65bf5d20122c1406ba582000ac599d5cf7af9a3466b',
    'prompts/coder.md': '95b6362f4538d76970b89e8103ff622e76138369e2d2f868777d2b70ba7d7e76',
}
MODEL_NAME = 'gemma-4-e4b-it-qat-w4a16-ct'
COMPETITION = 'gemma-4-developer-agent'


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_frozen_submission(submission: Path) -> dict[str, str]:
    actual = sorted(p.relative_to(submission).as_posix() for p in submission.rglob('*') if p.is_file())
    expected = sorted(EXPECTED_SHA256)
    if actual != expected:
        raise ValueError(f'frozen reliability-v1 file set drifted: actual={actual} expected={expected}')
    payload: dict[str, str] = {}
    for rel in expected:
        data = (submission / rel).read_bytes()
        digest = _sha(data)
        if digest != EXPECTED_SHA256[rel]:
            raise ValueError(f'frozen reliability-v1 hash drift for {rel}: {digest}')
        payload[rel] = data.decode('utf-8')
    agent = payload['agent.yaml']
    if 'agent_tool:' in agent or 'verifier' in agent.lower():
        raise ValueError('reliability-v1 must remain single-root')
    if agent.count('- submit_patch') != 1:
        raise ValueError('reliability-v1 must expose submit_patch exactly once')
    for tool in ('run_command','read_file','edit_file','get_status','get_code_neighbors','search_similar_code','get_code_subgraph'):
        if f'- {tool}' not in agent:
            raise ValueError(f'frozen tool surface drifted: missing {tool}')
    return payload


def _metadata(kernel_ref: str, code_file: str, *, gpu: bool) -> dict:
    meta = {
        'id': kernel_ref,
        'title': kernel_ref.split('/', 1)[1],
        'code_file': code_file,
        'language': 'python',
        'kernel_type': 'script',
        'is_private': True,
        'enable_gpu': gpu,
        'enable_tpu': False,
        'enable_internet': False,
        'competition_sources': [COMPETITION],
        'dataset_sources': [],
        'kernel_sources': [],
        'model_sources': [],
    }
    if gpu:
        meta.update({
            'machine_shape': 'NvidiaL4',
            'docker_image': 'gcr.io/kaggle-private-byod/python@sha256:37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461',
            'dataset_sources': ['metric/gemma-4-developer-agent-wheelhouse'],
            'model_sources': ['google/gemma-4/Other/gemma-4-e4b-it-qat-w4a16-ct/2'],
        })
    return meta


def render_diagnostic(repo: Path, out: Path, kernel_ref: str, manifest_path: Path) -> None:
    payload = load_frozen_submission(repo / 'submission')
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if manifest.get('selection_rule') != 'gold-pass AND no-op-fail':
        raise ValueError('diagnostic denominator drifted')
    if manifest.get('sampling_frozen') is not True or manifest.get('budget_frozen') is not True:
        raise ValueError('diagnostic sampling/budget must stay frozen')
    template = (repo / 'kaggle' / 'verifier_baseline_runtime.py').read_text(encoding='utf-8')
    payload_b64 = base64.b64encode(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).decode('ascii')
    marker = '__SUBMISSION_PAYLOAD_B64__'
    manifest_line = 'HOLDOUT_MANIFEST_JSON = "__VERIFIER_LORA_HOLDOUT_MANIFEST_JSON__"'
    if template.count(marker) != 1 or template.count(manifest_line) != 1:
        raise ValueError('diagnostic runtime placeholder drift')
    rendered = template.replace(marker, payload_b64, 1)
    rendered = rendered.replace(manifest_line, f'HOLDOUT_MANIFEST_JSON = {json.dumps(manifest, sort_keys=True)!r}', 1)
    compile(rendered, 'reliability_v1_diagnostic.py', 'exec')
    out.mkdir(parents=True, exist_ok=True)
    (out / 'reliability_v1_diagnostic.py').write_text(rendered, encoding='utf-8')
    (out / 'kernel-metadata.json').write_text(json.dumps(_metadata(kernel_ref, 'reliability_v1_diagnostic.py', gpu=True), indent=2)+'\n', encoding='utf-8')


def render_submit(repo: Path, out: Path, kernel_ref: str) -> None:
    payload = load_frozen_submission(repo / 'submission')
    encoded = base64.b64encode(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).decode('ascii')
    code = f'''from pathlib import Path\nimport base64, json, zipfile\nPAYLOAD = {encoded!r}\nfiles = json.loads(base64.b64decode(PAYLOAD).decode("utf-8"))\nout = Path("/kaggle/working/submission.zip")\nwith zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as z:\n    for name, text in sorted(files.items()):\n        z.writestr(name, text)\nprint("RELIABILITY_V1_SUBMISSION_ZIP", out, out.stat().st_size, sorted(files))\n'''
    compile(code, 'reliability_v1_submit_builder.py', 'exec')
    out.mkdir(parents=True, exist_ok=True)
    (out / 'reliability_v1_submit_builder.py').write_text(code, encoding='utf-8')
    (out / 'kernel-metadata.json').write_text(json.dumps(_metadata(kernel_ref, 'reliability_v1_submit_builder.py', gpu=False), indent=2)+'\n', encoding='utf-8')


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', type=Path, default=Path('.'))
    ap.add_argument('--mode', choices=('diagnostic','submit'), required=True)
    ap.add_argument('--kernel-dir', type=Path, required=True)
    ap.add_argument('--kernel-ref', required=True)
    ap.add_argument('--manifest', type=Path)
    args = ap.parse_args()
    repo = args.repo.resolve()
    if args.mode == 'diagnostic':
        if args.manifest is None:
            ap.error('--manifest is required for diagnostic mode')
        render_diagnostic(repo, args.kernel_dir, args.kernel_ref, args.manifest)
    else:
        render_submit(repo, args.kernel_dir, args.kernel_ref)
    print('reliability_v1_frozen=true')
    print('base_model=', MODEL_NAME)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
