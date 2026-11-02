# NOW — 2026-11-01

## North star

Build a competitive, evidence-driven Gemma 4 software-engineering agent. Optimize for real task resolution, not architectural novelty. Add complexity only when controlled failures justify it.

## Current decision

**Run one controlled verifier-only E4B LoRA v0 falsification experiment.**

Canonical topology remains unchanged:

1. root coder `LlmAgent`, unadapted;
2. verifier `AgentTool`, owns `submit_patch` and is the only component eligible for the v0 adapter;
3. base competition variant remains `gemma-4-e4b-it-qat-w4a16-ct` for every agent.

Do not reopen the 12B path, change topology, sweep hyperparameters, or add more prompt-only policy before this experiment is resolved.

PR #4 remains an experiment/evidence branch. It contains **no `submission/**` changes**.

## Why LoRA v0 exists

The E4B candidate repeatedly reaches verification but still shows F4/F5 failures: broad test selection, weak use of failing evidence, repeated repair loops, and premature submission. Verifier-only LoRA is a falsification test for that behavioral bottleneck; it is not evidence that the verifier explains every unresolved task.

Canonical design: `docs/design/verifier-lora-v0-2026-11-01.md`.
Implementation plan: `docs/superpowers/plans/2026-11-01-verifier-lora-v0.md`.

## Frozen evaluation boundaries

### Development validation

Existing nine gold-clean development-seen tasks:

- Rich: 4
- FastAPI: 5
- Requests: 0

These traces shaped the hypothesis and are not blind evidence.

### Independent blind reservation

`docs/evaluation/verifier-lora-blind-reservation-v0.json` is frozen at 10 tasks:

- Rich: 4
- FastAPI: 6
- Requests: 0

No untouched Requests candidate remains in the current training-side pool, so v0 cannot establish Requests generalization.

`docs/evaluation/verifier-lora-eval-contract-v1.json` points to this reservation. Blind task-level failure traces and blind reference patches remain manually uninspected until the adapter is frozen.

## Training-side evidence

- Frozen trace harvest: **18 tasks**, only **2/18** resolved; raw base trajectories are diagnostic only.
- Training gold screen: **12 clean / 6 confounded**; only the clean set may source deterministic supervision.
- Model gold-teacher control: executed but rejected as labels because the model still mutated/handled known-good workspaces unreliably.

## Task 4 — deterministic paired verifier supervision

### Positive-only artifact: mechanically valid, rejected for training

A previous deterministic run produced five approved `verified_submit` examples:

- `fastapi_14479`
- `rich_3718`
- `rich_3882`
- `rich_3953`
- `rich_4006`

`requests_6644` failed its old frozen gate because `tests/test_adapters.py` did not exist in that pre-fix snapshot.

**Do not train on this artifact.** Positive-only supervision does not directly teach the central F4/F5 invariant that failing relevant evidence must not be submitted.

### Paired contract

For each selected training-only task, collect two deterministic states with the same bounded public regression gate:

1. `<instance_id>:base-fail` — untouched baseline + genuinely failing relevant gate -> `safe_stop` only when the workspace stays clean/stable;
2. `<instance_id>:gold-pass` — training reference patch + passing relevant gate -> `verified_submit` only when the gold diff is non-empty/stable.

The SFT builder deduplicates by `example_id`, so one task may contribute both labels.

### Frozen public behavior gates

`docs/evaluation/verifier-lora-targeted-tests-v0.json` contains six training-only, gold-clean targets:

- `fastapi_14479` — targeted FastAPI regression test file;
- `requests_6644` — inline assertion for `HTTPAdapter.request_url()` trimming the excess leading slash while preserving `:h`;
- `rich_3718` — panel title/background ANSI assertion;
- `rich_3882` — `Confirm.ask` markup-disabled prompt assertion;
- `rich_3953` — zero-width ZWJ/control-character `cell_len` assertions;
- `rich_4006` — zero-width escape/grapheme assertion.

Inline `python -c` gates are accepted only when AST parsing finds a real `assert`; broad repository pytest remains rejected as positive verification evidence.

### Stale-kernel race discovered and closed

Run `41314500798` / job `124871578457` was launched from commit `311409448f43be45f55a05ab903661d4bbb57145` with paired runtime code, but the fixed Kaggle kernel slug allowed a stale earlier execution to be collected.

