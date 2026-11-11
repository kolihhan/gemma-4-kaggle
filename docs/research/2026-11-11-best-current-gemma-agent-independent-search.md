# Best currently evidenced Gemma 4 Developer Agent direction — 2026-11-11 (MYT)

## Executive decision

**Strongest demonstrated candidate under this account: keep the previous scored 31B V2 bounded single native-tool agent (Public 0.18, ref 58183466).** There is NO locally scored replacement better than 0.18. **The most informative newly reproducible challenger is an attributed public 31B single-agent, prompt-only alternative**, not another nested scope/coder architecture. This challenger has NOT been independently scored here and is not a new official Kaggle submission.

**Top leaderboard != top reproducible release.** The current third-party CLIST mirror shows first place at **0.29** and multiple **0.24** contenders (2026-11-11 snapshot), but the leading team's exact checked agent bundle is not publicly recovered in our evidence. Their scores are NOT a license to claim a reproducible 0.29 method. https://clist.by/standings/google-the-gemma-4-developer-agent-competition-coding-artificial-intelligence-custom-metric-70662440/

## What was verified, not assumed

| Option | Public claim or account score | Source/behavior evidence | Decision |
| --- | --- | --- | --- |
| Leader #1 (samson8) | CLIST 0.29 | Public ranking; no verified downloadable leading bundle | Competitor benchmark only, not replicable yet |
| Multiple top teams | CLIST 0.24 | Individual implementations/scored ZIPs unverified | Do not guess their technique |
| flexonafft v10, publicly tracked | **Version-specific Public 0.22** | SAME four-file SHA as seven other scored runs ranging **0.12–0.22**, average **0.15625** | Real high score, **no reliable evidence of better underlying configuration** |
| bliverrigpdoge 4 config files, no training | **Notebook title says 0.22; notebook's exact official scored best was NOT independently verified** | Kaggle authenticated public Notebook source pulled, one literal four-file bundle; three files **byte-identical** to our frozen V2, only `prompts/system.md` differs; no multi-agent, Skill, adapter or training | Highest-information **publicly inspectable prompt-only challenger**; do not label as verified 0.22 result |
| prvsiyan / Gemma and the Shape of Doubt | Kaggle page shows **Best Score 0.20 V32**, newest listed version scored 0.15 | Latest source pulled but no one-to-one attributable literal four-file ZIP; best V32 content not recovered | Real alternative, but avoid claiming latest code produces best score |
| honghanhhh / Gemma 4 Baseline LB 0.24 | **Title says 0.24; actual Kaggle page Best Score 0.18 V3** | Latest public source pulled, but its declared bundle not verified as submitted version | Reject title-based claims |
| Account V2 bounded | **Authenticated completed Public 0.18**, id 58183466 | Immutable third-party V2 reference, 31B single native tool agent | **Preserve as scored best** |
| Account V4 CGR | **Authenticated completed Public 0.15**, id 58222227 | Original ZIP SHA and official submission receipt | Demote; no identical resubmission |
| Account wrapped V5 | **0/1 resolved** on private public-dev task `requests_7328` | Real 31B invoked nested AgentTool once, error once, no successful return and NO patch in 302.5s | Reject unchanged nested architecture |
| Post-hoc V2 same task | **0/1 resolved, but produced 3454-character source patch** | Same 31B, same task, 5m/28 calls, 19 scorer tool calls; 377.9s total walltime including evaluator | Confirms direct root produced a patch; not statistical quality evidence |

## Scored 0.22 independently cross-checked — but it is a stochastic outlier

