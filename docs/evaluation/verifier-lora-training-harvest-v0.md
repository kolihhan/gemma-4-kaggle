# Verifier LoRA v0 training-trace harvest audit — 2026-11-01

## Evidence boundary

This audit uses only the frozen **training-side** trace harvest. It does not inspect blind task text, blind reference patches, blind base traces, or blind task-level outcomes.

Source evidence:

- GitHub Actions run: `41281236175`
- artifact: `gemma4-verifier-training-trace-harvest-v0-evidence`
- artifact digest: `sha256:c1e303062b7b2588dacfdf4519aef2957d9980e61ad1e231701ae0f8087bf765`
- model: `gemma-4-e4b-it-qat-w4a16-ct`
- requested/completed: `18/18`
- resolved: `2/18` (`requests_6644`, `rich_3882`)

## FACTS

Across the 18 harvested ATIF traces:

| Metric | Observed |
|---|---:|
| tasks completed | 18/18 |
| resolved by final evaluator | 2/18 |
| tasks that reached verifier | 13/18 |
| tasks that never reached verifier | 5/18 |
| verifier invocations | 16 |
| verifier `run_command` calls | 39 |
| broad `pytest` / `pytest -v` calls | 20 |
| targeted pytest calls | 1 |
| verifier `edit_file` calls | 23 |
| verifier `submit_patch` calls | 10 |
| verifier-reached tasks with no submit | 3 |

The only clearly targeted pytest command in the harvest was `pytest -v tests/test_syntax.py` on `rich_3772`; it passed before submission. Most verifier test activity was broad `pytest`.

For the 10 verifier-side submissions:

- 1 followed a passing targeted pytest (`rich_3772`);
- 2 had no verifier-side pytest before submit (`fastapi_14258`, `fastapi_14479`);
- 7 followed a broad pytest command that returned an error status.

Those seven broad-test errors are **not automatically task-relevant failures**: several repositories have environment/dependency collection failures. They are evidence that the raw trajectory is not a trustworthy positive label, not proof that every corresponding submission was semantically wrong.

## VERDICT

**DO NOT use the raw base-verifier trajectories as positive SFT targets by default.**

The harvest is useful as:

1. behavior/failure evidence;
2. state/context for constructing corrected training examples;
3. a source of controlled negatives;
4. a source of rare candidate-positive trajectories only after explicit evidence checks.

It is not a ready-made imitation dataset. Directly distilling it would teach the exact behaviors v0 is supposed to reduce: broad verification, unnecessary verifier edits, and weak submit gating.

## Dataset-builder contract implied by this audit

For verifier LoRA v0, every SFT target must be an **approved training-only target**, not merely a verifier-authored turn.

Preferred positive sources remain:

1. training-task trajectories with a task-relevant verification gate that passes before submit;
2. gold-patch verification trajectories generated on training tasks only;
3. deliberately corrected state transitions derived from training-only negative states.

Raw unresolved trajectories may provide prompts/state and negative evidence, but their bad actions must never be copied as the assistant target simply because they came from the base verifier.

The builder must reject blind IDs and record provenance/approval for every emitted example.

## Interpretation

This strengthens, rather than weakens, the verifier-LoRA hypothesis as a **behavioral falsification test**: the observed verifier has a real discipline problem. It does not establish that fixing that behavior will materially raise resolved count, because five training tasks never reached the verifier and many unresolved tasks may arrive with a fundamentally wrong coder patch.

Do not start adapter training until the independent blind evaluation set is gold-control eligible, frozen, and excluded from all training sources.
