# Independent Research Reset — Gemma 4 agent (2026-11-06 MYT)

## Official-score-only audit: precommitted global-budget counterfactual (2026-11-06)

**User-selected execution channel:** Audit → official Kaggle code submission → authenticated score verification. Do not launch local model inference, train, run an independent issue evaluation or consume personal GPU. This explicitly supersedes the conditional local-GPU diagnostic above, **not** the prior no-leak and do-not-overfit rules.

**Evidence reviewed before choosing intervention:** 4 existing official submissions all COMPLETE: E4B baseline `57879765` 0.03, Reliability `57921371` 0.03, 31B original `57983156` 0.08, exact attributed V2 ref `58019162` 0.17. Verified [Kaggle ledger audit, Action 42161771179](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42161771179). Upstream source V2 `submission.zip` pinned SHA256 `a4b10f6b8034fd7fffa144a7ee3fbd8faf9a84503ffb1349d1522ba048b534d3`, Apache-2.0 source: [lynnsakurai V2](https://www.kaggle.com/code/lynnsakurai/gemma-4-budget-fit-agent-w-bounded-rescue). The original V2 `timeout_seconds: 240` is a **single-command** timeout; `max_time_minutes: 8` is the separate **task-agent session** cap. These fields are NOT a configuration contradiction (harness reference `HARNESS_README.md` section 7.1).

**Exact candidate before seeing its score:** retain the **same** externally sourced single-root Gemma 4 31B system: same exact source zip members, model, prompt, nine tools, sampling parameters, evaluation `timeout_seconds: 240`, `max_tool_calls: 28`, `max_turns: 80`. Change **only** `evaluation.max_time_minutes: 8 → 5`. No user-visible claim of originality, novel architecture or private holdout efficacy. Marker: `audit-globalbudget-cap5-v0:public-v2-derived`.

**Mechanism hypothesis:** official 12-hour wallclock for ~120 hidden issues includes setup. Worst-case 120×8 = 960 agent-minutes, which exceeds 720 total; 120×5 = 600 agent-minutes, allowing 120 minutes for setup/other overhead. These are **worst-case caps**, not measured average execution times. This intervention sacrifices slow-case opportunity to preserve later-case coverage under the global cap. The author's claim that most resolved tasks averaged ~3 minutes is background from a different evaluation and not a guarantee. Source: competition official [overview](https://www.kaggle.com/competitions/gemma-4-developer-agent/overview).

**Decision contract:** Submit once (if Kaggle one-per-UTC-day slot and credential gates permit) to score the one-variable public V2 derivative. No private/local scorer run, no GPU kernel, no training. Inspect official exact ref and terminal status. If Public >0.17, record as an **exploratory** gain consistent with (but not proving) global-budget coverage; if =0.17, no demonstrated lift; if <0.17, this cap may be too tight. **Any** outcome could reflect stochastic execution, host epoch differences or limited 58-issue public sample. Never infer per-issue mechanism or hidden distribution from one leaderboard number; do not run a grid of caps or another candidate based on this result. If submission unavailable, report the blocker rather than bypass it or resubmit a copy. Preserve both original scored reference and original canonical `submission/`.

**STOP:** once candidate is officially submitted or a hard gate blocks it. The next *research* decision requires evidence beyond a single aggregate public score; do not call a cap sweep an innovation.

---

## Follow-up evidence — Nov 6, 2026 (authenticated, read-only)

**New official result:** Existing exact V2 reproduction ref `58019162` is **COMPLETE, Public 0.17, Private score not reported** as of **2026-11-06 04:08:31 UTC** (Actions [42160680339](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42160680339)). The author's claimed 0.18 was not our score; 0.17 is ours, and is a reproduction, **not original work**. Original 31B single-root 5-minute package ref `57983156` remains Public 0.08; these two runs change prompts/tool selections/budgets/turns and cannot identify a single causal variable. Both use pretrained 31B and no LoRA. Their 0.09 displayed-score difference is direct benchmark evidence of a stronger publicly shared **single-root** system, **not evidence for adding a sub-agent**.

**Current resource gate:** `kaggle quota --format json`, authenticated at **2026-11-06 04:10:34 UTC** (Actions [42160889153](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42160889153)): **GPU remaining 0.00 h / 30 h**, used 31.79 h; quota refresh **2026-11-07 00:00 UTC = 08:00 MYT**. TPU shows 19.97 h remaining but moving to TPU changes runtime/hardware and invalidates the intended same-environment 31B comparison. No new GPU session was launched.

**Research correction to the conditional 5 vs 8 minute plan below:** The 12-hour budget covers about 120 tasks including setup. A fixed 8-minute cap for every task could consume 960 minutes (vs 720 available); the cap is not mean time, so this does not itself prove V2 uses too much time. It does mean **5 vs 8 minutes alone is not yet the highest-value causal test**. A published author's multi-run 129-case v19 comparison reports 8-minute 44/129 vs 15-minute 44/129 in a separate configuration; not a direct 5-vs-8 controlled test or evidence of transfer. [Original author's Kaggle discussion](https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/747696).

