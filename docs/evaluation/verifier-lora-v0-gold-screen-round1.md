# Verifier LoRA v0 gold screen — round 1

Date: 2026-11-01 (Asia/Kuala_Lumpur)

Purpose: screen the frozen 12-task verifier-LoRA holdout with the current official verifier before any model baseline or training. This is a gold-reference control only; no model/submission agent was invoked.

## Evidence

- Branch: `exp/verifier-lora-v0`
- PR: #4
- Gold-sweep workflow run: `41219943705`
- Head commit: `83ec04fb28125229a93ad310d21e9ab400334f0d`
- Evidence artifact: `13049986241`
- Artifact SHA-256: `a5976191bff87058f3162ffcd4a3fc3869adc66c609009dacb0ac66d8900f994`
- Structured-result assertion: PASS
- Requested/completed: 12 / 12
- Raw reference patches were not serialized to the artifact.

## Result

Clean (`resolved=true`, `test_exit_code=0`): **4 / 12**

- `rich_3067`
- `rich_3942`
- `fastapi_13920`
- `fastapi_14077`

Harness-confounded: **8 / 12**

- `rich_3064` — exit 1
- `rich_4070` — exit 1
- `fastapi_14297` — exit 2
- `fastapi_14583` — exit 2
- `fastapi_14371` — exit 2
- `fastapi_15030` — exit 2
- `requests_6629` — exit 1
- `requests_7505` — exit 1

No agent-quality conclusion should be drawn from the eight confounded tasks because the current verifier does not resolve their gold reference patches.

## Decision

Do not run the base-verifier held-out baseline on this 12-task set.

Apply deterministic replacements for each confounded slot using the already-declared rule:

1. same repository;
2. same reference-patch-size bucket;
3. replacement chosen from the current training pool by the existing stable SHA-256 ordering;
4. confounded former holdout task moves permanently to `excluded` with reason `gold_control_confounded` and does not re-enter training;
5. clean holdout tasks stay fixed.

Repeat gold screening until the held-out set is clean enough for an interpretable base-vs-LoRA A/B, or stop if the repository/bucket cannot supply clean replacements.

This file intentionally records only status-level verifier metadata. Test-output tails and reference-patch contents remain private experiment evidence and are not used for training.
