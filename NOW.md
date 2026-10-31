# NOW — 2026-10-31

## North star

Build a competitive, evidence-driven Gemma 4 software-engineering agent. Optimize for real task resolution, not architectural novelty. Add complexity only when controlled failures justify it.

## Current decision

**Current candidate topology:** root coder `LlmAgent` + one verifier `AgentTool`.

1. Root coder owns inspect → patch → local verification and has no `submit_patch` / `write_file`.
2. Verifier AgentTool independently inspects the shared working tree, may make at most one narrow repair, and owns `submit_patch`.
3. The canonical candidate remains `gemma-4-e4b-it-qat-w4a16-ct`.

Why this replaced `SequentialAgent`: the official harness enables event compaction, and current ADK automatic compaction requires a root `LlmAgent` model. A root `SequentialAgent` produced `ValueError: No LlmAgent model available for event compaction summarizer` after a real run. Root `LlmAgent` + verifier AgentTool preserves two roles while giving the compactor a canonical root model.

The exact same topology/prompts/budgets were tested on 12B. The 12B model loaded successfully with the official HF override, but under the existing 4096-token thinking budget it timed out before editing or reaching the verifier. Therefore **12B@4096 is rejected as the current candidate**; the failure is throughput/tool-use efficiency, not the E4B verification-gate failure mode.

**Next controlled experiment:** one 12B follow-up on `rich_3278` with the same topology/prompts/time/tool budgets but a lower `thinking_budget` (1024). This isolates whether 12B was defeated by overthinking latency before abandoning the model-size path. Do not add a third agent, LoRA, or graph machinery yet.

## Verified current facts

- Kaggle currently permits 31B, 12B, E4B, and E2B QAT variants; all agents/sub-agents in one submission must use the same base variant.
- Public development corpus: **129 tasks** — FastAPI 67 / Rich 48 / Requests 13 / HTTPX 1.
- Reference changed-line buckets: **1–10: 60 / 11–30: 29 / 31–80: 20 / 81+: 20**.
- Deterministic `per_repo=3` diagnostic sample has **10 tasks** because HTTPX has only one public task.
- Current runtime uses the official scorer wheelhouse, pinned Python 3.12 Kaggle image, and L4 ×4 for E4B/12B smoke runs.
- Current wheelhouse observed: `adk-submission 0.2.13`, `swegemma 0.2.11`.
- `!include` paths resolve relative to the YAML file containing the include.
- `AgentTool` is accepted by the current Kaggle runtime; its exposed tool name is the child agent name.
- Kaggle staff says 12B needs a vLLM HF override mapping it to `Gemma4ForCausalLM` / `gemma4`; the 12B smoke proved that override can boot the model successfully in the current Kaggle environment.

## Clean diagnostic: `rich_3278`

### Gold control — PASS

- Hydrated reference patch under the current verifier: **23/23 tests pass**, `test_exit_code=0`, `resolved=true`.
- Reference patch size: **176 chars**.
- Therefore `rich_3278` is a clean agent-quality diagnostic.

### Single-agent E4B sequence

1. Original baseline: destructive ~4 KB rewrite; F3 EDIT plus F4/F5 repair/submission failure.
2. Soft guardrails: ~817-char patch; destructive rewrite disappeared, but failed verification still led to submission.
3. Hard no-submit/recovery: regressed to ~4.2 KB, 17 calls, context overflow; rejected.
4. Bounded tools (`write_file` removed): **319 chars, 4 calls**, no destructive rewrite. Remaining failure shifted to exact semantics/test-feedback handling.

Conclusion: edit safety improved materially; verification/reasoning is the remaining bottleneck.

## Two-role E4B evidence

### Sequential coder → verifier: mechanically valid but compaction-unsafe

First valid run after fixing relative `!include` paths:

- `rich_3278`, E4B
- **189.34 s**, **15 calls**, **320-char** patch
- `test_exit_code=1`, `resolved=false`

Initial diagnosis changed after trace review: the verifier submitted a known-failing patch because our old verifier prompt explicitly told it to preserve the smallest defensible patch and submit after the bounded repair. That policy bug was removed.

Corrected verifier-policy rerun:

- **142.04 s**, **5 calls**, **568-char** patch
- `test_exit_code=1`, `resolved=false`
- verifier still used broad `pytest` instead of the requested targeted gate
- final patch contained a clear semantic bug (`position = end` before `end` was assigned)
- after agent execution, current ADK event compaction raised `No LlmAgent model available for event compaction summarizer`

This made root `SequentialAgent` unsuitable for the official compaction-enabled harness.

