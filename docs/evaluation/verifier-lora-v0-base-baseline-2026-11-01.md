# Verifier-only LoRA v0 — base E4B development baseline

Date: 2026-11-01

## Verdict

The 9-task gold-clean base run is valid **development validation** evidence for verifier behavior, but it is **not a final blind holdout**. Its traces have been manually inspected and used to form the verifier-LoRA hypothesis.

A verifier-only LoRA remains justified as one controlled falsification experiment, not because verifier causal dominance has been proven.

- Model: `gemma-4-e4b-it-qat-w4a16-ct`
- Topology: unchanged root coder `LlmAgent` + verifier `AgentTool`
- Development denominator: 9 tasks selected by the frozen split + exact gold screen
- Coverage: Rich 4 / FastAPI 5 / Requests 0
- Kaggle run: `41276731977`
- Experiment head: `2dec284a758cb280b4fa657b4bdd22cba96a2be0`
- Artifact: `gemma4-verifier-baseline-v0-evidence`
- Artifact SHA-256: `ea79a63f9b75daa2cdb5dfef9b2af961e95dd659d07b606e24588b8fd115a319`
- Kernel terminal state: `COMPLETE`
- Result: **1 / 9 resolved**

The only resolved task was `rich_3067`.

## Per-task results

| Task | Resolved | Final verifier exit | Patch chars | Tool calls | Duration (s) |
|---|---:|---:|---:|---:|---:|
| `rich_3067` | yes | 0 | 652 | 30 | 253.9 |
| `rich_3934` | no | 1 | 477 | 27 | 308.9 |
| `rich_3942` | no | 1 | 0 | 13 | 140.0 |
| `rich_3061` | no | 1 | 1,104 | 32 | 255.9 |
| `fastapi_13920` | no | 1 | 1,355 | 20 | 261.8 |
| `fastapi_14463` | no | 1 | 665 | 8 | 101.7 |
| `fastapi_14077` | no | 2 | 2,221 | 17 | 153.3 |
| `fastapi_14986` | no | 1 | 1,461 | 15 | 148.2 |
| `fastapi_14851` | no | 2 | 11,938 | 32 | 304.8 |

## Verifier behavior diagnostics

Across the 9 development tasks:

- verifier reached: **8 / 9**;
- `submit_patch` called: **5 / 9**;
- submitted after the verifier's most recent test was still failing: **4 / 9**;
- verifier test commands: **9 broad** vs **4 targeted**;
- verifier `edit_file` calls: **10**;
- two tasks exhausted the 32-call budget (`rich_3061`, `fastapi_14851`);
- `fastapi_14851` grew to an 11,938-character patch and still ended with verifier exit 2.

The four clear premature-submit cases were:

- `fastapi_13920`: verifier ran broad `pytest`, observed failure, then submitted;
- `fastapi_14463`: verifier ran broad `pytest`, observed failure, edited again, then submitted without a passing rerun;
- `fastapi_14986`: verifier ran `pytest fastapi/openapi`, observed failure, then submitted;
- `rich_3942`: verifier ran broad `pytest`, observed failure, then submitted.

The one success, `rich_3067`, is informative: the verifier moved from a broad failure to targeted `pytest tests/test_highlighter.py`, got a passing result, and only then submitted.

## Causal-surface diagnostic

`8/9 reached verifier` is **not** evidence that verifier behavior caused 8/9 failures. Reaching a stage only establishes control-flow reachability.

Conservative trace classification:

| Task | Diagnostic class | Evidence |
|---|---|---|
| `rich_3067` | essentially correct / verification surface | targeted highlighter test passed, then submitted, resolved |
| `fastapi_14463` | one narrow repair / verification plausibly useful | task-aligned shallow-copy fix, but no clean passing relevant gate before submit |
| `fastapi_14986` | one narrow repair / verification plausibly useful | task-aligned OpenAPI/Swagger edits, but submitted after failed verification |
| `rich_3934` | one narrow repair might rescue, unproven | narrow semantic change, failing evidence remained, verifier drifted into changing tests / repeated repair |
| `fastapi_13920` | fundamentally wrong patch | invented placeholder `is_typealiastype(...): return False`; verifier accepted after failing tests |
| `fastapi_14077` | coder-stage failure / no verifier surface | invalid/unstable status-import edits; verifier never reached |
| `fastapi_14851` | fundamentally wrong patch | speculative invasive rewrite, duplicate machinery, 11.9k-char patch, budget exhaustion |
| `rich_3061` | fundamentally wrong / no clean repair state | speculative `expand_tabs` rewrite and repeated failed edits; budget exhausted |
| `rich_3942` | no useful verified patch | failed verification followed by submission; final evaluator patch 0 chars |

This supports a verifier-only experiment on a **subset** of failures. It does not prove that verifier-only training can materially increase resolved count across the full task distribution.

## Coverage limitation

The two proposed Requests holdout tasks failed gold-control, leaving **zero clean Requests tasks** in this development denominator. Therefore this run supports Rich/FastAPI diagnostics only. It must not be cited as evidence of Requests or broad cross-repository generalization.

## Infrastructure notes

The previous baseline attempt (`41268196580`) is infrastructure-confounded and must not be used as model evidence. Its workflow pushed the kernel successfully but polled the wrong Kaggle slug, producing repeated permission/slug errors before timing out.

The successful run exposed a separate CI-order assertion issue. Runtime order correctly followed the filtered frozen split; the assertion was fixed to derive expected order from the frozen split filtered by the clean set. No model rerun is required for that assertion-only correction.

## Decision

Proceed with verifier-only LoRA v0 **only after a genuinely blind evaluation set is frozen**.

Keep fixed for the first A/B:

- E4B base model family;
- coder weights and prompt;
- verifier prompt and tools;
- topology;
- sampling;
- 5-minute / 32-call task budget;
- LoRA rank `r=8`.

Evaluation roles:

- this 9-task set = **development validation**;
- final blind set = **pending freeze**;
- blind candidate selection may inspect metadata only;
- blind eligibility may use automated harness/gold-control only;
- do not inspect blind base failure traces or blind reference patches before the verifier adapter is frozen;
- do not use blind tasks in training or trace harvest.

Promotion requires development behavior + resolved count, independent blind resolved count, F4/F5 reduction, targeted-test behavior, premature-submit behavior, and runtime/tool-call cost. If v0 fails the blind set, stop v0 rather than immediately sweeping hyperparameters.

Canonical contract: `docs/evaluation/verifier-lora-eval-contract-v1.json`.
