# Verifier LoRA v0 training-trace harvest audit — 2026-11-01

## Evidence boundary

This audit uses only the frozen **training-side** trace harvest. It does not inspect blind task text, blind reference patches, blind base traces, or blind task-level outcomes.

Source evidence:

- GitHub Actions run: `41281236175`
- artifact: `gemma4-verifier-training-trace-harvest-v0-evidence`
- artifact ID: `13074443459`
- artifact digest: `sha256:c1e303062b7b2588dacfdf4519aef2957d9980e61ad1e231701ae0f8087bf765`
- model: `gemma-4-e4b-it-qat-w4a16-ct`
- requested/completed: `18/18`
- resolved: `2/18` (`requests_6644`, `rich_3882`)

The artifact contains the full evaluator trace JSON for every frozen training task, including exact verifier tool-call arguments and tool observations. A new harvest is therefore **not** required merely to recover tool-level supervision evidence.

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

The only clearly targeted pytest command in the harvest was `pytest -v tests/test_syntax.py` on `rich_3772`; it passed before submission. The official final evaluator nevertheless marked `rich_3772` unresolved (`test_exit_code=1`). This is direct evidence that a local targeted pass alone is not a sufficient positive label.

For the 10 verifier-side submissions:

- 1 followed a passing targeted pytest (`rich_3772`), but the final evaluator still failed it;
- 2 had no verifier-side pytest before submit (`fastapi_14258`, `fastapi_14479`);
- 7 followed a broad pytest command that returned an error status.

Those seven broad-test errors are **not automatically task-relevant failures**: several repositories have environment/dependency collection failures. They are evidence that the raw trajectory is not a trustworthy positive label, not proof that every corresponding submission was semantically wrong. Conversely, the two final resolved tasks (`requests_6644`, `rich_3882`) also contain verifier behavior that should not be imitated wholesale.

## Executable curation audit

The branch now contains two explicit gates:

- `scripts/extract_verifier_supervision_candidates.py` faithfully extracts verifier-only tool arguments/results from full training traces, marks every record `approved: false`, attaches behavioral audit flags, and requires the final evaluator outcome before suggesting any `verified_submit` positive;
- `scripts/build_verifier_sft.py` rejects unapproved/raw records, blind or non-training IDs, broad pytest positives, submit-after-failure positives, multiple repairs, and missing targeted/final verification evidence.

Tests cover both contracts. The initial extractor implementation passed GitHub Actions run `41290607206`. A real-trace counterexample (`rich_3772`) then exposed the missing evaluator-outcome gate; that correction passed GitHub Actions run `41290841503`.

Applying the corrected extractor audit to all 18 frozen training traces gives:

| Audit flag | Tasks |
|---|---:|
| no targeted pytest | 17/18 |
| final evaluator unresolved | 16/18 |
| broad pytest present | 11/18 |
| missing initial diff inspection | 8/18 |
| submit after latest failing test | 7/18 |
| no verifier tool steps | 5/18 |
| multiple successful verifier repairs | 3/18 |
| targeted-pass submit but missing final diff check | 1/18 |

**Corrected positive-suggestion count: 0/18.**

`rich_3772` reaches the weak behavioral state "targeted pytest passed before submit", but its final evaluator outcome is unresolved. The extractor therefore no longer suggests it as `verified_submit`. None of the 18 raw trajectories is directly approvable as positive SFT supervision under v0.

This is a supervision-quality blocker, not a trace-capture blocker.

## VERDICT

**DO NOT use the raw base-verifier trajectories as positive SFT targets by default.**

The harvest is useful as:

1. behavior/failure evidence;
2. state/context for constructing corrected training examples;
3. a source of controlled negatives;
4. provenance for deciding which additional training-only verification traces are worth generating.

It is not a ready-made imitation dataset. Directly distilling it would teach the exact behaviors v0 is supposed to reduce: broad verification, unnecessary verifier edits, weak submit gating, and locally plausible but globally incorrect acceptance.

## Dataset-builder contract implied by this audit

For verifier LoRA v0, every SFT target must be an **approved training-only target**, not merely a verifier-authored turn.

Preferred positive sources are now:

1. training-task gold-patch verification trajectories with a task-relevant verification gate and final evaluator-consistent outcome;
2. deliberately corrected state transitions derived from training-only negative states;
3. any future base trajectory only after it independently passes both behavioral and final-evaluator gates.

Raw unresolved trajectories may provide prompts/state and negative evidence, but their bad actions must never be copied as the assistant target simply because they came from the base verifier.

The builder must reject blind IDs and record provenance/approval for every emitted example.

## Interpretation

This strengthens, rather than weakens, the verifier-LoRA hypothesis as a **behavioral falsification test**: the observed verifier has a real discipline problem. It does not establish that fixing that behavior will materially raise resolved count, because five training tasks never reached the verifier and many unresolved tasks may arrive with a fundamentally wrong coder patch.

Do not start adapter training until both conditions hold:

1. the independent blind evaluation set is gold-control eligible, frozen, and excluded from all training sources;
2. a non-empty approved supervision dataset passes the SFT builder contract.
