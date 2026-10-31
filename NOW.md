# NOW — 2026-10-31

## North star

Build a competitive, evidence-driven Gemma 4 software-engineering agent. Optimize for real task resolution, not architectural novelty. Keep the first baseline diagnostic and cheap enough to iterate.

## Current decision

**Baseline v0:** `gemma-4-e4b-it-qat-w4a16-ct`, one `LlmAgent`, no LoRA, no sub-agents, no custom skill package. Give it all 9 harness tools and a disciplined inspect → hypothesize → edit → test → repair → submit loop.

Why E4B first:

- Current Kaggle rules allow E4B.
- E2B/E4B are eligible for the Small Model Development bonus.
- Smaller-model iteration gives us a useful test of whether better tool use / test-time compute can offset model size.
- This is a starting hypothesis, not a proven winner.

## Verified current facts

- Current official Kaggle model announcement permits four base variants: 31B, 12B, E4B, and E2B QAT models. A submission uses one base variant; agent-specific LoRA adapters may differ.
- The bundled `HARNESS_README.md` still says 31B-only. Treat that model-list statement as stale; keep using the file for harness/tool mechanics.
- Public development corpus: **129 tasks**.
- Real corpus breakdown from `tasks.jsonl`: **FastAPI 67 / Rich 48 / Requests 13 / HTTPX 1**.
- Reference-solution changed-line buckets: **1–10: 60 / 11–30: 29 / 31–80: 20 / 81+: 20**.
- Median problem statement length: **418 characters**; max: **10,095**.
- No public task currently has `hints_text` populated.
- The deterministic `per_repo=3` diagnostic sample has **10 tasks**, not 12, because HTTPX has only one public task.
- Harness mechanics expose 9 tools: `run_command`, `submit_patch`, `get_status`, `read_file`, `edit_file`, `write_file`, `get_code_neighbors`, `search_similar_code`, `get_code_subgraph`.
- Sandbox is offline; dependency downloads are not part of the agent strategy.

## Canonical artifacts

- Current fact check: `docs/research/competition-recon-2026-10-31.md`
- Public corpus profile: `docs/evaluation/public-corpus-summary.md`
- Baseline design: `docs/design/e4b-baseline-v0.md`
- Failure taxonomy: `docs/evaluation/failure-taxonomy.md`
- Implementation plan: `docs/superpowers/plans/2026-10-31-e4b-baseline-v0.md`
- Candidate submission: `submission/`

## Data mirror

- Repository is private.
- `KAGGLE_API_TOKEN` gate has passed.
- Full official competition archive is being mirrored to private GitHub Release `kaggle-data-2026-10-31` in 1.8 GB parts.
- Do **not** mark the mirror complete until all parts are `uploaded` and `manifests/latest.json` records the full archive size + SHA-256.
- A concurrent-main-update risk was discovered: the current long-running mirror started from an older commit, so its final manifest `git push` may require recovery/rebase even if all Release assets upload correctly.

## Score status

**NOT RUN.** No valid E4B local scorer result or Kaggle leaderboard score has been recorded yet.

## Next experiment order

1. Finish/verify the private full-data mirror and recover the manifest if the final push races with newer commits.
2. Validate the baseline submission against the **current** competition wheelhouse/scorer, especially E4B model acceptance.
3. Run a smoke task end-to-end.
4. Run the deterministic 10-task public diagnostic sample.
5. Classify failures with `docs/evaluation/failure-taxonomy.md`.
6. Only then choose the next intervention: graph policy, test/repair policy, context handling, sub-agent, or LoRA.

## Stop conditions

Do not add multi-agent orchestration or training just because they are available. Add complexity only when repeated baseline failures identify a concrete bottleneck it can plausibly fix.
