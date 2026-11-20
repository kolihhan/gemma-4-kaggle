# Genuine Gemma 4 31B failed repairs vs reference: evidence audit

Date: 2026-11-20. **DECISION: HOLD on a new solver intervention.** This is a completed CPU-only retrospective of existing *real 31B private scored development* trajectories, not an Agent improvement, a full semantic Patch audit, a new model run, or an official competition submission.

## Sources and reproducibility

- Historical official owner scoreboard authenticated on 2026-11-20: [Action 44659728947](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/44659728947), 31B Champion COMPLETE Public 0.18 ref `58183466`; Coder-LoRA COMPLETE 0.12 ref `58558350`.
- Nov12 matched 31B V2 vs prompt-only real grader: [Action 43057377220](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43057377220). Per-task gold/no-op validation, CURRENT at that epoch: [Action 43070401519](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43070401519).
- Nov15 matched 31B V2 vs optional Skill V3R real grader: [Action 43689217134](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43689217134). Native feedback retrospective: [Action 44750878666](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/44750878666). Gold/no-op validity for these **three different issues is UNVERIFIED** in this audit.
- New private-existing-output **CPU-only** audits: [44770840836](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/44770840836) and [44771279117](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/44771279117). Scripts: `scripts/audit_gemma31b_semantic_gap_private_20261120.py`; only two already-completed private Kaggle Kernel outputs were downloaded, no Kaggle push or GPU.
- The full task issue and reference data are read retrospectively from `tasks.jsonl` inside a controlled CPU audit. **Neither reference patches, raw issues, model outputs, test bodies, nor source file paths are exported or provided to the solver.**

## Fundamental recovery boundary

- **12/12 real 31B traces recovered**, six unique public-development issues across two distinct paired studies.
- **0/12 full final Agent Patch files recovered**; 0 `.patch` files in both recovered private output directories. The scored result itself records a nonempty patch on all 12 evaluations, so the failure is **artifact retention/availability**, not proof the Agent did not generate code.
- **12/12 visible edit-tool paths recovered** (some raw events may be duplicated; unique filenames are a localization signal, not a complete final diff; `run_command` may perform additional edits).
- **2/12 scorer PASS**, both on the SAME issue `rich_3718` under two different arms; **10/12 FAIL**. Never claim 2 independent successful issues.
- Consequently **no honest issue-level semantic root-cause or final-patch equivalence classification is currently possible**. File overlap and grader exit status are insufficient.

## Task-level observed evidence

`Gold file?` means **at least one unique explicit edit-tool target path** matches a source file changed by the retrospective reference patch. Not proof of a correct function, successful edit, or final diff.

| Real 31B task | Arm | Grader | Gold/no-op validity | Explicit edit reaches Gold file? | Scorer calls | Scorer seconds |
|---|---|---|---|---|---:|---:|
| fastapi_14487 | V2 | FAIL | PASS/FAIL: informative | **No** | 28 | 219.35 |
| fastapi_14487 | prompt-only | FAIL | PASS/FAIL: informative | **No** | 23 | 266.08 |
| rich_3782 | V2 | FAIL | PASS/FAIL: informative, 68-character linked issue | **No** | 23 | 304.34 |
| rich_3782 | prompt-only | FAIL | PASS/FAIL: informative, spec pointer-risk | Yes | 28 | 259.04 |
| requests_7427 | V2 | FAIL | **Gold FAIL** / no-op FAIL: confounded | Yes | 15 | 303.92 |
| requests_7427 | prompt-only | FAIL | **Gold FAIL** / no-op FAIL: confounded | Yes | 20 | 303.27 |
| fastapi_14258 | V2 | FAIL | **UNKNOWN** | Yes | 27 | 182.85 |
| fastapi_14258 | V3R | FAIL | **UNKNOWN** | Yes | 28 | 196.58 |
| requests_7205 | V2 | FAIL | **UNKNOWN** | Yes | 20 | 164.89 |
| requests_7205 | V3R | FAIL | **UNKNOWN** | Yes | 26 | 255.69 |
| rich_3718 | V2 | **PASS** | Gold/no-op unknown; actual scorer PASS | Yes | 15 | 257.21 |
| rich_3718 | V3R | **PASS** | Gold/no-op unknown; actual scorer PASS | Yes | 27 | 270.80 |

