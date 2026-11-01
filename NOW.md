# NOW — 2026-11-01

## North star

Build a competitive, evidence-driven Gemma 4 software-engineering agent. Optimize for real task resolution, not architectural novelty. Add complexity only when controlled failures justify it.

## Current decision

**Run one controlled verifier-only E4B LoRA v0 falsification experiment.**

The canonical agent topology remains:

1. root coder `LlmAgent`, unadapted;
2. verifier `AgentTool`, owns `submit_patch` and is the only component eligible for the v0 adapter;
3. base competition variant remains `gemma-4-e4b-it-qat-w4a16-ct` for every agent.

Do not reopen the 12B path, change topology, sweep hyperparameters, or add more prompt-only policy before this controlled experiment is resolved.

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

`docs/evaluation/verifier-lora-eval-contract-v1.json` now points exactly to this frozen reservation. Blind base failure traces and blind reference patches must remain manually uninspected until the adapter is frozen.

## Training-side evidence

### Frozen trace harvest — complete

Training subset: **18 tasks**.

The base verifier trace harvest completed for all 18. Only **2/18** ultimately resolved, and none of the raw trajectories is safe to auto-approve as a positive SFT target. Raw base behavior is therefore diagnostic evidence, not the positive training dataset.

### Training gold screen — complete

Automated gold-control screening over those 18 produced:

- **12 clean** training tasks;
- **6 confounded** training tasks.

Only the clean set may source deterministic positive supervision.

### Model gold-teacher control — complete, not accepted as labels

A verifier-only model run on gold-patched clean training tasks was executed. The model still mutated/handled known-good workspaces unreliably, so its behavioral traces are not automatically treated as positive teacher targets.

## Task 4 — deterministic verifier supervision

Current direction: construct small positive verifier trajectories from **deterministic evidence**, not model self-judgment.

Frozen targeted-test source set: `docs/evaluation/verifier-lora-targeted-tests-v0.json`.

Six training-only, gold-clean cases are selected:

- `fastapi_14479` → `pytest tests/test_invalid_sequence_param.py -q`
- `requests_6644` → `pytest tests/test_adapters.py -q`
- `rich_3718` → `pytest tests/test_panel.py -q`
- `rich_3882` → `pytest tests/test_prompt.py -q`
- `rich_3953` → `pytest tests/test_cells.py -q`
- `rich_4006` → `pytest tests/test_cells.py -q`

Approval contract for each case:

1. apply the training reference patch only after the official baseline commit;
2. `git diff --check && git diff` must pass;
3. the frozen targeted pytest gate must pass;
4. final `git diff --check && git diff` must pass;
5. only then emit `verified_submit` + `submit_patch`;
6. failed evidence remains unapproved and cannot enter positive SFT.

No raw reference patch, gold patch, solution patch, or hidden `test_patch` is persisted into the SFT record.

Implementation:

- `kaggle/verifier_gold_teacher_supervision.py`
- `kaggle/verifier_sft_teacher_runtime.py`
- `scripts/render_verifier_sft_teacher.py`
- `.github/workflows/run-verifier-sft-teacher.yml`
- existing contract checker `scripts/build_verifier_sft.py`

## Current execution status

### GitHub validation

Branch `exp/verifier-lora-v0`, PR #4.

Latest durable contract change: `41a16bbb14ab37d837ec1dd011f9146c2a653cbc`.

Full repo validation run `41308873255`: **PASS**.

The suite currently runs **129 tests** plus compile/corpus/restore checks.

### Deterministic SFT teacher run

Run `41308606160` was launched from commit `82ed6b813d1ac53aeceb8b670629a9a751019afb`.

The first attempt exposed a Kaggle packaging bug: script kernels materialized only the configured `code_file`, so sibling Python helpers were not importable. The root cause was fixed by bundling the runtime and both local helper modules into one standalone Kaggle script. The replacement run passed render and push and is executing inside Kaggle.

**Do not declare Task 4 complete until its artifact is inspected.** Required evidence is a non-empty contract-checked `verifier-sft-v0.jsonl` built only from approved deterministic records.

## Task 5 gate — not started

Do not launch LoRA training until Task 4 evidence is verified.

When the gate opens, the frozen v0 training configuration is:

- base: `google/gemma-4-E4B-it-qat-q4_0-unquantized`;
- PEFT/TRL SFT;
- rank `r=8`;
- alpha `16`;
- dropout `0.05`;
- causal LM;
- save adapter only: `adapter_config.json` + `adapter_model.safetensors`;
- one run, **no hyperparameter sweep**.

The coder stays unadapted. Adapter evaluation must keep coder, topology, prompts, tools, sampling, time limits, and base family fixed.

## Stop / promotion rule

Training loss is not a promotion metric.

After one adapter is frozen, compare it against the base verifier on development diagnostics and the independent frozen blind set. Promotion requires materially better verifier behavior/resolution without unacceptable runtime/tool-call cost.

If v0 fails the frozen blind evaluation, stop v0 rather than immediately sweeping rank, epochs, learning rate, or other knobs.

## Immediate next step

1. Finish run `41308606160` and inspect the raw supervision artifact plus generated SFT JSONL.
2. If at least one clean approved example survives `build_verifier_sft.py`, record the exact approved IDs/count and freeze Task 4 evidence.
3. Only then implement/run Task 5 rank-8 verifier LoRA training.
4. Do not inspect blind task-level failure traces before the adapter is frozen.
