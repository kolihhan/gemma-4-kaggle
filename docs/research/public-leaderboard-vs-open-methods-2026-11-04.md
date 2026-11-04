# Gemma 4 leaderboards vs open agent methods — reconnaissance (2026-11-04)

**Purpose:** Distinguish (a) current Public LB leaders, (b) scored publicly reproducible bundles, and (c) public causal experiments; compare against our frozen E4B Reliability-v1. This is desk research, NOT a new experiment or promotion decision.

## 1. Current standings versus public code

- Kaggle official leaderboard is public but dynamically rendered: https://www.kaggle.com/competitions/gemma-4-developer-agent/leaderboard
- Third-party CLIST listing, indexed/updated about six hours before the 2026-11-04 MYT search: #1 **Yurnero / samson8 0.29**, #2 **Yike Xu team 0.24**, #3–#9 **0.24**, #10 **Francis Joseph 0.22**: https://clist.by/standings/google-the-gemma-4-developer-agent-competition-coding-artificial-intelligence-custom-metric-70662440/. Treat this as a **time-stamped third-party snapshot**, not a direct official leaderboard export.
- **The first-place system's actual config/training/code is not established by the available primary disclosures.** Do not ascribe 31B, LoRA, a topology or any particular trick to Yurnero from leaderboard placement alone.
- Official scoring is all-or-nothing issue-level passing; final Private LB uses a different hidden half. Official: https://www.kaggle.com/competitions/gemma-4-developer-agent/overview/prizes.
- Community reverse engineering fits the Public score grid to about **58 tasks** with truncation; *not officially disclosed task IDs/size*. Thus 0.03 ~ 2, 0.17 ~ 10, 0.18 ~ 11, 0.24 ~ 14, 0.29 ~ 17 conditional solves. https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/743506
- The Kaggle notebook **“Gemma 4 Agent: What Took LB 0.12 → 0.24”** self-describes 0.24 but the readable indexed notebook page does not establish which exact bundled version produced that score, so it is not treated as a validated 0.24 open implementation: https://www.kaggle.com/code/hitarthjain0/gemma-4-dev-agent-what-moves-the-leaderboard
- Separately **“Gemma 4 Baseline | LB 0.24”** has the title 0.24, but Kaggle’s indexed notebook widget reports **Best Score 0.18 V3**. Do not equate title with verified version result: https://www.kaggle.com/code/honghanhhh/gemma-4-baseline-lb-0-24
- The open Budget-Fit notebook displays Best Score **0.18 V2**: https://www.kaggle.com/code/lynnsakurai/gemma-4-budget-fit-agent-w-bounded-rescue

## 2. Concrete open systems

### A. Public v19 (yiyu0716): 0.17, verified submission

Primary source and link to both original scored v19 code and full 11-file source notebook:
https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/747696

- Competition base: **Gemma 4 31B**, QAT, **no LoRA** in reported frozen v19 experiments.
- Architecture: analyzer + coder, deliberate localization/tracing in both agent instructions. Native edit tools (rather than replacing them with a safe-edit skill) were more robust within published series.
- Scored v19 submitted with **7.5 minutes/task** (Public LB **0.17**); do NOT conflate with its separately reported **15m/8m, 100 tool-call** local diagnostics.
- Local v19 controlled study on the publicly released 129 tasks: 15m 44/129 and 49/129 in separate runs, and an 8m 44/129 run; thinking disabled. These numbers are *local public-task performance*, not hidden LB.
- Earlier v2 w/ analyzer: 0.13. Removing analyzer's graph tools (v3): 0.08 Public LB. Prescribing tracing (v19): 0.17. These changes are **not single-factor same-host paired ablations** across the LB submissions; treat as directional, not direct causal proof.
- Turning on big thinking often increased local task timeouts and empty patches. For v19th at 15m 100 calls, 47/129 resolved but 49 timeouts and 28 empties (vs 3–7 timeouts and 9–15 empties in the 15m v19 runs).