**Updated next decision once a legitimate GPU becomes available:** Reuse the exact public V2 baseline to collect **one diagnostic 31B trajectory on already-inspected development task(s)** in the official private scorer. Record first useful edit, repeated reads/tools, patch validity and wall-time. Do not choose a new model, edit prompts, inspect reserved holdouts or report a quality gain. Then decide whether the next falsifiable intervention should target budget allocation, localization or patch semantics. If adequate original V2 trajectories already exist, analyze them instead of rerunning a task. A 5-vs-8 paired test is justified only if the trajectory actually points to time cutoff as a bottleneck; otherwise retire that proposed ablation.

**Interpretation:** We have a verified stronger external single-root baseline, but **no verified original agent improvement and no causal diagnosis**. No GPU/LoRA/training or new competition submission was performed in this follow-up.

---

**Decision: STOP extending the evidence-stage/verifier/topology lane. Do not treat the failed cohort gate as a negative model result. Do not default to another E4B-vs-31B benchmark either. Start with a simpler, architecture-neutral diagnosis of why attempts fail under the full competition budget.**

This is an independent, critical source review, **not an experimental performance improvement**. No task/model evaluation, training, LoRA, Kaggle competition submission, GPU startup, scored artifact modification, or change to `submission/` was performed for this reset. An existing frozen experiment's data and controls remain reserved.

## Actual evidence (and what it cannot establish)

| Finding | Provenance and directly established result | Does *not* prove |
|---|---|---|
| Same-policy model swap | Scored E4B Reliability-v1 ref `57921371` Public **0.03**; scored untrained 31B ref `57983156` Public **0.08**, same source prompt/config except model declaration, per `NOW.md` and Actions 41979509173 | Model capacity causality, same hidden task-level improvements, host epoch equivalence, statistical significance |
| Existing E4B development trajectories | Existing 17-task Reliability-v1 set resolved **1/17**; **16/17** made mutations, **11/17** ran an executable-classified test, **5/17** submitted after a nonzero test command with no intervening mutation, **0/17** had a recognized pre-edit test; `docs/evaluation/trace-test-evidence-v0-2026-11-05.json`, Actions 41987818297 | That verification is the primary bottleneck, that a nonzero command means wrong patch, or that 31B hidden failures match E4B development |
| 12B smoke under fixed 5-minute budget | Two `rich_3278` cases with 12B at thinking 4096 and 1024 both produced **no patch** despite the second raising tools from **3 to 18**; `docs/evaluation/12b-rich3278-model-size-ab-2026-10-31.md` | 12B is always worse, model scaling has reached a ceiling, or 31B will be inefficient under a different budget |
| Third-party reference scored bundle | Public Budget-Fit V2 reference uses 31B, **8 min/issue**, **28 tools**, **80 turns** and changes prompt/tools/sampling compared with our 31B **5 min/issue**, **32 tools**, **64 turns**; its author's claim is 0.18; our exact-source submitted ref `58019162` was **PENDING at last authenticated Nov 5 status check** | That 0.18 transferred to our account, that budget or any individual policy caused it, or that copying V2 is research |
| Latest model-free quality gate | Frozen research lane: Rich gold-pass **13/14**, FastAPI **6/16**, total **19/30**; subsequent **19/19** gold-pass candidates failed the no-op, so the preregistered balanced 4+12 remains **NO-GO**. Actions 42066105011, 42067120930 and 42068107095 (all SUCCESS as CPU workflows). | That 11 gold-control failures are faulty tasks rather than version/dependency/test problems, or that evidence transfer worsens/helps resolution |
| Harness scope | `submission/agent.yaml` on reviewed branch is a **single E4B root**, no evidence-stage. The Kaggle scorer currently supports declarative ADK agent configurations and closed bound workspace tools; a prior root SequentialAgent hit compaction. | That the more complex research-only B/C candidate has ever solved an issue or that any custom general-purpose Python tool can be submitted |

