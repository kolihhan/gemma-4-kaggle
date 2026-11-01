# Verifier-only LoRA v0 — base E4B held-out baseline

Date: 2026-11-01

## Verdict

The clean held-out base baseline is valid and weak enough to justify the verifier-only LoRA experiment.

- Model: `gemma-4-e4b-it-qat-w4a16-ct`
- Topology: unchanged root coder `LlmAgent` + verifier `AgentTool`
- Clean denominator: 9 tasks selected by the frozen split + exact gold screen
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

Across the 9 clean tasks:

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

The one success, `rich_3067`, is also informative: the verifier first saw a broad `pytest` failure, then ran targeted `pytest tests/test_highlighter.py`, got a passing result, and only then submitted. That is the behavior the adapter should make more reliable.

## Failure interpretation

This baseline strengthens the original F4/F5 hypothesis:

1. **Verification-gate adherence is poor.** Four tasks were submitted after known failing verification.
2. **Test selection remains too broad.** Broad `pytest` dominates verifier testing despite prompts requesting a narrow gate.
3. **Repair discipline is weak.** Several tasks spend substantial budget on repeated or fragile edits rather than one evidence-backed repair.
4. **Coder-only failures still exist.** `fastapi_14077` never reached the verifier, so verifier LoRA cannot solve every miss.
5. **The experiment is still worth running.** Eight of nine tasks do reach the verifier, so changing only verifier behavior has enough surface area to produce a measurable held-out gain.

## Infrastructure notes

The previous baseline attempt (`41268196580`) is **infra-confounded** and must not be used as model evidence. Its workflow pushed the kernel successfully but polled the wrong Kaggle slug (`kolihhan/gemma-4-verifier-baseline-v0` instead of `kolihhan/gemma-4-verifier-heldout-e4b-baseline-v0`), producing 300 permission/slug errors before timing out.

The successful run exposed a second harness-only issue: the final CI assertion compared result order directly to `gold-screen.clean_instance_ids`, while runtime order correctly followed the filtered frozen split. The structured result itself was valid. The assertion was fixed to derive expected order from the frozen split filtered by the clean set; no model rerun is required for that fix.

## Decision

Proceed with verifier-only LoRA v0.

Keep fixed for the first A/B:

- coder weights and prompt;
- verifier prompt and tools;
- topology;
- sampling;
- 5-minute / 32-call task budget;
- exact 9-task clean held-out denominator.

Do not use any holdout reference patch, holdout trace, or holdout verifier evidence to create training examples.
