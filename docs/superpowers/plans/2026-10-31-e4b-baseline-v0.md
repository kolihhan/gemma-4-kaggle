# E4B Baseline v0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn this repository from data-mirror plumbing into a reproducible competition workspace with a verified minimal E4B baseline and diagnostic evaluation path.

**Architecture:** Keep one canonical declarative submission under `submission/`. Keep mutable competition facts in dated research docs, durable current state in `NOW.md`, corpus/evaluation evidence under `docs/evaluation/`, and large competition data in the private Release mirror rather than Git history.

**Tech Stack:** Google ADK declarative submission YAML, Gemma 4 E4B, Python 3.12 standard library tooling, GitHub Actions, Kaggle competition harness.

**Spec:** `docs/design/e4b-baseline-v0.md`

## Global Constraints

- Current candidate model: `gemma-4-e4b-it-qat-w4a16-ct`.
- One base model per submission.
- No LoRA, sub-agent, or custom skill in baseline v0.
- Use all 9 official harness tools.
- Never expose reference `patch` / `test_patch` fields to a blind agent run.
- Full competition data stays private and out of ordinary Git history.
- No performance claim without an executed scorer/harness run.

## Review Focus

- Current Kaggle model eligibility must outrank stale bundled model-list text.
- Submission includes one root agent and no accidental adapter/sub-agent complexity.
- Public sample selection must handle the single HTTPX task without inventing 12 samples.
- Mirror completion and manifest completion are separate states.
- Evaluation budget values are provisional hypotheses, not official recommendations.

---

### Task 1: Establish repository source of truth

**Files:**
- Create: `AGENTS.md`
- Create: `NOW.md`
- Create: `docs/research/competition-recon-2026-10-31.md`
- Create: `docs/design/e4b-baseline-v0.md`
- Create: `docs/evaluation/failure-taxonomy.md`
- Modify: `README.md`

**Interfaces:**
- Produces: canonical entry order, current decisions, evidence precedence, and next-test contract for all later work.

- [x] Read personal router and target repository state.
- [x] Reconcile current Kaggle model announcement with stale bundled `HARNESS_README.md`.
- [x] Record canonical repo state and baseline design.
- [ ] Rewrite README as the project entry point after baseline files exist.

### Task 2: Build and verify public corpus analyzer

**Files:**
- Create: `tests/test_analyze_tasks.py`
- Create: `scripts/analyze_tasks.py`
- Modify: `.github/workflows/validate-tools.yml`
- Create: `docs/evaluation/public-corpus-summary.md`

**Interfaces:**
- Produces: `summarize_tasks()`, `choose_sample()`, and a deterministic diagnostic sample for later experiments.

- [x] Write analyzer tests first and verify RED on missing module.
- [x] Implement minimal analyzer and verify unit-test GREEN.
- [x] Run analyzer against real `tasks.jsonl`.
- [x] Correct the false 12-task assumption; real `per_repo=3` sample is 10 tasks.
- [x] Record verified corpus summary.

### Task 3: Create minimal canonical E4B submission

**Files:**
- Create: `tests/test_submission_layout.py`
- Create: `submission/agent.yaml`
- Create: `submission/configs/sampling.yaml`
- Create: `submission/prompts/system.md`
- Create: `submission/eval_config.yaml`

**Interfaces:**
- Produces: one baseline submission directory suitable for current-harness validation and first smoke evaluation.

- [x] Write static submission contract tests and verify RED because `submission/` is absent.
- [ ] Add root E4B `LlmAgent` with all 9 official tools.
- [ ] Add sample-derived generation config and bounded provisional eval budget.
- [ ] Add concise evidence/test/repair system prompt.
- [ ] Verify all repo-tool tests GREEN.

### Task 4: Verify and harden full-data mirror finalization

**Files:**
- Modify: `.github/workflows/mirror-full-kaggle-data.yml`
- Create/update: `manifests/latest.json`
- Create/update: dated mirror manifest and Kaggle inventory.
- Update: `NOW.md`

**Interfaces:**
- Produces: reconstructable private full dataset with checksummed Release parts and a durable manifest.

- [ ] Verify all Release parts finish in `uploaded` state.
- [ ] Confirm full archive byte count and SHA-256 from mirror output.
- [ ] Recover/rebase manifest commit if the long-running job loses a non-fast-forward race with newer `main` commits.
- [ ] Patch future manifest push to tolerate concurrent main changes without launching duplicate mirror work.
- [ ] Verify `scripts/restore_full_dataset.py` can authenticate to the private repo and manifests reference every Release part.

### Task 5: First execution gate

**Files:**
- Update: `NOW.md`
- Add run record under: `docs/evaluation/` when execution exists.

**Interfaces:**
- Consumes: `submission/`, private restored data, current scorer/wheelhouse.
- Produces: first actual task result and failure classification.

- [ ] Validate E4B model acceptance with current scorer/wheelhouse.
- [ ] Run one public task end-to-end.
- [ ] If smoke succeeds mechanically, run the fixed 10-task diagnostic sample.
- [ ] Record failure classes before selecting E1 architecture changes.
