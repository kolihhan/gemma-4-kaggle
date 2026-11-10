# Gemma 4 — PI Research-to-Submission Reset (2026-11-10)

**Status:** Current strategy and next delivery contract. This document replaces the diffuse previous plan at this path. It **does not** mean Solver V3 has already been implemented, measured or submitted. Historical plan is preserved in Git history.

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
