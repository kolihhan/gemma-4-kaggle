# Repository Agent Instructions

This repository is the source of truth for Ko Lih Han's **Google – The Gemma 4 Developer Agent Competition** work.

## Entry order

For substantive work in this repository:

1. Read `NOW.md` first.
2. Read `PUBLIC_VISIBILITY.md` before any task involving repository visibility, Actions billing, Releases, data mirroring, competition resources, or public sharing.
3. Read the relevant current artifact under `docs/`.
4. Inspect `submission/` before proposing or implementing agent changes.
5. Use the personal workflow router from `kolihhan/kolihhan` when available: Claude-like outer loop, then the smallest relevant inner mode (`Repo Understanding`, `Development`, `Research Mode Heavy`, or `Grill Mode`).
6. Execute and verify; update `NOW.md` after durable progress.

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
- `PUBLIC_VISIBILITY.md` — repository-publicity and competition-resource execution policy.
- `docs/research/` — dated competition reconnaissance and fact checks.
- `docs/design/` — approved experiment / agent designs.
- `docs/evaluation/` — corpus analysis, run logs, and failure taxonomy.
- `docs/superpowers/plans/` — implementation plans for non-trivial changes.
- `submission/` — the **only canonical candidate submission artifact**.

GitHub Release data mirrors are legacy infrastructure, not experiment state and not the supported path for new runs.

## Experiment discipline

- Never claim a leaderboard/local score without an actual recorded run.
- Every meaningful experiment should record: git commit, base model, config, sample/tasks, resolved count, elapsed time, tool calls when available, and dominant failure classes.
- Change one major variable at a time when diagnosing improvements.
- Do not add sub-agents, LoRA, skills, or extra orchestration without evidence from baseline failures.
- Reference patches in `tasks.jsonl` are analysis/evaluation labels. Do not expose them to the agent during a blind benchmark run.
- Prefer the smallest reproducible experiment that can falsify the current hypothesis.

### Resource discipline

- Reuse existing runs and artifacts before launching new compute. Do not rerun an already-inspected denominator merely to obtain another sample of the same evidence.
- For this public repository, use GitHub Actions freely for cheap orchestration, static checks, read-only probes, reproducibility, artifact handling, and deployment automation when they reduce manual work.
- Treat Kaggle GPU/kernel execution and full evaluations as expensive. Launch them only when the result can change a concrete decision or falsify a named hypothesis.
- Prefer a staged gate: static/read-only checks first, then the smallest useful execution, then an expensive run only if the earlier evidence leaves a material uncertainty.
- Never duplicate a diagnostic or submission while an equivalent run is already active or while an existing artifact answers the question.

### Mechanism-first research

- Do not optimize only for a reliable-looking combination of prompts, tools, topology, or model components. Explain **why** the intervention should work.
- Before implementing a research candidate, name: the targeted failure class/bottleneck, proposed mechanism, assumptions, expected observable side effects, and a falsifier.
- A leaderboard gain is outcome evidence, not proof of the proposed mechanism. Require an untouched/local check, ablation, counterfactual, or other discriminating evidence before making a strong causal claim.
- When evidence contradicts the current priority, rerank hypotheses instead of protecting the old plan. For example, low tool use with poor resolution weakens a pure compute-efficiency explanation and should shift attention toward information quality, root-cause understanding, editing, or repair.
- After each informative failure, ask what capability is missing, what assumption is unnecessarily restrictive, and what smallest new idea could break the bottleneck. Prefer a genuine new capability or decision rule over benchmark-specific prompt accumulation.
- Keep research and deployment coupled: once a mechanism survives an independent check, deploy the smallest implementation that expresses it, then compare expected vs observed behavior without silently tuning to the same evidence.

## Data handling

For **new** data-requiring runs, do not create new public GitHub mirrors of raw Competition Data.

Preferred execution path:

- hydrate Competition Data at runtime through authenticated/private Kaggle resources;
- for evaluation, prefer private Kaggle kernels with the competition attached through `competition_sources`;
- use Kaggle model sources or private Kaggle datasets for model/adapter resources as appropriate;
- GitHub Actions may consume vetted derived artifacts needed for reproducibility, but must not newly publish raw Competition Data, reference patches, hidden tests, or equivalent redistributable archives;
- keep `.github/workflows/mirror-full-kaggle-data.yml` fail-closed while this repository is public.

Existing Release/history/tree exposure is legacy cleanup debt. It must not be represented as leak-free, but it does **not** block scientific execution under the runtime-hydration policy.

## Public repository policy

`PUBLIC_VISIBILITY.md` is **not a hard scientific stop** merely because the repository is public.

- Continue experiments if they use the runtime-hydration policy and do not create new persistent public exposure.
- Do not create another full Competition Data GitHub Release or commit new raw data blobs.
- Do not assume public GitHub code alone satisfies every mutable Kaggle public-sharing requirement; verify current rules when that matters to an external publication/submission decision.
- Destructive cleanup such as deleting Release assets or rewriting history requires explicit user authorization unless the user has already authorized that exact action.
- Publicity/infrastructure changes must not alter scientific experiments, evaluation contracts, blind sets, LoRA configurations, prompts, reliability calibration, or submission candidates.

## Completion standard

Before saying work is complete, inspect the resulting repo state and run the relevant checks. Report verified, inferred, and unknown states separately when material.
