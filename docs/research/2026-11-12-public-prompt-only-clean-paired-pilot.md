# Public prompt-only SWE agent versus pinned V2 — preregistered paired 31B pilot

**Status: frozen before any prompt-vs-V2 real model comparison.** CPU tests and real-source ZIP validation are required; no competition submission, LoRA training or new public data mirrors.

## What is / is not proven by the open 0.22 score

1. The authenticated public Notebook score CSV [Action 43054776326](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43054776326) found a genuine **0.22 Public** for **`flexonafft/gemma-4-budget-aware-coding-agent-v2` version 10**, file-bundle SHA `56010e9e9d4c7f33856ce49d12ec3edae5c912261986e999a4aa989b3cd463cb`.
2. Independent [same-file SHA / version ledger Action 43055057050](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43055057050) identified **8** scored records with this same SHA: `0.12–0.22`, mean `0.1562`, median `0.16`. These are repeated public scoring observations, not paired matched issues. The top 0.22 observation is **not** reliable evidence of a 0.22 expected result or an improvement over the user's 0.18 best.
3. The **different** public Notebook `bliverrigpdoge/lb-0-22-4-config-files-no-training` offers a readable literal four-file config. Authenticated [AST source comparison Action 43053330477](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43053330477) confirmed its `agent.yaml`, sampling config and 8-minute/28-call eval config are **byte identical to pinned Budget-Fit V2**, and only `prompts/system.md` differs (SHA `475cc9b7fcc0dc295532f5cb5e1928f26a491f501837ad08b1c79bdbe1a3eaa4`). This Notebook's **title** claims `0.22`; we did **not** establish a corresponding official scored entry for that exact bundle. Do not equate it to `flexonafft` v10 or claim cloned candidate reproduces its score.
4. [CPU exact variant gate 43054075167](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43054075167) compiled candidate 8-minute ZIP SHA `ca4869eaa76547bf5c9dafcac0e2d796203ca4d0b4e7e2fbefef9db6a92dc542` and **5-minute ZIP SHA `fdb862b0f8391b0596f200ccb8e3bece40d9dc8f1e3d60e63537277ac626649d`. No model run or score. Public prompt strategy prioritizes localization, early editing, targeted tests and avoiding unnecessary graph searches, a broadly similar intended behavior to V2 with differences worth measuring rather than assuming.

## Predeclared causal question

Will a **prompt-only** intervention to the **same single native-root Gemma 31B coding Agent** increase resolved issue count at **equal 5-minute time, 28 tool calls and 80 turns**, particularly by avoiding read/search loops that prevented V5 from editing?

- **Control:** pinned public V2 source SHA256 `a4b10f6b8034fd7fffa144a7ee3fbd8faf9a84503ffb1349d1522ba048b534d3`; modify only its `eval_config.yaml` max_time_minutes `8 → 5`.
- **Treatment:** same V2 model, `agent.yaml`, tools, sampling and 5-minute config, but public `bliverrigpdoge` prompt above. This is attributed public prompt reuse, **not original research** or a verified 0.22 candidate.
- **Tasks:** choose one each from **FastAPI, Rich and Requests** private-runtime mounted public-development task IDs, via SHA256(salt+ID), exact [frozen manifest](../../experiments/public-prompt-vs-v2-disjoint-paired-20261112/manifest.json) and exclusion list; no issue text or oracle used to select. Each arm sees the same task. Alternate arm execution order by task. **6** maximum official evaluator task runs from **one** private GPU Notebook and one model server. No failed tasks silently dropped.
- **Primary:** number of independently resolved issues out of three per arm under official swegemma evaluator. **Secondary:** any materialized source patch, patch length, task duration, tool calls, validation/test exit, error/timeout. Saving a nonempty patch alone does **not** count as correct.
- **Kill / promotion:** if control and treatment both fail all tasks, prompt change has not shown useful signal; stop. One additional resolved task in treatment is preliminary, not statistically conclusive. At least one clean, separate corroborating sample required before claiming reliable improvement or spending an official competition submission. Avoid restating 0.22 as achieved.
- **Costs:** startup/adapter setup, compaction, private Kaggle sandbox, and task durations all count; report full kernel runtime and GPU quota. This three-task panel **cannot estimate Kaggle hidden generalization**.
- **Safety:** only approved Gemma 31B model, private L4x4 kernel with internet disabled, official task data mounted at runtime. GitHub Actions renders but does not upload raw issue text, source diffs, reference patches, or private traces. No new Kaggle official submission and no training.

## What has actually failed previously

- Actual V4 one-shot official submission `58222227` scored **0.15 Public**, below previous **0.18**.
- The wrapped two-stage V5 used `mandatory_scope_then_patch` once but threw and produced **0 patch** on `requests_7328`, `0/1` resolved after `302.5 s`.
- The direct V2 5min one-task posthoc comparator on that same issue created a **3,454-character patch** but still resolved **0/1** with test exit 1 ([Action 43051007173](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43051007173)). Therefore, prompt style should aim at correct edits, not merely faster edits. This exact issue is **excluded** from the present three-task panel.

The paired runtime builder is [`scripts/render_public_prompt_vs_v2_paired_31b.py`](../../scripts/render_public_prompt_vs_v2_paired_31b.py). Static tests and the exact public ZIP SHA gate are [here](../../tests/test_render_public_prompt_vs_v2_paired_31b.py). Do not run a second kernel on the same manifest if the first is queued/active or completed; do not tune task choice based on these results.
