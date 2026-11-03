# Evidence-before-mutation v0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Test whether forcing a bounded pre-edit evidence phase improves repair correctness enough to justify its extra model-stage cost.

**Architecture:** Preserve frozen Reliability-v1 as control. Treatment uses a deterministic `SequentialAgent` root whose first child is one pre-edit evidence `LlmAgent` and whose second child is one editing coder `LlmAgent`. The evidence agent writes a compact witness/localization package to an `output_key`; the coder runs with `include_contents: none` and consumes the original task state plus that explicit handoff, then owns editing, verification, bounded repair, and submission. Promotion uses only a newly frozen untouched paired denominator.

**Tech Stack:** Existing declarative agent YAML/prompts, Python validation/analyzer scripts, pytest, GitHub Actions orchestration, private Kaggle runtime hydration.

**Spec:** `docs/design/evidence-before-mutation-v0-2026-11-03.md`

## Global Constraints

- Do not start implementation while Kaggle submission ref `57921371` is pending unless a later explicit repo decision changes that gate.
- Do not mutate frozen `submission/**` on `exp/reliability-v1`; implementation starts on a new experiment branch from the then-current research head.
- One major scientific variable only: pre-edit evidence stage placement.
- Stage order must be structural, not model-discretionary: use a root `SequentialAgent`, not a root `LlmAgent` that may or may not invoke an `AgentTool`.
- No known-17-task promotion run, no task-specific rules, no LoRA/RL/larger-model/third-agent bundle.
- Freeze the new denominator before inspecting selected task content or traces.
- Run static/read-only checks before any Kaggle GPU/full task execution.

## Review Focus

- Evidence stage accidentally mutates via `run_command` despite lacking `edit_file`.
- Evidence agent hands off a broad or behaviorally irrelevant test, creating false confidence.
- Coder receives hidden conversation/history leakage rather than only the original task state plus the explicit evidence package.
- Added model stage increases elapsed/model cost enough to reduce resolved-per-budget.
- Paired denominator accidentally overlaps previously inspected/development tasks.

---

### Task 1: Freeze untouched paired denominator contract

**Files:**
- Create: `docs/evaluation/evidence-before-mutation-v0-denominator-contract.json`
- Create: `scripts/select_evidence_v0_denominator.py`
- Test: `tests/test_select_evidence_v0_denominator.py`

**Interfaces:**
- Consumes: fixed competition task pool available only at runtime; committed exclusion provenance.
- Produces: deterministic task IDs from `sha256(seed || instance_id)` ordering plus denominator fingerprint, without content-based selection.

- [ ] **Step 1:** Write tests proving determinism, exclusion, no duplicates, count stability, and order independence.
- [ ] **Step 2:** Run focused tests and confirm they fail before the selector exists.
- [ ] **Step 3:** Implement the minimal deterministic selector; do not inspect task problem text.
- [ ] **Step 4:** Run focused tests and `py_compile`.
- [ ] **Step 5:** Materialize only the selection rule/count/fingerprint needed for preregistration before any trace inspection.
- [ ] **Step 6:** Commit.

### Task 2: Build treatment topology without touching frozen control

**Files:**
- Create: `experiments/evidence-before-mutation-v0/submission/agent.yaml`
- Create: `experiments/evidence-before-mutation-v0/submission/sub_agents/evidence.yaml`
- Create: `experiments/evidence-before-mutation-v0/submission/prompts/evidence.md`
- Create: `experiments/evidence-before-mutation-v0/submission/sub_agents/coder.yaml`
- Create: `experiments/evidence-before-mutation-v0/submission/prompts/coder.md`
- Reuse/copy unchanged sampling/eval config from Reliability-v1 with provenance recorded.
- Test: `tests/test_evidence_before_mutation_v0_contract.py`

**Interfaces:**
- Root `agent.yaml`: `agent_class: SequentialAgent`, fixed order `evidence -> coder`; no model-discretionary delegation.
- Evidence agent: `LlmAgent`, has read/search/status plus bounded `run_command`, has no `edit_file` or `submit_patch`, and stores its final compact package in `output_key: pre_edit_evidence`.
- Evidence stage produces: hypothesis, source location, witness command/result when available, falsifier, and clean-tree status.
- Coder: `LlmAgent`, `include_contents: none`, receives `{problem_description}` and `{pre_edit_evidence}` explicitly in its instruction, and owns edit/verify/repair/submit.

