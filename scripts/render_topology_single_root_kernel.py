#!/usr/bin/env python3
"""Render a topology-only single-root E4B evaluation kernel.

Only two candidate behaviors change relative to canonical submission:
1. remove the verifier AgentTool from the root tool list and add submit_patch;
2. give the existing coder prompt final verify/submit ownership.

Sampling, evaluation budget, model family, code-intelligence tools, and the
remaining coder policy are asserted unchanged.
"""
from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path

MODEL_NAME = 'gemma-4-e4b-it-qat-w4a16-ct'
EXPECTED_SAMPLING = """temperature: 0.2
top_p: 0.95
max_output_tokens: 16384
thinking_config:
  thinking_budget: 4096
  include_thoughts: true
"""
EXPECTED_EVAL = """# Provisional diagnostic budget. Tune from real traces; these are not official recommended values.
evaluation:
  timeout_seconds: 300
  max_tool_calls: 32
  max_time_minutes: 5
  max_turns: 64
"""

AGENT_TOOL_BLOCK = """  - agent_tool:
      config_path: sub_agents/verifier.yaml
      skip_summarization: true
"""

OLD_INTRO = """You are the coding stage of a two-stage software-engineering pipeline working inside `/workspace`.

Task:
{problem_description}

Your job is to leave the smallest credible fix in the working tree and useful verification evidence for the verifier. You do not own final submission.
"""
NEW_INTRO = """You are a software-engineering agent solving one repository issue inside `/workspace`.

Task:
{problem_description}

Your job is to leave the smallest credible fix in the working tree, verify it with the available local evidence, and submit only when verification passes.
"""

OLD_STEP8 = """8. If targeted verification fails, make at most one evidence-backed narrow repair/test cycle. If it still fails, stop expanding scope and hand off the current small diff plus the failure evidence to the verifier.
"""
NEW_STEP8 = """8. If targeted verification fails, make at most one evidence-backed narrow repair/test cycle. If it still fails, stop expanding scope and do not submit a known-failing patch.
"""

OLD_STEP9 = """9. Do not submit. You do not have the submission tool. Call `swe_e4b_verifier` exactly once after your coding/verification pass, asking it to inspect the current working tree and evidence, perform its bounded independent verification/repair policy, and submit only if verified. After that tool returns, do not make further edits or tool calls; finish with a concise summary.
"""
NEW_STEP9 = """9. Own final submission. After targeted verification passes, inspect `git diff --check`, `git diff`, and `git status` once. If the remaining patch is narrow and intended, call `submit_patch` as the final tool action. Never call `submit_patch` while the most recent directly relevant verification is failing.
"""


def _replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        raise ValueError(f'{label}: expected exactly one replacement target, got {text.count(old)}')
    return text.replace(old, new, 1)


def build_candidate_payload(submission: Path) -> dict[str, str]:
    sampling = (submission / 'configs' / 'sampling.yaml').read_text(encoding='utf-8')
    eval_config = (submission / 'eval_config.yaml').read_text(encoding='utf-8')
    if sampling != EXPECTED_SAMPLING:
        raise ValueError('sampling config drifted; topology A/B must freeze sampling exactly')
    if eval_config != EXPECTED_EVAL:
        raise ValueError('eval budget drifted; topology A/B must freeze runtime budget exactly')

    payload: dict[str, str] = {}
    for path in sorted(submission.rglob('*')):
        if not path.is_file():
            continue
        rel = path.relative_to(submission).as_posix()
        if rel in {'sub_agents/verifier.yaml', 'prompts/verifier.md'}:
            continue
        if rel.startswith('adapters/'):
            raise ValueError(f'topology A/B candidate must not contain adapters: {rel}')
        payload[rel] = path.read_text(encoding='utf-8')

    agent = payload['agent.yaml']
    if agent.count(AGENT_TOOL_BLOCK) != 1:
        raise ValueError('root verifier AgentTool block drifted')
    agent = agent.replace(AGENT_TOOL_BLOCK, '  - submit_patch\n', 1)
    agent = _replace_once(
        agent,
        'description: Makes the smallest evidence-backed code change, then delegates final verification and submission to one verifier tool.\n',
        'description: Makes the smallest evidence-backed code change, verifies it narrowly, and submits only after passing evidence.\n',
        'agent description',
    )
    if 'agent_tool:' in agent or 'sub_agents/verifier.yaml' in agent:
        raise ValueError('verifier AgentTool remained in single-root candidate')
    if agent.count('- submit_patch') != 1:
        raise ValueError('single-root candidate must expose submit_patch exactly once')
    for required in ('- run_command', '- read_file', '- edit_file', '- get_status', '- get_code_neighbors', '- search_similar_code', '- get_code_subgraph'):
        if required not in agent:
            raise ValueError(f'root tool drift: missing {required}')
    payload['agent.yaml'] = agent

    prompt = payload['prompts/coder.md']
    prompt = _replace_once(prompt, OLD_INTRO, NEW_INTRO, 'coder intro')
    prompt = _replace_once(prompt, OLD_STEP8, NEW_STEP8, 'coder step 8')
    prompt = _replace_once(prompt, OLD_STEP9, NEW_STEP9, 'coder step 9')
    if 'swe_e4b_verifier' in prompt or 'hand off' in prompt or 'You do not own final submission' in prompt:
        raise ValueError('verifier handoff language remained in candidate prompt')
    for invariant in (
        'After two failed `edit_file` attempts',
        'assert the exact old text',
        'inspect `git diff`',
        'targeted verification',
        'Never reinterpret a non-zero test result as success',
        'at most one evidence-backed narrow repair/test cycle',
    ):
        if invariant not in prompt:
            raise ValueError(f'coder policy drift: missing {invariant!r}')
    payload['prompts/coder.md'] = prompt

    if payload.get('configs/sampling.yaml') != EXPECTED_SAMPLING:
        raise ValueError('rendered candidate sampling drifted')
    if payload.get('eval_config.yaml') != EXPECTED_EVAL:
        raise ValueError('rendered candidate eval budget drifted')
    return payload


