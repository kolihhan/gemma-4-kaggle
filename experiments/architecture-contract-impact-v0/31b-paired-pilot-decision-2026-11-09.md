# Contract & Impact 31B — finished paired pilot and architecture decision

Date: 2026-11-09 (MYT). This is a completed **public development** four-task pilot, not a Kaggle Public or Private leaderboard score and not an independent generalization result.

## Terminal outcome: NO PROMOTION

The exact V2 control and the experimental Contract & Impact candidate were each evaluated on the **same four preregistered public development tasks** using the original Gemma 4 31B model and budget, with arm order alternated. The official `swegemma` private evaluator returned **0/4 independently resolved for each arm**. The full experiment completed successfully; no model environment failure or competition submission is inferred from its GitHub Actions success.

| Task ID | V2: resolved / patch / calls / seconds | Contract & Impact: resolved / patch / calls / seconds |
| --- | --- | --- |
| `fastapi_15661` | no / 876 chars / 28 / 292.6 | no / 1,529 chars / 19 / 317.1 |
| `fastapi_14303` | no / 2,896 chars / 28 / 284.8 | no / 2,922 chars / 18 / 210.9 |
| `rich_3180` | no / 1,204 chars / 23 / 485.7 | no / 423 chars / 13 / 483.8 |
| `rich_3064` | no / 1,447 chars / 28 / 407.3 | no / **empty patch** / 28 / 209.2 |

Aggregate:

| Metric | Exact V2 | Contract & Impact |
| --- | ---: | ---: |
| Resolved | **0 / 4** | **0 / 4** |
| Nonempty final patches | 4 / 4 | 3 / 4 |
| Native tool calls | 107 | 78 |
| Agent elapsed seconds | 1,470.36 | 1,220.90 |
| Prompt tokens recorded by 4 private traces | 1,070,932 | 892,081 |
| Completion tokens recorded by 4 private traces | 40,961 | 32,118 |
| Eval test exit statuses | 1 or 2 | 1 or 2 |
| Task-level evaluator execution exceptions | none reported | none reported |

**No gain demonstrated.** Fewer calls or faster termination do not imply better reasoning or reduced compute cost overall. The measured test counts are tiny and V2's expected performance on these particular tasks is not independently calibrated; a 0/4 V2 outcome does not imply that its previously authenticated public Kaggle score of 0.17 is invalid.

## What actually changed—and did it execute?

The candidate changed **two things together**: (1) a complete replacement root instruction and (2) an optional read-only `contract-impact` Skill. Model, sampling config, native tools and individual evaluation budget remained identical. This was not a hard deterministic stage controller and not a mandatory planner→coder→verifier topology. It does not isolate a Skill effect.

- The downloaded private evaluator produced **four structured trace JSON files and four task .log files per arm**, with no raw data published.
- Across all four Contract & Impact trajectories, text scans found **zero** `load_skill` or `run_skill_script` markers. Four `contract-impact` mentions appeared in trace messages (likely configuration/instructions, not proof of calls); task .log files contained zero exact Skill name markers.
- Trace `steps[].extra.event_type` observed `thinking`, `system_instruction`, `task_prompt`, `final`, and `continuation_nudge`; it **did not provide a complete explicit tool-call event stream**. Therefore the marker scan is **evidence of no observed Skill uptake, not proof that the Skill was never invoked**. Native tool names are also inconsistently represented in those messages.
- V2 made 107 native tool calls and delivered four nonempty patches; Contract & Impact made 78 and delivered three. This could reflect altered policy, task difficulty, optional-tool confusion, or simple stochastic variation. No direct causal attribution is justified.
- Independent test exit code 1/2 means none passed according to the evaluator; it is **not** enough to distinguish environment/collection errors from semantic code failures or missing requirements.

## Evidence / reproducibility

- [Preregistered 4-task/8-evaluation manifest](31b-pilot-manifest.json): deterministic salted SHA-256 task selection, two FastAPI and two Rich, with 18 old inspected IDs excluded. Public development data are not a fully untouched blind holdout.
- [Authenticated private Kaggle run 42576094444](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42576094444): terminal **success**, pulled exact pinned V2 ZIP SHA-256 `a4b10f6b8034fd7fffa144a7ee3fbd8faf9a84503ffb1349d1522ba048b534d3`, rendered shared 31B runtime, eight task evaluations; safe derived result artifact.
- [Per-task metrics read-only 42606267763](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42606267763).
- [Trace format schema 42606666306](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42606666306).
- [Token totals and tool marker counts 42606827788](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42606827788), [event type metadata 42607052760](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42607052760), and [private per-task log marker check 42607214238](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42607214238).
- Kaggle kernel `kolihhan/gemma4-contractpair-31b-42576094444` was **private**, never submitted to the competition. No model weights were trained.

## Research decision

**REJECT promotion of the current Contract & Impact candidate.** This is a failed/inconclusive test of the combined instruction+optional-Skill package, **not** a falsification of rigorous requirement analysis, broader architecture redesign, multi-agent systems, branch-search, or learning-based coders.

**Do not do:** retune the root prompt on these four tasks; add more optional Skill instructions; rerun the same denominator; claim the Skill improved quality or failed due to non-invocation; or use tool-call reduction as a win.

**Next architecture gate:** Before committing expensive 31B compute to another end-to-end agent, separate **control-flow reliability** from patch quality with a synthetic, exposure-free model interaction: does the current model invoke a declared structured tool when required, and does it use the returned evidence to choose the next action? Unlike this experiment, instrumentation must record the **actual ADK function-call/tool-result event**, not search for marker text. If the optional Skill is reliably ignored, a serious architecture should change the **action interface/topology**, e.g. a minimal managed editing tool that is the only available mutation path, instead of assuming an instruction makes stages compulsory. Such a new interface must compile under the closed official ToolRegistry and still allow a root `LlmAgent` for event compaction. If it cannot be made reliable, consider a different solver or training policy rather than more text instructions. Test user-requested substantial refactoring as a distinct method class, but do not stack unsupported components.

Even a successful synthetic control-flow test would **not** prove improved issue resolution. Subsequent clean, matched-budget 31B task evidence is required before official submission. Keep branch-search and supervised coder adaptation as genuine alternatives under `RESEARCH_DOCTRINE.md`; neither is established as dominant from this 4-task pilot.

**Execution boundary:** all 8 real-model evaluations have finished; no new GPU inference, training, production candidate promotion or official Kaggle submission in this analysis.
