## Authenticated competitive checkpoint — 0.18 Public (2026-11-10)

[Read-only authenticated Kaggle ledger, Actions 42845134459](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42845134459) confirms new **Public best `0.18`**, submission `58183466`, `toolcap60-safetime5-v1-20261110`, COMPLETE. This is the 5-minute **V2 Toolcap60** budget variant and **not** the V3-R mechanism. The old attributed V2 control ref `58019162` scored `0.17`. The older 8-minute Toolcap60 ref `58164176` is COMPLETE with blank score.

**Updated success definition:** Any eventual V3-R public claim must exceed **0.18**, not 0.17; prove V3-R mechanism uptake on actual 31B and compare on disjoint independent tasks with matched 5min/28-call control, while acknowledging 5min/60-call 0.18 official best is a different budget. At 2026-11-10 15:31 UTC the old private 31B pilot remained QUEUED; no new expensive model run or V3 official submission is authorized based on CPU scripted proof alone.

---
## M1 COMPLETE — official injected CodeExecutor + real ADK tool-event integration (2026-11-10)

**Passed:** [Actions 42785080724](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42785080724) **SUCCESS**. This is more than ZIP compilation: the exact V3-R research ZIP was compiled with the **official** `swegemma.harness.agent_runner.AdkSandboxCodeExecutor` attached to `compile_submission`, and a no-inference scripted `BaseLlm` drove the real `google.adk.runners.Runner` with actual tools through an isolated synthetic git checkout. Every step emitted both `FunctionCall` and `FunctionResponse`:

`load_skill → run_skill_script(before) → edit_file → run_skill_script(after) → submit_patch`.

The actual packaged `skills/repair-witness/scripts/witness.py` invoked real pytest: **before** returned `status=fail, comparison=baseline_recorded`, the registered native `edit_file` changed one synthetic source line, **after** returned `status=pass, comparison=repair_demonstrated`, and the synthetic model read that structured feedback before it called `submit_patch`. **12 focused tests pass**, official ADK / `swegemma` compilation and limits pass. Verifiable exact ZIP SHA256: `ae8201c0ce30daf581102ef5d22886f8a4dcebfae47236dffb02ffa6426f9b0c`.

**Real runtime bug fixed:** the official subprocess sandbox may use an isolated checkout path different from literal `/workspace`. `witness.py` now finds an actual git workspace using `SWE_WORKSPACE`, then `PWD`, then `/workspace`, then cwd. A CLI subprocess test reproducing execution from a distinct skill cwd passes. The official `swegemma` runtime source confirms it constructs `AdkSandboxCodeExecutor(sandbox=context.sandbox, ...)` and passes `code_executor` to `compile_submission` (verified in [Actions 42783433294](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42783433294)). An ordinary ADK Runner *without* that injection returns `NO_CODE_EXECUTOR`; this is expected and not representative of official scoring.

**Critical scientific boundary:** this uses a scripted model, **not** a real Gemma 4 31B model. It proves production-legal mechanics and evidence-driven conditional actions, **not** that 31B autonomously selects the witness or that issue-resolution improves. The private 31B Kaggle kernel was still `QUEUED` at 2026-11-10 08:30 UTC. No GPU inference, new Kaggle competition submission or score resulted from M1. The true verified Public best is still **0.17**. M2 must preregister a disjoint real model uptake check at matched five-minute/28-call budgets and only proceed when private Kaggle inference is available. Do not promote the V3-R ZIP as scored.

**Source:** `scripts/probe_solver_v3r_official_executor.py`, `.github/workflows/solver-v3r-cpu-gate.yml`, `tests/test_solver_v3r_witness.py`, `experiments/solver-v3/skill/scripts/witness.py`.

---

# Solver V3-R — executable pytest evidence witness (2026-11-10)

**Status: candidate IMPLEMENTED + CPU verified, NOT proven competitive, NOT officially submitted.**

## What changed and why

Existing exact, third-party Apache-2.0 Budget-Fit V2 31B control scored **0.17** Public (ref 58019162). It frequently produced nonempty patches without independently resolved issues on exposed private pilot tasks. The proposed V3-R mechanism is to provide an *actual* feedback instrument rather than simply add another verifier prompt: a model-invoked, 20-second-bounded real pytest **witness** that compares an existing targeted test before and after a workspace edit and emits structured regression/repair evidence.

