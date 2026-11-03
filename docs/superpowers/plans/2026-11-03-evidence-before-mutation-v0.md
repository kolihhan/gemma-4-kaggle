# Evidence-before-mutation v0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Test whether a bounded pre-edit evidence phase improves repair correctness enough to justify its extra model-stage cost.

**Architecture:** Preserve frozen Reliability-v1 as control. Treatment uses a root evidence `LlmAgent` with no mutation/submission tools and exactly one editing coder `LlmAgent` sub-agent. The root gathers a compact behavioral witness/localization package, verifies a clean working tree, then transfers to the coder; the coder owns editing, verification, bounded repair, and submission. A root `SequentialAgent` is explicitly forbidden because the current official `google-adk 1.36.1` compaction path still raises when the root is not an `LlmAgent`.

**Tech Stack:** Existing declarative agent YAML/prompts, Python validation/analyzer scripts, pytest, GitHub Actions orchestration, private Kaggle runtime hydration.

**Spec:** `docs/design/evidence-before-mutation-v0-2026-11-03.md`

**Runtime constraint evidence:** `docs/research/current-compaction-probe-2026-11-03.md`

## Global Constraints

- Do not start implementation while Kaggle submission ref `57921371` is pending unless a later explicit repo decision changes that gate.
- Do not mutate frozen `submission/**` on `exp/reliability-v1`; implementation starts on a new experiment branch from the then-current research head.
- One major scientific variable only: pre-edit evidence placement/availability.
- Root must remain an `LlmAgent`; do **not** use a root `SequentialAgent` under the current scorer wheelhouse.
- Root evidence role must not expose `edit_file`, `write_file`, or `submit_patch`; coder is the only mutation/submission role.
- Transfer is model-controlled, so lifecycle compliance must be measured rather than assumed.
- No known-17-task promotion run, no task-specific rules, no LoRA/RL/larger-model/third-agent bundle.
- Freeze the new denominator before inspecting selected task content or traces.
- Run static/read-only checks before any Kaggle GPU/full task execution.

## Review Focus

- Evidence root mutates through `run_command` despite lacking edit/write tools.
- Root fails to transfer to coder, causing empty patches or wasted budget.
- Evidence stage hands off a broad or behaviorally irrelevant test, creating false confidence.
- Null-handoff B accidentally receives root evidence/history, invalidating the causal control.
- Added model stage increases elapsed/model cost enough to reduce resolved-per-budget.

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
- Create: `experiments/evidence-before-mutation-v0/submission/prompts/evidence.md`
- Create: `experiments/evidence-before-mutation-v0/submission/sub_agents/coder.yaml`
- Create: `experiments/evidence-before-mutation-v0/submission/prompts/coder.md`
- Reuse/copy unchanged sampling/eval config from Reliability-v1 with provenance recorded.
- Test: `tests/test_evidence_before_mutation_v0_contract.py`

**Interfaces:**
- Root `agent.yaml`: `agent_class: LlmAgent`, same frozen E4B model/sampling, evidence instruction, read/search/status plus bounded `run_command`, and exactly one coder sub-agent.
- Root has **no** `edit_file`, `write_file`, or `submit_patch`.
- Root evidence output before transfer contains: hypothesis, source location, smallest relevant witness command/result when available, falsifier, and clean-tree status.
- Coder: same E4B model/sampling, receives the original task plus root evidence/history in treatment C, and owns edit/verify/repair/submit.

- [ ] **Step 1:** Write static contract tests proving root is `LlmAgent`, root has no mutation/submission tools, exactly one coder exists, coder is the only editing/submitting role, no workflow-agent root exists, model/sampling remain frozen, and no third agent exists.
- [ ] **Step 2:** Run tests red.
- [ ] **Step 3:** Implement minimal root-evidence/coder YAML and prompts.
- [ ] **Step 4:** Add explicit zero-diff-before-transfer invariant; do not claim cryptographic read-only isolation because `run_command` can write.
- [ ] **Step 5:** Run focused tests plus current submission schema/compiler validation.
- [ ] **Step 6:** Re-run a cheap current-wheel source/static guard confirming the root-compaction assumption has not materially changed since `docs/research/current-compaction-probe-2026-11-03.md`.
- [ ] **Step 7:** Commit.

