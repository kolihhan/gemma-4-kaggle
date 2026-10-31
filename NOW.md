# NOW — 2026-10-31

## North star

Build a competitive, evidence-driven Gemma 4 software-engineering agent. Optimize for real task resolution, not architectural novelty. Add complexity only when controlled failures justify it.

## Current decision

**Current experiment:** E4B `SequentialAgent` with exactly two roles:

1. `coder` — makes the smallest evidence-backed patch and runs targeted verification; no `submit_patch`, no `write_file`.
2. `verifier` — independently inspects the existing diff/test evidence, may make at most one narrow repair, and owns final `submit_patch`; no `write_file`.

This is the first justified step beyond the single-agent baseline. It was introduced only after repeated clean-task evidence showed that one E4B agent could make a small patch but still submit despite failed targeted verification.

## Verified current facts

- Current Kaggle rules permit four base variants: 31B, 12B, E4B, and E2B QAT models.
- The bundled `HARNESS_README.md` has a stale 31B-only model-list statement; use it for harness mechanics, not current model eligibility.
- Public development corpus: **129 tasks** — FastAPI 67 / Rich 48 / Requests 13 / HTTPX 1.
- Reference changed-line buckets: **1–10: 60 / 11–30: 29 / 31–80: 20 / 81+: 20**.
- Deterministic `per_repo=3` diagnostic sample has **10 tasks** because HTTPX has only one public task.
- Current runtime uses the official scorer wheelhouse, pinned Python 3.12 Kaggle image, and L4 ×4 for E4B.
- Current `adk-submission` wheel observed in the scorer wheelhouse is **0.2.13**.
- `SequentialAgent` and nested `config_path` sub-agents are supported by the current compiler.
- `discover_declared_models()` recursively follows nested `config_path` references and collects `model` fields.
- `!include` paths are resolved **relative to the YAML file containing the include**, not the submission root.

## Clean diagnostic evidence: `rich_3278`

### Gold control — PASS

- Exact current verifier with the hydrated reference patch: **23/23 tests pass**, `test_exit_code=0`, `resolved=true`.
- Reference patch size: **176 chars**.
- Therefore `rich_3278` is a clean agent-quality diagnostic.

### Single-agent experiment sequence

1. **Original baseline:** failed; destructive full-file rewrite, patch about 4 KB. Main failure: F3 EDIT plus F4/F5 repair/submission behavior.
2. **Soft edit/test guardrails:** failed, but materially improved edit safety; patch shrank to about 817 chars and whole-file rewrite disappeared. Agent still submitted after failed verification.
3. **Hard no-submit / automatic patch recovery:** regressed; 17 tool calls, about 4.2 KB patch, full-file rewrite returned, then context overflow. Rejected as an intervention.
4. **Bounded edit tools (`write_file` removed, `submit_patch` restored):** failed but was much cleaner — **319-char / one-line patch, 4 tool calls**, no destructive rewrite. Remaining failure shifted to F2 exact semantics plus F4/F5 test-feedback handling; the agent still submitted after targeted tests failed.

Conclusion: edit safety is largely addressed. The next bottleneck is independent verification/repair before final submission, which justifies the two-role coder → verifier experiment.

## Sequential coder → verifier status

- Canonical root: `submission/agent.yaml` with `agent_class: SequentialAgent`.
- Canonical sub-agents: `submission/sub_agents/coder.yaml` and `submission/sub_agents/verifier.yaml`.
- First L4 attempt failed **before agent execution** with `expected only gemma-4-e4b-it-qat-w4a16-ct, got []`.
- Root cause was submission plumbing, not the architecture: sub-agent YAML files used root-looking `!include prompts/...` and `!include configs/...` paths, but current `adk-submission` resolves includes relative to the including YAML's directory. Model discovery silently skipped those sub-agent configs when loading them failed.
- TDD regression contract now requires sub-agent-relative includes.
- Fixed paths are `../prompts/...` and `../configs/...` in both sub-agent configs.
- Repo validation CI is green after the fix.
- **Same-task L4 rerun on `rich_3278` is currently pending/in progress.** Do not change coder/verifier prompts, tools, model, or budget until this rerun reaches a structured result.

## HTTPX exclusion

`httpx_3672` remains harness-confounded:

- E4B smoke produced a patch but verifier returned exit 2.
- Gold reference patch also returned exit 2 due test-collection failure (`httpx.Stream` mismatch).
- Exclude it from agent-quality conclusions unless the harness changes.

## Canonical artifacts

- Current state: `NOW.md`
- Current fact check: `docs/research/competition-recon-2026-10-31.md`
- Public corpus profile: `docs/evaluation/public-corpus-summary.md`
- Failure taxonomy: `docs/evaluation/failure-taxonomy.md`
- Candidate submission: `submission/`
- Smoke runtime: `kaggle/smoke_runtime.py`

## Data mirror

**COMPLETE and checksummed.**

- Private Release: `kaggle-data-2026-10-31`.
- **13/13** archive parts uploaded.
- Archive size: **21,929,290,938 bytes**.
- Kaggle HTTP Content-Length matched exactly.
- Whole-archive SHA-256: `69c4c4c3f98bc5e9b0ff80f8660cd1435f69dcc3a3c041198f4b974da5ffea69`.
- Durable manifests: `manifests/latest.json` and `manifests/kaggle-data-2026-10-31.json`.

## Score status

**NO CLEAN RESOLVED AGENT CASE YET. NO LEADERBOARD SCORE RECORDED.**

Gold `rich_3278` passes, so the next valid evidence is the coder → verifier rerun on that exact task.

## Next step

1. Finish the current `rich_3278` coder → verifier L4 rerun.
2. If the runtime is mechanically valid, classify the actual coder/verifier outcome from trace + patch + verifier result.
3. If it resolves, run the fixed clean-task diagnostic sample before adding more architecture.
4. If it still fails, change only the failure mechanism demonstrated by the trace; do not add LoRA/graph/more agents by default.
