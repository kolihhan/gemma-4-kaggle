## 2026-11-10 — Research pivot: counterexample-guided repair, not additional prompt polishing

**PI decision (supersedes V3-R as the active NEW candidate):** V3-R M1 proved a working code-execution channel but merely repeats existing tests. Inspecting E4B development evidence shows many nonempty unresolved patches and frequently unsuccessful or unclear existing tests. The primary hypothesis is an **issue-to-observation gap**: the agent lacks a task-specific falsifiable behavioral witness before editing. This is not a verified diagnosis for 31B and may be false.

**New V4-CGR implementation:** [experiments/solver-v4/README.md](../../experiments/solver-v4/README.md). One Gemma 4 31B coder (same model, native tools, sampling and 5min/28call/80turn budget as V3-R) can synthesize **one** test from an observed issue API, run it before mutation using a legal ADK skill, and get deterministic `baseline_fail` evidence. The script locks test SHA outside repo and permits after-edit comparison only on the same exact test. It distinguishes fail→pass from blocked, baseline-pass or still-failing cases and returns `independent_issue_resolved=false`, `test_relevance_verified=false`. Existing tests remain regression constraints. Method is known in Agentless reproduction tests; no novelty or leaderboard gain claimed.

**Engineering gate passed:** [Actions 42847735843](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42847735843) official injected sandbox CodeExecutor used real ADK function calls/results and pytest to drive scripted failure→native edit→same-test pass→submit. V4 ZIP is SHA-pinned `3e56add0b7a94d81e46bff35326df314459e8a8fb3c2e80e68691222809cc9bc`. This proves the architecture **can execute** in the allowed tool environment, not that Gemma 31B will use it.

**Leaderboard and resource gate:** latest authenticated official best `0.18` ref `58183466` is a V2 time/tool-budget configuration, NOT this candidate. Kaggle authenticated at 2026-11-10 15:50 UTC showed `allowed_now=0`, `num_today=1`, no active submissions ([Action 42848511113](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42848511113)). Independent private 31B kernel was still queued. The V4 official one-shot workflow is **manual, not scheduled**, and its default action does not submit; do not retry or bypass quota.

**Single discriminating test:** when genuine 31B inference is available, measure whether the *real model* authors a relevant baseline-failing contract, changes a real source file, reruns the exact contract and achieves a positive independent task resolution rather than just self-consistent tests. Match 5min/28calls against V3-R for mechanistic attribution. Record tool uptake, first edit, test overhead, timeout, independent PASS/FAIL, rescues and regressions. If few valid contracts or net-negative score, **reject V4-CGR** and consider a different representation (issue-to-call-graph, tool-guided localization, or targeted model adaptation) rather than endlessly changing prompts. A successful official competition result must exceed actual best **0.18**.

---
## 2026-11-10 23:31 MYT — official competitive target reset

Authenticated read-only [Actions 42845134459](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42845134459): Kaggle official submission `58183466` (Toolcap60 SafeTime5, **V2 config variation**, not V3-R) **COMPLETE, Public `0.18`**. This supersedes `0.17` as best scored Public and raises the eventual V3-R official win requirement to **strictly above 0.18**. Prior attributed V2 31B ref `58019162` remains an accurate historical `0.17` baseline; do not rewrite its score.

**Fair experiment:** On disjoint issues measure V3-R against unchanged V2 with the **same 5-minute / 28-tool budget** for mechanism attribution; do not mistake the 5-minute/60-call `0.18` score for a matched V3-R control. A follow-up official V3-R must beat the separate overall best 0.18. The M1 official sandbox/scripted model trace and real pytest evidence mechanics have passed [Actions 42785080724](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42785080724); real Gemma 31B uptake and issue resolution remain unmeasured.

**Current blocker:** Existing private 31B Kaggle kernel `kolihhan/gemma4-toolcap-31b-42609260933` was still `QUEUED` when authenticated check ran at 15:31 UTC. Its prior GitHub pollers already terminated, providing no valid independent 31B task scores. Existing paired renderer `scripts/render_v2_toolcap_31b_pilot.py` is for V2 28-vs-60 with an 8-minute time cap and cannot itself serve as a matched V3-R M2 test without replacing both payload and budget contract. Do not duplicate GPU sessions or claim M2 started.

---
# Gemma 4 — PI Research-to-Submission Reset (2026-11-10)

**Status:** Current strategy and next delivery contract. This document replaces the diffuse previous plan at this path. It **does not** mean Solver V3 has already been implemented, measured or submitted. Historical plan is preserved in Git history.