def render_runtime(template: str, payload: dict[str, str], manifest: dict) -> str:
    encoded = base64.b64encode(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).decode('ascii')
    submission_marker = '__SUBMISSION_PAYLOAD_B64__'
    manifest_line = 'HOLDOUT_MANIFEST_JSON = "__VERIFIER_LORA_HOLDOUT_MANIFEST_JSON__"'
    if template.count(submission_marker) != 1 or template.count(manifest_line) != 1:
        raise ValueError('baseline runtime placeholders drifted')
    text = template.replace(submission_marker, encoded, 1)
    text = text.replace(manifest_line, f'HOLDOUT_MANIFEST_JSON = {json.dumps(manifest, sort_keys=True)!r}', 1)
    compile(text, 'topology_single_root_runtime.py', 'exec')
    return text


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', type=Path, default=Path('.'))
    ap.add_argument('--kernel-dir', type=Path, required=True)
    ap.add_argument('--kernel-ref', required=True)
    ap.add_argument('--manifest', type=Path, required=True)
    args = ap.parse_args()

    repo = args.repo.resolve()
    manifest = json.loads(args.manifest.read_text(encoding='utf-8'))
    if manifest.get('version') != 'verifier-lora-v0':
        raise SystemExit('manifest version must match baseline runtime contract')
    holdout = manifest.get('holdout')
    if not isinstance(holdout, list) or not holdout:
        raise SystemExit('manifest holdout must be non-empty')
    ids = [str(x.get('instance_id') or '') for x in holdout]
    if len(ids) != len(set(ids)) or any(not x for x in ids):
        raise SystemExit('manifest task IDs must be unique and non-empty')

    payload = build_candidate_payload(repo / 'submission')
    template = (repo / 'kaggle' / 'verifier_baseline_runtime.py').read_text(encoding='utf-8')
    rendered = render_runtime(template, payload, manifest)

    args.kernel_dir.mkdir(parents=True, exist_ok=True)
    (args.kernel_dir / 'topology_single_root_runtime.py').write_text(rendered, encoding='utf-8')
    metadata = {
        'id': args.kernel_ref,
        'title': args.kernel_ref.split('/', 1)[1],
        'code_file': 'topology_single_root_runtime.py',
        'language': 'python',
        'kernel_type': 'script',
        'is_private': True,
        'enable_gpu': True,
        'enable_tpu': False,
        'enable_internet': False,
        'machine_shape': 'NvidiaL4',
        'docker_image': 'gcr.io/kaggle-private-byod/python@sha256:37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461',
        'dataset_sources': ['metric/gemma-4-developer-agent-wheelhouse'],
        'competition_sources': ['gemma-4-developer-agent'],
        'kernel_sources': [],
        'model_sources': ['google/gemma-4/Other/gemma-4-e4b-it-qat-w4a16-ct/2'],
    }
    (args.kernel_dir / 'kernel-metadata.json').write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')
    print('topology_candidate_tasks=', ids)
    print('topology_candidate_submission_files=', sorted(payload))
    print('sampling_and_budget_frozen=true')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
