# Gemma 4 PRO: actual frozen 31B native feedback evidence, not new inference

Date: 2026-11-16 MYT.

## Method

[Authenticated GitHub Action #43805384362](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43805384362) fetched the **existing** successfully completed private public-development 31B 3-issue × 2-arm scorer output from `kolihhan/gemma4-v3r-v2-pro-nov15-v1`. All six real grader traces were found. Used existing audited scripts `audit_pro_v3r_real31b_uptake_20261115.py` trace locator and `audit_paired_31b_feedback_v2.py` structural native command recognizer; no issue data, patches, tests, raw commands or evaluator gold were copied to GitHub.

## Real results

| Evidence (per arm, three SAME issues) | Frozen V2 31B | V3R optional Skill |
|---|---:|---:|
| Official public-development grader-resolved issues | 1/3 | 1/3 |
| Genuine physical scorer tool calls | 62 | 81 |
| Genuine elapsed seconds summed | 604.94 | 723.06 |
| Model-visible structured command exit info present on ≥1 command | 3/3 | 3/3 |
| Edit-tool presence in trace | 3/3 | 3/3 |
| Recognized explicit test-like command present | **0/3** | **0/3** |
| Recognized post-edit explicit test present | **0/3** | **0/3** |
| Opaque shell command classification observed | **3/3** | **3/3** |
| Some failed command followed by later edit | 1/3 | 3/3 |

Additional older [V3R Skills uptake audit #43691444649](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43691444649) found **0 actual load_skill and 0 run_skill_script** calls. The optional Skill mechanism was **never taken**.

### Limits and decision

**Scientific result:** V3R invoked more native shell/edits after nonzero command exits but did **not** resolve more problems. This weakens the "simply add more actions/calls/failure retries" hypothesis. Simply extending call budgets is not a validated rescue mechanism.

**Critical ambiguity:** all six traces contain **opaque commands**; therefore **0 recognized explicit tests does not prove the agent executed zero tests**, and model-visible command exit codes do **not** prove an issue-specific post-edit test was useful or consumed. The grader `resolved` flag is **not** directly visible to the agent. Raw tool trace events have duplicated `submit_patch` entries; use only scorer tool counts for physical cost.

The next meaningful experimental mechanism must be a **legally model-visible, issue-targeted executable validation and root-cause evidence path**, not an optional Skill or cosmetic prompt. Before another expensive 31B pilot, prove the official ADK/Kaggle submission format can actually invoke that path on the native agent run with no hidden grader oracle, and verify nonzero failure → relevant repair → passing targeted test → grader resolution on **new** preregistered tasks. A synthetic smoke or private host-only plugin cannot count as generalization.

Recent exact Gemma 12B size-swap was independently negative [#43781086310](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43781086310), 0/3 versus 31B 1/3, no rescues and one regression. Retire both prompt-only optional-Skill and size-only branches for now.

**Scored Kaggle best remains 0.18**, ref `#58183466`; `#58350278` completed with blank public score. No model training, new GPU or official submission was performed for this native-feedback read-only audit.