## PI directive — architecture and Kaggle outcome over process metrics (2026-11-10 11:06 MYT)

This section is the **current user-aligned decision contract**, superseding procedural priorities below where they disagree. Do not create a second plan file. Existing frozen experimental results and official receipts remain unchanged.

### Four required outcomes

1. **Competitive strength** — beat our actual verified scored 31B Public **0.17** (attributed third-party Budget-Fit V2, `58019162`), not merely finish ZIP compilation, get a Kaggle submission ID or beat the failed original E4B baseline. Maintain 12-hour **aggregate** issue+sandbox time feasibility. Our own V3 must be a new independent candidate, not misattributed copy.
2. **Technical substance** — improve a meaningful **agent decision mechanism or action interface** that could change which GitHub issue fixes are correct. An extra prompt, timeout tweak, tool-call budget increase, or optional Reviewer is not a scientific architecture contribution. Do not claim a deterministic gate unless the exact official ADK runtime can execute it.
3. **Complete delivery** — Research hypothesis → **running** native-ADK Solver → independently measured issue PASS/FAIL and cost → one frozen legal `submission.zip` → one official submission → official scored result and honest keep/reject decision. A candidate without independent correctness evidence may only be submitted as one explicitly marked exploratory end-to-end probe when separate 31B infrastructure is inaccessible and the CPU runtime path is verified.
4. **Resource discipline** — reuse scored original V2 ZIP and existing diagnostics; do not initiate repeated user-managed training, speculative LoRA, redundant private GPU runs, 4-task overfitting, repeated failed score submissions or unlimited queue polling. New training requires an explicit new user decision and evidence that the bottleneck is model generation, not harness mechanics.

### Clear model of the architecture (31B)

**Official production path:** GitHub issue + mounted source → **one Gemma 4 31B patch writer** with official ADK tools → gathered code/requirements witnesses → **concrete materialized candidate patch** → targeted test and typed result → select a repair / preserve the supported patch / finalize → `submit_patch` → independent scorer. The submitted code ZIP is **declarative**, not an arbitrary Python harness. Only officially registered tools and permitted skills/subagents can run in the official evaluator.

**Control plane** (outside production): GitHub tests and scripts, private Kaggle source hydration, official ADK compilation, score/trace observers, independent grader, one-shot competition ZIP build and authenticated score ledger. Nothing in the control plane should be passed off as an agent improvement. Our `scripts/candidate_history.py` observer runs privately for diagnostics; Kaggle's closed registry **does not** register our Python callback as a submission capability.

### Primary engineering candidate: Solver V3-R (conditional evidence-to-repair)

**Question:** Can a coder turn *actual source and test observations* into a more correct second edit, without merely increasing calls or time?

**Decision policy to implement in a supported action path:**

- **Localize only until there is a falsifiable hypothesis.** Extract explicit issue requirements, implementation/caller obligations, and relevant source/test witnesses. Unknown requirements stay UNKNOWN; broad unrelated reads are not rewarded.
- **Materialize one minimum viable candidate** and identify its exact actual diff. Preserve worktree state when the official available native tools permit it; check that this is actually observable/usable in the production sandbox. A private diagnostic snapshot alone does **not** give the submitted agent rollback capability.
- **Interpret evidence, not exit-code mythology:** distinguish (i) directly relevant behavioral assertion failed, (ii) environment/collection/import failure, (iii) test passed but incomplete requirement coverage, and (iv) inconclusive result. Each leads to a different **next action**: narrow semantic repair, alternative focused check, inspect another affected path, or terminate within budget.
- **One purposeful recovery:** update the mistaken hypothesis based on the observed failure and make a targeted second patch; do not automatically revert on any nonzero exit or repeat a Reviewer. Save the best supported candidate only if the runtime can actually restore it under the allowed tools.
- **Finish deliberately:** verify touched behavior, current diff and patch completeness. Submit once within the global budget. If the supported runtime cannot enforce some intended guard, label it **model-mediated** rather than pretend a reliable external callback exists.

**What is genuinely different from a prompt:** The first prototype must have **typed tool-call / tool-result traces plus observable, non-illusory state transitions**, not just a changed instruction paragraph. Where a deterministic action requires an unregistered custom callback/tool, **stop** that mechanism and select a legal native-tool/ADK alternative. Verify tool events in a scripted clean CPU fixture; this proves mechanics only, not repair quality.

**Global competing hypotheses / falsifiers:**

