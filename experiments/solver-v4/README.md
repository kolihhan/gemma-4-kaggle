## Delivery checkpoint — 2026-11-10

**Engineering COMPLETE (not research efficacy):** [official CPU mechanism Actions 42847735843](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42847735843) and [full immutable official preflight Actions 42848898816](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42848898816) both **SUCCESS**. Exact V4 archive SHA-256: `3e56add0b7a94d81e46bff35326df314459e8a8fb3c2e80e68691222809cc9bc`. The standard V2/31B native tools/sampling are unchanged from V3-R; same 5-min/28-call budget. The new test is locked and executed through official ADK-injected CodeExecutor with synthetic no-inference LLM, pytest fail→edit→pytest pass. A full CPU Kaggle Notebook builder was prepared but **not uploaded or scored**.

**Quota gate:** [authenticated Kaggle Action 42848511113](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42848511113) reported `allowed_now=0`, `num_today=1`, no active submissions. No new official submission attempted. The manual-only `solver-v4-cgr-manual-official-once.yml` workflow requires explicit `workflow_dispatch.submit_official=true` and quota to push and submit once. Push-triggered preflight is not a submission. Real 31B tool uptake and independent resolution **UNKNOWN**. Best scored Public **0.18** is unrelated V2 Toolcap60.

---
# Solver V4-CGR — Counterexample-Guided Repair

**Status:** New unscored research candidate, *not* a competitive breakthrough yet.
Current verified Kaggle Public best: **0.18**, attributed to V2 Toolcap60 SafeTime5,
official submission **58183466**; V4 has no scored submission.

## Hypothesis and prior art

Old development E4B traces show 12/17 terminal attempts with nonempty but
unresolved patches; of 13 recognized test calls, 12 returned nonzero exit
codes (some may be unrelated dependency/collection failures). This suggests
a limitation in issue semantics and repair feedback, but it is **not** a 31B
failure-rate estimate. The 31B matched blind denominator remains unmeasured
because an existing private Kaggle model kernel is QUEUED.

**H1:** Testing only existing repository tests often misses the reported
behavior. Give the single 31B coder the ability to turn an *observed issue
contract* into one runnable, *model-authored* counterexample and require the
same exact test to fail before repair and pass after. This could catch wrong
root-cause patches that pass unrelated existing tests.

This idea is **not novel**: the open-source Agentless project already uses
generated reproduction tests for patch selection. Our candidate is one
budget-bounded adaptation to the competition's restricted offline ADK Skill
runtime, not a claim to invent counterexample-guided repair.

## Actual new capability

- Reuses the exact frozen V3-R root Gemma 4 31B model, native tools,
  sampling and **5 minutes / 28 calls / 80 turns**.
- Adds one script to the existing official `repair-witness` Skill:
  `scripts/counterexample.py`. There is no new model, LoRA, arbitrary
  ToolRegistry callback, training, or multi-agent hierarchy.
- BEFORE: model creates a *short, concrete pytest test_* function* from
  user Issue + observed repository API, then passes the test source via the
  official `run_skill_script` function argument. The script runs actual
  pytest in the git checkout and records the frozen test under temp state
  **outside the repository**, keyed by workspace and SHA256. A real assertion
  failure is required to count as a discriminatory baseline.
- AFTER: model edits source using native tools, passes the returned exact
  case_id back to the script. The script rejects changed tests and compares
  real test outcomes. Only original fail → final pass yields
  `counterexample_repaired`.
- Candidate must still run relevant existing tests and inspect the diff:
  a passing *self-authored* test is a **local witness**, not proof that
  the issue statement was faithfully modeled or that hidden tests pass.
- If the issue is ambiguous, the generated test's API is invented, or the
  initial test passes/blocks, the agent should abandon the generated test
  and use the original existing-test witness / source analysis instead.

**Files:** `scripts/build_solver_v4_cgr_candidate.py`,
`experiments/solver-v4/skill/scripts/counterexample.py`,
`tests/test_solver_v4_counterexample.py`,
`tests/test_build_solver_v4_cgr_candidate.py`,
`scripts/probe_solver_v4_cgr_official_executor.py`, and
`.github/workflows/solver-v4-cgr-cpu-gate.yml`.

## Falsifiers and decision gates

1. **Mechanics:** Official `swegemma` ADK loads ZIP and executes the actual
   generated-test script through its injected `AdkSandboxCodeExecutor`.
   A scripted no-inference model must exhibit genuine typed tool calls/results
   for locked before → native edit → locked after → submit. CPU mechanics only.
2. **Actual 31B uptake:** On a preregistered disjoint task that actually has a
   testable contract, 31B must **autonomously** produce a baseline-failing
   relevant witness, consume structured result, materialize a patch, and use
   the same witness for post-edit check. If missing/invalid/ignored, reject
   this intervention; don't add louder instructions.
3. **Independent correctness:** Paired blind task-level `swegemma` results
   V3-R vs V4 at the *same* 5min/28call budget. Measure actual issue
   resolution, rescues/regressions, valid counterexample uptake and aggregate
   time. Use task IDs never optimized against before. Existing E4B history
   is diagnosis only, not confirmation.
4. **Competitive outcome:** A single frozen legal official Kaggle submission
   with no timeout and Public **>0.18**; otherwise no breakthrough claim.
   Merely exceeding the historical 0.17 Budget-Fit control is insufficient.

## Strongest risk and pivot

The original issue can be underspecified (129 public tasks, median statement
about 418 characters, some multi-file or 80+ line reference patches).
Generated tests can encode a *wrong interpretation* and reward a wrong patch,
or cost so much 31B time that an otherwise valid repair is not produced.
An independently graded gain, not just a fail→pass of self-authored tests, is
required. If 31B rarely generates a valid witness, prefer a different
representation/search policy or reconsider targeted training; do not keep
decorating this Skill.

**Resources:** No user-funded training, new private GPU kernel, official
submission, raw dataset mirror, or hidden-gold access is initiated by the CPU
prototype.
