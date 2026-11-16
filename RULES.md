# RULES — Gemma 4 Developer Agent (checked 2026-11-16)
Source precedence: current Kaggle [overview](https://www.kaggle.com/competitions/gemma-4-developer-agent/overview/prizes), [official rules](https://www.kaggle.com/competitions/gemma-4-developer-agent/rules), [staff model update](https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/748287). Older cached overview pages and bundled HARNESS_README model list may be stale.

## Verified
- Metric: issue-resolution **PASS/FAIL** aggregated over held-out repository issues; grader applies submitted patch and evaluates tests.
- Scored run: **12h aggregate agent time**, including sandbox setup, excluding patch validation. Per-task cap may be configured via `eval_config.yaml`; our historical **5min/28-calls/80-turns** is a *chosen experimental setting*, not a globally imposed Kaggle rule.
- Format: `submission.zip`, required root `agent.yaml`, optional prompts/custom tools/skills and PEFT LoRA adapters. Sandbox offline.
- **Allowed variants**: `gemma-4-31b-it-qat-w4a16-ct`, `gemma-4-12b-it-qat-w4a16-ct`, `gemma-4-e4b-it-qat-w4a16-ct`, `gemma-4-e2b-it-qat-w4a16-ct` (current staff update and revised overview). One base variant for *all agents/subagents in one submission*; different supported LoRA adapters on same base allowed.
- Official competition-specific Rules: **1 submission/day** and up to **2 final submissions**. Final deadline **2026-12-02 23:59 UTC** (timeline mutable); entry **2026-11-25**.
- External data and models: official Rules §2.6 allow public/free or reasonably accessible/minimal cost under host's Reasonableness Standard, subject to competition-specific model/sandbox constraints, provenance and licensing; public availability alone does not override competition-data security.
- No private sharing of competition code outside team, no new public raw-data/patch mirrors; follow `PUBLIC_VISIBILITY.md`.

## Unresolved / fail-closed
- Paid online **inference** inside offline agent sandbox is not executable/authorized. Paid services for *offline development* are not blanket-approved: require source-specific Reasonableness/licensing review and current host confirmation if ambiguous.
- Exact eligibility/allowed *custom tool action paths*, and any changes to official harness, must be validated before executing a new test-feedback intervention.
- Submission count/active jobs/remaining GPU quota require authenticated read-only ledger and run-state check **immediately before** any official action; this document is not a quota receipt.

## Scientific research gates (user contract)
- Actual grader result over matched independent issues is primary; `COMPLETE`, green CI, patch creation, tool-count savings and test-smoke are not correct resolutions.
- Minimum **30 genuinely independent paired issues proposed**, subject to user confirmation and observed variance. Never promote/reject general capability on the spent 3/4-issue cohorts. Report paired task n, bootstrap CI, rescues and regressions.
- Official numeric reference **0.18 #58183466**; #58350278 COMPLETE/no numeric score is *not* 0.18+.
- No duplicate submission or restarted job; source, trace IDs, model and selection rule frozen pre-run.