| Hypothesis | Observable support | What would reject or demote it |
| --- | --- | --- |
| H1: Missing issue semantics / feedback utilization (first) | Code reached and test evidence identifies overlooked behavior; corrected second patch independently resolves issue | Valid evidence is consumed but repeated candidate repairs remain wrong; overhead harms matched-budget resolution |
| H2: Lost good intermediate patch (conditional, NOT assumed) | A pre-submit snapshot independently passes but later final patch fails | History contains no passing intermediate patch; rollback machinery cannot add a real rescue |
| H3: Model generation ceiling | Correct source/evidence is accessible yet no acceptable candidate ever materializes | Meaningful non-training decision intervention consistently improves clean resolution |
| H4: Genuine specialist value | Same-budget role provides disjoint new evidence absent in coder continuation | Repeat of Reviewer v0's extra cost and no added issue resolutions |

### One executable sequence, no more parallel experiments

**M0 (read-only, current state):** Keep frozen V2 31B control ZIP hash `a4b10f6b8034fd7fffa144a7ee3fbd8faf9a84503ffb1349d1522ba048b534d3`. Official scoring best 0.17. Check Toolcap60 recovery `58183466` to terminal status using the existing ledger job, but **do not turn timeout recovery into the next research lane**; close it after that one result.

**M1 (FIRST CODE CHANGE):** Implement **one** true V3-R candidate in `experiments/solver-v3/`, with `build_` runner, exact V2 provenance, official native YAML/Skill/AgentTool support check, scripted non-competition CPU fixture that emits real ADK invocation/result events, and an explicit fail-closed prohibition on unregistered hooks. No modification to historical `submission/` or scored V2 source. Gate: a real production-legal mechanism is reached through an actual tool event and changes the chosen action based on a deliberately contrasting returned observation. If not, reject this prototype before GPU.

**M2 (CORRECTNESS GATE):** If M1 passes, run exactly one preregistered **fresh task-disjoint**, matched-budget 31B control vs V3-R experiment when private Kaggle inference is available. Collect actual `swegemma` resolved per issue, rescues/regressions, affected source paths, patch validity, tool-result handling and *aggregate* time. Previously exposed four-task Contract & Impact and old E4B failures are diagnostics only. If private GPU queue is unavailable, no repeated queue-wait kernels: optionally one clearly marked **exploratory** official end-to-end submission after CPU compiler and valid ZIP tests, authorized resources and available quota. Do not claim its score proves mechanism.

**M3 (OFFICIAL SHIP):** Build one immutable candidate ZIP, run the official CPU preflight, publish the exact package using existing Kaggle tooling, submit ONCE, and capture official terminal score and no-timeout outcome. Keep if real independently resolved issues improve **and** official score beats 0.17 without breaking runtime. Otherwise record failure and pivot a **method class**, not model prompt/call count/time limit.

**Scope controls:** no fresh GPU runs or new official submissions as part of *this replan*. Implementation work is a separate execution milestone, not secretly completed by this design record. One active candidate, one matched experiment, one official Kaggle receipt, one source of truth (`NOW.md`). Do not proliferate Action YAMLs or start a new training project to avoid architecture work.

---

## 1. Purpose — what the user is paying attention to

**Build a genuinely stronger Gemma 4 coding agent that fixes more unseen GitHub issues, fits the competition's global runtime, and produces competitive, scored Kaggle submissions.**

This is an end-to-end research + engineering + competition project. The **first outcome is a working and scored solver**, not another paper, CPU test suite, list of reviews, orchestration workflow, prompt patch or borrowed reference. The user delegates decisions to the PI, including a **large architecture redesign** when justified. No user-managed training or new LoRA should be a default path. Kaggle official scoring provides the real full-task validation; no infinite local GPU spend.

**Definition of success:** (a) actual issue-level PASS/FAIL score with no Notebook Timeout; (b) target above our verified best Public **0.17**, without promising a guaranteed gain; (c) exact runnable source artifact/sha and some defensible explanation of what changed; (d) no contamination or repeated tuning to exposed failures.

## 2. Two separate layers — never confuse them

**The product / Agent:**

Competition issue and offline code → Gemma 4 policy + official ADK tools → localize source and behavior → materialize edit → run targeted evidence/test → repair from observed failure → verify final diff → submit_patch → independent issue PASS/FAIL.

**The delivery / Control plane:**

GitHub research branch → candidate builder / source provenance → cheap official ADK validity check → one actual scored comparison when feasible → private Kaggle CPU ZIP publisher → one official submission → authenticated score/decision.

