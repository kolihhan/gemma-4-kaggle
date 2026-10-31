# E4B Coder → Verifier v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the single-agent E4B diagnostic with the smallest two-stage coder→verifier experiment so only a verifier can submit a patch.

**Architecture:** A root `SequentialAgent` runs two E4B `LlmAgent`s against the same task workspace. The coder can inspect/edit/test but cannot submit; the verifier independently checks the current diff and targeted tests, may make one narrow evidence-backed repair, and exclusively owns `submit_patch`.

**Tech Stack:** `adk-submission` declarative YAML, `swegemma` harness tools, Python `unittest`, GitHub Actions/Kaggle L4 smoke path.

**Spec:** `docs/design/e4b-coder-verifier-v1.md`

## Global Constraints

- Base model remains `gemma-4-e4b-it-qat-w4a16-ct` for both LLM agents.
- Keep `submission/eval_config.yaml` unchanged: 300 s command timeout, 32 tool calls, 5 minutes, 64 turns.
- No LoRA, `write_file`, LoopAgent, third agent, or task-specific reference-patch knowledge.
- Only verifier may expose `submit_patch`.
- Change one major variable: orchestration/submit ownership.

## Review Focus

- Root YAML must compile as `SequentialAgent` with exactly two `config_path` sub-agents.
- Both child agents must receive task context via `{problem_description}` even though the root is non-LLM.
- Coder must not terminate the session via `submit_patch`.
- Verifier must inspect/test the coder’s existing workspace rather than starting a separate solution path.
- Verifier repair must remain narrow; no whole-file fallback.

---

### Task 1: Lock the sequential submit-ownership contract

**Files:**
- Modify: `tests/test_submission_layout.py`
- Test: `tests/test_submission_layout.py`

**Interfaces:**
- Consumes: current single-agent `submission/` layout.
- Produces: a failing contract for root SequentialAgent, coder/verifier files, and exclusive verifier submit ownership.

- [ ] **Step 1: Write the failing layout test** asserting root `agent_class: SequentialAgent`, exactly the coder/verifier config paths, both E4B child configs, no `write_file`, no coder `submit_patch`, verifier `submit_patch` present.
- [ ] **Step 2: Run repo validation and verify RED** — expected failure because the current root is one `LlmAgent` and child files do not exist.

### Task 2: Implement the minimal coder→verifier submission

**Files:**
- Modify: `submission/agent.yaml`
- Create: `submission/sub_agents/coder.yaml`
- Create: `submission/sub_agents/verifier.yaml`
- Create: `submission/prompts/coder.md`
- Create: `submission/prompts/verifier.md`
- Keep: `submission/configs/sampling.yaml`, `submission/eval_config.yaml`

**Interfaces:**
- Consumes: `{problem_description}`, existing shared `/workspace`, official harness tools.
- Produces: coder changes in the working tree; verifier final verified patch via `submit_patch`.

- [ ] **Step 1: Replace root config with a two-child `SequentialAgent`.**
- [ ] **Step 2: Add coder config/prompt** with bounded edit policy, targeted test requirement, no submission tool.
- [ ] **Step 3: Add verifier config/prompt** that begins from `git diff`, re-runs targeted verification, permits at most one evidence-backed narrow repair cycle, and submits only after passing verification.
- [ ] **Step 4: Run repo validation and verify GREEN** — expected all existing + new unit/static tests pass.

### Task 3: Run the same clean `rich_3278` diagnostic

**Files:**
- Modify: `.github/workflows/run-e4b-smoke.yml` comment only to trigger the connector-safe run.
- Update after evidence: `NOW.md`

**Interfaces:**
- Consumes: canonical `submission/`, existing `rich_3278` smoke runtime and gold-positive-control result.
- Produces: one comparable two-agent trace/result on the same task/model/budget.

- [ ] **Step 1: Trigger the existing private Kaggle smoke without changing task/model/budget.**
- [ ] **Step 2: Verify terminal structured result and read patch/trace evidence.** Record resolved, test exit, patch chars, tool calls, duration, and dominant failure class.
- [ ] **Step 3: Update `NOW.md`** with all four single-agent diagnostics plus this coder→verifier result and the next evidence-based decision.
