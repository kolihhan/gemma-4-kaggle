# Architecture search reset — 2026-11-09 (Gemma 4 SWE agent)

**Decision:** REOPEN end-to-end agent architecture. No assumption that Budget-Fit V2 topology, its first-edit deadline, a single Coder, its tools, its graph policy, or its prompt-only controller is optimal. V2 is a byte-pinned **control**, not a required foundation for every research candidate. The scored Recovery Reviewer v0 (ref 58112753, Public 0.13) is **not promoted** against the scored V2 (0.17); this outcome cannot isolate the reason or rule out other multi-agent designs. Do not build another Reviewer on the same evidence.

## Evidence that changes our question

1. The 17 archived E4B development tasks are not the current thinking-on 31B population. Their complete intermediate candidate histories are absent. Four empty finals and 12 unresolved nonempty finals do not identify generation-versus-selection failures for 31B.
2. Already-inspected E4B failures include: `fastapi_14448` (explicit requirement covered both path operations **and dependencies**, but the edit covered only one surface); `rich_3061` (span invariants, not only appended text styling); `rich_4079` / `rich_3105` (critical task behavior largely absent from short task title); `fastapi_14873` (three failed edit attempts and empty submission). These suggest **different** mechanisms: requirements, cross-file impact, semantic implementation, and tool materialization. They are case studies, not a 31B failure distribution.
3. The new private candidate-history observer passed 33 scripted CPU checks, including the submit-request boundary. It is an **instrument**, not evidence that candidate selection is dominant.
4. Official Kaggle scoring is issue-level pass/fail with a shared 12-hour evaluation allowance. A large architecture is allowed in research but must improve correctness **per total evaluation compute**, not merely add stages or improve local process metrics.
5. Published SWE agent work explores both staged localization/repair/validation, process-aware search, and trajectory-level learning; broad architecture ideas themselves are not novel. Any future research claim must isolate a narrower mechanism and disjoint evidence.

## Competing architectural hypotheses — deliberately non-exhaustive

| Lane | End-to-end redesign | Predicts improvement when | Falsifier / reason to reject |
| --- | --- | --- | --- |
| **A. Contract & Impact solver** (first *engineering* candidate) | Use an explicit evidence-backed behavior contract and impacted call-site/dependency map before choosing mutation scope; then implement, check requirement coverage and verify. A single root may orchestrate the stages through **actual** structured state/skills, rather than more English instructions. | Requirements are present but overlooked; edits satisfy a local symptom while missing another entry point or invariant. | The contract is mostly invented/missing, scope expands needlessly, or matched-budget resolved rate does not improve. |
| **B. Branch & Select repair search** | Isolated patch candidates/workspaces, checkpointed evidence, bounded search and test-guided choice instead of one mutable linear repair. | Independently correct candidate(s) are often generated but overwritten, not submitted, or reliably identifiable from discriminating tests. | No passing candidate appears, selectors cannot distinguish outcomes, or overhead dominates. |
| **C. Coder adaptation** | Train/finetune 31B-compatible policy (trajectory SFT/LoRA, then possibly preference/RL) on clean issue→navigation→implementation→verification behavior; test against frozen zero-training solver. | Correct patches rarely appear despite adequate source evidence; deterministic interfaces alone cannot fix repeated semantic generation errors. | Data contamination, no independent held-out transfer, verifier/generator mismatch, or training cost outweighs gains. No local training without separate explicit authorization. |
| **D. Multi-agent orchestration** | Distinct specialist roles with measured information handoff and tools (e.g. pre-implementation impact analysis), rather than an optional prompt-only recovery critic. | Specialization adds *new information* or better task decomposition than the same 31B Coder at matched budget. | No role uptake, correlated errors, or cost-adjusted performance fails vs equivalent single-Coder continuation. Reviewer v0's 0.13 is negative evidence for that specific design only. |

These options are **genuinely competing**; they need not be stacked. Reconsider graph retrieval only when it provides relationships not accessible cheaply through ordinary repo search. Maintain a simpler no-extra-architecture control.

## Preferred first architecture: A (provisional, not promoted)

```text
Task input + accessible repo evidence
   ↓
Behavior Contract — explicit requirements / missing information / no invented oracle
   ↓
Impact Map — affected entry points, callers, tests, cross-module invariants
   ↓
Solver — targeted changes with reversible worktree state
   ↓
Verifier — map checks to requirements and avoid pretending a green partial test proves all
   ↓
Finalization — precise materialized diff, budget check, submit
```

**Why A before B:** the inspected cases give concrete examples of wrong scope and missing implementation invariants, but **no observed 31B passing intermediate patch discarded**. A addresses upstream capability and may still fail; B should move up if the now-verified observer finds repeated candidate loss. **Why not rush to C/D:** added model roles and training require resources and independent evidence; neither is a permanent exclusion.

**Critical distinction:** This is not “add a planning paragraph to V2.” A serious architecture prototype must pass state/flow contracts that can be checked without a neural model: tracked requirement IDs, explicit unknown requirements, exact affected-symbol coverage, allowed tool interface, evidence provenance, pre/post mutation state, bounded work, and final patch verification. A model can decline a stage if there is no evidence. This can be a substantial rewrite of the candidate topology and tools; **not** a modification to canonical `submission/` or frozen ZIPs.

## Experiment to distinguish mechanisms, not tune Public LB

- **Baseline:** exact V2 ZIP and scorer contract, held byte-identical.
- **Population:** preregister repository-separated, exposure-clean tasks before reading treatment results; preserve the original task text (including absent details), failures and timeouts. Keep diagnostics from historically inspected E4B tasks separate from 31B confirmation.
- **Controls:** A full structured contract/impact architecture vs a minimal control with equivalent 31B model, total time/token/tool budget and source access. If multi-role, compare with a same-budget ordinary single-Coder stage.
- **Primary outcome:** independently resolved issues under the **global 12-hour** budget; include overhead and unsubmitted tasks.
- **Secondary diagnostics:** explicit requirement coverage, impacted entry-point coverage, tool-call errors, patch materialization, verifier discriminating power, per-task time, final submit attempts.
- **Competing explanations:** stronger process structure, more tokens, earlier source reads, hidden task exposure, evaluation noise, and external issue URL incompleteness.
- **Gate 1 (CPU, no model):** demonstrate exact usable state transitions and ADK/Skill compiler validity with scripted missing-requirement, multiple-entry-point, and tool-failure cases. Confirm unchanged native/budget constraints where intended; any differences are documented.
- **Gate 2 (private 31B inference):** only after Gate 1, execute a preregistered matched-budget pilot on clean tasks. One Public score cannot establish mechanism; do not infer success from CPU packaging.
- **Gate 3 (official submission):** require experimental justification and the user's express confirmation before spending a slot. No new training or submission in this decision.

## Global pivot triggers

- **Repeated incomplete multi-entrypoint repairs / overlooked explicit constraints** → prioritize A; a large implementation is justified if its independent pilot helps.
- **Passing intermediate candidates lost before submission** → elevate B instead.
- **Failure to produce correct candidates despite usable evidence** → reopen C (and train only when authorized).
- **Pre-analysis reduces incorrect edits enough to pay its time cost** → consider D specialization, but not the failed recovery-critic variant.
- **No transfer or prohibitive overhead** → reject corresponding class, preserve V2 only as fallback, and test the next strongest architecture rather than adding prompt patches.

**State:** research search space and decision contract revised. No new architecture code, 31B execution, GPU inference, training, or Kaggle submission yet. The architecture **choice** is provisional and cannot be described as a measured breakthrough.
