# PRO real Gemma 4 31B V3-R vs pinned V2: negative and mechanism falsified

Date: 2026-11-15. **Authenticated actual scorer, not CI-only.**

## Frozen comparison and genuine result

- [Immutable manifest](../../experiments/solver-v3/pro-v3r-vs-v2-fresh-paired-20261115.json). One SHA-hash-selected public-development issue from each of FastAPI, Rich, and Requests, excluding prior inspected IDs; same three issue IDs, 6 real 31B evaluations. This is **new relative to our prior pilots**, but **not** independent hidden-Kaggle evidence.
- Frozen 31B model, identical native tools and sampling. Budget both arms 5 minutes, max 28 **scorer** tool calls, max 80 turns. Only V3-R adds the previously official-ADK-supported optional executable `repair-witness` Skill plus its system guidance.
- [Completed actual real model runner #43689217134](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43689217134), private Kaggle kernel `kolihhan/gemma4-v3r-v2-pro-nov15-v1` COMPLETE.
- V2: **1/3 resolved**, 3 patches, 62 scorer tool calls, **604.94 s** total.
- V3-R: **1/3 resolved**, 3 patches, 81 scorer tool calls, **723.06 s** total.
- Pairwise **zero rescued, zero regressed, net 0**. V3 adds **19 scorer tool calls** and **118.12 s** with no correction gain. This is an actual grader result, not an inferred Public leaderboard score.

## Real model uptake is absent

- [Post-terminal genuine trace read-only audit #43691444649 rerun](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43691444649) reported 6/6 available private traces, for V3-R **0 `load_skill` calls; 0 recognized `run_skill_script` before/after calls; 0 unrecognized `run_skill_script` calls**. There is also zero Skill usage in V2, as expected.
- This falsifies the *intended intervention mechanism* for these actual three tasks. **The model never invoked the optional tool**. The synthetic scripted-ADK proof previously demonstrated only interface legality, not 31B uptake.
- [Native-tool exploratory audit #43691841171](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43691841171) confirmed **no explicit/inline test recognized by the conservative classifier in either arm**; **opaque shell commands** exist (22 V2 / 25 V3R). Do not claim zero tests were actually run or equate nonzero shell exits with failing issue tests.
- **Important instrumentation caveat:** raw trace `tool_calls` entries total 134 (V2) and 92 (V3R), different from **scorer counted** 62 and 81. Raw V2 trace's `submit_patch` name repetitions can exceed the scorer budget. Therefore **do not use the raw per-function call totals as physical cost or a causal localization finding**. Trust scorer totals for budget; raw trace is only evidence of the *presence/absence* of optional Skill invocations in the six emitted traces. Dedupe or event-schema reconciliation would be required for per-tool quantitative attribution.

## Research decision and next falsifier

**REJECT V3-R as a score-improving mechanism.** Do not keep tuning longer prompts, retry the same issue IDs, or submit this unchanged candidate to the official competition.

Competing explanations for remaining failures: H1 context/evidence quality, H2 semantic/root-cause and patch accuracy, H3 underused executable feedback and tool-choice policy, H4 evaluator/evidence mismatch. The trial proves only that **optional Skill was not used and outcomes were unchanged**; it cannot conclude that testing can never help or that prompt policies universally fail.

Next substantial candidate must **change the actual action/evidence path** through competition-legal native operations or a separately justified training/search policy, not merely bundle another optional skill. Before another 31B GPU run, verify tool/harness legality, pre-register a new disjoint test set and a model-visible behavioral contrast, and prioritize grader-resolved rescues/regressions.

Current authenticated Kaggle best remains **0.18** (#58183466), separate exact existing #58350278 was still **PENDING** at [read-only audit #43691444649](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43691444649). No new official submission or training this round.
