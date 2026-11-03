# Public Repository Execution Policy

**Status: PUBLIC EXECUTION ALLOWED — LEGACY EXPOSURE CLEANUP DEFERRED.**

Last decision: 2026-11-03.

The repository may remain public while scientific work continues. Public visibility by itself is **not** a blocker for verifier-LoRA, reliability calibration, or other experiments.

This is not a claim that the repository has never exposed Competition Data or that all historical exposure has been cleaned up.

## Current execution model

For all new data-requiring experiment runs:

- keep GitHub focused on code, configuration, frozen task IDs, derived metrics, and non-sensitive experiment evidence;
- hydrate Competition Data at execution time through authenticated/private Kaggle resources rather than creating a new GitHub data mirror;
- prefer private Kaggle kernels with `competition_sources: ["gemma-4-developer-agent"]` for evaluation runs;
- use Kaggle `model_sources` / private Kaggle datasets for model or adapter resources where appropriate;
- authenticated GitHub Actions may download vetted derived artifacts needed to continue a run, but must not publish raw Competition Data, reference patches, hidden test material, or equivalent redistributable archives as new public GitHub artifacts/Releases;
- do not create a new full Competition Data GitHub Release or commit new raw Competition Data blobs;
- keep `.github/workflows/mirror-full-kaggle-data.yml` fail-closed while the repository is public.

The current verifier-LoRA/reliability execution paths follow the intended direction: GitHub renders and pushes private Kaggle kernels, while Kaggle mounts competition resources at runtime. Private Kaggle datasets/model sources carry adapters or model resources where needed.

## Legacy exposure

Historical exposure remains separate cleanup debt:

- the old GitHub Release tagged `kaggle-data-2026-10-31` may still exist;
- `tasks.jsonl` exists in reachable repository state/history;
- older workflow artifacts and historical commits may require a later cleanup audit.

These facts mean the repository must **not** be described as leak-free today. They do not, by themselves, block new scientific execution under the runtime-hydration policy above.

Destructive cleanup such as deleting Release assets or rewriting Git history still requires explicit authorization.

## Agent instruction

If a task involves repository visibility, GitHub Actions, Releases, competition resources, or public sharing:

1. read this file first;
2. do **not** stop scientific work solely because the repository is public;
3. do stop any proposed change that would create **new persistent public exposure** of raw Competition Data, reference solutions/patches, hidden tests, secrets, or equivalent material;
4. use authenticated/runtime resource hydration for new runs instead of GitHub raw-data mirrors;
5. treat legacy Release/history cleanup as a separate infrastructure task unless the user explicitly asks to perform it;
6. do not claim the repository is leak-free until a separate cleanup audit establishes that.

Keep repository-publicity decisions independent from scientific experiment contracts: visibility policy must not silently alter blind sets, prompts, topology, LoRA configuration, evaluation metrics, reliability calibration, or submission candidates.