Following the first audit, I downloaded the public scored-version CSV from [Gemma 4 Agent: Public Config Draws](https://www.kaggle.com/dariushafshar/gemma-4-agent-public-config-draws) and verified its **VERSION 10** entry for [`flexonafft/gemma-4-budget-aware-coding-agent-v2`](https://www.kaggle.com/code/flexonafft/gemma-4-budget-aware-coding-agent-v2?scriptVersionId=357955943). That score is **0.22** with a concrete traced `files_sha256` of **`56010e9e9d4c7f33856ce49d12ec3edae5c912261986e999a4aa989b3cd463cb`**; unlike a title-only claim, this table records an actual version score. [Authenticated read-only public ledger cross-check](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43055057050).

**Crucial:** eight scored rows share that **EXACT same four-file hash** (across authors and repeat submissions). Their Public scores are **0.13, 0.12, 0.17, 0.22, 0.17, 0.17, 0.12, 0.15** — mean **0.15625**, median **0.16**, min **0.12**, max **0.22**. This 0.10 within-config spread makes the high 0.22 **insufficient evidence of a superior method**. Source publication and selection effects mean the mean is descriptive, not a guaranteed expected score. It explains why chasing isolated maxima is dangerous and why a 0.18 scored baseline can be the most defensible fallback.

The exact `flexonafft` v10 public Notebook was fetched successfully; simple `ast.literal_eval` found no unique literal four-file dict in that version's code, so our own static tool did **not** independently recover its bundle bytes. The published version-indexed CSV was compiled from source by its maintainer and supports the matching hash; preserve that **provenance distinction**. Do not silently attribute the unrelated `bliverrigpdoge` public prompt `475cc9...` to `flexonafft` v10.

Additional false-title check: `jingshuifu/gemma-4-dev-agent-lb024` v1 was actually scored **0.15**, and `honghanhhh/gemma-4-baseline-lb-0-24` had a verified v3 best **0.18**, despite both titles implying 0.24. [Source rows](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43054776326). **No reproducible, version-specific public 0.24/0.29 agent bundle has been independently verified.**

This **reinforces** the present decision: retain scored 0.18 V2, use the strictly controlled `bliverrigpdoge` prompt-only 5min candidate ONLY as an unscored experimental arm, and prioritize issue correctness + early source edit rather than raw leaderboard maximization. No new GPU inference was launched during these source investigations.

## The actually recovered public notebook — exact comparison

Public source ref: https://www.kaggle.com/code/bliverrigpdoge/lb-0-22-4-config-files-no-training

- Real Kaggle source pull and static non-executing analysis: [Action 43053330477](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43053330477).
- Prompt source explanation and version-metadata attempt: [Action 43053571359](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43053571359). Kaggle `kernels_list` did not expose `score`/`bestScore` for this Notebook; thus **0.22 remains a notebook TITLE claim**, not a verified version score.
- Public system prompt SHA-256 `475cc9b7fcc0dc295532f5cb5e1928f26a491f501837ad08b1c79bdbe1a3eaa4`. Frozen V2 prompt SHA-256 `a42c35081c08f316fc76b02886c82d4073e6c143b63c40a86085b382b8bf113e`.
- **Everything else matches original V2 file bytes**: `agent.yaml` `680799291cc7d156d06fb7bfb5577f683ccc0d555b00e8ddb662d577f9bfa5e4`, `configs/sampling.yaml` `571a934e89911734927533f1d36cbcc7b8d493592febe63b217e911cf7ed4926`, `eval_config.yaml` `916cf6cb34a6cc3de39837fa72cac681599b9ac2a3ee0b893adadfd36474c531`. Original has 31B, 28 tool calls, 80 turns, 8min task cap, thinking budget 4096.
- Public prompt emphasizes localizing and editing by ~call 12, one targeted test and immediate patch. **But V2 already has the same edit-by-call-12 constraint**; the evidence supports a difference in instruction wording and priority, **not a new control mechanism** or causal explanation for any higher score.
- Public prompt recommends avoiding all graph tools because they allegedly return nothing; **this is stale/contested under modern wheelhouse**. Community public CPU replay reports 270/314 code-graph queries returning matches for `swegemma 0.2.10/0.2.11`, versus 82/314 under earlier builds. The original V2 wisely uses graph as a backup, not default. https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/748323
- Strong run-to-run variability is reported even for identical ZIPs, so a single title score cannot demonstrate a robust prompt gain. Independent scored version-specific comparison required. https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/750350

## Exactly reproduced challenger, CPU-only

[Deterministic attributed builder](../../scripts/build_public_prompt_only_control_20261111.py) fetches the PUBLIC Notebook externally and safely uses `ast.literal_eval`; **never executes its third-party notebook code**. It enforces exact public prompt SHA, immutable V2 source ZIP SHA `a4b10f6b8034fd7fffa144a7ee3fbd8faf9a84503ffb1349d1522ba048b534d3`, equality of original model/tool/sampling config and exactly two allowed task clocks. The public source files are not copied into this public repository.

[Four tests plus real Kaggle source CPU build](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43054075167) **SUCCESS**, no GPU, no Kaggle push, no official submission.

| Variant | Frozen SHA-256 | What changes vs source V2 | Score |
| --- | --- | --- | --- |
| Public-original 8min | `ca4869eaa76547bf5c9dafcac0e2d796203ca4d0b4e7e2fbefef9db6a92dc542` | Exactly the public Notebook prompt, otherwise identical config | **Unscored here**, public 0.22 only title claim |
| Fair matched 5min | `fdb862b0f8391b0596f200ccb8e3bece40d9dc8f1e3d60e63537277ac626649d` | Public prompt plus 8→5 minute cap, unchanged 28 calls/80 turns/model/sampling | **Unscored** |

The 8min and 5min candidate file contents differ only in the time-budget line. The 5min variant is a NEW unscored combination and must NOT be attributed with the public Notebook's title score.

## Updated rules and model choices

The official competition rule page currently permits **31B, 12B, E4B, E2B**, same model variant for every agent/subagent in a submission (the old repository assumption of 31B-only is outdated). See https://www.kaggle.com/competitions/gemma-4-developer-agent/overview/prizes and Kaggle staff announcement https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/748287.

This opens a real speed/quality trade-off: smaller models could finish more edits before the **12h total scorer budget**, including sandbox preparation, but a smaller variant can degrade reasoning/repair quality. No independent 12B vs 31B head-to-head evidence for this exact harness is present, so **do not automatically pivot models**. Google LiveCodeBench v6 published 31B 80.0 vs 12B 72.0, but competitive coding benchmarks are not this exact issue-repair evaluation. https://gemma.ai/models/gemma-4/model-card/

## Action ranking (PI decision)

1. **KEEP** scored 0.18 31B V2 as safety/final fallback.
2. **HIGHEST INFORMATION/LOWEST COMPLEXITY:** private predeclared disjoint-task 5min direct-single-agent head-to-head, V2 control versus the exact public prompt-only 5min challenger. Measure resolved, first edit, patch, latency and complete denominator. Attribution and source digests locked. Do not submit an untested prompt just because its Notebook title says 0.22.
3. **SECONDARY:** consider 12B same prompt/runtime as a throughput experiment only after confirming model weight availability in Kaggle and private startup feasibility; do not mix models, do not treat Google's general coding benchmark as target score.
4. **REJECT FOR NOW:** V4-CGR 0.15 official, V5 wrapped 0/1 no patch, old optional Contract & Impact 0/4 versus V2 0/4, and any unverified '0.24' Notebook title.
5. **DO NOT repeat** identical scoring submissions or keep creating multi-agent topology merely to collect green CPU gates.

No official Kaggle competition submission was triggered by this analysis. No training or new 31B GPU inference was triggered by this public notebook comparison. Future task selection, model choice and GPU resource use require fresh preflight.