### B. Public Budget-Fit single-root: 0.18 observed

Kaggle notebook: https://www.kaggle.com/code/lynnsakurai/gemma-4-budget-fit-agent-w-bounded-rescue
Independent long-form experiment account with local/hosted records:
https://pilkwangkim.github.io/posts/Gemma-4-Developer-Agent-Part-2-Measuring-an-Agent-While-Its-Evaluator-Moved/

- **Gemma 4 31B**; **single-root**, so a two-agent topology is not required for 0.18.
- Published E0052 reference: **8 minutes/task, 28 tool calls, 4096 thinking budget**, with a short budget subsection in prompt.
- The byte-identical reference had observed scores **0.15, 0.15, 0.15, 0.17, 0.18** over different host epochs. At least one clean epoch was 0.18; those five are not same-environment replicates.
- Some variants seemed better on development yet got 0.10–0.15 on hosted. For an identical variant ZIP, hosted scores **0.10 versus 0.15** in one same observed host epoch. This is direct evidence of *substantial score variability* independent of file changes; do not identify a mechanism from one LB score.
- With matched local 22 tasks × two seeds, removing 701-byte budget subsection changed 17/44 to 22/44, **but hosted did not reliably beat reference**. Increasing tool cap 28→36 yielded 17/44→14/44, so simply raising tool limits is no magic answer.
- 512 thinking vs thinking-off in a historical 22-task paired test solved 7 vs 5, cut repeated-command loops and increased patch capture, but evidence on binary outcome improvement was weak (p=0.5). Thus *both thinking-on and thinking-off strategies can be viable*, with budget-dependent trade-offs.
- Also shows failures of intended pre-edit evidence protocol: only **1/8** full pinned pre-edit check opportunities performed, which parallels our concerns about **soft prompt instructions** being skipped.

### C. Pre-registered model-size × scaffold experiment (local, not Kaggle LB)

Research: https://mobius.style/2026/10/31/kaggle-gemma4-scaffold-capacity/
Public code/summary: https://github.com/mobius-style/gemma4-scaffold-capacity

- **104 eligible public issues, 3 model sizes × 2 scaffold levels × 5 seeds**; llama.cpp/GGUF on self-hosted hardware, repaired local official verifier. This is **not hidden Kaggle Public LB**.
- Richer scaffold (rules + graph + analyzer) changed:
  - **E4B 10.0% -> 15.4% (+5.4pp; reported 95% CI +2.3 to +8.8)**;
  - **12B 25.2% -> 23.1% (-2.1pp)**;
  - **26B A4B 27.7% -> 26.7% (-1.0pp)**.