Source for accurate metrics/observed unique edit-path overlap: [44771279117](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/44771279117).

## Failure evidence counts — observed / suspected / unknown separated

Ten failed **evaluations** (not ten independent issues):

| Evidence state | Count | Interpretation |
|---|---:|---|
| Scorer confounded, reference Gold itself fails | **2/10** | Both `requests_7427`; do NOT blame the model |
| Gold passes/no-op fails, explicit edited file misses Gold source file | **3/10** | Two `fastapi_14487`, one `rich_3782` V2: localization **suspicion**, not confirmed full-patch mismatch |
| Gold passes/no-op fails, explicit edited file reaches Gold source but task unresolved | **1/10** | `rich_3782` prompt-only: insufficient requirements or incorrect patch semantics both plausible |
| Grader validity not checked on this cohort | **4/10** | `fastapi_14258`, `requests_7205`, each V2/V3R; source path overlaps in 4/4, not enough for semantic blame |
| Final Agent Patch available for true code-vs-gold comparison | **0/10** | The core missing evidence |

These are **mutually exclusive evidence strata**, not causal classes. For the requested causes:
- ROOT-CAUSE MISUNDERSTANDING: no verified assignment (UNKNOWN).
- CODE LOCALIZATION: 3 **suspected** missing-Gold-source edits among 4 Gold-valid failures; 0 proven wrong-final-patch cases.
- PATCH SEMANTICS: no verified assignment; Gold-file overlap without resolution is not enough.
- TOOL/ENVIRONMENT: 2 documented scorer-confounded failure evaluations; exact mechanism unknown.
- VERIFICATION FEEDBACK: classifier recognized 0 explicit post-edit test invocations on 12 traces; opaque commands remain and may contain tests; no proven ignored actionable failing assertion.
- BUDGET/STOPPING: 3 of 12 scored calls hit 28; time-limit terminal cause not verified, and edit existence alone does not prove good stopping.

## Paired execution costs

| Frozen experiment | Control | Candidate | Control tools / sec | Candidate tools / sec | Paired rescues / regressions |
|---|---|---|---|---|---|
| Nov12 V2 vs prompt-only | 0/3 | 0/3 | 66 / 827.61 | 71 / 828.39 | 0 / 0 |
| Nov15 V2 vs V3R | 1/3 | 1/3 | 62 / 604.95 | 81 / 723.07 | 0 / 0 |

Total 12 scored model-task evaluations: 280 scorer tools, approximately 2,984.02 recorded seconds. These are summed run durations and not GPU billing/elapsed wall time. Raw trace action multiplicities may differ; scorer call counts take precedence.

## Mechanism decision: one conditional follow-up, NO solver modification

**Most informative actionable hypothesis**: the 31B sometimes fails to edit the relevant source target *before* patch synthesis, while editing a matching source file still does not ensure correct behavior. The strongest clean evidence is two independent model attempts on `fastapi_14487`, both failing despite valid Gold/no-op and no observed explicit edit to the Gold source. But one task is not enough to declare localization dominant or promote an Agent mechanism. There is no verified final-patch semantic comparison, and the Nov15 failed cases lack gold/no-op validity.

**Single next evidence-gathering intervention (CPU-only, NO new GPU or agent change):** recover or retain *exact, final scored `agent_patch` bytes* for existing tasks, and independently complete current official gold/no-op controls for the Nov15 three issues. Keep all raw outputs and reference patches in private evaluation storage; expose only per-issue semantic rubric classifications verified against actual patches. Only then freeze a genuinely new paired 31B intervention and disjoint cohort if the causal pattern warrants it. Do not retry optional Skills, extra agents, or text-only prompts on spent cases.

**Decision:** HOLD for a new model/agent change. Gold/reference data never enter the solver context; maintain official 0.18 Champion. The observed improvement since this audit is **research evidence only**, official score delta **+0.00**.
