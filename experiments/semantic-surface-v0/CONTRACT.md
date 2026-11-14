# Frozen Gemma 31B Semantic Surface prospective paired pilot — 2026-11-14

## Decision and bottleneck
We retain the authentic scored 31B best **0.180** (#58183466), rather than treating any CPU/Action PASS as solver quality. Earlier 31B reproduce-first 2/4 vs 2/4, wrapped Scope/Coder 0/1 without a patch, V4 counterexample 0.15 official, and 12B-vs-31B same-task 2/4 vs 3/4 establish failed nearby lanes. These are development effects, not conclusions about hidden tasks.

**Hypothesis:** Some patch failures reflect incomplete *code-surface propagation*, not lack of arbitrary test-first instructions or tool-call throughput. The smallest structurally different intervention is a **read-only executable, zero-dependency source observation**: after a real Python edit, the agent may call an official registered ADK Skill that extracts actual changed functions/methods via `git diff` + `ast` and reports other code/test references to those symbols. No self-claimed requirement map, invented test oracle, or new agent. A symbol link is a heuristic lead, not required edit or gold correctness.

**Counterhypotheses:** The target may lack a self-contained specification, the model may never invoke the Skill, the referenced symbols may be irrelevant, extra tool cost may hurt, or the model may still produce a wrong patch after correct retrieval. A one-task failure does not prove architecture class universally impossible.

## Frozen build and causal comparison
- Exact scored 31B 5min/60 tools/80 turns champion ZIP SHA256 `ff08c10240a38e151a2ea1d0478e999ee5d2f437d2dad5571d912cf12859922b`, rendered from the SHA-pinned public Budget-Fit V2 archive through the existing champion builder.
- Candidate is **same root LlmAgent, same 31B model, same YAML tools, sampler and task limits**, with precisely one registered `semantic-surface` Skill (`SKILL.md`, `scripts/surface.py`) and one small conditional invocation instruction. SHA256 `b705301954c8f56a39644b3bde1d24da1213615bf07dac4d2710b1c62251bc69`.
- Source implementation: `experiments/semantic-surface-v0/skill/scripts/surface.py`; builders `scripts/build_semantic_surface_31b.py`, `scripts/render_semantic_surface_31b.py`. No training, custom callback/tool registry, internet access or task reference supplied to the model. Skill execution is **model-mediated**, not deterministic or guaranteed.
- [CPU candidate #43585937791](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43585937791) **PASS**; [full paired renderer CPU #43586208893](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43586208893) **PASS**, all AST/synthetic tests and exact rendered private runtime. The first renderer attempt failed only on packaging-source SHA check; it was corrected to use the official champion packager before model launch.

## Prospective denominator and privacy
- Select **exactly four** public-development tasks: the first two SHA256-ranked `fastapi_*` and first two `rich_*`, ranked by `prospective-31b-semantic-surface-repair-20261114-v0|instance_id`. Exclusions are fixed in renderer: previously explicitly studied tasks from patch checkpoint, reproduce-first, model-capacity and source failure audits; no replacements after labels or model outcomes.
- Immediately before any model inference, require **gold patch passes/no-op fails** for every selected task through the official private verifier. This is a *benchmark-integrity check* only; its reference patch and test results are never given to the actual agent. Any failure stops the run, not selective exclusion of unfavorable tasks.
- Two arms alternate order, same official `Evaluator`, 31B weights, 5min/60calls/80 turns, same task texts and grader. **8 total model evaluations** on 4 fixed issues. Use one private Kaggle L4×4 kernel, authenticated source mounts, no internet. No public raw task, patch, test, trajectory, hidden label, or reference text artifacts; print only task IDs, resolved flags, errors, timings, tool counts and Skill invocation counts.
- CPU/static proof of script invocation semantics is **not** a claim that autonomous 31B will use the Skill.

## Preregistered decision
1. Runtime: both arms compile, all 4 integrity checks pass, 8 task evaluations finish, no model/push errors; otherwise mark **infrastructure / invalid cohort** and do not infer accuracy.
2. Mechanism uptake: treatment must autonomously issue a real `run_skill_script` call; record counts from native trace and evidence that at least one source file was edited. If zero, the *present system* fails the mechanism regardless of any observed score fluctuation.
3. Correctness: compare same-task independent `resolved` and pairwise rescues/regressions, retain failed evaluations. **Net <= 0 rejects promotion.** Net > 0 with clear mechanism uptake suggests a second task-disjoint prospective confirmation; it does **not** itself justify an official competition entry or claim hidden Public >0.180.
4. Cost: compare total task duration and tool calls under same per-task cap; a correctness win with grossly higher time cannot fit 12h aggregate without further scale check.
5. Do not adjust prompt, Skill code, issue cohort or thresholds after seeing this result; no leaderboard tuning and **zero official Kaggle submissions** from this pilot.

**Global pivot rule:** if the Skill is ignored or no independent gains occur, stop adding tools/prompts to this lineage and reopen a data-driven repair policy/finetuning hypothesis only after training reward/trajectory availability is verified. Do not equate returned symbol references with hidden semantic correctness.


## TERMINAL: 2026-11-14 19:35 MYT — 31B GPU paired decision

Actual [private GPU Action #43586412434](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43586412434) **SUCCESS**, after a single L4×4 kernel. All eight fixed task evaluations finished and official verifier outcomes were emitted. The results are public-development diagnostics, **not official Kaggle competition scores**.

| Task ID | Champion | Semantic Surface | Champion / treatment tools | Champion / treatment seconds |
|---|---:|---:|---:|---:|
| fastapi_13537 | 1 | 1 | 26 / 14 | 304.668 / 260.276 |
| fastapi_14479 | 0 | 0 | 11 / 25 | 88.668 / 305.150 |
| rich_3953 | 0 | 0 | 21 / 21 | 296.321 / 303.631 |
| rich_3471 | 0 | 0 | 33 / 13 | 304.015 / 303.976 |
| **Total** | **1/4** | **1/4** | **91 / 73** | **993.672 / 1173.032** |

All 8 rows have `status=completed`, `has_patch=true`, no row-level grader error. Treatment `load_skill=0` and `run_skill_script=0` on **all 4**. The metric uses trace tool-call events and cannot prove why the model did not choose the Skill. **Mechanism not adopted, no paired correctness gain.** Source was frozen and code passed CPU gates, but usefulness is not demonstrated. Reject optional Skill promotion and official submission by the predeclared stop rule. Do not tune these same four task outcomes or rerun them to chase sampling noise. Nothing was trained or submitted to the official competition.

A plausible alternative is a data-driven policy change (SFT/LoRA or other route), but legality, training signal, resource cost and source-disjoint success have **not yet** been established. This observed result should lead to a method-class reevaluation, not automatically to a new GPU job.
