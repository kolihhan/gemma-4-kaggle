# Verifier LoRA v0 gold screen — round 2

Date: 2026-11-01 (Asia/Kuala_Lumpur)

Purpose: re-screen the 12-task verifier-LoRA holdout after deterministic round-1 replacements. This remains a gold-reference verifier control only; no model/submission agent was invoked.

## Evidence

- Branch: `exp/verifier-lora-v0`
- PR: #4
- Gold-sweep workflow run: `41220881728`
- Head commit: `db8086357f3b827081bdff03451b5960ce1d0344`
- Evidence artifact: `13049972251`
- Artifact SHA-256: `9a207e3d48f58a4aef10064ebed82932a09ca091c39d3b00385329e324a98cbb`
- Structured-result assertion: PASS
- Requested/completed: 12 / 12
- Raw reference patches were not serialized to the artifact.

## Result

Clean (`resolved=true`, `test_exit_code=0`): **7 / 12**

- `rich_3067`
- `rich_3942`
- `rich_3061`
- `fastapi_13920`
- `fastapi_14463`
- `fastapi_14077`
- `fastapi_14851`

Harness-confounded: **5 / 12**

- `rich_3130` — exit 1
- `fastapi_15023` — exit 2
- `fastapi_14605` — exit 2
- `requests_6589` — exit 1
- `requests_7309` — exit 1

Round 1 had 4 / 12 clean. Round 2 therefore added three clean replacement tasks without losing any previously clean task.

## Requests medium-slot exhaustion

`requests_7309` occupies the Requests `11-30` patch-size slot. After round 1, the current training pool contains no remaining Requests `11-30` task. The other known Requests medium tasks are already excluded because they were development-seen or gold-control-confounded. Therefore the original same-repository + same-bucket replacement rule cannot produce another candidate for this slot.

This is a holdout-feasibility issue, not an agent-quality signal.

## Decision

Do not run the model baseline yet.

For round 3:

1. keep all seven clean tasks fixed;
2. replace the four confounded slots that still have same-repository + same-bucket candidates using the existing stable SHA-256 rule;
3. for an exhausted bucket only, allow a deterministic **same-repository fallback** from the current training pool;
4. record the original bucket and replacement bucket explicitly in manifest history;
5. never return a gold-confounded task to training;
6. do not use model output, model score, reference-patch content, or test-output content to choose a replacement.

The fallback keeps the original Requests quota of two tasks instead of silently reallocating the slot to FastAPI or Rich. It relaxes only within-repository patch-size coverage after the exact bucket has been proven infeasible under the current verifier.
