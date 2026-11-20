# Latest verified improvement — 2026-11-16

| Metric | Verified best | New verified best | Improvement |
| --- | ---: | ---: | ---: |
| Official Kaggle Public resolved-task fraction | **0.18** | **none** | **+0.00** |

- Score receipt: submission **#58183466**. Other historical COMPLETE submission #58350278 has **no verified numeric score**.
- Actual local grader matched experiment: frozen 31B V2 **1/3** versus mandatory SequentialAgent **1/3**, **0 rescues, 0 regressions**, 62 → 69 scorer calls. [Verified Action #43808826562](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43808826562). **NOT promoted**.
- New official submission scored this round: **0**. No new GPU candidate score.
- **Decision:** preserve 0.18. No repeat GPU on spent 3 tasks; no improvement claim from green workflows or unverified reviewer traces. Source [NOW](NOW.md), [VALIDATION](VALIDATION.md).

## 2026-11-20 — Real 31B failure-vs-reference audit (scientific HOLD)

- **Official Public:** best **0.18** unchanged, ref `58183466`; Coder-LoRA `58558350` **0.12**; authenticated owner receipt [#44659728947](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/44659728947).
- CPU-only existing-output audit [#44771279117](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/44771279117): 12 genuine 31B real-development trajectories, 2 PASS on one duplicated-control Issue, 10 FAIL; **0 actual final Patch artifacts available**, 12/12 trace edit-path summaries recovered.
- Current Gold/no-op controls: `fastapi_14487` and `rich_3782` informative; `requests_7427` gold itself FAIL (scorer confound). Three of four informative failed attempts miss the Gold source path in explicit edit tools, but final patch semantics are **unverified**. Nov15 three-issue validity unknown.
- Historical paired corrected-resolution gain: Nov12 prompt-only **0/3 vs 0/3**; Nov15 V3R **1/3 vs 1/3**. Neither promoted. No new GPU or official entry from this audit. [Detailed task-level report](docs/evaluation/gemma31b-failed-repair-vs-gold-20261120.md).
- **Next evidence gate:** recover the exact final scored patch and certify Gold/no-op for Nov15 before a new mechanism A/B. Decision **HOLD**.
