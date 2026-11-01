# Verifier LoRA v0 deterministic SFT teacher — 2026-11-01

## Verdict

**Task 4 supervision gate: PASS.**

A training-only deterministic teacher run produced a small contract-checked verifier SFT dataset without using blind task traces or persisted solution patches.

## Execution evidence

- GitHub Actions run: `41308606160`
- Source commit: `82ed6b813d1ac53aeceb8b670629a9a751019afb`
- Artifact: `gemma4-verifier-sft-teacher-v0-evidence`
- Artifact ID: `13084786774`
- Artifact digest: `sha256:bd60e357686f52cf59aa505c5d5a8667d1aaf5622ed516b7b1db66bc8d126593`
- Teacher status: `completed`
- Requested tasks: `6`
- Approved positive examples: `5`
- Model/runtime base: `gemma-4-e4b-it-qat-w4a16-ct`
- Visible GPUs: `4`
- Tensor parallel size: `4`

## Approved training-only examples

1. `fastapi_14479`
2. `rich_3718`
3. `rich_3882`
4. `rich_3953`
5. `rich_4006`

Each approved example has exactly this verifier trajectory:

1. `run_command`: `git diff --check && git diff`
2. `run_command`: frozen task-specific targeted pytest gate
3. `run_command`: `git diff --check && git diff`
4. `submit_patch`

For all five approved examples:

- pre-diff exit code = `0`;
- targeted-test exit code = `0`;
- final-diff exit code = `0`;
- pre-diff is non-empty;
- final-diff is non-empty;
- pre-diff and final-diff are byte-for-byte identical.

Observed diff-output lengths in characters:

- `fastapi_14479`: `525`
- `rich_3718`: `1234`
- `rich_3882`: `503`
- `rich_3953`: `2124`
- `rich_4006`: `4088`

This post-hoc audit also satisfies the stricter stable/non-empty-diff guard added after the run. The current helper now enforces that guard before assigning `verified_submit`.

## Rejected case

`requests_6644` was **not** approved.

- pre-diff exit code = `0`
- targeted-test exit code = `4`
- final-diff exit code = `0`
- diff stayed non-empty and unchanged
- audit flag: `failed_targeted_test`

It is excluded from positive SFT.

## SFT output audit

`verifier-sft-v0.jsonl` contains exactly `5` unique examples, one per approved task.

All five rows were emitted through `scripts/build_verifier_sft.py` and contain the expected four tool calls in order:

`run_command → run_command → run_command → submit_patch`

A recursive artifact audit found no fields named:

- `reference_patch`
- `reference_solution`
- `gold_patch`
- `solution_patch`
- `test_patch`

The raw artifact is intentionally not committed to the repository. Only this metadata/evidence summary is durable repo state.

## Boundary

This is **training supervision evidence**, not evaluation evidence. It must not be used to claim task-resolution improvement.

The independent blind reservation remains frozen separately in `docs/evaluation/verifier-lora-blind-reservation-v0.json`. Blind task-level failure traces and blind reference patches remain off-limits until the adapter is frozen.

## Next gate

Task 5 may now implement one verifier-only PEFT/TRL LoRA training run with the already-frozen configuration:

- base: `google/gemma-4-E4B-it-qat-q4_0-unquantized`
- rank: `8`
- alpha: `16`
- dropout: `0.05`
- adapter only
- no hyperparameter sweep

Training loss is not a promotion metric.
