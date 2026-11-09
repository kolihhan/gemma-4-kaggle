# Gemma 4 Developer Agent — competition workspace

**Public** research and engineering workspace for **Google – The Gemma 4 Developer Agent Competition**.

**North star:** build a genuinely stronger, independently verifiable offline software-engineering agent, measured by correctly resolved repository issues **per total evaluation compute**. A valid Kaggle submission is the end-to-end validation deliverable—not the research method.

**Current research plan:** [Goal-aligned replan (2026-11-10)](docs/design/goal-aligned-replan-2026-11-10.md). Prioritize real patch correctness and distinct evidence-backed mechanisms over prompt tuning, extra reviewers, more tool calls, or repeated leaderboard submissions.

**Artifact distinction:** `submission/` currently contains a historical **E4B diagnostic baseline**, **not** the latest scored 31B archive. The best previously scored Public result is **0.17** from an attributed external Budget-Fit V2 reproduction. The later 60-call 31B submission `58164176` was **PENDING** at the last authenticated check. Actual candidate archives are constructed from pinned, verifiable sources by experiment-specific builders; do not assume the in-tree E4B YAML was used for those 31B submissions. Consult [NOW.md](NOW.md) for newer verified results.

**Public-data warning:** this repo is currently PUBLIC. Legacy full-dataset mirrors are historical exposure debt, not a permitted pipeline for new competition data; follow [PUBLIC_VISIBILITY.md](PUBLIC_VISIBILITY.md) and hydrate competition resources at runtime.

## Start here

1. `AGENTS.md` — repo-specific working rules and evidence precedence.
2. `NOW.md` — current decision, verified state, blockers, and next experiment.
3. `docs/research/competition-recon-2026-10-31.md` — current competition fact check, including the stale bundled model-list warning.
4. `docs/design/e4b-baseline-v0.md` — approved minimal baseline design.
5. `submission/` — historical E4B baseline; scored 31B candidates are pinned external-source builds. See the current plan and `NOW.md` before promotion.
6. `docs/evaluation/` — public-corpus profile and failure taxonomy.

## Current baseline

Baseline v0 is deliberately simple:

- base model: `gemma-4-e4b-it-qat-w4a16-ct`
- one root agent
- no LoRA
- no sub-agents
- all 9 official harness tools
- inspect → hypothesize → smallest edit → targeted test → repair → diff/status → `submit_patch`

This is a diagnostic baseline, not a claim that E4B is the best final model. See `NOW.md` before changing it.

## Public development corpus

`tasks.jsonl` contains **129 tasks**. `scripts/analyze_tasks.py` profiles the corpus and produces a deterministic diagnostic sample without requiring the large data mirror.

Verified repo mix:

- FastAPI: 67
- Rich: 48
- Requests: 13
- HTTPX: 1

Run:

```bash
python scripts/analyze_tasks.py tasks.jsonl --per-repo 3
```

See `docs/evaluation/public-corpus-summary.md` for the verified distribution and fixed 10-task diagnostic sample.

## Full competition data

**Historical state only:** this repository used to be private when the legacy mirror was created; it is now **public**. Do not create or publish new raw Competition Data mirrors. For current permitted data handling, follow `PUBLIC_VISIBILITY.md`.

The official `download-all` archive was mirrored on 2026-10-31 to private GitHub Release `kaggle-data-2026-10-31` as **13 checksummed parts**:

- archive bytes: `21,929,290,938`
- archive SHA-256: `69c4c4c3f98bc5e9b0ff80f8660cd1435f69dcc3a3c041198f4b974da5ffea69`
- durable manifest: `manifests/latest.json`

The initial mirror's Kaggle CLI file-inventory command was paginated, so its first-page count is intentionally not treated as an exhaustive inventory. Archive integrity is instead pinned by the official HTTP Content-Length, full archive SHA-256, and all 13 Release-part hashes.

### Restore everything locally

Authenticate `gh` for this private repository, or set `GH_TOKEN` / `GITHUB_TOKEN`, then run:

```bash
python scripts/restore_full_dataset.py --extract-to data --delete-zip-after-extract
```

The restore tool downloads each private Release part, verifies the part checksum, reconstructs the original zip, verifies the full archive size + SHA-256, and extracts it.

Expected extracted competition data includes `docker/`, `embeddings/`, `graphs/`, `sample_submission/`, `sandbox/`, `snapshots/`, `wheels/`, `HARNESS_README.md`, and `tasks.jsonl`.

## Validation

GitHub Actions runs:

- Python compile checks for repo tooling
- unit tests for task-corpus analysis
- static contract tests for the canonical E4B baseline submission
- a real `tasks.jsonl` corpus gate (`129` tasks, `4` repos, deterministic sample)
- restore CLI smoke test

These checks prove repo/tool/layout consistency. They do **not** substitute for an actual competition scorer run; current score status lives in `NOW.md`.
