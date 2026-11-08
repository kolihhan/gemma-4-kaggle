# Recovery Decision v0 — two matched 31B candidate packages

**State: CPU-packaged and contract-tested, not officially compiled/scored.** No inference, Kaggle submission, training or modification of frozen/canonical candidates.

## Built mechanism

Source: byte-pinned Apache-2.0 external [Budget-Fit V2](https://www.kaggle.com/code/lynnsakurai/gemma-4-budget-fit-agent-w-bounded-rescue/2), exactly the reference that scored 0.17 on our account.

Builder: [scripts/build_recovery_decision_candidate.py](../../scripts/build_recovery_decision_candidate.py). It accepts that exact source ZIP, rejects a different archive, and outputs two deterministic ZIP files. Both keep all nine native tools, the same Gemma 4 31B base, original sampling, original 8-minute/28-native-call/80-turn budget and identical root instructions. The only difference **between the two new arms** is `prompts/recovery-adviser.md`.

- `fresh_coder`: tool-free, fresh-context ordinary Coder proposes a falsifiable next step based on the task and evidence.
- `recovery_reviewer`: tool-free, fresh-context Reviewer searches for a contradiction, missing requirement, non-materialized edit or regression, then proposes a falsifiable next step.

The root Coder remains the sole writer and submitter. The optional adviser is requested at most once **by instruction, not enforced by harness code**, only after a specific stalled hypothesis with sufficient remaining time. Both receive the same current diff, issue facts, observed test details and budget summary, assuming root compliance. No task-specific rules or hidden reference patches.

## Real-source CPU verification

[GitHub Actions run 42438857122](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42438857122) passed:

- 3 unit tests; compiled the new Python builder.
- Authenticated download of exact pinned public V2 ZIP; validated the hard-coded source SHA-256 and all four original members.
- Generated, ZIP-integrity-tested and compared both 31B candidate packages.
- Verified identical original sampling/eval files and only helper prompt differs across new arms.
- Verified the child `!include` path is relative to its YAML location.

| Arm | ZIP SHA-256 | Bytes |
| --- | --- | ---: |
| fresh_coder | `18996e1a99265f938fdd702d258fdf21bf5cb60c8fc785b96a70c08d300503c4` | 4,737 |
| recovery_reviewer | `430e64d2c9a60a737f197a5372afa33c4813526239828b71c5971eda283a743e` | 4,779 |

These ZIPs were built inside the Action runner, not published as a new Kaggle notebook and not submitted.

## Scientific contract and next gate

Comparison requires the same pre-selected tasks, model, sampling, original budget, evidence packet and actual wall-time/token accounting. The first outcome is whether the adviser is invoked and changes the next action. The primary outcome is independently graded **final resolved patches per total compute**; empty patches, timeouts, failures and non-invocations stay in the denominator. Original V2 and the already-scored base-only helper (58081411 = 0.17) are external controls.

**Not established yet:** official ADK compiler acceptability, actual model invocation, matched evidence packet formation, reviewer value versus fresh Coder, candidate-history observations, any score gain or transfer.

Before model execution or another official submission: CPU-compile both archives with the current official `adk_submission` wheelhouse and a no-inference model stub; verify `AgentTool` child session behavior; then run a preregistered exposure-clean comparison and budget feasibility check. If the conditional adviser adds overhead without independent correctness gains, remove it; do not add RL or more prompts as a rescue.
