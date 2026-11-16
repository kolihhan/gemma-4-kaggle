# SOL EXECUTION HANDOFF — Gemma 4 Developer Agent (2026-11-17)

> **North Star: measured issue-resolution gains that reach an authenticated Kaggle `submission.zip` submission, not a perpetual sequence of private local graders.** This file authorizes no skipping of repo scientific/safety policy and is not a substitute for a valid candidate. Work as an independent Kaggle medal-seeking researcher, not a CI operator.

## READ BEFORE ANY ACTION

Read `AGENTS.md`, `NOW.md`, `RESEARCH_DOCTRINE.md`, `PUBLIC_VISIBILITY.md`, `RULES.md`, `submission/`, current experiment manifests and recent Actions. Official Kaggle Overview/Rules and latest staff announcement outrank stale cached files or old model lists. Do not create new public competition data/reference patch mirrors. This repo remains public and legacy exposure is not certified clean.

Study @yuanzhezhou's independently documented medal solutions, but copy the **scientific habits** (attack the generating mechanism, generate diverse candidate strategies, validate transfer, avoid Public LB overfitting; often collaborate), not a specific classifier. Relevant direct evidence:
- https://www.kaggle.com/competitions/llm-prompt-recovery/writeups/z-d-z-5th-place-solution
- https://www.kaggle.com/competitions/cmi-detect-behavior-with-sensor-data/writeups/cmi-1st-place-solution
- https://www.kaggle.com/yuanzhezhou/competitions

## AUTHENTIC STARTING STATE

