# Verifier-only E4B LoRA v0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the smallest leakage-safe verifier-only LoRA experiment around the existing E4B coder + verifier-AgentTool candidate.

**Architecture:** Keep `main/submission/` behavior unchanged while an experiment branch adds deterministic split tooling, gold-control screening, verifier-training data preparation, and a Kaggle training/evaluation path. Only the verifier receives the adapter in the final A/B; coder, topology, prompt, tools, sampling, and time limits remain fixed.

**Tech Stack:** Python 3.12, stdlib for split tooling, current `swegemma`/`adk-submission` verifier path, Hugging Face Transformers + TRL + PEFT for training, Kaggle L4 runtime.

**Spec:** `docs/design/verifier-lora-v0-2026-11-01.md`

## Global Constraints

- Base submission variant remains `gemma-4-e4b-it-qat-w4a16-ct` for every agent.
- The root coder remains unadapted in v0.
- `main/submission/` is not changed before a clean held-out win.
- The existing 10-task diagnostic sample may not enter the LoRA holdout.
- `httpx_3672` is excluded from v0 training/evaluation because its gold path is harness-confounded.
- Holdout reference patches and holdout verification evidence may never be used to build training examples.
- Change one major variable at a time.

## Review Focus

- A diagnostic/development-seen task must never appear in holdout.
- The single HTTPX task must be excluded rather than silently assigned to train/holdout.
- Small repositories must still receive the exact requested holdout quota or fail loudly.
- Split output must be deterministic across input order.
- Gold-control replacement must not cross the train/holdout boundary or leak holdout labels into training data.

---

### Task 1: Deterministic leakage-safe split manifest

**Files:**
- Create: `scripts/build_verifier_split.py`
- Create: `tests/test_build_verifier_split.py`
- Create: `docs/evaluation/verifier-lora-split-v0.json`

**Interfaces:**
- Produces: `build_split(tasks: list[dict], holdout_quota: dict[str, int], excluded_ids: set[str]) -> dict`
- Produces manifest keys: `version`, `holdout`, `train`, `excluded`, `counts`.

- [ ] **Step 1: Write failing unit tests**

Cover deterministic selection independent of input order, exact repo quotas (FastAPI 6 / Rich 4 / Requests 2 on the real corpus), patch-size-bucket spread, exclusion of all diagnostic IDs, and complete exclusion of HTTPX.

- [ ] **Step 2: Run tests and confirm RED**

Run: `python -m unittest tests.test_build_verifier_split -v`

Expected: FAIL because `scripts.build_verifier_split` does not exist.

- [ ] **Step 3: Implement `build_split(...)` and CLI**

CLI:

`python scripts/build_verifier_split.py tasks.jsonl --output docs/evaluation/verifier-lora-split-v0.json`

Selection rule: per repository, round-robin over non-empty reference-patch-size buckets; within each bucket order by SHA-256 of `verifier-lora-v0:<instance_id>`. Never use source-file order.

- [ ] **Step 4: Run focused and full repo tests**

Run:

`python -m unittest tests.test_build_verifier_split -v`

`python -m unittest discover -s tests -v`

Expected: PASS.

- [ ] **Step 5: Generate and inspect the real manifest**

Verify 12 holdout tasks, no diagnostic IDs in holdout, no HTTPX in train/holdout, and stable counts.

- [ ] **Step 6: Commit**

`git commit -am "feat: add verifier LoRA split manifest"`

### Task 2: Multi-task gold-control screening

**Files:**
- Create: `kaggle/gold_control_sweep.py`
- Create: `tests/test_gold_control_sweep.py`
- Create: `.github/workflows/run-verifier-gold-sweep.yml`

**Interfaces:**
- Consumes holdout IDs from `docs/evaluation/verifier-lora-split-v0.json`.
- Produces `/kaggle/working/verifier_gold_sweep.json` with per-task `resolved`, `test_exit_code`, error, duration, and patch hash/length only.

- [ ] **Step 1: Write failing tests**

