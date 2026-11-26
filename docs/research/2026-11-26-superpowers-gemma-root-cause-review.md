# Gemma 4 — Superpowers root-cause research review (2026-11-26)

## Decision

**Do not submit Frontier Balanced or another sampling/budget variant based on this review.** The 0.18 scored champion (`58183466`) remains the owner baseline. FastPath (`58808118`) and Sampling (`58875512`) scored 0.15 each on authenticated Kaggle. The evidence favors investigating **semantic requirements-to-implementation coverage** rather than additional actions, editing mechanics or minute-cap changes. This is **research prioritization, not a tested score gain**.

Method: Superpowers' systematic-debugging phases — examine actual failures, compare working patterns, articulate competing explanations, test a single falsifiable mechanism, and verify before claiming completion. No Agent or submission modification.

## Evidence acquired

1. An independent genuine 31B 68-task paired experiment: [TechNaom k0/k4 results](https://github.com/TechNaom/gemma4-agentic-swe/blob/main/experiments/g4swe-ablation-full-20261031/SUMMARY.md). I independently recomputed outcome categories from the **literal** public `runs.jsonl`: k0 **34/68 resolved**, **34 failed**, of which **32 submitted a nonempty patch** and **2 produced no patch**. k4 **32/68 resolved**, **36 failed**, of which **35 had a nonempty patch**, **1 none**. Matched outcomes: both=30, k0-only=4, k4-only=2, neither=32. This is a 15-minute/60-tool-call public-development setup **not** our 5-minute hidden scoring, and a nonempty failed patch alone does not reveal the causal bug.
2. Read publicly released k0 trajectory logs and confirmed **at least three** independent failure examples where the agent's own ad-hoc reproduction/check passed before submission but the scorer rejected the final patch: `fastapi_15588`, `rich_4077`, `fastapi_14986`. [k0 public logs](https://github.com/TechNaom/gemma4-agentic-swe/tree/main/experiments/g4swe-abl1-202610241241/20261024-124919_agent_k0/logs). These were deliberately inspected examples, **not prevalence estimates**. The model's own "test passed" is not a sound proxy for hidden requirement completeness.
3. A second team's released [3,985-task-attempt dataset and paper](https://github.com/rathko/kaggle-glassbox/blob/main/competitions/gemma4-swe-agent/paper/paper.md) also reports that incorrect patches eventually dominate failure. The distribution is across different attempts, not the same 68-task cohort. Its same-byte public re-submissions differ by up to three solved tasks; one official point estimate has substantial variance.
4. The owner's [2026-11-06 semantic repair audit](https://github.com/kolihhan/gemma-4-kaggle/blob/research/single-edit-channel-20261124/docs/research/semantic-repair-gap-audit-2026-11-06.md) had ALREADY investigated "contrastive contract checking" on 17 older E4B development traces. It found no confirmed multiple-interpretations-with-available-witness examples and **downranked** the mechanism. Five task statements omitted essential externally linked information. **Do not rename/retry it without new qualifying evidence.**
5. The owner's [31B patch-vs-gold audit](https://github.com/kolihhan/gemma-4-kaggle/blob/research/single-edit-channel-20261124/docs/evaluation/gemma31b-failed-repair-vs-gold-20261120.md) recovered 12 scored traces but no final patch artifacts in those two experiments. A newer six-issue single-edit comparison did retain eight final patches across arms, with zero grader resolutions; only source-path/hunk overlap was audited and gold/no-op validity for those issues was not established. No honest ownership-level root-cause prevalence can be claimed yet.
6. [Assertion-preservation Gemma 31B research](https://github.com/msingatullin/gemma-4-developer-agent/blob/main/paper/writeup.md): dropping specific `pytest.raises(..., match=...)` and nearby assertion constraints caused wrong behaviors in synthetic exercises. The new compressor saved tokens but did **not** improve resolution on five authentic repo issues (1/5 each variant); do not ship a compressor as a presumed score gain.
7. [TechNaom gold/no-op controls](https://github.com/TechNaom/gemma4-agentic-swe/blob/main/paper/paper.md): only 68/129 tasks discriminated fixes in THEIR local environment, not necessarily in ours. Validity controls must precede causal labels; the correct diff need not textually match a gold patch.

## Rejected short cuts

- **Parameter soup:** the prepared 5.5-minute/40-call/2,048-thinking Frontier Balanced changes multiple settings. Its own 120-task, 30-minute setup, 30-second per-task-overhead scenario leaves only ~8.5 minutes of global 12-hour slack; a 20% speed regression makes it time out. It was CPU compiled, not grader evaluated. Do not submit this candidate based on compile success.
- **More graph tools, more agents, LoRA, forced tests, automatic editing and longer prompts:** previous owner interventions or public matched evidence have no demonstrated transfer, so they require an independently supported changed mechanism before a new expensive trial.
- **"Self-test green = solved"**: contradicted by three inspected public 31B failure traces and by weak-test audits.

## One research hypothesis — explicit requirement coverage

**H:** For issues with multiple **explicit** acceptance conditions present in the issue and locally available code/tests, the 31B may fix one obvious example but miss another branch/API/edge condition. A bounded check of *coverage of the explicitly stated conditions*, rather than a generic "run more tests" rule, could remove some semantically wrong patches without more inference stages.

**Rival explanations to distinguish first:** wrong source component; incomplete issue body or external URL; test/harness confound; implementation-invariant misunderstanding; no model-visible executable test; insufficient time. Some issues are unidentifiable offline; no tool or prompt can invent an unavailable external contract.

**Minimum experiment contract (NOT launched):**

1. Recover actual final patches + available model-visible issue text + trace/tool feedback for only already-owned development experiments, privately; separately gold-patch PASS and empty-patch FAIL on the exact evaluator revision. Never feed gold, hidden tests, patch comparisons or task IDs back to the solver.
2. Label every failing patch as `wrong-source`, `explicit-condition-omitted`, `implementation-invariant-wrong`, `spec-insufficient`, `environment-invalid`, or `unknown` with direct supporting evidence. Do not infer prevalence from 3 cherry-picked examples.
3. Proceed to a ONE-VARIABLE conditional intervention only if several independent, gold/no-op-valid cases actually demonstrate `explicit-condition-omitted` with accessible evidence. Freeze fresh task IDs before model runs and exclude all past diagnostics.
4. Compare Champion and treatment under identical model, sampling, tools, 5 min / 60 calls / 80 turns, same evaluator, paired real resolve rates. Report both rescues and regressions plus patch correctness, time, and global 12-hour completion risk. Any single small-panel win is exploratory: keep an untouched confirmation group before spending an official submission.
5. If the prerequisite labels fail, do NOT write a speculative prompt patch; pivot to the empirically dominant actual cause.

**This review made no model calls, consumed no Kaggle GPU, pushed no Kaggle notebook, and created no official submission.**