- Kaggle competition https://www.kaggle.com/competitions/gemma-4-developer-agent awards Kaggle points/medals. **Issue-level PASS/FAIL** judged by submitted patches and official tests; **12-hour aggregate task time**, not arbitrary global 5-minute constraint. Allowed Gemma 4: E2B/E4B/12B/31B base variant, one base across agents; current 31B baseline. Offline sandbox. Format **`submission.zip` root `agent.yaml`**; current official deadline **2026-12-02 23:59 UTC**, entry **Nov 25**, **1 official submission per day**, up to **2 final**; verify live official page and authenticated quota before acting.
- Account best authenticated numeric official **0.18**, Kaggle submission **#58183466**. Do NOT treat later COMPLETE-but-unscored **#58350278** as a gain. Medal target is *ranking*, not an invented numeric “silver threshold”.
- Reference source source-pinned public Budget Fit 31B V2, 5min/28 native calls/80 turns in historical paired tests; this is a strategic experiment cap, not Kaggle's global max. Frozen root `submission/` is canonical candidate, not ad hoc experiment ZIP.
- Empirically tested and **retired exact configurations**:
  * SequentialAgent mandatory native reviewer: [actual 31B paired grader #43808826562](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43808826562) **1/3 → 1/3**, 0 rescues, +7 calls.
  * Single-stage pre-edit behavior counterexample: [actual 31B paired grader #43886580883](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43886580883) **V2 2/3, treatment 1/3**, 0 rescues / 1 regression, calls 84→55, patches 3→1. Retire this configuration.
- **EXISTING LIVE HINGE — DO THIS FIRST BEFORE ANOTHER GPU RUN**:
  * [GitHub Actions #43900577392](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43900577392), private Kaggle `kolihhan/gemma4-textonly31b-six-nov16`, has been pushed and was **IN PROGRESS at last authenticated check** (do not assume that is still true).
  * 6 new hash-selected dev issues across FastAPI/Rich/Requests, **12 actual scorer evals (6 per arm)**, pinned V2 vs text-only native search/removed 3 graph tools, same model/time/other tools; SHA256 treatment ZIP `f60429bcd3e9f4f149cc1e85381dfa7b58c4e02feee46fde3bb99de08b6e53eb`. CPU render validated [#43900123890](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43900123890). Preregistered [manifest](experiments/solver-v3/pro-textonly31b-independent6-20261116.json).
  * **Before any other GPU:** inspect Actions final status + safe actual grader `PRO_TEXTONLY_V2_ACTUAL_31B_PAIRED_GRADER_RESULT` from job logs; if absent query the *same existing private Kaggle kernel* read-only (no duplicate push). Use only sanitized aggregates; no reference patches/issue text in public GitHub.
  * Exact preregistered pilot advances only if **>=2 unique rescues, 0 regressions, 0 evaluation errors**; otherwise retire exact tool-removal policy. n=6 is NOT independent confidence for official promotion.

## WHY WE KEEP PLATEAUING — SCIENTIFIC REFRAMING

Repeated prompt/tool/topology tweaks trade tokens/time but do not reliably raise **true patch test pass**. Both failed pilot configs add procedural behavior without proving missing root-cause understanding. Another “before edit, inspect” instruction can suppress patch completion. More calls or fewer calls are not the target.

Two rival explanations to pursue only after resolving live run:
- **H_rootcause**: the agent edits plausible but semantically wrong locations; higher-value evidence comes from direct interpretation of the issue, tests/caller contracts, and alternative hypotheses. Predict concrete *new* grader rescues on fresh issues.
- **H_budget/interaction**: the agent spends too much time/calls probing, never submits good patches; simpler tool use, shorter control loop or better context selection improves completion. Predict higher patch rate and resolved success under matched time budget with no quality regression.

Find and compare genuine solver trajectories for why the reference fails vs succeeds: tool evidence used, edit location, actual existing test feedback, wrong-root-cause signature, runtime; **do not copy hidden reference patches into agent context**, repeat familiar n=3 issues, or tune based on revealed outcomes. If trace inaccessible, state UNKNOWN, don't infer tool behavior from prompt. Consider a **model class/capability pivot** (e.g., available legal pretrained fine-tuned same-base adapters, different topology, retrieval quality) only when the pilot mechanism and competition rules warrant; do not force more scaffold.

## PATH FROM SCIENCE TO A REAL SUBMISSION

1. Consume existing live pilot. If pilot loses, stop that configuration. If it passes exploratory preregistered gate, confirm on **>=30 genuinely new gold-pass/noop-fail matched issues** according to `RULES.md`, with paired rescued/regressed count, confidence interval, independent repository/issue distribution and 31B runtime/quota feasibility. No material change to the hypothesis after seeing score.
2. Only after validation: select original vs new candidate on evidence; **build canonical `submission/`** with `submission.zip`, native wheelhouse schema, root `agent.yaml`, one supported base, valid budgets/tools/skills and offline execution. Freeze SHA and result manifest; verify legitimate public source / licenses. Avoid duplicate private kernel reruns and wrong-base artifacts.
3. Check Kaggle account entry, exact current daily submissions left (1/day), final slots (2) and currently running/queued official submissions; uphold 12-hour end-to-end budget. Deadline **Dec 2, 2026**, no last-minute placeholder submission if not validated.
4. **ACTUALLY call the authenticated Kaggle competition submission mechanism** using existing repo-supported path, not merely `kaggle kernels push`, private pilot, green CI or `submission.zip` on disk. Record official submission ID, COMPLETE/PENDING/ERROR and authoritative numeric Kaggle score (if returned). Never invent score or presume a non-numeric COMPLETE is 0.18+.
5. Record commit, `NOW.md`, official result receipt and next decision. Preserve best scored 0.18 unless actual new score wins. The user's request to reach submission is a **delivery objective**, not permission to bypass scientific validation or competition rules.

## Sol's RESPONSE CONTRACT

Use a tiny scorecard:
| Project | Official best before → after | New Kaggle submission ID/status | Real paired grader rescues/regressions | Decision |
Then **忙了什么** (at most 3 short lines). Distinguish a live scorer, a private Kaggle kernel, and an actual official competition submission. If nothing improves, say **NO IMPROVEMENT**, what changed, and the next falsifier — not a green-CI victory lap.

**Do not stop at this handoff document. Continue the actual connected-app workflow toward qualified, authenticated official submission.**
