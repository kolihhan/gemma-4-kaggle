# Gemma 4 — Evgen source-grounded comparison and action-funnel gate

**Date:** 2026-11-23 MYT. **Scope:** public Notebook READ ONLY + own public
GitHub repository + authenticated owner-score READ ONLY. No author code executed,
no new Gemma GPU, no Kaggle competition submission, no modification of the
frozen 0.18 champion.

## Exact provenance and caveat

- [Public author Notebook](https://www.kaggle.com/code/evgendvorkin/can-gemma-4-become-a-software-engineer).
  Authenticated Kaggle CLI retrieved **the latest code**, not a proven copy of
  the linked V41 source. [Source audit and 3 CPU tests](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/45103325460);
  [Section 11 previews](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/45103494366).
- Latest Notebook contains 14 cells, Section 11, and its three explicit research
  aims: inspect real PASS/FAIL trajectories; compare original Patchsmith with P2
  on identical issues; change **one** action-selection mechanism, including a
  candidate explore/edit/verify checkpoint near calls **16 and 20**, then repeat
  on held-out issues.
- The author's Notebook describes **6 PASS and 6 FAIL** in its new local panel.
  It does NOT establish an official 6/12 public leaderboard result; it does not
  identify a matched effect of the proposed call checkpoints.
- The claims **150 read_file lines** and **second repair 0/10** are *not present
  in the downloaded Section 11*. The competition harness may have a 150-line
  read limit, but attributing a 0/10 second-attempt outcome to this author from
  Section 11 was unsupported. Do not use those as the author's main finding.

## Frozen baseline and most current owner experiment

- Own [official 0.18 Champion](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/44659728947):
  ref 58183466, 31B, historical Budget-Fit V2 derivative, 5 min/60 calls.
- Own new [mandatory Evidence-Channel](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/45040840527):
  official ref 58729456, submitted and still **PENDING** at live 2026-11-23
  authenticated CLI read; numeric Public score blank. It removes free-form
  shell, graph and semantic search, retaining four native tools plus a
  bounded source/test/diff Skill. This is not a verified improvement yet.
- Own scored Coder LoRA ref 58558350 is COMPLETE **0.12** (worse than control).
- Own [real private 31B trace audit](../evaluation/gemma31b-failed-repair-vs-gold-20261120.md):
  12 traces, 2 PASS evaluations on the *same* issue; 0/12 full final scored
  Patch artifacts recovered; 3 of 4 gold-informative failed evaluations had
  an explicit edit-path localization mismatch. The file-path proxy does not
  prove the final patch root cause.
- Own two-issue private Candidate History diagnostic is now **FAILED** per a
  2026-11-23 authenticated Kaggle state read; it had previously been QUEUED.
  No independent real-model patch-history grade exists. Do not relaunch GPU
  without distinguishing an infrastructure failure from model behavior.

## Comparison: what to borrow and what to reject

| Idea | Public author's Section 11 | Our verified state | Decision |
| --- | --- | --- | --- |
| Judge trajectories | Inspect PASS/FAIL actions, not prompt length | Prior traces and candidate-history tools exist, but final patches incomplete | **Adopt** per-tool action-funnel diagnostic |
| Same-issue counterfactual | Original Patchsmith vs P2 | Prior paired V2/V3R 1/3 vs 1/3, with 62 vs 81 calls | **Adopt** matched outcome + cost, not just action counts |
| Calls 16/20 | Proposed decision checkpoints | No proof fixed checkpoints address our main failure | **Measure before hard-coding** |
| More prompt text | Author explicitly questions this | Several prompts/skills have not transferred to resolved-task gains | **Avoid** prompt accumulation |
| Model training | No training claim from Section 11 | Our third-party Coder LoRA scored 0.12 | **Do not resume** without a new causal reason |

## Implemented in this branch

- `scripts/audit_evgen_notebook_20261123.py`: safely extracts public notebook
  headings, Section 11 and relevant keyword evidence without cell execution;
  deliberately does not assert latest code equals historical V41.
- `scripts/gemma_action_funnel_20261123.py`: analyzes **existing** Candidate
  History tool-boundary JSON. It measures the first materialized patch,
  explicit edit, submit request, observation/opaque calls, and patch existence
  at calls 16/20. It does **not** grade code or infer that nonempty patches are
  correct. Submission attempt/result callback is deduplicated.
- Pure CPU unit tests cover no-execution, version caveat, event boundaries,
  patch timing and duplicate-submit calls.

## Next genuine model-quality experiment (NOT yet launched)

**Question:** When a 31B agent already sees repository evidence, do its tool
decisions cause correct early edits that later survive verification and
submission, or merely more tool activity?

**Precondition gate:** first diagnose the FAILED existing history Notebook;
then obtain an actual COMPLETE independent Candidate History grade, with gold
PASS/no-op FAIL controls and verified candidate coverage. An infrastructure
crash or incomplete history cannot be counted as a bad model repair.
If unavailable or scored candidate missing, report UNKNOWN, not 0%.

**Only after that evidence and the pending official submission resolve:**

1. Select untouched, disjoint issues before observing the treatment outcome.
   Compare unchanged source+budget control to exactly one action-selection
   treatment (for example, evidence-completeness before first edit), not
   topology + toolset + prompts combined.
2. Fix model Gemma 31B, wheelhouse, 5 min/60 calls/80 turns, prompt/tool
   availability except the **one** tested mechanism, and random seeds/run
   ordering where supported. No hidden reference/test content enters agent.
3. Record per-issue official-native grader resolved, rescue/regression matrix,
   first source change, exact submit-boundary/final patch, test feedback uptake,
   tool calls, wall time and packaging/runtime errors.
4. Primary decision = **net independently resolved tasks**, not patch rate,
   hit@k, shorter prompts or fewer tools. Treat small-n effects and repeated
   Public score stochasticity as uncertain. No promotion to official
   competition submission without a positive paired result.

**Stop/pivot:** if there are no passing intermediate patches, do not spend
budget on patch retention; work on requirements understanding/patch generation.
If correct patches exist but are lost, pursue retention. If evidence is
truncated or not acted upon, test a bounded context-coverage decision rule.
No checkpoint-at-call-16/20 prompt is assumed to help without matching results.

**Current experimental status:** code/CPU instrumentation implemented; no new
real-model treatment. Official owner best remains 0.18 while #58729456 PENDING.
