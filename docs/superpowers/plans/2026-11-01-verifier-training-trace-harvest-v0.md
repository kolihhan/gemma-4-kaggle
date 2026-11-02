# Verifier Training Trace Harvest v0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a deterministic, leakage-safe base-E4B training-trace harvest for verifier-only LoRA v0 without touching the frozen 9-task held-out evaluation set.

**Architecture:** Select a small training-only subset directly from `verifier-lora-split-v0.json`, using repo quotas plus bucket-round-robin stable hashing. Render that subset into a private Kaggle runtime that reuses one E4B server and the unchanged canonical coder+verifier submission, then save structured per-task results, logs, and full traces as a GitHub Actions artifact. This phase harvests behavior only; it does not construct SFT targets or train an adapter yet.

**Tech Stack:** Python 3.12, stdlib `json/hashlib/unittest`, existing SWE-gemma/adk submission runtime, Kaggle CLI, GitHub Actions.

**Spec:** `docs/design/verifier-lora-v0-2026-11-01.md`

## Global Constraints

- Base model remains `gemma-4-e4b-it-qat-w4a16-ct`.
- Canonical coder, verifier prompt, tools, sampling, topology, 5-minute budget, and 32-call budget remain unchanged.
- Training harvest may use only IDs in the current split's `train` array.
- No `holdout` or `excluded` task may enter the harvest.
- No holdout reference patch, holdout trace, or holdout verification evidence may enter training artifacts.
- v0 harvest size is exactly **18** tasks: Rich 8, FastAPI 8, Requests 2.
- Selection is deterministic and spreads each repo quota across patch-size buckets before taking a second item from a bucket.
- This phase does not train or package a LoRA adapter.

## Review Focus

1. Split drift: a changed split must fail if selected IDs are no longer train-only; covered by Task 1 real-manifest contract.
2. Small Requests pool: the selector must include both available Requests train tasks without duplicating IDs; covered by Task 1 quota test.
3. Holdout leakage: runtime/workflow must embed only the dedicated training subset manifest; covered by Tasks 1–2.
4. Multi-task runtime state: one vLLM server may be reused, but each SWE task must still get its own isolated evaluator workspace; covered by Task 2 runtime contract.
5. Infra evidence: a Kaggle error/timeout must be separated from model outcomes and still upload logs; covered by Task 3 workflow contract.

---

### Task 1: Deterministic training-only subset

**Files:**
- Create: `scripts/build_verifier_training_subset.py`
- Create: `tests/test_build_verifier_training_subset.py`
- Create: `docs/evaluation/verifier-lora-train-subset-v0.json`

**Interfaces:**
- Consumes: `docs/evaluation/verifier-lora-split-v0.json` with `train`, `holdout`, and `excluded` arrays.
- Produces: `build_training_subset(split: dict, quota: dict[str, int] | None = None) -> dict` and a manifest with `version`, `selection`, `tasks`, and `counts`.

- [ ] **Step 1: Write failing selector tests**

Test that the default quota is exactly Rich 8 / FastAPI 8 / Requests 2, IDs are unique, every selected ID comes from `split.train`, no selected ID intersects `holdout` or `excluded`, and repeated input produces byte-equivalent selection.

- [ ] **Step 2: Run selector tests and verify RED**

Run: `python -m unittest tests.test_build_verifier_training_subset -v`

Expected: FAIL because the script/function does not exist.

- [ ] **Step 3: Implement the minimal selector**

Implement deterministic per-repo bucket round-robin using bucket order `1-10`, `11-30`, `31-80`, `81+`, `0` and SHA-256 namespace `verifier-lora-v0-train-harvest:<instance_id>`.

- [ ] **Step 4: Add the real-manifest leakage contract**

Test the repository's current split directly and assert selected count 18, repo counts 8/8/2, and zero overlap with both non-training partitions.

- [ ] **Step 5: Materialize the frozen training subset**

Run: `python scripts/build_verifier_training_subset.py --input docs/evaluation/verifier-lora-split-v0.json --output docs/evaluation/verifier-lora-train-subset-v0.json`

Expected: JSON manifest with 18 deterministic training-only IDs.

