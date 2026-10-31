# Gemma 4 Developer Agent — competition workspace

Private working repository for **Google – The Gemma 4 Developer Agent Competition**.

This repo is not just a dataset mirror. It is the source of truth for competition facts, the current experiment, the candidate submission, evaluation evidence, and the private full-data mirror.

## Start here

1. `AGENTS.md` — repo-specific working rules and evidence precedence.
2. `NOW.md` — current decision, verified state, blockers, and next experiment.
3. `docs/research/competition-recon-2026-10-31.md` — current competition fact check, including the stale bundled model-list warning.
4. `docs/design/e4b-baseline-v0.md` — approved minimal baseline design.
5. `submission/` — the **only canonical candidate submission**.
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

The repository is private because Kaggle Competition Data must not be redistributed publicly.

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