**Repo-state warning:** default-branch `NOW.md` is dated Oct 31 and describes a different candidate; it must not override Nov 5–6 research artifacts. `PUBLIC_VISIBILITY.md` also differs between older main and later research branches. This audit intentionally does **not** change sharing/security policy or mark anything public-safe.

**Competition constraint (official):** issue-level PASS/FAIL patch verification; **12 total hours for the agent phase across all tasks**, plus the model-variant and restricted tool rules. Source: https://www.kaggle.com/competitions/gemma-4-developer-agent/overview . Kaggle Staff subsequently added E4B/E2B/12B as supported variants; this announcement outranks the stale overview model allow-list: https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/748287 . The mismatch is explicit, not a licence to assume unsupported capabilities.

## Audit of our past reasoning

1. **Premise unsupported:** `0/17 pre-edit tests` was treated as proof that a new evidence stage should raise solved rate. This is only a trace characteristic; agent correctness may be limited by patch semantics, context, tool use, test reliability or insufficient time.
2. **Causal inference error:** observed F4/F5 behavior on inspected E4B tasks was projected onto a different scored 31B system without matching trajectories. Even E4B's nonzero test exits were not classified as assertion vs import/dependency/collection failures.
3. **Engineering became the research product:** multiple cohorts, replacements, CI and B/C schema validations delivered rigor but zero new quality outcomes. The FastAPI gate failed on source/test eligibility, **not** evidence-stage effectiveness.
4. **Baseline confounding:** the attributed public V2 candidate differs in wall-time, tools, turns and prompt; comparing its public result with ours cannot isolate one cause. Per-task 8-minute caps must also be assessed against the **global 12-hour cap**; spending more on every task may reduce throughput.
5. **No demonstrated benchmark overfitting in model parameters:** no scored quality tuning of the new stage was performed. The accurate diagnosis is **hypothesis lock-in, high research overhead, and risk of selection-driven evaluation overfitting**—not proof that a trained model overfit.
6. **Research-direction lock-in:** neither new agent roles nor new LoRA nor 31B-only scaling should be default options just because prior protocols were frozen. All require a capability-level mechanism and a cheaper strong alternative.

## External counterevidence (transfer is NOT guaranteed)

- **Agentless**, Xia et al., *FSE 2025*, shows that a relatively simple localization → candidate repair → validation method can compete with complex autonomous agents; its original results use different base models and SWE-bench, **not our Gemma scorer**. https://conf.researchr.org/details/fse-2025/fse-2025-research-papers/85/Demystifying-LLM-based-Software-Engineering-Agents
- **SWE-agent**, Yang et al., *NeurIPS 2024*, isolates the value of better agent–computer interfaces; the interface, not just the model, can change actual task outcomes. https://proceedings.nips.cc/paper_files/paper/2024/hash/5a7c947568c1b1328ccc5230172e1e7c-Abstract-Conference.html
- **SWE-Bench Pro V2**, Scale, 2026, specifically reports benchmark instruction, baseline-vs-gold tests and clean-environment issues requiring remediation; this supports taking eligibility seriously **but not building ever more selection workflows** in lieu of agent research. https://labs.scale.com/leaderboard/swe_bench_pro_public_v2
- **OpenAI, July 8, 2026** found substantial task validity problems in SWE-Bench Pro, so a single aggregate score should not be read as a pure measure of reasoning. This finding is about a *different* benchmark; the 30-case Gemma gold audit has its own concrete evidence. https://openai.com/index/separating-signal-from-noise-coding-evaluations/

