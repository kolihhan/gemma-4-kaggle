# Gemma 4 — paired 31B prompt-only pilot: completed negative result

**Evidence:** [GitHub Actions run 43057377220](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43057377220), completed 2026-11-11 16:56 UTC. Original preregistration: `experiments/public-prompt-vs-v2-disjoint-paired-20261112/manifest.json` on `research/dual-agent-recovery-v0-20261108`.

## Actual measured results

| Preselected public-dev issue | Pinned V2 31B, five minutes | Public prompt-only 31B, five minutes |
|---|---|---|
| `fastapi_14487` | unresolved; patch 10,297 chars; 28 calls; 219.35s | unresolved; patch 5,571 chars; 23 calls; 266.08s |
| `rich_3782` | unresolved; patch 635 chars; 23 calls; 304.34s | unresolved; patch 868 chars; 28 calls; 259.04s |
| `requests_7427` | unresolved; patch 2,918 chars; 15 calls; 303.92s | unresolved; patch 1,150 chars; 20 calls; 303.27s |
| **Total** | **0/3 resolved, 3/3 patches** | **0/3 resolved, 3/3 patches** |

All six runs ended with scorer `test_exit_code=1`. Both arms used identical Gemma 31B weights, tools, sampler, 5min agent limit, 28-tool cap and 80-turn cap. Only `prompts/system.md` changed. Measured task duration includes evaluator overhead. This was private model evaluation, **not an official Kaggle submission**.

## Decision

**Do not promote the public prompt-only treatment:** no observed correctness lift on these three paired issues. This is not proof that the prompts are globally equivalent, and the high stochastic variation in independently scored exact-bundle public entries further limits conclusions. Best authenticated Kaggle Public remains **0.18** for the attributed single-root V2 31B, submission `58183466`; V4-CGR `58222227` scored **0.15**.

Six produced patches and six failed grader tests. **This does NOT establish** why: possible semantic mistakes, incomplete multi-file changes, evaluator setup, insufficient issue context, poor local verification, or repair-loop failures are not separable from grader exit=1.

## Next research action (zero new inference)

The read-only script `scripts/audit_paired_31b_existing_traces.py` targets the **existing private kernel** `kolihhan/gemma4-prompt-v2-paired-43057377220`. If six traces exist, it counts model-called reads, edits, test-like commands, possible repair after a test-like command, submission and tool chronology. If traces are missing it prints **UNOBSERVED**, not a false zero. The GitHub workflow downloads only existing Kaggle outputs, derives safe metadata and prevents raw prompts, patches, test text and grader messages from appearing on public GitHub. No GPU, no official Kaggle submission.

**Pivot rule after safe diagnosis:** late edits / excessive browsing → time-aware direct-agent policy; available test signal without repair → targeted feedback-to-repair; wrong semantics despite adequate inspection → investigate generation capability, task-specification completeness and data-driven adaptation. Do not add more agents or repeat a failed prompt experiment.

## PPO/GRPO checkpoint

- **Restriction:** PPO/GRPO training temporarily deferred, **not permanently forbidden**.
- **Reason:** no robust dataset of independently verified successful coding trajectories, no demonstrated dense/reliable reward scheme for agent actions, and no measured train-vs-inference marginal gain that warrants 31B rollout costs.
- **Pivot trigger:** a reproducible corpus of clean, non-leaking task trajectories and reward checks; a disjoint baseline showing failure mainly from model policy rather than unavailable task instructions; or positive independent test evidence from smaller SFT/LoRA adaptation.
- **Decision:** diagnose the finished six-run experiment first. Any new model training requires an explicit method/budget hypothesis, train/eval separation and frozen tasks.

No change to `submission/`, current Kaggle score, or the pre-existing date-gated one-shot official submission workflow.