Github Actions, ZIP packaging, Kaggle queue polling and compiler tests **are not the agent's research contribution**.

**Official constraints (recheck before official submission):** 12 hours aggregate agent+sandbox time across all issues, excluding patch validation; a per-task limit is optional and does not guarantee total success. The official agent ZIP requires a root agent.yaml. Supported Gemma variants include 31B/12B/E4B/E2B but **cannot be mixed within one submission**. The offline harness exposes a closed native tool registry; participant custom callback wrappers are **not registered** under the existing scorer. Root LlmAgent, AgentTool and nested workflow agents may be supported, but roles are not hard-coded correctness guarantees. Final deadline: **December 2, 2026**, per Kaggle timeline.

Official references: https://www.kaggle.com/competitions/gemma-4-developer-agent/overview and https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/748287. Prior code-level ADK probe: docs/research/adk-lifecycle-probe-2026-10-31.md.

## 3. What is really proven (do not reset or overclaim)

| Evidence | Observation | Meaning |
| --- | --- | --- |
| In-tree historical E4B Baseline / Reliability | 0.03 Public each | Diagnostics, **not** our current strongest competitor |
| Original homegrown 31B | 0.08 Public | Valid but weak scored system |
| **External attributed** Budget-Fit V2 reproduction, ref 58019162 | **0.17** Public | Best scored benchmark control, **not our original invention** |
| V2 5-minute/28-tool variant, ref 58045795 | 0.15 Public | Time reduction alone not an improvement |
| Recovery Reviewer, ref 58112753 | 0.13 Public | Rejected specific Reviewer design, not all multiagent systems |
| Contract & Impact private 31B pilot | V2 0/4 vs new arm 0/4; optional Skill invocation not established | Full prompt + optional tool did not demonstrate correctness gain |
| Toolcap60 8-minute, ref 58164176 | COMPLETE, blank score; user saw **Notebook Timeout** | Failure of whole evaluation/runtime, not proven bad individual patch semantics |
| Toolcap60 5-minute, ref 58183466 | PENDING at latest authenticated **2026-11-10 02:55 UTC** | Operational timeout-recovery candidate, NOT Solver V3 |

Existing E4B trace audit: 1/17 tasks resolved, very few classifier-recognized targeted tests; an existing 31B 4-task pilot made 4/4 patches but resolved 0/4. These are different and small exposed groups. They weaken the assumption that **more tools / nonempty patches / more prompt steps** are enough, but do **not** establish which mechanism dominates hidden 31B failures.

Documentation/runtime drift: the public repo has 100+ workflows; almost all are historical jobs, not live solver architecture. The tree under submission/ is still historical E4B, while the scored 31B ZIPs are built from separately pinned upstream sources. Do not confuse them.

## 4. Current bottleneck and competing solutions

**Primary global hypothesis:** many attempts reach/edit source without producing a **semantically correct, independently verifiable repair**. Prioritize understanding impacted behavior, executing meaningful feedback, and turning failure into a converging second edit. This is not a proven failure-rate distribution.

Do **not** declare checkpoint-first or adding Reviewer/Skill as the answer.

| Research lane | Trigger for pursuing | Stop condition |
| --- | --- | --- |
| **A. Evidence-conditioned semantic repair** | Correct file reached but issue requirement, caller contract, invariant or test feedback mishandled | Explicit evidence is considered yet no correct fixes; overhead exceeds useful work |
| B. Checkpoint/branch-select | Actual independently passing intermediate patch was overwritten/lost before submit | Only failing candidates ever existed; selector adds cost but no rescues |
| C. Coder policy adaptation/SFT/LoRA | Proper evidence present but no good patch generation | Data leakage/cost or disjoint test fails; no training without user approval |
| D. Specialist subagents | A specialist provides distinct information under the same full model/time budget | Repeats Reviewer v0 failure, redundant analysis, reduced solve rate |

**Preferred first new candidate:** Solver V3-R, **bounded evidence-to-repair** with a Gemma 4 31B root writer. Real improvements must involve a *supported executed action or state interface*, not simply another paragraph instructing the model to do better. If a necessary deterministic gate cannot be implemented through official ADK/Skill/AgentTool APIs, **reject that mechanism** rather than inventing a participant callback. Do not force costly upfront analysis on every easy issue.

