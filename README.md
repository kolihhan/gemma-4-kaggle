# Gemma 4 — Stronger SWE Agent, Kaggle Competition

This **public** repository is a research and execution workspace for Google's **Gemma 4 Developer Agent Competition**.

**Actual mission:** design and deliver a *stronger offline software-engineering coding agent* that resolves more unseen GitHub issues, completes Kaggle's **12-hour aggregate agent budget**, and earns a verified official score. **CPU compilation, GitHub Actions success and submission acceptance are not solver-quality results.** We own the next substantial architecture improvement; no speculative self-managed training or endless leaderboard tuning.

**Read first:** [Current PI execution plan](docs/design/goal-aligned-replan-2026-11-10.md) → [NOW](NOW.md) → [Repo instructions](AGENTS.md). Only one new primary solver candidate and one idempotent official submission per candidate.

**Current provenance (authenticated 2026-11-10 02:55 UTC):** Best scored public reference **0.17** from an attributed, third-party Budget-Fit V2 31B reproduction (ref **58019162**). Toolcap60 8-minute **58164176** produced an unscored Notebook Timeout; bounded 5-minute recovery **58183466** remains **PENDING** at that check. Neither is an original V3-quality improvement. See [timeout analysis](docs/evaluation/toolcap60-notebook-timeout-recovery-2026-11-10.md).

**Real architecture:** Competition issue + offline repo → Gemma 4 ADK coder → code evidence → materialized patch → diagnostic test/repair → submit_patch → independent PASS/FAIL. GitHub scripts/Actions and Kaggle CPU notebooks are only the build, validation and submission **control plane**. The historical **submission/** tree is E4B and is **not** the currently scored 31B artifact; experiments/solver-v3/ is the future candidate lane and is **not yet implemented**.

**Public-data safety:** follow [PUBLIC_VISIBILITY.md](PUBLIC_VISIBILITY.md). Historical full Kaggle data mirrors are legacy exposure debt. Do not add raw competition files, reference patches, private task traces or credentials to this public repo. Hydrate private competition resources at run time.

## Start here

1. `AGENTS.md` — repo-specific working rules and evidence precedence.
2. `NOW.md` — current decision, verified state, blockers, and next experiment.
3. `docs/research/competition-recon-2026-10-31.md` — current competition fact check, including the stale bundled model-list warning.
4. `docs/design/e4b-baseline-v0.md` — approved minimal baseline design.
5. `submission/` — historical E4B diagnostic baseline, not the current 31B competition ZIP. See the PI plan for deliberate candidate promotion.
6. `docs/evaluation/` — public-corpus profile and failure taxonomy.

## Historical E4B diagnostic baseline (not the current competitive system)

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

Historical restore instruction (not a new data-mirroring workflow): authenticate an appropriately authorized GitHub client, then run:

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
