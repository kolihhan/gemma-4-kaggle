# Competition Recon — 2026-10-31

## Decision supported

What is the smallest credible baseline for the current Google – The Gemma 4 Developer Agent Competition, and which competition facts are safe to build against today?

## Primary sources

- Competition Overview / current rules: https://www.kaggle.com/competitions/gemma-4-developer-agent/overview
- Kaggle Staff model announcement: https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/748287
- Official Getting Started notebook / data description: https://www.kaggle.com/code/ryanholbrook/getting-started-gemma-4-developer-agent
- Bundled harness mechanics: repository `HARNESS_README.md`

## FACT / EVIDENCE

### Current model choice

Kaggle's current official material allows these competition base variants:

- `gemma-4-31b-it-qat-w4a16-ct`
- `gemma-4-12b-it-qat-w4a16-ct`
- `gemma-4-e4b-it-qat-w4a16-ct`
- `gemma-4-e2b-it-qat-w4a16-ct`

A single submission must use one base-model variant. Different agents may use different LoRA adapters on that same base model.

E2B/E4B are eligible for the competition's Small Model Development bonus while still participating in the main competition.

### Stale bundled documentation

The bundled `HARNESS_README.md` describes a 31B-only competition allow-list. That section predates the current Kaggle Staff update adding 12B/E4B/E2B. Therefore:

- Use current Kaggle sources for mutable competition rules and model eligibility.
- Continue using `HARNESS_README.md` for the technical submission schema, sandbox behavior, tool contract, patch extraction, and evaluator mechanics unless a newer official source contradicts them.

### Task and scoring shape

- Public development corpus: 129 tasks.
- Hidden evaluation is issue-resolution style: each task ultimately resolves or does not resolve after the submitted patch is tested.
- Competition evaluation has a 12-hour total runtime constraint.
- Public data provides repository snapshots plus graph/embedding assets and an offline wheelhouse.

### Harness mechanics relevant to agent design

The harness exposes 9 workspace/code-intelligence tools:

1. `run_command`
2. `submit_patch`
3. `get_status`
4. `read_file`
5. `edit_file`
6. `write_file`
7. `get_code_neighbors`
8. `search_similar_code`
9. `get_code_subgraph`

The task sandbox is offline. The agent should not attempt package downloads. It should work inside `/workspace`, verify changes, and call `submit_patch` when finished.

The graph tools are only useful when graph/embedding assets are available and should be treated as navigation aids, not mandatory ritual calls.

## INFERENCE

### Why E4B is the first baseline

E4B is a rational first experiment because it creates a clean small-model track, is eligible for the small-model bonus, and makes it easier to test whether navigation discipline, targeted tests, and additional test-time compute can compensate for model size.

This does **not** establish that E4B will outperform 12B or 31B. The first requirement is scorer compatibility and an actual end-to-end run.

### Baseline should remain single-agent

The public task is already a closed-loop SWE task with useful tools and test feedback. Before adding sub-agents, we need evidence that failures come from decomposition/role specialization rather than simple location, reasoning, editing, testing, or budget errors.

### No LoRA initially

A no-LoRA baseline isolates agent policy from training effects. Fine-tuning becomes justified only if repeated failures remain systematic after prompt/tool/repair improvements.

## UNKNOWN

- E4B scorer reliability on the newest competition wheelhouse has not yet been demonstrated in this repo.
- E4B versus 12B versus 31B resolution/time trade-off is unmeasured here.
- Optimal tool-call/time/turn budgets are unmeasured.
- Whether explicit graph-first navigation improves resolution is unmeasured.
- Whether a sub-agent improves performance enough to justify extra context/tool overhead is unmeasured.
- No current leaderboard score belongs to this repository yet.

## REJECTED / corrected assumptions

- **Rejected:** bundled `HARNESS_README.md` proves the competition is 31B-only. It is stale on this mutable rule.
- **Rejected:** a `3 tasks × 4 repos = 12 task` public diagnostic sample exists. HTTPX has only one public task; the deterministic `per_repo=3` sample contains 10 tasks.
- **Rejected:** dataset mirroring alone constitutes a competition project. Data infrastructure is necessary but is not the experiment/submission source of truth.

## NEXT TEST

Validate `submission/` with the current competition wheelhouse/scorer using E4B. If accepted, run one public task end-to-end before changing architecture or adding training.