Mechanism objective: find affected entry points/requirements; collect one narrow discriminating test or source witness only when it changes the edit; update a concrete hypothesis after a real failing test; preserve a valid final workspace diff and submit. Under the full runtime, reserve budget for finalization rather than spending it on unproductive loops. Candidate-specific CPU checks must **observe actual invoked tools/results**, not merely confirm that instructions or scripts exist.

**Budget:** the 60-tool/8-minute attempt timed out; do not reintroduce it. If there are approximately 120 hidden issues, 120×5=600 agent-minutes leaves roughly 120 minutes of nominal headroom within the 720-minute aggregate, *before other overhead*. This is a scenario, not a guarantee, and extra tasks or host stalls can break it. Avoid spending time on new budget sweeps. Use the known 0.17 V2 as an exact **quality control** and maintain an explicit **complete-scoring** constraint.

## 5. Execution milestones — exactly one new primary candidate

**M0 — Confirm status, freeze control.** Use the existing read-only Kaggle workflow to capture refs 58183466, 58164176, 58019162, 58045795, 58112753. Freeze external V2 archive, SHA, task exclusions and official scoring assumptions; no duplicate submit. **Status done for latest check, 58183466 still PENDING then.**

**M1 — Make a real V3 candidate (the next actual work).** Implement in experiments/solver-v3/ with a repeatable ZIP builder. Prove in CPU/ADK synthetic fixtures that the new *actual tool invocation and feedback path* runs; do not call optional Skill metadata evidence. Record exact source diff vs V2, agent model/tool/config and cost limits. If the proposed mechanism can't execute in the supported tool registry, pivot once to the best supported alternative instead of more prompts. Do not modify old scored artifacts. Promote a validated ready candidate to canonical submission/ only when the E4B historical state is preserved as a reference.

**M2 — Test correct issue resolution, not CI status.** Compare one V3 architecture with byte-frozen V2 on a disjoint, preregistered development/confirmation sample when private 31B is **actually runnable**. Count paired correct rescues/regressions, nonempty patches, tool events, wall-time and independent grader results, including timeouts/unfinished tasks. Never use exposed 17 E4B / four Contract Impact cases as new blind confirmation.

If private Kaggle GPU is QUEUED again, **stop polling/relaunching**. Build and verify the executable mechanism on CPU, then (with real quota and a working notebook) make **at most one clearly labeled exploratory official submission** to learn a *real* outcome. A Public score alone is an uncertain estimate, not a causal experiment; no leaderboard hyperparameter grid.

**M3 — Decide and ship once.** The official version must have one deterministic source ZIP, official ADK compile, idempotent Kaggle private CPU builder, authenticated completed-score receipt, and no notebook timeout. Compare to scored control 0.17 with host variation caveat. If no correctness signal, reject or pivot **method class**, not just tool cap, minute cap or reviewer instructions. Do not submit the same ZIP twice.

**Pivots:** actual passing patches discarded → B; no passing patch ever synthesized despite evidence → C; specialized evidence truly additive at matched budget → D; official timeout → repair infrastructure/budget before claiming a model result. One failed exploratory architecture is permission to investigate a new class, not to tune the same 4 tasks.

## 6. Operating model — no more workflow proliferation

Current canonical orientation: AGENTS.md + RESEARCH_DOCTRINE.md + PUBLIC_VISIBILITY.md (rules); README.md (truthful overview); NOW.md (short current state and single next executable action); **this file** (one PI plan); experiments/solver-v3/ (one active research lane); submission/ (historical E4B until deliberate promotion); scripts/ and .github/workflows/ (historical plumbing + selected active build/status/submit jobs).

Do not create yet another replan, scheduler, optional reviewer, status workflow or "V3b" branch to avoid making a decision. Reuse current read-only ledger and existing Kaggle submission tooling; future consolidation can replace scattered builders, but deleting historical workflows/branches is **not** required to improve score and needs separate scope.

## 7. Immediate next engineer task and acceptance contract

1. Trace actual supported ADK tool/event route and identify one mechanism that the current root 31B can **execute**, not merely mention.
2. Implement isolated official-compatible V3-R builder + one exposure-free synthetic tool-result behavior test + official compiler gate. Demonstrate the new behavior in execution traces.
3. Measure on fresh independent issues **if inference is runnable**; if not, ship one explicitly exploratory official run only after source/CPU validity and available quota.
4. Report real score/cost and keep or reject the mechanism. **Success** is a scored end-to-end improvement, not just a green Action or receipt.

**State at this replan:** status ledger checked and plan updated; **new Solver V3 has not yet been implemented, measured or submitted**.
