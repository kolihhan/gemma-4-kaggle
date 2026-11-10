# Public Gemma 4 references — forensic source comparison (2026-11-10)

## Decision

**Keep Solver V3-R as the only independently new agent mechanism under investigation.** Do **not** copy the two public notebook bundles as a claimed novel architecture or burn another competition submission. Borrow their economical `early materialize → targeted verification → preserve/submit` procedure as a behavioral constraint to be evaluated on **real model traces**, not as a verified causal gain.

## Provenance

User supplied:
- https://www.kaggle.com/code/prvsiyan/gemma-and-the-shape-of-doubt
- https://www.kaggle.com/code/bliverrigpdoge/lb-0-22-4-config-files-no-training

All code-source and archive inspections were read-only: no training, no inference, no new official submission. Evidence:
- [Kaggle public source notebooks pulled, static parsed, and our score ledger read (Actions 42773762918)](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42773762918)
- [Independent public code source inspection (Actions 42774739938)](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42774739938)
- [Exact historical high-score V32 output artifact versus current output (Actions 42775023705)](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42775023705)

## A. prvsiyan — Gemma and the Shape of Doubt

**Displayed score evidence:** Kaggle public UI showed **Best Public Score 0.20 V32**, while the latest publicly displayed version showed **0.15** (as browsed on 2026-11-10). Do not mistake the current Notebook source for the actual V32 scoring artifact.

The exact **V32 output** was independently recovered from the public versioned Kaggle kernel. Submitted ZIP SHA-256: `d92b7b6f3ea6d9ee6ac4180c0f8f55154b41d3b70385bacfd53d4aecbd2b9ab0`. The latest output ZIP was independently recovered with SHA-256 `6ff73d104725cc31deadd18787f3f55e5ce534889cec82387e3b280637d34887`; member hashes below are the meaningful comparison.

V32 output ZIP contains exactly four files:
- `agent.yaml`, 31B model `gemma-4-31b-it-qat-w4a16-ct`, nine built-in tools, including graph search tools.
- `configs/sampling.yaml`, temp 0.2, top-p 0.95, max output 8192, thinking budget 4096.
- `eval_config.yaml`, 28 tool calls / 8 task minutes / 80 turns.
- `prompts/system.md`.

**Verified four-member diff versus latest output:** the first three files are byte-identical, while `prompts/system.md` differs. V32 system prompt SHA-256 `811d013466d5a89b7e4aac44e7629c5ee73830bcdb13ff67e5f81de8b5b9c386` (6862 chars); latest prompt SHA-256 `7f8dde62578a247ffbfc1a519b712ae65849fcfae1ee70c49e0628cab74cbef6` (6323 chars). The V32 version contains an explicit **post-final-edit verification checkpoint** absent from latest. Their broad procedure budgets early localization, first source edit before tool call 12, constrained targeted testing (at most two calls), final `git diff` and `submit_patch`.

The latest Notebook is an extensive *analysis and reproduction artifact* rather than a verified new uncertainty calibration subsystem: its own code states **0 explicit confidence scores** and reports that calibration error cannot be estimated. It reproduces a prior Flexonafft prompt variant. Despite graph tools being present in YAML, the system prompt directs the model not to use them. **Do not claim a working calibrated doubt controller or a novel graph-planning agent.**

A single V32 0.20 and latest 0.15 do **not** identify the causal effect of the changed checkpoint: source, version selection, stochastic model runs and grader variance remain confounded.

## B. bliverrigpdoge — LB 0.22 | 4 config files, no training

Authenticated public Kaggle CLI pulled the latest Notebook's one source cell and parsed its **literal four-file `FILES` package**:
- `agent.yaml`: same Gemma 4 31B family, native tools incl. graph tools.
- `configs/sampling.yaml`: temp 0.2, top-p 0.95, max output 8192, thinking budget 4096.
- `eval_config.yaml`: 28 calls, 8 minutes, 80 turns.
- `prompts/system.md`: 4677 characters of direct surgical-repair policy: find relevant files quickly, implement source change promptly, run **targeted** tests and avoid broad test runs, distinguish pre-existing unrelated failures, submit patch promptly.
- No independent multi-agent runtime, LoRA adapter, training loop, verifier agent, or custom decision controller is present in the four-file archive.

**Score caveat:** `0.22` is asserted in the author's *title*, which is not itself an authenticated official scoring receipt. Public kernel-list metadata exposed the reference, title and last run, but not `bestPublicScore`; this review does not independently validate the 0.22 score. Do not use it as a rigorously controlled effect size.

## Direct implications for our Solver V3-R

| Question | Reference observation | Decision |
| --- | --- | --- |
| Does stronger leaderboard imply complex new agent? | Both packages have one root 31B coder; no trained adapter, no actual deterministic multi-agent workflow | Reject complexity-as-progress |
| Can a narrow test help repair correctness? | Both explicitly prioritize targeted testing, early edits; V32 differs in post-edit checkpoint | V3-R's real pytest witness tests a *potential* mechanism, but uptake and net issue resolutions are unproven |
| Can we adopt 8-minute limits? | Both use 8-minute cap, but our 8-minute Toolcap60 officially timed out | Do not copy budget blindly; retain the current 5-minute feasible envelope until a scored full run shows otherwise |
| Do we need graph tools? | Present in YAML; first prompt explicitly forbids calling them | Inclusion is not proof of useful graph navigation; observe actual calls |
| Are prompt-only variants a competitive breakthrough? | V32 vs latest changes only prompt; public score varies | No. Require independent disjoint task improvements, not a single leaderboard difference |
| What is still missing? | Source-grounded action selection and real model feedback consumption | Measure real `load_skill → run_skill_script → output consumed → edit/repair` in official ADK before submitting V3-R |

## Next falsifiable experiment, not another submission yet

1. **Mechanism uptake (mandatory):** On **one disjoint, preregistered 31B task** when private inference becomes available, capture native ADK function call/result types for `load_skill` and `run_skill_script`; verify model explicitly uses feedback in repair or preserves a correct edit. Existing CPU compiler tests do not satisfy this.
2. **Cost measurement:** In that same trace measure first edit index, targeted test count, wasted graph calls, and total time. Compare to the simple references' call-phase discipline without copying an 8-minute budget.
3. **Matched independent task correctness:** Only if uptake exists, compare V3-R to pinned attributed V2 at matched model and task-time. Score true independent resolutions, rescues and regressions, not patch nonemptiness.
4. **Official score:** Freeze one true new mechanism candidate, verify ZIP and complete full runner, then submit once. Do not use the two outside scores as direct evidence of causality.

**Restriction / pivot:** Current no-training rule exists to respect user GPU discipline; revisit only if comparable real traces show the 31B fails at generating adequate edits despite valid feedback. Optional Skill is not permanent: reject it if ignored or if it harms task success/time. The source research contains **no newly trained model and no new competition submission**.