## Architecture-neutral competing bottleneck hypotheses

These are hypotheses, not a claimed ordered ranking of causes.

| Explanation | Why plausible | Key disconfirming observation |
|---|---|---|
| **H1: useful work per wall-time / context** | 12B 5-minute runs stalled before patch; V2 uses 8 rather than 5 minutes; official **12-hour total** creates a real allocation problem | More time under identical 31B policy yields no more correct progress, or reduces solved tasks per 12-hour budget |
| **H2: semantic patch generation / candidate discrimination** | E4B often reaches edits but resolves little; a successful test exit does not guarantee issue resolution | High-quality independently checked candidate patches are routinely generated but agent merely fails to select or submit them |
| **H3: issue localization / information selection** | Repeated reads and missing recognized pre-edit checks may waste context; graph/embedding tools exist | Correct file/function is already read early and supplied to the model but the fix remains wrong |
| **H4: verification and repair control** | Five E4B cases submit after nonzero test commands with no edit; visible lifecycle weakness | Most unsuccessfully scored patches are already wrong before any meaningful test, or test infrastructure is confounded |
| **H5: evaluation harness / distribution mismatch** | FastAPI gold 6/16 and corpus heavily Rich/FastAPI; no hidden 31B per-task feedback | Independent clean tests across repositories reproduce the same failure stage and ordering |

We currently **cannot adjudicate H1–H4 as a primary bottleneck** from the aggregate official Kaggle score. They are not mutually exclusive.

## Research decision and smallest discriminating next step

**Immediate (no model/GPU required):**
- Stop new evidence-stage/cohort/verifier engineering, and do not repurpose the pre-existing capacity-v0 holdout.
- Do **not** re-submit V2; treat `58019162` as pending **until a new authenticated terminal status is actually observed**.
- Preserve the original 31B single-root scored ZIP and the externally attributed V2 ZIP. They are two reference *systems*, not proof of one mechanism. Do not extrapolate a stronger 31B hidden-scorer conclusion from 17 inspected E4B cases.
- Separate **task eligibility**, **agent process quality**, **semantic patch validity** and **Kaggle hidden score** in reports. Do not create another evaluation platform to do so.

**First new inference experiment, only when legitimate private 31B runtime exists:**

> **Does extra usable compute help the *same* single-root Gemma 4 31B solve problems, or just prolong unproductive tool loops?**

Compare **exact same frozen 31B model, prompt, tools, and task setup**, varying only an operational per-task cap from **5 to 8 minutes**. Start on a few **already-inspected development** cases with verified gold-pass/no-op-fail controls (not frozen independent confirmation). Measure **first useful edit latency, correct/incorrect diff, targeted test result, resolved, total wall-time** and most importantly **resolved-per-12-hour global budget**. The purpose is **mechanism diagnosis**, not a performance claim or final tuning on those dev cases. One paired test only; no multi-arm architecture redesign, no gold hints to the agent, and no fresh post-score holdout selected in response to failures.

- If extra compute yields meaningful additional correct patches *at acceptable global cost*, consider a **budget allocation/stop policy** hypothesis instead of adding agents.
- If extra compute only adds rereads or wrong patches, pivot to **code understanding / candidate discrimination**; challenge the autonomous-agent scaffold against a simple staged localization/repair candidate, *provided the official declarative harness can implement it*. Agentless is a source of counter-hypotheses, **not** a method to copy.
- If patches already appear semantically correct before failures, reopen **verification/test selection**, or, where warranted, **model adaptation**. No training/LoRA is authorized by this document.

**Stop/pivot triggers:** no controlled 31B private runtime → no fabricated model experiment; B/C stage not actually run → no efficacy or failure claim; qualitative evidence limited to repeatedly inspected dev issues → no generalization claim; external V2 score alone → no method selection or leaderboard hill-climbing.

## Minimal handoff for the next agent

The useful next output is **one falsifiable causal insight with task-level evidence**, not another 200-line preflight, new task pool, or tweak copied from a public prompt. Keep `submission/`, previous experiment contracts, source archives, and existing Kaggle submissions unchanged. Research lane may be reopened only when new observations actually favor its mechanism.
