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

## Prospective owner-sanctioned execution gate — 2026-11-17

- **For new experiments, the required local gate before ONE official hypothesis-driven Kaggle submission is sanity-only:** candidate bundle compiles with official native validation, supported 31B model and legal tools are retained, the archive and receipt are reproducible, estimated full scoring budget is plausible, and no previous submission or active duplicate exists. A statistically significant paired local improvement on 30 independent issues is **not required to submit**. Thirty-task paired evidence remains the stronger standard for a *general scientific claim*, not a veto on official experimental scoring. Historical preregistered gates remain part of the record, not retroactively changed.
- **Allowed GPU:** an official Kaggle competition scoring rerun of the submitted Code Competition candidate. **Forbidden development:** new local/Kaggle/GitHub-Actions GPU pilots, training, batch model evaluation and paid APIs without further explicit owner authorization. Do not restart the Nov-17 failed 31-case private solvers.
- Every score experiment must predeclare one decision-level mechanism, a numerical expected Public improvement as a hypothesis (never a guarantee), and a kill condition; change only one main variable. Existing Kaggle submission code/CLI path must be used, not a new workflow, and a fresh kernel slug must not overwrite any champion.
- Check authenticated competition daily allowance and active submissions before attempting official submission. **Kaggle's 1/day limit cannot simultaneously permit submission and 'reserve 1 unused slot/day'.** Treat this as a scheduling constraint to resolve when a viable candidate exists; do not falsely claim that a remaining slot was preserved after its only use.
- Publish only aggregate diagnostics, not hidden issues, patches, trace text, private grader data or secrets. Distinguish developer cohorts with invalid reference/no-op controls from genuine solver failures.
- Current authentic best **0.18/#58183466**; a COMPLETE submission with empty score is not improvement.

## Scientific research gates (user contract)
- Actual grader result over matched independent issues is primary; `COMPLETE`, green CI, patch creation, tool-count savings and test-smoke are not correct resolutions.
- Minimum **30 genuinely independent paired issues proposed**, subject to user confirmation and observed variance. Never promote/reject general capability on the spent 3/4-issue cohorts. Report paired task n, bootstrap CI, rescues and regressions.
- Official numeric reference **0.18 #58183466**; #58350278 COMPLETE/no numeric score is *not* 0.18+.
- No duplicate submission or restarted job; source, trace IDs, model and selection rule frozen pre-run.
