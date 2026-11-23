# Gemma 4: Learning from winning coding agents — actual 31B edit audit
Date: 2026-11-24 MYT. Decision: **Reject mandatory Behavioral Verification; investigate edit-call validity and finalization**.

## External source-to-mechanism comparison
- [Konwinski Prize winner Eduardo Rocha de Andrade](https://www.kaggle.com/competitions/konwinski-prize/writeups/eduardo-rocha-de-andrade-1st-place-solution-write-): Agentless 1.5, focused localization and SEARCH/REPLACE; do not equate tests with improvement.
- [Konwinski public 2nd Camaro](https://www.kaggle.com/competitions/konwinski-prize/writeups/camaro-public-2nd-place-solution): fail-before/pass-after reproduction tests when available, not universal broad testing.
- [Konwinski 5th Kenj](https://www.kaggle.com/competitions/konwinski-prize/writeups/5th-place-solution): traceback-to-line localization, narrow replacement, Git-produced diff; cannot copy a penalty-driven skip policy.
- [Agentless](https://github.com/OpenAutoCoder/Agentless) and [SWE-agent](https://proceedings.neurips.cc/paper_files/paper/2024/file/5a7c947568c1b1328ccc5230172e1e7c-Paper-Conference.pdf): compact usable tools rather than elaborate agent choreography.
- [Gemma competition discussion](https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/748323) and [tool-call format analysis](https://pilkwangkim.github.io/posts/Gemma-4-Developer-Agent-Part-2-Measuring-an-Agent-While-Its-Evaluator-Moved/): wrong or missing parsed tool arguments can prevent edits; those authors' rates must not be transferred to our experiment.

## Real paired evidence
Previously completed [31B same-issue paired test #45211599647](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/45211599647), 8 distinct public-development issues, 16 task evaluations. No fresh GPU. Read-only CPU analyses: [initial #45227499305](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/45227499305), [precise categories #45227822525](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/45227822525), [paired outcome cross-tab #45228018995](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/45228018995), 6/6 unit tests passing.

| Metric | Champion 4min | Behavioral 4min |
| --- | ---: | ---: |
| Grader resolved | **4/8** | **2/8** |
| Scorer tool calls | 147 | 167 |
| Summed task duration seconds | 1432.01 | 1719.27 |
| Recorded task duration above 240s | 4/8 | 6/8 |
| Final nonempty patch records | 6/8 | 6/8 |
| Trace edit events (possible callback duplication) | 16 | 40 |
| Edit argument missing required string / wrong type events | **0** | **19**, in 2 tasks |
| Edit observations of unknown outcome | 0 | 19 |
| Traces with at least one explicit submit_patch | 6/8 | 2/8 |

**Paired outcome cross-tab:** 2 both resolved, 4 neither, 2 regression, 0 rescue. In **both** regressions the Candidate recorded invalid edit arguments and no explicit submit; Champion explicitly submitted in both. None of the other six Candidate tasks recorded invalid edit arguments. This is a strong association but only two regressed issues, **not proof that corrupted calls caused failure**. Trace edit events can repeat; unknown edit observation is not proven tool rejection. A patch recorded after agent timeout need not have an explicit submit event and need not be correct.

## Decision and next discriminating test
Prioritize **tool grammar and patch survival**, not adding validation or multi-agent stages. Next *single variable* test: only change how edits are attempted (e.g., minimal asserted run_command fallback after an unusable edit call), without also changing submit timing or tool inventory. Preserve original 31B model, all native tools, sampling, 4min/60-call matched budget and same official grader. This is a hypothesis, not a candidate known to improve score. If successful on clean, fresh, independent tasks and overall runtime budget allows, only then consider official submission.

Never assume a per-task 4-minute setting guarantees global Kaggle Notebook completion: setup + hidden task count share a 12-hour global patch-generation cap. Some real task records exceed four minutes. Require full-batch conservative runtime forecast with >=1-hour margin.

Only aggregate metrics are exported. Raw issue, source paths, traces, tool arguments, patches, references and grader output stay private on Kaggle. The verified official Champion remains **0.18**. The latest separate official Evidence-Channel #58729456 was PENDING at last authenticated check. No new competition submission from this audit.
