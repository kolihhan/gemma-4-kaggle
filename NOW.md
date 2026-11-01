# NOW — 2026-11-01

## North star

Build a competitive, evidence-driven Gemma 4 software-engineering agent. Optimize for real task resolution, not architectural novelty. Add complexity only when controlled failures justify it.

## Current decision

**Run one controlled verifier-only E4B LoRA v0 falsification experiment.**

The canonical agent topology remains unchanged:

1. root coder `LlmAgent`, unadapted;
2. verifier `AgentTool`, owns `submit_patch` and is the only component eligible for the v0 adapter;
3. base competition variant remains `gemma-4-e4b-it-qat-w4a16-ct` for every agent.

Do not reopen the 12B path, change topology, sweep hyperparameters, or add more prompt-only policy before this controlled experiment is resolved.

PR #4 remains an experiment/evidence branch. It still contains **no `submission/**` changes**.

## Why LoRA v0 exists

The current E4B candidate repeatedly reaches verification but still shows F4/F5 failures: broad test selection, weak use of failing evidence, repeated repair loops, and premature submission. Verifier-only LoRA is a falsification test for that behavioral bottleneck; it is **not** evidence that the verifier is the dominant cause of all unresolved tasks.

Several development failures still have fundamentally wrong or missing coder patches. Even a better verifier cannot rescue all of them.

Canonical design: `docs/design/verifier-lora-v0-2026-11-01.md`.
Implementation plan: `docs/superpowers/plans/2026-11-01-verifier-lora-v0.md`.

## Evaluation boundaries — frozen

### Development validation

The existing nine gold-clean tasks are development-seen, not blind evidence:

- Rich: 4
- FastAPI: 5
- Requests: 0

Their traces shaped the LoRA hypothesis, so they may be used only for development diagnostics.

### Independent blind reservation

`docs/evaluation/verifier-lora-blind-reservation-v0.json` is frozen at **10 tasks**:

- Rich: 4
- FastAPI: 6
- Requests: 0

No untouched Requests candidate remains in the current training-side pool because both Requests train tasks were already used by the frozen training trace harvest. Therefore v0 cannot establish Requests generalization.

`docs/evaluation/verifier-lora-eval-contract-v1.json` points exactly to this frozen reservation. The final blind IDs are disjoint from the 18-task training harvest. Blind base failure traces and blind reference patches remain manually uninspected until the adapter is frozen.

## Training-side evidence

### Frozen trace harvest — complete

Training subset: **18 tasks**.

The base verifier trace harvest completed for all 18. Only **2/18** ultimately resolved, and none of the raw trajectories is safe to auto-approve as a positive SFT target. Raw base behavior is diagnostic evidence, not the positive training dataset.

### Training gold screen — complete

Automated gold-control screening over those 18 produced:

- **12 clean** training tasks;
- **6 confounded** training tasks.

Only the clean set may source deterministic supervision.

### Model gold-teacher control — complete, not accepted as labels

A verifier-only model run on gold-patched clean training tasks was executed. The model still mutated/handled known-good workspaces unreliably, so its behavioral traces are not automatically treated as positive teacher targets.

## Task 4 — deterministic paired verifier supervision

### First deterministic dataset — mechanically successful, rejected for training

Run `41309594361` completed end-to-end and produced a contract-checked SFT JSONL.

It yielded five approved `verified_submit` examples:

- `fastapi_14479`
- `rich_3718`
- `rich_3882`
- `rich_3953`
- `rich_4006`

`requests_6644` was correctly rejected because its frozen `tests/test_adapters.py` path did not exist in the pre-fix snapshot.

**Do not train on this artifact.** It is positive-only supervision and would weakly teach “verification -> submit” without directly teaching the central F4/F5 invariant that failing relevant evidence must not be submitted.

### Paired v0 contract — implemented

For each selected training-only task, collect two deterministic states using the same bounded public regression gate:

1. **base-fail**: untouched baseline + failing regression gate -> approved `safe_stop` only when the base diff is empty/stable and the gate actually fails;
2. **gold-pass**: training reference patch + passing regression gate -> approved `verified_submit` only when the gold diff is non-empty/stable and the gate passes.