Evidence artifact `13087455809` contained only six old `:gold-pass` records (5 approved) rather than the required 12 paired records. The GitHub assertion correctly failed and `verifier-sft-v0.jsonl` was not built.

That artifact is **rejected** and must never source training.

Root cause: canceled/replaced GitHub teacher runs could leave Kaggle executions alive under the same `KERNEL_REF`, so a later workflow could observe/download another version's terminal output.

Fixes now on branch:

- runtime emits `teacher_build_id` and refuses an unrendered placeholder;
- workflow renders `TEACHER_BUILD_ID=${{ github.sha }}` and verifies it in the downloaded result;
- every teacher run uses a unique Kaggle kernel slug: `gemma-4-verifier-sft-teacher-v0-${{ github.run_id }}`;
- Kaggle push failures are fail-closed;
- regression tests lock both build provenance and unique kernel identity.

### Current authoritative Task-4 run

**Run `41323128858`** was launched from commit `688db814d5caa0f300660cbe880cb8f322a78942` after the stale-kernel fix.

Current state at this breakpoint:

- render: PASS;
- unique Kaggle kernel push: PASS;
- Kaggle execution/poll: IN PROGRESS;
- artifact assertion/build: not yet reached.

Later branch-only regression-test commit `96f01a8adbe234dab3792664855fff9c7522270a` does not change the running teacher payload and did not trigger another teacher run.

Task-4 acceptance requires:

- exactly 12 audit records, two per target;
- all six `:gold-pass` examples approved;
- at least one genuinely failing `:base-fail` example approved as `safe_stop`;
- no blind IDs or hidden `test_patch` content;
- non-empty contract-checked `verifier-sft-v0.jsonl` containing both `safe_stop` and `verified_submit`;
- `teacher_build_id == 688db814d5caa0f300660cbe880cb8f322a78942` for this run.

If any gold-pass gate fails, repair the public regression gate. Do not weaken the approval contract.

## Task 5 — trainer implementation ready, execution gated

`kaggle/train_verifier_lora.py` is implemented for the paired dataset. **Training has not been launched and no training workflow exists yet.**

Dataset contract:

- all six frozen targets must have exactly one approved `:gold-pass` / `verified_submit` example;
- at least one approved `:base-fail` / `safe_stop` example must exist;
- examples are unique by `example_id`;
- unknown IDs, missing gold coverage, duplicate examples, wrong labels/sources, or forbidden solution fields fail closed;
- token-length preflight is keyed by `example_id` and aborts instead of truncating.

Frozen training config:

- base: `google/gemma-4-E4B-it-qat-q4_0-unquantized`;
- PEFT/TRL SFT;
- `r=8`, alpha `16`, dropout `0.05`;
- learning rate `1e-4`;
- 3 epochs;
- seed `42`;
- max length `4096`, no silent truncation;
- exact text-decoder LoRA targets under `model.language_model.layers.*` only;
- save adapter only: `adapter_config.json` + `adapter_model.safetensors`;
- one run, no hyperparameter sweep.

Current Transformers maps `gemma4` through `AutoModelForCausalLM` to `Gemma4ForConditionalGeneration`; the trainer validates that class and filters exact text-decoder module names before constructing `LoraConfig`.

Latest full repo validation: run `41323312996` on commit `96f01a8adbe234dab3792664855fff9c7522270a` — **PASS**.

Do not wire or trigger Task 5 against any old teacher artifact. Lock the exact accepted paired teacher run/artifact first.

## Stop / promotion rule

Training loss is not a promotion metric.

After one adapter is frozen, compare it against the base verifier with coder, topology, prompts, tools, sampling, time limits, and base family fixed. Use development diagnostics plus the independent frozen blind reservation.

Promotion requires materially better verifier behavior/resolution without unacceptable runtime/tool-call cost.

If v0 fails the frozen blind evaluation, stop v0 rather than immediately sweeping rank, epochs, learning rate, or other knobs.

## Immediate next step

1. Finish and inspect authoritative paired teacher run `41323128858`.
2. Require six approved gold-pass examples and at least one approved safe-stop example.
3. Freeze the accepted run/artifact ID and dataset hash.
4. Only then wire and launch the single rank-8 LoRA training run.
5. Do not inspect blind task-level failure traces before the adapter is frozen.
