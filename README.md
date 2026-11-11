# Gemma 4 Developer Agent — competition research workspace

**Repository visibility: PUBLIC.** Historical competition resources may still be exposed through Git history. Do not upload raw competition data, hidden tests, private evaluation traces, reference patches or credentials. See [PUBLIC_VISIBILITY.md](PUBLIC_VISIBILITY.md).

**Mission:** produce a stronger offline GitHub-issue repair agent under the official Kaggle time and model constraints. Prefer independent issue resolution, task completion and reproducible scoring over prompt complexity or CPU compilation success.

## Read first

- [NOW.md](NOW.md) — concise verified project status, current score, submission ID, active and rejected methods. Date-stamped: check the authenticated Kaggle ledger again for live results.
- [AGENTS.md](AGENTS.md) — repository instructions and execution order.
- [RESEARCH_DOCTRINE.md](RESEARCH_DOCTRINE.md) — methodology, negative evidence and pivot triggers.
- [EVALUATION_POLICY.md](EVALUATION_POLICY.md) — criteria distinguishing CPU mechanical checks, real model behavior, independently resolved tasks and official scores.
- [PUBLIC_VISIBILITY.md](PUBLIC_VISIBILITY.md) — public repository / private competition-resource safeguards.

## Source and execution branches

**The default `main` branch is NOT the complete research implementation.** The latest architecture experiments, private Kaggle pilots, official result audits and detailed evidence currently live on [`research/dual-agent-recovery-v0-20261108`](https://github.com/kolihhan/gemma-4-kaggle/tree/research/dual-agent-recovery-v0-20261108). Do not silently treat `main/submission/` as the latest scoring artifact; it is a historical E4B implementation.

The research branch includes `scripts/build_wrapped_scope_coder_candidate.py` and the official scripted-model ADK/compaction gate. Its engineering gate passed, but **real Gemma 31B task correctness and autonomous workflow uptake remain unmeasured**.

## Official results — authenticated 2026-11-11 23:36 MYT

- Best **completed/scored** Public result: **0.18**, submission **58183466**, attributed Budget-Fit V2 bounded configuration.
- Official V4-CGR submission **58222227** is **COMPLETE, Public 0.15**, below the 0.18 best. [Official receipt](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42946421274); [authenticated score check](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42947403444). Do not resubmit unchanged.
- Old optional Contract & Impact 31B private pilot: **0/4 resolved vs 0/4 for V2** on four public-development tasks. This does not prove that all contract-based repair approaches fail.
- Wrapped Scope/Coder: **scripted ADK CPU pass**, but actual private Gemma 31B [one-task test](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42988852829) had **1 Workflow call, 0 successful returns, 1 error, 0 edits, 0/1 resolved** after about 302.5 seconds. This is a negative feasibility result, not an architecture improvement. [Read-only trace diagnosis](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43050260136).

## Minimal contribution/experiment rules

1. Preregister tasks, baseline/treatment code digests, model and shared end-to-end budget. Do not choose tasks after viewing treatment outcomes.
2. Check current official Kaggle rules and quota before any new private GPU inference or competition submission. Use unique private kernels.
3. Keep all raw Competition Data and reference answers away from model input and from **new** persistent public GitHub mirrors. Public repo history remains legacy cleanup debt.
4. Report *verified*, *inferred* and *unknown* separately. Model/tool scripted tests are not proof of correct code patches or leaderboard gains.
5. Update the current source of truth through a reviewed change; do not let `NOW.md` grow by endlessly prepending historical logs.

Historical `main` baseline and private-mirror setup details remain available in prior Git revisions; they are **not** instructions to recreate a public competition-data mirror.
