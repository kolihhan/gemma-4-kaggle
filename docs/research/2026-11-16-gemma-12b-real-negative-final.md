# Gemma PRO — exact real 12B vs previously evaluated 31B: negative

Date: 2026-11-16 (MYT). Real private Kaggle scorer finished. No new official competition submission and no training.

## Actual authenticated result

- GitHub Actions [#43781086310](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43781086310), job `133018189199` SUCCESS. **One** private kernel `kolihhan/gemma4-model12b-v2-matched-20261116` reached `KernelWorkerStatus.COMPLETE`; exact output was downloaded; against frozen original 31B same-task 5-minute/28-call control:
  
| metric | frozen 31B V2 | new 12B |
|---|---:|---:|
| same public-development task IDs | 3 | 3 |
| independently grader-resolved | **1** | **0** |
| patches produced | 3 | 3 |
| errors | 0 | 0 |
| scorer tool calls total | 62 | 84 |
| runtime seconds total | **604.94** | **820.42** |
  
- Pairwise: **0 rescues, 1 regression, net -1**. Both arms same model-visible original V2 prompt/native tools/sampling and five-minute, 28-max-tool-call, 80-turn limit. Changed root inference model 31B→12B and vLLM architecture-required override in research runtime. The 12B did not actually improve observed runtime. These are **only three already-spent public-development tasks**, not an independent hidden score estimate.
- Exact private 12B evaluator logs: `GEMMA_PRO_REAL_12B_VS_31B_MATCHED_GRADER` in linked Action. No task text, model's raw outputs, issue patches or gold grader solution exported.
- Old own scored public best 0.18, official `#58183466`. Unscored official `#58350278` remained COMPLETE with blank numeric score, not a quality improvement.

## Decision

**RETIRE exact model-size-only 12B substitution for this 31B prompt/harness.** It worsened actual resolution on this matched sample, consumed 84 rather than 62 scorer calls and ran longer in aggregate. This does NOT prove all 12B models or differently designed 12B agents are inferior; do not run more 12B tuning on the same three task IDs.

## Competing next mechanisms, distinct from failed prompt/Skill/model-size variants

1. **Action/feedback bottleneck**: native agent invokes costly exploration and no reliable model-visible post-edit targeted test; a *mandatory host-native test feedback* mechanism might rescue bugs but is not in a validated Kaggle submission yet. Correctness requires real 31B uptake, same-task rescues, and a supported legal harness; an optional Skill was not used at all.
2. **Reasoning/representation bottleneck**: even with tools, agent cannot localize/correct issue within budget. Need actual failure chronology (post-edit test signal, first code edit timing, output interpreted), then consider training data and model policy, rather than prompting the unchanged agent again.
3. **Independent benchmarks**: pick a fresh source-disjoint unseen issue batch and a stronger one-scientific-change candidate before spending further GPU. Freeze new task selection before looking at treatment results.

**Next action:** analyze already existing private 31B traces against grader outputs to distinguish evidence acquisition vs edit correctness. Avoid counting raw duplicated `submit_patch` trace events as physical tool calls; scorer totals are authoritative.
