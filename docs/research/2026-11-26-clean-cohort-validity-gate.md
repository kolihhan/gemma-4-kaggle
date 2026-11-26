# Gemma 4 31B — real patch failure vs invalid public-development targets (2026-11-26)

**Research decision:** The previously used six-task panel must not drive new solver prompts or official submissions until gold/reference and empty/no-op controls are revalidated under the exact currently installed Kaggle wheelhouse. A third-party gold/noop audit indicates that only **2 of these 6** discriminate successful from unsuccessful patches in its environment. This is a **proxy**, not a new measurement of our own verifier.

## Actual owner model evidence (complete)

The [CPU-only private patch audit #45744952897](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/45744952897) reran all six synthetic software tests of its conservative auditor, then downloaded original output of the previously completed real 31B matched paired scorer \`kolihhan/gemma4-single-edit-channel-paired-20261124-v1\`. Zero new inference, training, or submission.

| Actual outcome, 6 same issues / arm | FastPath 4 min | Single-Edit 4 min |
| --- | ---: | ---: |
| Scorer resolved | 0 | 0 |
| Final nonempty patch recorded and recovered | 4 | 4 |
| Recovered patch intersects source file changed by reference patch | 3 | 2 |
| Reference-hunk neighborhood overlap | 3 | 2 |
| Recovered patch source path disjoint from reference patch | 1 | 2 |
| Patch absent from scorer / artifact unavailable | 2 | 2 |
| Task statement contains an external URL | 5 | 5 |
| Very short statement with external URL | 2 | 2 |
| Gold/noop validity confirmed in current environment | **UNVERIFIED** | **UNVERIFIED** |

**Do not promote path overlap to semantic competence.** The public reference is one accepted solution, not the only correct one. We did not verify whether a failed patch omitted an explicit requirement, misread the issue, was ungradeable, or had an unrelated environment/test failure. No actual agent improvement was tested by the CPU audit. Six *distinct tasks*, not twelve independent issues.

## Cross-environment gold/noop audit (complete)

[Owner's pinned independent proxy #45745134040](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/45745134040) joins the **same six original public-development task IDs internally** to TechNaom's exact 2026-10-15 public 129-task gold- and empty-patch scorer records, pinned at commit \`f3b6d3ac4c532a2bf3745872fe171747d0bf3e31\`.

- Gold reference passes: **4/6**.
- Empty/no-op passes: **2/6**.
- Gold PASS + no-op FAIL on the same issue: **2/6**.
- Not an informative classifier under that **other** evaluator: **4/6**.
- The two audits use different runtime revisions and may differ on dependencies; this is not proof that our scorer also considers 4/6 invalid.

Third-party source: [literal gold records](https://github.com/TechNaom/gemma4-agentic-swe/blob/f3b6d3ac4c532a2bf3745872fe171747d0bf3e31/experiments/audit-2026-10-15/gold_runs.jsonl) and [literal no-op records](https://github.com/TechNaom/gemma4-agentic-swe/blob/f3b6d3ac4c532a2bf3745872fe171747d0bf3e31/experiments/audit-2026-10-15/empty_runs.jsonl).

## Available independent public-dev pool (complete)

The [CPU-only exclusion census #45745504627](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/45745504627) read the existing preregistration (43 previously excluded task IDs) plus three previously completed real paired studies (22 more distinct task IDs). It identified **65 prior used/excluded IDs**, with no overlap in those three paired cohorts.

Of TechNaom's independently gold/noop-valid **68** public tasks, **28** remain unused/unexcluded under our current ledger: 12 FastAPI and 16 Rich. Among those 28, 11 have a very short issue statement with an external URL; **17** do not exhibit that exact short-link signal. This is a feasibility pool, NOT a frozen result slate, and **not yet vetted by our wheelhouse**.

## Current-wheelhouse experiment

[Private Kaggle CPU gold/noop control run #45745386035](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/45745386035) was started to test the same six actual owner tasks with the official Kaggle wheelhouse's \`verify_task\` path, feeding the original reference patch and an empty patch with **zero model inference**. It writes only anonymous validation counts to a private Kaggle CPU notebook. It has now returned an authenticated terminal COMPLETE result: see the measured addendum below. These controls run our current installed wheelhouse, not an assertion about hidden competition scoring.

## Next decision rule

1. Confirm the CPU Kaggle kernel is actually registered and reaches terminal COMPLETE; do not substitute GitHub Action green for the Kaggle result.
2. If at most 2/6 are clean under our wheelhouse, **retire this panel for causal solver diagnosis**. It is fine as a case study of evaluation confounds but not a tuning set.
3. If enough are clean, investigate the actual failed patches *on those clean issues* for the presence of explicit missing requirements that were visible to the agent; keep any missing/ambiguous category UNKNOWN.
4. For fresh agent tests, freeze a new cohort **before viewing outcome/patches**, from the remaining disjoint pool. First check real gold/noop validity on the same current verifier. Prefer non-short external-link tasks when possible, but do not silently bias or retune from earlier failures.
5. Only after repeating a concrete, agent-accessible causal failure across several independent clean tasks should we implement and pair one 31B mechanism against the preserved **0.18 official Champion**, with identical budgets and actual grader resolution. No more sampling/budget bundles or premature official submit.

No exposed task IDs, issue text, reference patches, agent patches, paths or private traces are included in this document. No official submission or GPU was used for the above CPU analyses.


## Verified addendum: current Kaggle controls + clean-only patch diagnosis (2026-11-26)

- [Our current Kaggle wheelhouse verifier #45745386035](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/45745386035): registered CPU kernel COMPLETE; 6/6 gold-noop pairs executed without unknown status; **gold PASS 2/6, no-op PASS 0/6, discriminating 2/6, non-discriminating 4/6**. Zero solver inference, GPU and contest submissions.
- [Direct itemwise current-vs-third-party comparison #45748400156](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/45748400156): **both-valid 2, neither-valid 4**, so the exact two discriminating tasks match between the independent October source and our current November wheelhouse despite two gold disagreements and two no-op disagreements.
- [Real own model failures conditioned on those two clean tasks #45748104637](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/45748104637): for **each** of FastPath and Single-Edit, 0/2 resolved, one task had no patch and the other produced a patch with **zero source-file overlap** to the reference solution; both tasks had short externally linked issue statements. **Neither task supports an observed explicit-requirement-omission or correct-source-wrong-semantics label**. The four not-valid issues had a mixture of source-overlapping wrong patches, but must not drive a solver score claim.
- Research decision: **RETIRE these six old paired issues as a semantic-repair treatment gate**; zero passing patches on an invalid-majority cohort cannot diagnose whether semantic patching or narrower prompt changes help. They remain useful only as an illustration of evaluator confounding.
- [Fresh pool current Kaggle CPU validity check #45748245882](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/45748245882): 17 previously unused tasks (selected deterministically from 28 independently valid proxy tasks after excluding short external-link statements), frozen before reading any current-wheelhouse results. The live result must be checked, not assumed; no new agent inference or official submit was authorized by this CPU control.
- Separately, [Kaggle Staff acknowledged a thinking-history bridge bug](https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/744354) and said the wheelhouse was patched. Historical official scores across host updates should not be treated as a controlled ablation without same-epoch evaluation; this does **not** imply the staff fix changed our 0.18 vs 0.15 outcomes.

**Next research gate**: only choose genuinely discriminating, previously unseen, information-sufficient tasks under the *current* wheelhouse; distinguish incorrect source selection, missing requirements, and invalid tests before deciding on a single targeted solver change. No untested Frontier Balanced submission.
