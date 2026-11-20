# Gemma 4 Independent Observer — Baseline and Failure-Mechanism Audit

**Recorded:** 2026-11-21 (MYT). **Evidence reviewed:** authenticated GitHub Actions and repository research records through 2026-11-20. **Scope:** read-only independent review, plus user-authorized documentation-only handoff. **Current decision:** **PIVOT** from simplistic test-path retrieval / extra agent calls toward real scored patch-failure mechanism analysis; **HOLD** on new GPU / fine-tuning / official submissions without new evidence.

## Verified evidence (not new experiments)

1. **Official incumbent:** 31B Kaggle submission `58183466` = `SubmissionStatus.COMPLETE`, Public **0.18**; Coder-LoRA `58558350` = `SubmissionStatus.COMPLETE`, Public **0.12**; Private scores blank. Direct authenticated Kaggle CLI output in [Action 44659728947](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/44659728947). This is a dated receipt, not a permanent assertion of real-time leaderboard state.
2. **Existing genuine 31B paired development traces:** V2 **1/3 resolved, 62 physical scorer tool calls**, V3R optional Skill **1/3 resolved, 81 calls**; both edited all 3 tasks. No net rescues. Conservative trace classifier saw **0/3 recognized explicit post-edit tests** in each arm, but **opaque commands in 3/3** of each; this *cannot* prove no actual tests ran. [Action 44750878666](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/44750878666); [bounded scope](https://github.com/kolihhan/gemma-4-kaggle/blob/research/dual-agent-recovery-v0-20261108/docs/research/2026-11-20-31b-real-feedback-signatures-decision.md).
3. **Real public upstream test-retrieval proxy:** exact basename hit@1 **21/53** versus token/path ranker **23/53**, 2 rescues / 0 regressions; preregistered +5 gate **FAILED**. Developer co-modified tests are an imperfect proxy for task-relevant runnable tests and not model resolution results. [Action 44763807938](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/44763807938).
4. **Private CPU native test-opportunity parser repair:** original four gold-pass/no-op-fail development tasks had unified diff reference patches, which defeated the first git-header-only parser. Corrected v2 extracted **4/4** source `.py` paths; only **1/4** had an exact-basename test candidate. Absence of a basename match does **not** prove absence of an actionable relevant test. CPU-only, no new inference or scoring. [Action 44764497251](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/44764497251).
5. **Small paired early-edit pilot (context only):** 31B early-edit **3/4** vs V2 **3/4** on same public-dev issues, 66 vs 79 scorer tool calls. One rescue and one regression; *no correctness improvement*. [Action 43178431152](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43178431152). Do not promote time/call savings to hidden task resolution.

## Review actions completed

- Read `AGENTS.md` and the current research branch `NOW.md`.
- Retrieved authenticated official score job log, existing 31B real-feedback job log, test retrieval and private CPU output logs.
- Cross-checked the dated research reports against direct Actions records; separated graded task results, local development experiments, CPU metadata audits and conjectures.
- Evaluated whether the recent experiments causally test resolved-task success rather than more tools, better-looking test retrieval or pipeline execution.
- Did **not** run inference, training, new paired scorer evaluations, Kaggle submissions, or modify agent/solver logic.

## Problems and root cause

**VERIFIED limitations:** additional agent actions have not demonstrated more resolved tasks on small paired development denominators. Current test retrieval heuristic failed its prespecified proxy threshold. No available observation in these summaries proves which failed patch was semantically wrong and why. A nonzero shell exit is not necessarily a failed relevant test; a missing recognized test signature is not evidence of absent testing.

**INFERENCE:** incorrect edit semantics and/or wrong localization may be more important than missing exact-name test retrieval. Unexcluded alternatives: root-cause misunderstanding, tools/environment errors, unavailable or unusable verification feedback, and premature stopping/budget exhaustion. Cannot rank these from limited tool-signature counts alone.

## Next best *proposed* experiment (NOT authorized/executed)

**Blind Failed-Patch Root-Cause Audit** on already graded, gold-clean development traces. Separate task text, model-visible evidence, patch and test traces (analyst access) from reference patches (analyst-only retrospective labels, never solver input). Classify **requirements understanding / localization / semantics / tool-environment / test-feedback / stopping** with ambiguous and multi-cause labels rather than fabricated certainty. Include successful controls and per-task causal evidence. Prioritize one mechanism only if category prevalence, disagreement and actionability justify a prospective matched 31B trial.

**Pass:** credible, repeated, issue-level evidence identifies an actionable dominant mechanism and a falsifiable small paired intervention. **Stop:** cases too few, absent, ambiguous, or no intervention can be distinguished from alternatives. Distinct tasks count once; repeats are paired variance estimates, not independent issue denominators.

## Observer handoff

Next invocation: read [`OBSERVER.md`](../../OBSERVER.md), verify latest official receipts and real issue-level scored traces, and compare new Executor claims to the frozen 0.18 incumbent. Do not launch more agent/Skills/LoRA experiments merely because a proxy improved. Append dated log only after explicit write authorization. This record is not an autonomous background monitor.

**No Executor source modifications, PR, GPU, training or submission occurred in this handoff.**