- [ ] **Step 6: Commit**

Commit message: `feat: freeze verifier LoRA training trace subset`

### Task 2: Base-E4B training trace runtime

**Files:**
- Create: `kaggle/verifier_training_trace_runtime.py`
- Create: `tests/test_verifier_training_trace_runtime.py`

**Interfaces:**
- Consumes: embedded canonical `submission/` payload and embedded `verifier-lora-train-subset-v0.json`.
- Produces: `verifier_training_trace_results.json`, per-task evaluator logs, and per-task trace JSON files. Summary fields: `version`, `model`, `requested`, `completed`, `resolved`, `resolved_instance_ids`, `status`, `visible_gpus`, `tensor_parallel_size`.

- [ ] **Step 1: Write failing runtime contracts**

Require the runtime to use the base E4B model with `enable_lora=False`, reject any adapter in the embedded submission, reuse exactly one server, iterate exactly the embedded training task IDs, save full traces/logs, and never read patch/reference-solution fields.

- [ ] **Step 2: Run runtime tests and verify RED**

Run: `python -m unittest tests.test_verifier_training_trace_runtime -v`

Expected: FAIL because the runtime does not exist.

- [ ] **Step 3: Implement runtime by adapting the proven baseline runtime**

Keep evaluator semantics identical to `kaggle/verifier_baseline_runtime.py`; change only the embedded manifest type and output names. Preserve per-task isolation and structured summaries.

- [ ] **Step 4: Run runtime tests and full repo tests**

Run: `python -m unittest discover -s tests -v`

Expected: PASS.

- [ ] **Step 5: Commit**

Commit message: `feat: add verifier training trace runtime`

### Task 3: Private Kaggle harvest workflow

**Files:**
- Create: `.github/workflows/run-verifier-training-trace-harvest.yml`
- Create: `experiments/verifier-training-trace-harvest-v0-trigger.txt`
- Modify: `tests/test_verifier_training_trace_runtime.py`

**Interfaces:**
- Consumes: Task 1 frozen subset and Task 2 runtime.
- Produces: Actions artifact `gemma4-verifier-training-trace-harvest-v0-evidence` containing the structured result, kernel log, evaluator logs, and traces.

- [ ] **Step 1: Write failing workflow contract**

Require a private Nvidia L4 kernel, exact kernel metadata ID/ref consistency, base E4B model source, 7200-second Kaggle kernel timeout, 150-minute Actions timeout, structured-result assertion for all 18 selected IDs in frozen manifest order, and `if: always()` evidence upload.

- [ ] **Step 2: Run tests and verify RED**

Run: `python -m unittest tests.test_verifier_training_trace_runtime -v`

Expected: FAIL because the workflow does not exist.

- [ ] **Step 3: Implement the workflow**

Render the canonical submission and training subset into a single Kaggle script, push the private kernel, poll to a real terminal state, collect output/logs, assert the 18-task structured result, and always upload evidence.

- [ ] **Step 4: Run full repository validation**

Run: `python -m unittest discover -s tests -v`

Expected: PASS, followed by the repository's normal corpus and restore smoke checks in CI.

- [ ] **Step 5: Trigger one real harvest run**

Change only `experiments/verifier-training-trace-harvest-v0-trigger.txt` after the workflow validation is green.

- [ ] **Step 6: Classify the real run**

If Kaggle/runtime infrastructure fails, debug and rerun without interpreting it as model evidence. If it completes, freeze artifact run ID/SHA and inspect the harvested verifier traces before designing SFT conversion.

- [ ] **Step 7: Commit**

Commit message: `experiment: harvest verifier LoRA training traces`

## Self-review

- Spec coverage: this plan covers only the next self-contained phase—training-only trace collection. SFT target construction and adapter training intentionally remain separate because the correct target transformation depends on the observed training traces.
- Leakage: the selector starts from `split.train`; both tests and workflow assert zero use of held-out/excluded IDs.
- Attribution: no model, prompt, topology, sampling, or task-budget change is introduced.
- Cost: 18 tasks bound nominal agent runtime to 90 task-minutes plus one E4B server startup, small enough for a first harvest while still covering both major repositories and all remaining Requests training examples.
