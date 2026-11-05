# Scored public Budget-Fit V2 reproduction — 2026-11-05

Status: **OUR KAGGLE SUBMISSION ACCEPTED; PUBLIC SCORE PENDING**. This is an **attributed reproduction of a third-party openly licensed public package**, not an original agent improvement.

## What we actually executed

- Original Kaggle author: **lynnsakurai**; publicly shared notebook: https://www.kaggle.com/code/lynnsakurai/gemma-4-budget-fit-agent-w-bounded-rescue ; stated license: **Apache 2.0**.
- **Precisely scored reference:** notebook **Version 2**, advertised Best Score **0.18 V2** on its public Kaggle page. Do not confuse latest Version 3 with scored Version 2. Authenticated, read-only version-addressed Kaggle output retrieval was verified to resolve different V2/V3 sources and different `submission.zip` SHA-256s: [Actions 42007379647](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42007379647).
- Original V2 output `submission.zip`: SHA-256 **a4b10f6b8034fd7fffa144a7ee3fbd8faf9a84503ffb1349d1522ba048b534d3** (3291 bytes). Version 3 output: different ZIP; must NOT be substituted.
- V2 package includes four paths (`agent.yaml`, `prompts/system.md`, `configs/sampling.yaml`, `eval_config.yaml`), declares one pretrained Gemma 4 31B, no LoRA, 28 tool calls, 8 min/task, 80 turns, 4096 thinking; uses single root and the native run/read/edit/write/status/submit plus graph-code tools. Exact V2 member SHA-256s pinned in `scripts/prepare_public_budgetfit_v2.py`.
- **Static validation succeeded**: [Actions 42007948296](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42007948296), 4/4 unit tests, CPU builder emitted byte-identical output ZIP, no task data, no GPU.
- **OUR OFFICIAL SUBMISSION**: [Actions 42008171687](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42008171687), accepted **2026-11-05 10:09:09 UTC** (official Kaggle listing), ref **58019162**; description **attributed-public-budgetfit-v2-repro:no-train**; read-back **SubmissionStatus.PENDING**, Public/Private scores empty. The private CPU builder was `kolihhan/gemma4-budgetfit-v2-reference-42008171687`, version 1. This is a successful submission, **not a new scored 0.18 on our account**.
- Builder confirmed remote Kaggle output ZIP bytes identical to V2 source; response ref and read-back listing matched. No model trained, no personal Kaggle GPU notebook, no duplicate submission. Official scoring can use platform GPUs.
- Frozen original scored control remains ref **57983156**, Public **0.08**. Our submitted original `submission/` files are not mutated. Subsequent comparison must separate host epoch/hidden-run variation and publicly reported V2 score from our result.

## Scientific question and decision gate

Question: Does a public 31B no-training reference with documented 0.18 transfer to OUR official hosted score under the current scorer? This reproduction tests *replicability of a public bundle*, not whether our own 31B design improved.

- **If PENDING**: no second submit; read-only status query on exact ID 58019162 when needed. Never infer score from the author’s 0.18.
- **If COMPLETE >=0.15**: regard the full V2 bundle (policy + budget + tool interface + sampling) as a viable external reference; **not** evidence any one component caused the gain. Freeze it as a non-original comparator. Select one controlled original change and justify from independent process evidence.
- **If COMPLETE <0.15**: treat cross-run host variance / transfer as a live alternative, not automatically a V2 design failure; compare exact ZIP and epoch and revisit the independent verification plan before another submission.
- **If ERROR**: identify accepted vs scoring/runtime failure before attempting a different bundle or any re-submit. Do not make endless edits/submit retries.

## Next original intervention (research-only until score)

The E4B development traces diagnosed a narrower process failure: 5 of 17 Reliability-v1 tasks submitted after a nonzero test-command exit with no subsequent mutation; however these are **not** 31B hidden tasks. The Budget-Fit V2 prompt already claims bounded rescue and has 4096 thinking. Therefore adding another generic instruction to test is **not** meaningful innovation.

Before proposing an original V2 derivative:
1. Inspect the V2 prompt’s actual existing recovery behavior (not just its title) and identify a missing capability, if any.
2. Choose ONE intervention with an observable trajectory mechanism, e.g. task-relevant failure classification or evidence synthesis, and freeze an independent validation denominator before running it.
3. Preserve the untouched 12-task reserve. Personal Kaggle L4x4 GPU attempts remained quota-blocked in [Actions 41980782896](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41980782896); do not claim an independent quality test was run.
4. Avoid new GPU/LoRA/training and avoid Public LB-driven prompt sweeps.

### Method-class restrictions

- **No self-training / LoRA for this run**: user direction and absence of evidence it addresses main bottleneck. Pivot only if untouched evidence shows model adaptation is necessary and better than a reproducible no-training baseline.
- **No unsolicited repeated official submission**: quota, queue and public-score overfit. Pivot only with a materially distinct, statically valid, separately justified candidate.