- The official scorer currently allows 31B/12B/E4B/E2B QAT, *not 26B A4B*; this external 26B local result cannot directly define a valid competition submission.
- Mechanism interpretation (authors' inference): E4B often quits early and scaffold helps it use tools/produce tested patches; larger models use their budgets and the additional scaffold creates tool-call-cap overhead. That may partially generalize to our under-utilized E4B agent (0/17 tool cap hits), but **our 17-task rich/fastapi dev sample and their 104-task panel are incomparable**, as are E4B GGUF and official scorer QAT runtime.
- The paper's registered prediction and statistical tests have nuance: author explains the observed direction was contrary to preregistration; raw study evidence remains informative but is **not** a proven leaderboard upgrade for our specific build.

### D. Other public designs that are NOT scored validation

https://github.com/Gosling-dude/gemma4-developer-agent publishes a single-root graph/test discovery/script skill design with tests and review helper. Its own README says **no real Gemma LB submission / resolution rate measured**. Do not cite as evidence that skill design wins.

## 3. Head-to-head with frozen Reliability-v1

**Our actual bundle (repo source, not a new claim):**
- `gemma-4-e4b-it-qat-w4a16-ct` E4B base; no adapter.
- Single-root coder, 8 tool names including three code-graph/search variants; tool use is optional and empirically rare.
- `max_time_minutes=5`, `max_tool_calls=32`, `max_turns=64`, command timeout 300s.
- Sampling temp 0.2 / top_p 0.95 / max_output_tokens 16384 / thinking_budget 4096.
- The coder prompt says localize cheaply, smallest patch, avoid bare pytest, run directly relevant verification, one narrow repair only after failure, submit only after pass. **Prompt is a soft policy**.
- Development local: 17/17 completed, **1 resolved**; 13 non-empty patches, 4 empty, mean 89.21 sec, mean 10.41 tools, **0 task cap hits**.
- Same-classifier traces: 0/17 pre-edit targeted behavioral evidence, 3 recognized targeted test calls, 14/17 no targeted test, 2 recognized targeted failures followed by no repair mutation, 14 explicit submissions.
- Actual hosted 0.03 baseline and v1; v1 preregistered 0.08 [0.05,0.12], prediction failed.

| Axis | Our Reliability-v1 | Open v19 | Open Budget-Fit |
| --- | --- | --- | --- |
| Base | E4B | 31B | 31B |
| Topology | single coder | analyzer + coder | single root |
| Thinking | 4096 | off (tested scored lineage) | 4096 |
| Per task | 5m | 7.5m in scored submission; 8/15m local | 8m |
| Tool call cap | 32 | 100 local, scored cap not established here | 28 |
| Mechanism | heuristic cheapest localization, minimal patch, test afterward | explicit localization/tracing, coder editing; graph tools were helpful in study | budget-fit single agent; reasoning with bounded calls |
| Hosted Public | **0.03** | **0.17** | **0.18** |

**Unjustified leaps:**
1. “31B alone explains the gap.” False; no same-policy 31B vs E4B paired test in *our* repo and public architecture/hosting differ.
2. “Multi-agent is what wins.” Contradicted by the 0.18 single-root example.
3. “Thinking off always wins.” Contradicted by Budget-Fit 0.18 with 4096 thinking and local 512-thinking repeat suppression. But it may be much costlier for some models.
4. “Raise tool limit.” Our existing 17 don't hit tool cap and Budget-Fit 28→36 didn't help in a small local comparison.
5. “Public 0.24 notebook title proves reproducible 0.24.” Not established.
6. “The runner is stable.” A host epoch study reports meaningful variance on byte-identical zips and tool behavior changed across wheelhouse builds.

## 4. Interpretation for the active pivot

We have at least **two plausible independent deficits**:

1. **Underlying repair competence (model-capacity/policy class):** The best public 31B systems outperform our E4B by much more than superficial tool-limit adjustments suggest. Model-size/scaffold factorial backs a capacity effect on a different local test population.
2. **Verification information quality and state transitions:** Our E4B often edits without pre-edit behavioral evidence, does not convert reduced broad tests to targeted tests, and skips repair after recognized failure; shared model-space experiments show E4B can benefit from a richer scaffold.

The strongest single experiment is an **untouched same-policy 31B vs frozen E4B paired test**, *after* feasibility/throughput validation. It distinguishes whether changing only model class helps under our policy; it does not explain all potential gains from v19/Budget-Fit topology, prompts or test behavior. If capacity wins but is too slow, consider teacher-trajectory distillation/scaffold improvements rather than automatically promoting 31B; if both fail, prioritize test-aware issue evidence and repair search, not a longer prompt.

**Alternative strategically meaningful objective:** the competition now offers **$10,000 for E2B/E4B small-model entries**, eligible only when selected among two final submissions. Official https://www.kaggle.com/competitions/gemma-4-developer-agent/overview/prizes. This makes an E4B research lane worthwhile even if it is not competitive for the main 31B leader; but the small-model leaderboard score as of Nov 4 was **not independently checked**.

No new model inference, leaderboard submission, or candidate changes were made in this reconnaissance.
