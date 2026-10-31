# Repository Agent Instructions

This repository is the source of truth for Ko Lih Han's **Google – The Gemma 4 Developer Agent Competition** work.

## Entry order

For substantive work in this repository:

1. Read `NOW.md` first.
2. Read the relevant current artifact under `docs/`.
3. Inspect `submission/` before proposing or implementing agent changes.
4. Use the personal workflow router from `kolihhan/kolihhan` when available: Claude-like outer loop, then the smallest relevant inner mode (`Repo Understanding`, `Development`, `Research Mode Heavy`, or `Grill Mode`).
5. Execute and verify; update `NOW.md` after durable progress.

Do not restart from old chat assumptions when repo state is available.

## Evidence precedence

Mutable competition facts can change during the event. Use this precedence:

1. Current official Kaggle Overview / Rules / Data pages.
2. Current Kaggle Staff announcements in the competition discussion.
3. Competition-provided files and `HARNESS_README.md` for harness mechanics.
4. Community discussion only as supplementary evidence.

`HARNESS_README.md` is bundled competition documentation, but it is **not automatically current for mutable rules**. As of 2026-10-31 its model allow-list section is stale relative to Kaggle's current official model announcement. Do not let that stale section override current Kaggle rules.

## Canonical project state

- `NOW.md` — current status, decisions, blockers, and next experiment.
- `docs/research/` — dated competition reconnaissance and fact checks.
- `docs/design/` — approved experiment / agent designs.
- `docs/evaluation/` — corpus analysis, run logs, and failure taxonomy.
- `docs/superpowers/plans/` — implementation plans for non-trivial changes.
- `submission/` — the **only canonical candidate submission artifact**.

GitHub Release data mirrors are infrastructure, not experiment state.

## Experiment discipline

- Never claim a leaderboard/local score without an actual recorded run.
- Every meaningful experiment should record: git commit, base model, config, sample/tasks, resolved count, elapsed time, tool calls when available, and dominant failure classes.
- Change one major variable at a time when diagnosing improvements.
- Do not add sub-agents, LoRA, skills, or extra orchestration without evidence from baseline failures.
- Reference patches in `tasks.jsonl` are analysis/evaluation labels. Do not expose them to the agent during a blind benchmark run.
- Prefer the smallest reproducible experiment that can falsify the current hypothesis.

## Data handling

Competition data must remain private. Do not commit the full dataset as ordinary Git blobs and do not publish it in a public Release. The private Release mirror and `scripts/restore_full_dataset.py` are the supported storage path.

## Completion standard

Before saying work is complete, inspect the resulting repo state and run the relevant checks. Report verified, inferred, and unknown states separately when material.
