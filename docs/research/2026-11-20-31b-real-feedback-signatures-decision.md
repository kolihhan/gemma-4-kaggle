# Gemma 4 — REAL 31B post-edit model-visible feedback signal census

2026-11-20. **Actual authenticated completed GitHub Actions #44750878666**: https://github.com/kolihhan/gemma-4-kaggle/actions/runs/44750878666

Same pre-existing private finished scorer `kolihhan/gemma4-v3r-v2-pro-nov15-v1`; frozen 31B 3 development issues × 2 arms; NO new GPU/inference/training/competition submission. Model and actual grader outcomes from original matched trial; sensitive tool commands/outputs remain ephemeral on runner. Verified tests and removal of private output from runner. Source: [safe reducer](../../scripts/gemma_31b_feedback_signatures_20261120.py).

| Genuine observation | V2 frozen 31B | V3R optional Skill 31B |
| --- | ---: | ---: |
| Same grader issues resolved | **1/3** | **1/3** |
| Cases with edits in raw trace | 3/3 | 3/3 |
| Cases with recognized explicit post-edit tests | **0/3** | **0/3** |
| Cases with a lexical test/assert hint post-edit | **1/3** | **0/3** |
| Cases with post-edit nonzero command exits | **1/3** | **3/3** |
| Cases with post-edit recognized AssertionError / pytest failure signature | **0/3** | **0/3** |
| Cases with post-edit opaque/unclassified commands | **3/3** | **3/3** |
| Recognized failing test followed by repair in raw trace | 0/3 | 0/3 |
| Actual scorer tool calls | **62** | **81** |

Important boundaries:

- A text-search hit on `pytest`, `unittest` or `assert` in a shell command is a **lexical hint**, not proof the command ran a relevant test. The grader-resolved flag is not shown to the agent.
- Zero recognized explicit tests or error signatures **does not prove zero testing**: opaque shell/Python commands exist on all six task traces; observations can lack structured exits, and raw trace events may be duplicated. Trust scorer tool-call totals only for physical cost.
- V3R had more nonzero post-edit shell calls and costs, but zero rescues, so additional tool actions are NOT evidence of useful repair.
- All cases are previously inspected public-development tasks; no hidden or source-disjoint accuracy claim.

## Mechanism decision

**Retire V3R optional Skill and generic extra-agent/test reminder as score-improvement tactics.** The previous mandatory SequentialAgent achieved 1/3 vs 1/3, +7 genuine calls with no rescues. Existing synthetic host-postedit prototype only proves executable test selection on synthetic projects; no genuine 31B uptake or correctness evidence exists. Do not launch another broadly similar model run or call more source/test-read actions progress.

**Next discriminating question:** among certified gold-pass/no-op-fail tasks that can be run inside the official ADK runtime, is there an *existing issue-relevant test that a legal native tool can execute and whose result is exposed to the root model after its edit*? If no, invest in patch/requirements understanding rather than another verification Skill. If yes, preregister ONE bounded, genuinely new paired 31B comparison (native same model, 5min/60 calls, matched scorer), measure actual PASS rescues/regressions and time before score-facing submission. No reference patches in solver context.

Current official best 0.18 #58183466; Coder LoRA #58558350 COMPLETE Public 0.12, do not repeat. No new Kaggle score from this diagnostic.