### Task 3: Extend mechanics analyzer for stage-order compliance

**Files:**
- Modify: `scripts/analyze_root_trace_mechanics.py`
- Modify: `tests/test_analyze_root_trace_mechanics.py`

**Interfaces:**
- Produces compact stage-order/mechanism metrics only; no raw problem/message/patch content in public artifacts.

- [ ] **Step 1:** Add failing synthetic tests for pre-coder mutation detection, root-to-coder transfer detection, evidence-before-mutation detection, witness reuse, and stage overhead accounting.
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
- [ ] **Step 2:** Use the smallest predeclared untouched slice sufficient to verify root evidence activity, zero pre-coder mutation, successful transfer, coder receipt/use of evidence, absence of root-compaction failure, and overhead.
- [ ] **Step 3:** Run only after Reliability-v1 terminal feedback is reconciled and current repo decision authorizes execution.
- [ ] **Step 4:** If root mutates, fails to transfer, coder does not receive evidence, or compaction fails, STOP; this is an implementation/lifecycle failure, not evidence against the scientific mechanism.
- [ ] **Step 5:** If overhead is obviously competition-prohibitive, record negative result and STOP.
- [ ] **Step 6:** Commit result.

### Task 5: Paired untouched practical A/C test and conditional causal guard

**Files:**
- Create: `.github/workflows/evidence-before-mutation-v0-paired-ab-once.yml`
- Create before execution: `experiments/evidence-before-mutation-v0-null-handoff/` as frozen B configuration.
- Create after run: `docs/evaluation/evidence-before-mutation-v0-result.md`
- Modify after durable decision: `NOW.md`

**Interfaces:**
- A practical control: exact frozen Reliability-v1 candidate.
- C treatment: root evidence `LlmAgent` -> coder `LlmAgent`, where coder can receive the evidence-stage history/handoff.
- B conditional causal control: same root evidence work, same root/coder topology/model/sampling/budget, but coder uses `include_contents: none` and receives the original task through session-state templating; it must not receive root evidence/history.
- Same untouched denominator, scorer, model family, and evaluation conditions.

- [ ] **Step 1:** Before any A/C run, freeze A/B/C definitions plus expected mechanism effect, practical promotion criterion, resource cost, and falsifiers.
- [ ] **Step 2:** Run A and C without inspecting task-level traces between arms.
- [ ] **Step 3:** Compare resolved, failing-relevant-verification rate, pre-edit witness rate, transfer rate, witness reuse, repair-after-failure, elapsed time, model/agent invocations, tool calls, patch size, and empty-patch rate.
- [ ] **Step 4:** If C does not beat A by the predeclared practical criterion, STOP; do not spend compute on B.
- [ ] **Step 5:** If C beats A, run the already-frozen B on the same denominator before inspecting task-level traces.
- [ ] **Step 6:** Only after all required arms finish, inspect residual traces to explain result.
- [ ] **Step 7:** Treat `C > A` as practical architecture evidence only. A strong evidence-before-mutation mechanism claim additionally requires C to beat B meaningfully and mechanism metrics to confirm real evidence transfer/use.
- [ ] **Step 8:** If `C ~= B > A`, attribute the gain primarily to the extra reasoning stage/context effects rather than evidence transfer; do not protect the original mechanism story.
- [ ] **Step 9:** If pre-edit evidence rises but correctness does not, RETIRE this implementation and reopen downstream/model-class/training/search hypotheses instead of adding prompt patches.
- [ ] **Step 10:** Update `NOW.md` and restriction statuses; commit.