Test manifest loading, result schema, refusal to emit raw reference patches, and task selection restricted to holdout IDs.

- [ ] **Step 2: Confirm RED**

Run: `python -m unittest tests.test_gold_control_sweep -v`.

- [ ] **Step 3: Implement sweep by generalizing the current `gold_control_runtime.py` verifier path**

Do not invoke a model. Hydrate each holdout task, pass its reference patch directly to the official verifier, and record only metadata/hash plus test-output tail.

- [ ] **Step 4: Run unit/full tests**

Expected: PASS.

- [ ] **Step 5: Run Kaggle gold sweep**

Use the current wheelhouse and competition data mount. Record clean vs confounded holdout tasks. If a task is confounded, replace it deterministically from the same repo/bucket before any adapter evaluation.

- [ ] **Step 6: Commit results metadata only**

No raw hydrated secret/test patch/reference patch is committed.

### Task 3: Base-verifier held-out baseline

**Files:**
- Create: `kaggle/verifier_baseline_runtime.py`
- Create: `docs/evaluation/verifier-lora-v0-baseline.md`

**Interfaces:**
- Consumes clean holdout manifest.
- Uses current `submission/` unchanged.
- Produces per-task resolved/test/tool/duration/patch-size diagnostics.

- [ ] **Step 1: Add a bounded multi-task runner using the same scorer/runtime path as existing smoke runs**
- [ ] **Step 2: Run the base E4B verifier on the clean held-out tasks**
- [ ] **Step 3: Record F4/F5 baseline and exact run/commit evidence**

No training begins until this baseline exists.

### Task 4: Verifier supervision dataset builder

**Files:**
- Create: `scripts/build_verifier_sft.py`
- Create: `tests/test_build_verifier_sft.py`
- Output (not necessarily committed if it contains hydrated evidence): `artifacts/verifier-sft-v0.jsonl`

**Interfaces:**
- Consumes training-split task IDs plus approved training-only traces.
- Produces Gemma 4 conversational examples with `messages` and `tools` suitable for `tokenizer.apply_chat_template(..., tools=...)` / TRL SFT.

- [ ] **Step 1: Define tests proving holdout IDs are rejected**
- [ ] **Step 2: Build examples around verifier state transitions: inspect → targeted test → evidence → repair/retest or submit**
- [ ] **Step 3: Add structural validation for tool-call names/arguments and no raw holdout evidence**
- [ ] **Step 4: Generate a small inspected v0 dataset**

### Task 5: Train rank-8 verifier adapter

**Files:**
- Create: `kaggle/train_verifier_lora.py`
- Create: `.github/workflows/run-verifier-lora-train.yml` only if CI→Kaggle handoff is still the established execution path.

**Interfaces:**
- Base: `google/gemma-4-E4B-it-qat-q4_0-unquantized`.
- Output: PEFT adapter directory with `adapter_config.json` and `adapter_model.safetensors`.

- [ ] **Step 1: Add dry-run/config validation that does not require GPU**
- [ ] **Step 2: Train `r=8`, alpha `16`, dropout `0.05` without hyperparameter sweep**
- [ ] **Step 3: Validate adapter files and loadability**
- [ ] **Step 4: Persist adapter artifact privately for experiment use**

### Task 6: Adapter-only verifier A/B

**Files:**
- Experiment branch only: copy adapter to `submission/adapters/verifier_lora_v0/`
- Experiment branch only: add `adapter: verifier_lora_v0` to `submission/sub_agents/verifier.yaml`
- Create: `docs/evaluation/verifier-lora-v0-ab.md`

**Interfaces:**
- Coder/topology/prompts/tools/sampling/time limits identical to Task 3 baseline.

- [ ] **Step 1: Run submission validation and repo tests**
- [ ] **Step 2: Run exact held-out A/B**
- [ ] **Step 3: Compare resolved count plus F4/F5 diagnostics and runtime**
- [ ] **Step 4: Promote only if held-out behavior materially improves; otherwise close the branch unmerged and record the negative result**