### Root coder LlmAgent + verifier AgentTool — mechanically PASS, task FAIL

TDD migration:

- RED contract commit: `cc2c8599cf2d4497facd58a24b251153944be7ca`
- root changed to `LlmAgent`; verifier became an `AgentTool`; redundant coder sub-agent removed
- standard repo validation after the final wording fix passed compile, all unit/static tests, real 129-task corpus checks, and restore-CLI smoke.

Official Kaggle L4 smoke run `41199444320` on `rich_3278`:

- runtime completed successfully; AgentTool config was accepted
- verifier AgentTool was actually invoked
- prior root-Sequential compaction exception did **not** recur
- duration: **253.37 s**
- tool calls: **18 / 32**
- final patch: **275 chars**, one file
- `test_exit_code=1`
- `resolved=false`

Final patch added a broad regex branch:

```text
(?:\x1b[0-?].*) |
```

Behavioral findings from the trace:

- coder still ran bare `pytest` rather than a narrow targeted check;
- verifier did inspect `git diff` and read `tests/test_ansi.py`, which is progress;
- verifier still repeatedly ran bare `pytest` rather than the smallest relevant test;
- verifier eventually called `submit_patch` even though its immediately preceding verification still had exit code 1;
- root coder invoked the verifier twice: after the first AgentTool returned without submission, the outer harness issued its normal “continue your work” turn, the root resumed editing, and called the verifier again.

Conclusion: **the AgentTool topology fixes the compaction/plumbing problem, but E4B still does not reliably follow the verification gate.** More prompt wording is unlikely to be the highest-ROI next intervention.

## 12B controlled A/B evidence

Exact model-size A/B branch: `exp/12b-rich3278-ab`, draft PR #1. The topology, prompts, sampling config, 5-minute task budget, 32-tool budget, and 64-turn budget were held constant; only E4B → 12B plus the required official 12B vLLM HF override changed.

TDD contract validation:

- RED: 25 tests ran with exactly 4 expected failures while the implementation still referenced E4B / lacked the 12B override.
- GREEN: compile, all 25 unit/static tests, 129-task corpus gate, and restore-CLI smoke passed after the 12B implementation.

Official Kaggle L4 ×4 smoke run `41206261407` on `rich_3278`:

- 12B vLLM booted successfully with tensor parallel size 4.
- runtime completed without infrastructure error.
- duration: **304.35 s** (task timeout)
- tool calls: **3 / 32**
- final patch: **0 chars**
- `test_exit_code=-1`
- `resolved=false`
- verifier AgentTool was never reached.

Trace findings:

- the first two real tool calls were only `grep` and `read_file`;
- after reading `rich/ansi.py`, the model spent a long generation reasoning over the regex and emitted a `read_file` call as ordinary text instead of a parsed tool call;
- the harness issued its continuation nudge, after which 12B spent another long reasoning pass and performed only one more `read_file`;
- the task then hit the 5-minute budget with no working-tree modification and no explicit submission;
- trace totals were **20,130 prompt tokens / 7,416 completion tokens / 27,546 total tokens** across only a few effective actions.

Conclusion: **12B@4096 thinking budget is not viable under the current 5-minute task budget.** This is a different failure from E4B: E4B reaches edit/test/verifier but makes semantic/policy mistakes; 12B consumed the budget before reaching those stages. Do not promote the 12B A/B branch to the canonical candidate.

## Static current-wheel validation note

GitHub Actions run `41199130515` is **infrastructure-confounded, not a submission failure**. The vanilla runner filled its disk while pip tried to resolve/download a large PyTorch/CUDA/vLLM dependency stack; the actual `validate_directory()` step never ran. Kaggle smoke is the authoritative current-environment validation path for now.

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

Gold `rich_3278` passes. E4B reaches the coding/verification loop but remains semantically unreliable; 12B with the same 4096-token thinking budget timed out before editing. The canonical candidate therefore remains the mechanically viable E4B root-LlmAgent + verifier-AgentTool configuration while one bounded 12B latency follow-up is tested.

## Next step

1. Keep `main/submission/` on E4B; do not merge the failed 12B A/B candidate.
2. Run one controlled 12B follow-up on `rich_3278` with `thinking_budget: 1024`, changing no topology, prompt, time, tool, or turn budgets.
3. If 12B now reaches edit/test/verifier and materially improves over E4B, continue model-size tuning on the fixed clean sample. If it still times out/stalls or remains unresolved without a clear quality gain, stop the 12B path.
4. Then return to the E4B evidence and test the smallest structural intervention that enforces verification mechanically rather than with more prompt wording.