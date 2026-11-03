# Recovered 12B capacity evidence — 2026-11-03

Status: **historical evidence recovery only. No new model run or submission.**

## Why this matters

The current architecture recon reopened model capacity as a global hypothesis because a public 31B-era system materially outperformed this repo's completed E4B baseline. Before spending new compute on a larger-model probe, the repository history must be checked for already-completed capacity experiments.

Two old branches already contain controlled 12B one-task smokes on `rich_3278` using the same root-coder + verifier-AgentTool lineage:

- `exp/12b-rich3278-ab`
- `exp/12b-thinking1024-rich3278`

These runs were previously not incorporated into the current `exp/reliability-v1` decision state.

## E4B reference on the same task

Historical E4B root-coder + verifier-AgentTool smoke on `rich_3278`:

- official Kaggle L4 runtime;
- duration: about **253.37 s**;
- tool calls: **18 / 32**;
- produced a **275-character** patch;
- `test_exit_code=1`;
- `resolved=false`.

The patch was wrong, but E4B reached mutation/submission behavior inside the five-minute task budget.

## 12B run 1 — default thinking configuration

GitHub Actions run: `41206261407`
Job: `124551828249`
Branch/head: `exp/12b-rich3278-ab` / `41cf1534c7d117d75e594da4fff9f6884aee0f63`
Kaggle kernel: `kolihhan/gemma-4-12b-one-task-smoke`, version 1

Observed structured result:

- model: `gemma-4-12b-it-qat-w4a16-ct`;
- duration: **304.35 s**;
- tool calls: **3**;
- patch chars: **0**;
- `has_patch=false`;
- `test_exit_code=-1`;
- `resolved=false`;
- task hit the five-minute agent timeout without working-tree modifications.

Trace-level behavior shows long reasoning around `rich/ansi.py` and repeated inspection, but no edit before timeout.

## 12B run 2 — thinking budget 1024

GitHub Actions run: `41215364633`
Job: `124578645553`
Branch/head: `exp/12b-thinking1024-rich3278` / `1fcf4cc5526a4f80d47d55cc8d29ad23b8ea0137`
Kaggle kernel: `kolihhan/gemma-4-12b-one-task-smoke`, version 2

Observed structured result:

- model: `gemma-4-12b-it-qat-w4a16-ct`;
- duration: **302.32 s**;
- tool calls: **18**;
- patch chars: **0**;
- `has_patch=false`;
- `test_exit_code=-1`;
- `resolved=false`;
- again hit the five-minute task timeout without working-tree modifications.

Reducing thinking budget increased tool activity from 3 to 18 calls, but did not produce a patch. The trace repeatedly reread the same regex region and attempted small ad-hoc Python checks without converging to an edit.

## What this establishes

### FACT

A naive same-lineage E4B -> 12B swap has already been tried on one clean diagnostic task, twice, including a lower-thinking follow-up.

On that task and five-minute budget:

- E4B produced a wrong patch;
- both 12B variants produced no patch before timeout;
- lower 12B thinking improved action throughput but not task completion.

### INFERENCE

This weakens the hypothesis that **model size alone** is the smallest missing ingredient. It also shows that larger-model capacity and useful task throughput are coupled under the competition's global runtime objective.

The evidence is only one repeatedly inspected task, so it does **not** prove 12B is globally worse than E4B and cannot be used as fresh promotion evidence.

It is sufficient to rule out blindly repeating the same 12B `rich_3278` experiment.

## Updated capacity hypothesis

`H-capacity` remains **REOPENED**, but it must now be stated more precisely:

> A materially stronger model / model-policy combination may improve hidden resolution, but naive 12B substitution under the existing five-minute lineage did not help the historical clean diagnostic.

Therefore do not equate capacity with `swap E4B -> 12B`.

A future capacity test, if triggered by Reliability-v1 feedback, must add new information. Plausible discriminating options include:

1. a carefully frozen **31B same-policy probe** on an untouched denominator, if runtime feasibility is acceptable; or
2. a faithful reproduction of a demonstrably stronger public 31B-era architecture, treated as an architecture/model-class comparison rather than a pure size ablation.

Do not rerun the old 12B `rich_3278` smokes.

## Decision impact while Reliability-v1 is pending

No execution change now:

- keep Reliability-v1 frozen;
- no duplicate Kaggle submission;
- no new GPU run;
- keep evidence-before-mutation as the current provisional lifecycle candidate;
- keep capacity/training hypotheses open;
- when Reliability-v1 becomes terminal, use this recovered evidence before selecting any larger-model experiment.