- [ ] **Step 1:** Write static contract tests proving the root is `SequentialAgent`, the exact child order is evidence then coder, the evidence agent has no `edit_file`/`submit_patch`, the coder is the only editing/submitting stage, the coder uses `include_contents: none`, the coder instruction consumes the evidence `output_key`, model/sampling remain frozen, and no third agent exists.
- [ ] **Step 2:** Run tests red.
- [ ] **Step 3:** Implement the minimal root/evidence/coder YAML and prompts.
- [ ] **Step 4:** Add explicit clean-tree handoff invariant; do not claim cryptographic read-only isolation because `run_command` can write.
- [ ] **Step 5:** Run focused tests plus existing submission schema/compiler validation, including a compile check that the sequential root and both children resolve correctly.
- [ ] **Step 6:** Commit.

### Task 3: Extend mechanics analyzer for stage-order compliance

**Files:**
- Modify: `scripts/analyze_root_trace_mechanics.py`
- Modify: `tests/test_analyze_root_trace_mechanics.py`

**Interfaces:**
- Produces compact stage-order metrics only; no raw problem/message/patch content in public artifacts.

- [ ] **Step 1:** Add failing synthetic tests for pre-coder mutation detection, evidence-before-mutation detection, explicit evidence-handoff detection, witness reuse, and stage overhead accounting.
- [ ] **Step 2:** Run tests red.
- [ ] **Step 3:** Implement minimal stage-aware reduction while preserving fail-closed safe-output behavior.
- [ ] **Step 4:** Run full analyzer test file and `py_compile`.
- [ ] **Step 5:** Verify legacy Reliability-v1 trace summaries remain stable or document intentional metric-version changes.
- [ ] **Step 6:** Commit.

### Task 4: Run smallest untouched compliance smoke

**Files:**
- Create: `.github/workflows/evidence-before-mutation-v0-smoke-once.yml`
- Create after run: `docs/evaluation/evidence-before-mutation-v0-smoke-result.md`

**Interfaces:**
- Consumes: frozen denominator selector and treatment artifact.
- Produces: compact compliance/resource metrics, not promotion evidence.

- [ ] **Step 1:** Add workflow static checks and private runtime hydration; ensure no raw Competition Data or raw traces are uploaded publicly.
- [ ] **Step 2:** Use the smallest predeclared untouched slice sufficient to verify deterministic stage order, explicit evidence handoff, no pre-coder mutation, and measure overhead.
- [ ] **Step 3:** Run only after Reliability-v1 terminal feedback is reconciled and current repo decision authorizes execution.
- [ ] **Step 4:** If pre-coder mutation occurs, stage order/handoff is not instantiated, or coder history isolation fails, STOP and fix contract/mechanics before any paired A/B.
- [ ] **Step 5:** If overhead is obviously competition-prohibitive, record negative result and STOP.
- [ ] **Step 6:** Commit result.

### Task 5: Paired untouched practical A/C test and conditional causal guard

**Files:**
- Create: `.github/workflows/evidence-before-mutation-v0-paired-ab-once.yml`
- Create before execution: `experiments/evidence-before-mutation-v0-null-handoff/` as the already-frozen topology-matched B configuration described in `docs/research/evidence-before-mutation-v0-causal-identifiability-review-2026-11-03.md`.
- Create after run: `docs/evaluation/evidence-before-mutation-v0-result.md`
- Modify after durable decision: `NOW.md`

**Interfaces:**
- A practical control: exact frozen Reliability-v1 candidate.
- C treatment: exact Task-2 sequential evidence-handoff treatment.
- B conditional causal control: same evidence stage/topology as C, but coder runs with `include_contents: none` and does not receive/interpolate `pre_edit_evidence`.
- Same untouched denominator, scorer, model family, and evaluation conditions.

- [ ] **Step 1:** Before any A/C run, freeze A/B/C definitions plus the expected mechanism effect, practical promotion criterion, resource cost, and falsifiers.
- [ ] **Step 2:** Run A and C without inspecting task-level traces between arms.
- [ ] **Step 3:** Compare resolved, failing-relevant-verification rate, pre-edit witness rate, witness reuse, repair-after-failure, elapsed time, model/agent invocations, tool calls, patch size, and empty-patch rate.
- [ ] **Step 4:** If C does not beat A by the predeclared practical criterion, STOP; do not spend compute on B.
- [ ] **Step 5:** If C beats A, run the already-frozen B on the same denominator before inspecting task-level traces.
- [ ] **Step 6:** Only after all required arms finish, inspect residual traces to explain result.
- [ ] **Step 7:** Treat `C > A` as practical architecture evidence only. A strong evidence-before-mutation mechanism claim additionally requires C to beat B meaningfully and mechanism metrics to confirm real evidence transfer/use.
- [ ] **Step 8:** If `C ~= B > A`, attribute the gain primarily to topology/context partition/independent reasoning rather than evidence transfer; do not protect the original mechanism story.
- [ ] **Step 9:** If pre-edit evidence rises but correctness does not, RETIRE this implementation and reopen downstream/model-class hypotheses instead of adding prompt patches.
- [ ] **Step 10:** Update `NOW.md` and restriction statuses; commit.
