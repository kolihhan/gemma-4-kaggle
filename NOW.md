# NOW — 2026-10-31

## North star

Build a competitive, evidence-driven Gemma 4 software-engineering agent. Optimize for real task resolution, not architectural novelty. Add complexity only when controlled failures justify it.

## Current decision

**Current experiment:** E4B `SequentialAgent` with exactly two roles:

1. `coder` — makes the smallest evidence-backed patch and runs targeted verification; no `submit_patch`, no `write_file`.
2. `verifier` — independently inspects the existing diff/test evidence, may make at most one narrow repair, and owns final `submit_patch`; no `write_file`.

The topology is mechanically valid. The current variable under test is the verifier policy: it must verify first, read failing-test evidence before repair, and must not submit a patch that is still known to fail.

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
4. **Bounded edit tools (`write_file` removed, `submit_patch` restored):** failed but was much cleaner — **319-char / one-line patch, 4 tool calls**, no destructive rewrite. Remaining failure shifted to exact semantics plus test-feedback handling.

Conclusion: edit safety is largely addressed. Independent verification is justified; extra agents beyond coder → verifier are not yet justified.

## Sequential coder → verifier evidence

### Plumbing

- Canonical root: `submission/agent.yaml` with `agent_class: SequentialAgent`.
- Canonical sub-agents: `submission/sub_agents/coder.yaml` and `submission/sub_agents/verifier.yaml`.
- First L4 attempt failed before agent execution with `expected only gemma-4-e4b-it-qat-w4a16-ct, got []`.
- Root cause: sub-agent `!include` paths were interpreted relative to `submission/sub_agents/`; the resulting load failures made model discovery silently skip both sub-agents.
- Fixed paths: `../prompts/...` and `../configs/...`.
- Regression contract now locks this include behavior.

### First mechanically valid coder → verifier run — FAIL

Same task/model/budget (`rich_3278`, E4B):

- duration: **189.34 s**
- tool calls: **15 / 32**
- final patch: **320 chars**, one file / one-line regex change
- `test_exit_code=1`
- `resolved=false`
- coder and verifier both executed successfully; the topology and model discovery are valid.

The full trace changed the diagnosis: the verifier did **not** arbitrarily ignore failed tests. The old verifier prompt explicitly instructed it that after one bounded repair, if tests still failed, it should preserve the “smallest defensible patch” and call `submit_patch` to terminate. The verifier followed that instruction almost literally after its second failing test.

Therefore the known-failing submission was a **policy bug in our prompt**, not sufficient evidence of E4B incapacity.

### Verifier policy fix — CI GREEN

The verifier now must:

1. inspect the existing diff before editing;
2. run the **smallest directly relevant test** rather than starting with the full suite;
3. read failing-test output and the failing test / nearby assertions before repair;
4. make at most one evidence-backed narrow repair;
5. re-run the same targeted verification;
6. call `submit_patch` **only after targeted verification passes**;
7. if verification still fails, **do not submit**; finish and let harness patch recovery preserve the working-tree diff.

TDD regression tests cover these rules. Latest repo validation passes compile, all unit tests, the real 129-task corpus gate, and restore CLI smoke.

**Next evidence required:** rerun the exact same `rich_3278` E4B coder → verifier experiment with only this verifier-policy change.

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

Gold `rich_3278` passes. The next valid evidence is the same-task coder → verifier rerun after the verifier-policy fix.

## Next step

1. Rerun `rich_3278` with the current E4B coder → verifier submission; change no other variable.
2. Inspect trace for targeted-test selection, failing-test reading, bounded repair, and submit/no-submit behavior.
3. If it resolves, expand to the fixed clean-task diagnostic sample before adding architecture.
4. If it still fails after following the corrected policy, compare the same topology with a larger allowed base model before adding a third agent, LoRA, or more graph machinery.
