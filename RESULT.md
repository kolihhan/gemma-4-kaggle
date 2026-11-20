# Gemma 4 Developer Agent — Executor → Independent Observer handoff

Date: 2026-11-20. **DECISION: HOLD / DIAGNOSTIC PIVOT.** CPU-only retrospective, no solver change, model inference, GPU job, training or Kaggle competition submission.

## PROJECT
Gemma 4 Developer Agent — real 31B scored development failure-vs-Gold audit.

## VERIFIED BASELINE
Authenticated owner Kaggle ledger in [GHA #44659728947](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/44659728947): Champion `58183466` COMPLETE Public **0.18**; Coder-LoRA `58558350` COMPLETE Public **0.12**. No new official score from this work. Original 0.18 champion ZIP unchanged.

## ROOT CAUSE / COMPETING HYPOTHESES
H1: wrong source location/root-cause target. On the only gold/no-op-valid `fastapi_14487`, **both** previously completed 31B arms FAIL and their explicit edit tools do not touch Gold source path. On valid-but-underspecified `rich_3782`, one arm does not touch Gold source.

H2: correct broad code location but wrong requirement interpretation, missing behavioral invariant or patch semantics. The other `rich_3782` arm edits Gold source and fails; both failed Nov15 issues have Gold source-path edit overlap in both arms. **Not proven:** no complete final Agent Patch exists in recovered output, and Nov15 gold/no-op controls remain unknown.

H3: grader/information confounds. In the original trio, `requests_7427` Gold itself FAILS while no-op FAILS, meaning 2/12 failed attempts are unfit for model-repair attribution. `rich_3782` has a model-visible 68-character URL-linked statement with no hints; missing requirements are a credible risk, not proved.

No dominant causal failure category is established.

## IMPLEMENTATION
Read-only CPU evaluator script:
`scripts/audit_gemma31b_semantic_gap_private_20261120.py`;
one-shot workflow:
`.github/workflows/gemma-31b-patch-gold-semantic-audit-private-cpu-20261120.yml`;
full scientific report:
`docs/evaluation/gemma31b-failed-repair-vs-gold-20261120.md`.

Research commits include `cc074e3044b209ee6314d51b1467e8d8e19c4934`, `60130e64df1efe5712e0dd420970258f0b28a43a`, documentation commit `2b278aadfd83195fb65252621401ed12850c33fd`. No PR created. `submission/` untouched.

## EXPERIMENT
[CPU-only existing-output GHA #44770840836](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/44770840836) and [final #44771279117](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/44771279117): downloaded two **already completed** private 31B Kaggle development kernels; read-only access to 12 existing trace files and public-development Gold labels; no new notebook, grading execution, server, GPU, or model submission. Synthetic unit tests and protected export passed. Runtime source model from frozen original 31B runs: `gemma-4-31b-it-qat-w4a16-ct`.

## TASK-LEVEL RESULTS

| Issue | 31B frozen V2 | Other frozen arm | Gold/no-op control | Explicit edit-source overlap |
|---|---|---|---|---|
| `fastapi_14487` | FAIL | prompt-only FAIL | gold PASS, no-op FAIL | neither |
| `rich_3782` | FAIL | prompt-only FAIL | gold PASS, no-op FAIL; short URL issue | prompt-only yes; V2 no |
| `requests_7427` | FAIL | prompt-only FAIL | gold FAIL, no-op FAIL | both, confounded |
| `fastapi_14258` | FAIL | V3R FAIL | unknown | both |
| `requests_7205` | FAIL | V3R FAIL | unknown | both |
| `rich_3718` | PASS | V3R PASS | unknown | both (successful control) |

Exactly 12 scored evaluations on **6 unique issues**: 10 FAIL, 2 PASS on **one duplicated issue**. 12/12 raw traces recovered; **0/12 final Agent Patch files recovered**, confirmed no `.patch` files in either private download. Trace edit target does not prove final patch application or coverage of opaque shell edits.

**Costs:** Nov12 control 66 calls / 827.61 sec, prompt-only 71 / 828.39, 0 rescues / 0 regressions. Nov15 control 62 / 604.95, V3R 81 / 723.07, 0 rescues / 0 regressions. Combined 280 scorer calls / 2,984.02 summed seconds; not a GPU invoice.

## MECHANISM ANALYSIS
The distinct observable signal is incomplete source targeting on some *gold-informative* failures, not proof that file-path correction alone fixes an issue. Same-source failure and actual same-source SUCCESS controls show that localization is not sufficient for semantic correctness. No confirmed post-edit relevant test-failure → recovery event; all traces contain opaque shell commands. Optional V3R Skill previously had zero observed tool uptake, so extra Skills/tools are not a credible next default.

## LIMITATIONS
No exact model-final patch bytes, so code semantics, requirement compliance, regression edits and Gold equivalence remain **UNKNOWN**. Reference patches are not necessarily unique acceptable solutions. Original gold/no-op controls are prior epoch; Nov15 controls absent. Previously inspected tasks are not blind and experiments do not share one exchangeable denominator. Event-level edit-call counts may duplicate physical actions; score tool totals take precedence. CPU CI SUCCESS only means audit worked.

## DECISION
**HOLD** Champion 0.18. No claim of Kaggle increase. No solver-intervention A/B yet. Single justified next step, if authorized: controlled **CPU-only evidence recovery** of exact final scored patches and independent gold/no-op checks of Nov15 three issues, with private-only reference handling, before fixing an issue-localization or semantic repair mechanism.

## OBSERVER REVIEW REQUEST
1. Verify official score provenance from authenticated ledger, original run IDs, 12 records and paired cost sums.
2. Confirm 0/12 full final-patch files is artifact absence, not agent non-editing.
3. Check the 3/4 gold-informative explicit-edit localization signal and shell-edit caveat.
4. Keep all unproven semantic diagnoses UNKNOWN. Do not promote training, new Agent topology, or another official submission on this evidence.

[Full task-level, category and uncertainty report](docs/evaluation/gemma31b-failed-repair-vs-gold-20261120.md).