- The script is **real and independently executable**: `skill/scripts/witness.py` executes a focused pytest subprocess and returns actual output, status, comparison, and limitations. It does **not** edit source, inspect gold/reference patches, or certify hidden issue correctness.
- The exact compiled ADK root is one 31B `LlmAgent`, with the existing native tools plus an official `SkillToolset` for `repair-witness`. No new custom ToolRegistry, user callback, second model, LoRA or training.
- The prompt explicitly requests `load_skill`/`run_skill_script` **only when an existing narrow test and sufficient budget are available**. This call is still **model-discretionary**; an optional tool's presence does not prove it was used.
- The candidate uses **5 minutes / 28 native tool calls / 80 turns**, not the 8min / 60 calls combination that previously triggered Notebook Timeout. Sampling and native tools are preserved from pinned Budget-Fit V2. The budget differs from the scored 8-minute V2 control: no isolated semantic-quality claim from comparing Public scores.

## Source and exact build

| File | Purpose |
| --- | --- |
| `experiments/solver-v3/skill/SKILL.md` | Activation and evidence semantics for one executable Skill |
| `experiments/solver-v3/skill/scripts/witness.py` | Actual pytest subprocess and before/after regression comparison |
| `scripts/build_solver_v3r_candidate.py` | Deterministic ZIP builder from byte-pinned external V2 |
| `tests/test_solver_v3r_witness.py` | Real tests: fail→pass, pass→fail, no baseline, path safety, empty suite, isolated state |
| `tests/test_build_solver_v3r_candidate.py` | Source provenance, exact model, budget, build determinism, script included |
| `scripts/verify_solver_v3r_official.py` | Official wheelhouse ADK compiler + sandbox-free synthetic ZIP script execution |
| `.github/workflows/solver-v3r-cpu-gate.yml` | One focused CPU CI execution gate |

**Verified final CPU Actions (with required load_skill-before-run_skill_script protocol)**: [42749343409](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42749343409) **SUCCESS**, 10 focused unit tests; compilation with `adk-submission==0.2.13` / `swegemma==0.2.11` accepted the ZIP, root model 31B, and displayed `SkillToolset` in compiled agent.tools. The **actual script from unpacked ZIP** ran a real synthetic pytest and reported pass. ZIP SHA256: `25e86f12c992a068cac77ae532482374be5a3dc508a55b4844869aa0241cc50d`.

**Explicitly NOT verified:** genuine 31B model chose to call `run_skill_script`; the scorer sandbox's live CodeExecutor executed it; real issue-level correctness improved; full hidden evaluation completed without timeout. Synthetic scripted tool availability/CPU tests are not substitutes for a model trace or a scored solution.

## Promotion gates

1. **Actual model uptake:** trace 31B function calls on a private, previously uninspected, correctly scoped development task; prove `run_skill_script` is called, that output is consumed, and that overhead remains acceptable. Do not infer uptake from the presence of SkillToolset. The previous optional Contract & Impact Skill's tool-call evidence was inconclusive.
2. **Valid independent resolution:** paired test against exact 31B V2 with matched **5min / 28 calls** runtime; freeze disjoint task IDs before inspecting outcomes. Count independently resolved tasks, rescues, regressions, tool usage and elapsed time. Earlier E4B 17 and 31B pilot four are *exposed*, not confirmation.
3. **Official score:** only after supported mechanism uptake and authenticity checks, stage one idempotent Kaggle official submission with an exact ZIP hash. Compare a completed score with the 0.17 best scored reference, acknowledging its 8-minute ceiling and run-to-run variance.

**Current blocker:** [authenticated status probe 42617516719](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42617516719) at **2026-11-10 03:21 UTC** reported the pre-existing private 31B kernel `kolihhan/gemma4-toolcap-31b-42609260933` still `QUEUED`. No new private 31B pilot was launched. The operational 5-minute Toolcap60 submission `58183466` remained PENDING at the last authenticated ledger check. **No new V3-R official submission was made.**

## Falsifier/pivot

If the real model never invokes this Skill, or its extra tool/pytest overhead reduces correctly resolved issues, **reject this candidate**, do not just add louder prompt instructions or another optional Reviewer. Reopen a supported alternative (single-root direct native test policy, evidence-aware Coder policy adaptation, or model-independent search/selection if evidence supports it). The previous checkpoint-first V3 proposal is historical; candidate loss is not established as the bottleneck.