Records use separate `example_id`s:

- `<instance_id>:base-fail`
- `<instance_id>:gold-pass`

The SFT builder deduplicates by `example_id`, so one task can contribute both behavior labels.

### Frozen public behavior gates

`docs/evaluation/verifier-lora-targeted-tests-v0.json` now uses bounded public upstream regression behavior rather than assuming post-fix test files already exist in the pre-fix snapshot.

Selected tasks:

- `fastapi_14479` — targeted FastAPI regression test file;
- `requests_6644` — inline assertion for `HTTPAdapter.request_url()` trimming the excess leading slash while preserving `:h`;
- `rich_3718` — inline panel title/background ANSI assertion;
- `rich_3882` — inline `Confirm.ask` markup-disabled prompt assertion;
- `rich_3953` — inline zero-width ZWJ/control-character `cell_len` assertions;
- `rich_4006` — inline zero-width escape/grapheme assertion.

A `python -c` gate is accepted only when AST parsing finds a real `assert`; shell chaining is rejected. Broad repository pytest is still rejected as positive verification evidence.

### Current paired teacher execution

Run `41314500798` / job `124871578457` was launched from commit `311409448f43be45f55a05ab903661d4bbb57145` after the standalone Kaggle bundler was updated for paired supervision.

Render and Kaggle push both passed. The run is currently executing inside Kaggle.

Required Task-4 acceptance evidence:

- exactly 12 audit records, two per target;
- all six `:gold-pass` examples approved;
- at least one genuinely failing `:base-fail` example approved as `safe_stop`;
- no blind IDs or hidden `test_patch` content;
- non-empty contract-checked `verifier-sft-v0.jsonl` containing both `safe_stop` and `verified_submit`.

If any gold-pass gate fails, fix the public regression gate before training. Do not weaken the approval contract.

## Task 5 — trainer implementation ready, execution still gated

`kaggle/train_verifier_lora.py` is implemented for the paired dataset but **training has not been launched**.

Dataset contract:

- all six frozen targets must have exactly one approved `:gold-pass` / `verified_submit` example;
- at least one approved `:base-fail` / `safe_stop` example must exist;
- examples are unique by `example_id`;
- unknown IDs, missing gold coverage, duplicate examples, wrong labels/sources, or forbidden solution fields fail closed;
- token-length preflight is keyed by `example_id` and aborts instead of truncating.

Frozen training configuration remains:

- base: `google/gemma-4-E4B-it-qat-q4_0-unquantized`;
- PEFT/TRL SFT;
- rank `r=8`;
- alpha `16`;
- dropout `0.05`;
- learning rate `1e-4`;
- 3 epochs;
- seed `42`;
- max length `4096` with no silent truncation;
- text-decoder LoRA targets only;
- save adapter only: `adapter_config.json` + `adapter_model.safetensors`;
- one run, **no hyperparameter sweep**.

Latest full repo validation after the paired trainer update: run `41314790821` — **PASS**.

Do not create/trigger the training execution workflow against an old teacher artifact. Lock the exact accepted paired-teacher run/artifact first.

## Stop / promotion rule

Training loss is not a promotion metric.

After one adapter is frozen, compare it against the base verifier with coder, topology, prompts, tools, sampling, time limits, and base family fixed. Use development diagnostics plus the independent frozen blind reservation.

Promotion requires materially better verifier behavior/resolution without unacceptable runtime/tool-call cost.

If v0 fails the frozen blind evaluation, stop v0 rather than immediately sweeping rank, epochs, learning rate, or other knobs.

## Immediate next step

1. Finish paired teacher run `41314500798` and inspect every base-fail/gold-pass record plus generated SFT JSONL.
2. Require six approved gold-pass examples and at least one approved safe-stop example; otherwise repair the deterministic public gate, not the label threshold.
3. Freeze the exact accepted teacher artifact/run ID.
4. Only then wire and launch the single rank-8 LoRA training run.
5. Do not inspect blind task-level failure traces before the adapter is frozen.
