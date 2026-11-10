# NOW — V4-CGR manual official preflight FULL PASS, no submission due to Kaggle quota (2026-11-10 23:55 MYT)

**One-shippable-candidate delivery validated:** [Manual one-shot preflight Actions 42848898816](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42848898816) **SUCCESS**. The actual exact SHA-locked V4-CGR archive `3e56add0b7a94d81e46bff35326df314459e8a8fb3c2e80e68691222809cc9bc` passed preflight, the official `swegemma` injected CodeExecutor drove a scripted-model counterexample fail→native edit→same-test pass→submit real event chain, and a *private CPU Notebook builder* was correctly prepared for `kolihhan/gemma4-solver-v4-cgr-one-shot-20261110`. This is a tested **preparation artifact**, not an already-pushed Kaggle kernel or submitted competition entry.

**No new Kaggle submission made:** On the push-triggered preflight run, the official submission step was **SKIPPED** and `V4_CGR_NO_OFFICIAL_SUBMISSION_TRIGGERED=TRUE` logged. Authenticated quota from [Action 42848511113](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42848511113) at 15:50:24 UTC: `allowed_now=0`, `num_today=1`, `active=[]`; do not attempt submit while quota blocked. One-shot official workflow [.github/workflows/solver-v4-cgr-manual-official-once.yml](.github/workflows/solver-v4-cgr-manual-official-once.yml) **only** attempts a real submit on explicit `workflow_dispatch` `submit_official=true` and a fresh authenticated slot. Marker `solver-v4-cgr-one-shot-20261110` prevents repeated receipts. No scheduled or background automatic future submission.

**Scientific state:** no actual Gemma 4 31B tool uptake and no independent issue-level score for V4 yet. Best *real scored Public* stays **0.18** from old V2 SafeTime5 ref `58183466`; do not misattribute it to V4. Do not retune V4 based on CPU fixture. Next decision when inference/official quota is available: perform **one** real 31B V4 exploratory official submission or a matched disjoint private 31B uptake experiment, then score issue correctness and cost; if real contract-generation uptake is low or score fails to improve, change method class rather than accumulate prompt changes.

---
# NOW — V4 Counterexample-Guided Repair implemented, official CPU integration verified (2026-11-10)

**New substantive mechanism (not another 60-call sweep):** implemented [Solver V4-CGR](experiments/solver-v4/README.md). The single 31B agent now has a production-legal `run_skill_script` capability to CREATE an issue-specific executable pytest contract from observed repository APIs, require a genuine assertion failure BEFORE editing, lock the exact authored test outside the repository, then run precisely that same test AFTER a native source edit. Only original fail→post-edit pass counts as `counterexample_repaired`; unknown relevance and hidden issue resolution remain **FALSE**. This is an adaptation of the known Agentless generated reproduction-test method, not a new scientific invention. If it is not selected by the actual model or does not improve hidden issue resolution, reject it.

**Verified actual shipped mechanics:** [Official CPU end-to-end Actions 42847735843](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42847735843) **SUCCESS**. Candidate built from byte-pinned public Apache-2.0 Budget-Fit V2 31B through V3-R; SHA256 **`3e56add0b7a94d81e46bff35326df314459e8a8fb3c2e80e68691222809cc9bc`**. At unchanged 5min/28calls/80turns the official `swegemma` `AdkSandboxCodeExecutor` with scripted no-inference ADK Model executed actual `load_skill→run_skill_script(before)→edit_file→run_skill_script(after)→submit_patch` events and demonstrated true pytest fail→pass with identical locked test. All independent unit tests and package checks passed; no new GPU or official competition entry was created. The **real Gemma 31B uptake and independent task success are not measured**.

**Kaggle reality:** [Authenticated official slot check 42848511113](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42848511113) found **`allowed_now=0`, `num_today=1`, no active submissions**, so no further competition submission was attempted. Actual best scored Public remains **0.18** from prior V2 Toolcap60 5-minute ref `58183466`, unrelated to V4. The previous private 31B GPU kernel was still `QUEUED` at the last read. Do not claim a model-performance breakthrough or schedule repeat submissions.

**Ship-ready route in progress:** [manual-only one-shot V4 preflight workflow](.github/workflows/solver-v4-cgr-manual-official-once.yml) checks quota and source ZIP SHA then creates a private CPU Notebook builder; a real official code submit is gated behind an explicit manual `workflow_dispatch.submit_official=true` and fresh authorized quota. Creation/push events run **preflight ONLY**. No automatic future submission. Record its final preflight conclusion separately.

**Current research decision:** V4-CGR is the *only* new candidate; freeze it rather than accumulate V4 prompt tweaks. Next measurement must use real 31B under actual quota/inference availability, record contract generation uptake, evidence consumption, independent issue PASS/FAIL, model cost and rescues/regressions. For a causal local comparison keep V3-R or pinned V2 at matched 5min/28calls; eventual official Public claim must **exceed 0.18**. An internally generated test passing does not certify the reported issue. Existing V3-R's CPU-only success remains valid historical evidence, not a competitive result.

---
# NOW — New OFFICIAL Public Best 0.18; V3-R remains unscored (2026-11-10 23:31 MYT)

**New authenticated official Kaggle result:** [Actions 42845134459](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42845134459) at **2026-11-10 15:31:14 UTC** read Kaggle's own competition ledger: **submission ref `58183466` `toolcap60-safetime5-v1-20261110` COMPLETE, Public Score `0.18`**. Prior exact V2 31B reproduction ref `58019162` COMPLETE `0.17`. This is the actual new best by **+0.01**, and is **only** a 5-minute tool-call-budget variant, **not** Solver V3-R or an independently verified architectural win. Earlier 8-minute Toolcap60 ref `58164176` COMPLETE **without** a score. Do not report 0.17 as current best anymore.

**The scientific next gate is M2, and competitive bar rises to >0.18:** Existing V3-R exact ZIP `ae8201c0ce30daf581102ef5d22886f8a4dcebfae47236dffb02ffa6426f9b0c` has passed true official CodeExecutor + scripted ADK FunctionCall/FunctionResponse + real pytest fail→edit→pass→submit (Actions 42785080724), but has **no real 31B model uptake or independently graded issue resolution**. A matched-budget fresh-issue probe is mandatory before claiming it improves on a control. Use the matched 5-minute/28-call V2 control for causal comparison; compare final official result separately against best scored 5-minute/60-call `0.18` because budgets differ.

**Inference blocker remains:** The same authenticated [Actions 42845134459](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42845134459) found the pre-existing private 31B kernel `kolihhan/gemma4-toolcap-31b-42609260933` still **QUEUED** (2026-11-10 15:31:13 UTC). Its GitHub polling Actions already exhausted without private model results. Do not launch duplicate expensive GPU kernels, misdescribe `QUEUED` as evaluating, or use CPU scripted tests as evidence of Gemma's skill uptake.

---
# NOW — V3-R actual official ADK sandbox repair mechanism CPU PASS (2026-11-10)

**M1 DONE, true official executor-level integration:** [Actions 42785080724](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42785080724) SUCCESS. The frozen V3-R ZIP was compiled with the actual swegemma AdkSandboxCodeExecutor. A **scripted, no-inference BaseLlm** made real ADK FunctionCall/FunctionResponse events: `load_skill → run_skill_script(before) → edit_file → run_skill_script(after) → submit_patch`. The packaged witness executed actual pytest on a synthetic local git repository: failure before edit, pass after, response consumed to select repair and submission. **12 tests, official compiler and limits all passed.** Exact new candidate ZIP SHA256: `ae8201c0ce30daf581102ef5d22886f8a4dcebfae47236dffb02ffa6426f9b0c`. See [implementation evidence](experiments/solver-v3/README.md).

**Real bug repaired:** original witness assumed `/workspace`, while official subprocess sandbox can remap checkout. Script now resolves actual checkout via `SWE_WORKSPACE`, `PWD`, `/workspace`, cwd. [Official swegemma source check 42783433294](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42783433294) confirmed the evaluator injects its sandbox CodeExecutor into compile_submission. The NO_CODE_EXECUTOR error in ordinary standalone ADK is not an official-run failure.

**Not yet proven:** the successful model in this CPU probe is scripted, **not real Gemma 4 31B**; independent unseen-issue resolutions and an official V3-R score have **not** been measured. The old private 31B kernel was QUEUED at 2026-11-10 08:30 UTC. Existing ref `58183466` was PENDING; best scored Public still **0.17**. Do not launch duplicate GPU pilots or new V3-R official submission based on only synthetic evidence. Next M2: a single preregistered disjoint real 31B tool-uptake probe and matched issue-level correctness test as soon as GPU is actually available. Reject Skill mechanism if ignored or net-negative.

---

# NOW — Reference research: actual V32 artifact and user-provided config-only 0.22 (2026-11-10)

**Completed forensic source review:** [2026-11-10 public Kaggle notebooks comparison](docs/research/2026-11-10-two-public-gemma-notebook-comparison.md) with read-only evidence [42773762918](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42773762918), [42774739938](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42774739938) and [42775023705](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42775023705). **prvsiyan high-scoring V32 archived ZIP retrieved**, not guessed from latest Notebook: V32 public best displayed 0.20, latest displayed 0.15. The model, nine tools, 28-call/8-minute budget and sampling are byte-identical; only `prompts/system.md` differs; V32 includes a post-final-edit checkpoint. This is a controlled archive diff, **not proof of causal scoring gain**.

**bliverrigpdoge `LB 0.22` source pulled:** a one-cell, literal four-config, no-training 31B agent with native tools, 28 calls/8 minutes/80 turns, early localization, prompt edit, narrow tests and submission; **0.22 is title-asserted, not independently verified official score** from the public kernel metadata. Neither reference demonstrates a novel deterministic repair controller. **Decision:** do NOT copy/re-submit their prompt-only or 8-minute configs or claim agent architecture improvement.

**Research objective unchanged:** our 31B V3-R CPU-valid executable pytest witness still requires a real model function-call/result trace, feedback uptake and independent resolution improvement at matched time before a single V3-R official submission. This public-reference research did **not** start new inference or competition submissions. Earlier official 8-minute/60-tool variant failed timeout; do not use reference budgets blindly.

---

# NOW — Solver V3-R executable candidate built, official CPU VERIFIED (2026-11-10)

**Actual new software:** `experiments/solver-v3/skill/scripts/witness.py` runs real, bounded targeted pytest, saves pre-edit evidence outside the worktree, classifies after-edit repair vs introduced regression vs unchanged failure vs blocked, and refuses to equate a narrow test with hidden issue resolution. The deterministic 31B candidate builder `scripts/build_solver_v3r_candidate.py` combines the pinned attributed V2 source, the witness `SkillToolset`, a bounded evidence-feedback instruction, and **5min / 28 calls / 80 turns** (avoids failed 8min / 60 calls). No training, LoRA, second model, or novel custom callback/tool registry.

**VERIFIED:** [Actions 42749343409](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42749343409) **SUCCESS** — all **10** focused real pytest/build unit tests, official `adk-submission 0.2.13` + `swegemma 0.2.11` CPU compiler and limits checks, compiled root with `SkillToolset`, and **actual script from ZIP** executed on a synthetic repository. SHA256 of exact V3-R research ZIP: **`25e86f12c992a068cac77ae532482374be5a3dc508a55b4844869aa0241cc50d`**. [Detailed V3-R implementation/evidence](experiments/solver-v3/README.md).

**NOT VERIFIED:** Gemma 4 31B selecting `run_skill_script` in a real task, feedback consumed, disjoint issue-resolution improvement, non-timeout full official scoring. **No V3-R competition submission was performed.** Do not report this as a stronger scored system or merge/promote to canonical `submission/` prematurely.

**Current inference blocker:** authenticated read-only [Kaggle status action 42617516719](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42617516719) rechecked at 2026-11-10 03:21 UTC and found the older private 31B pilot **QUEUED**. No duplicate private GPU pilot launched. Existing official Toolcap60 SafeTime5 ref `58183466` remained PENDING in authenticated [Action 42746055733](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42746055733) read at 03:18 UTC. Best actual scored Public **0.17** from attributed external V2; no V3 score.

**ONE next decision:** as soon as private 31B execution is actually available, run a **small, disjoint, preregistered live tool-call probe** and require typed evidence that the model called and used the repair-witness result. If it doesn't, reject Skill V3-R rather than extend prompt. Then only if mechanism and total cost warrant it, do a matched 31B task-level resolution comparison and eventually a single official submission. While the Kaggle GPU queue blocks, stop at reproducible CPU proofs; no empty Kaggle submissions or further time-cap parameter tuning.

---

# NOW — ONE Solver V3 research-to-Kaggle lane (2026-11-10)

## USER-ALIGNED PI RESET — architecture → correctness → official score (2026-11-10 11:06 MYT)

**Current single mission:** Create a genuinely stronger **Gemma 4 Developer Agent**, not another prompt, timeout, tool-cap or Reviewer variation. The user has four non-negotiable outcomes: (1) competitive performance **beyond scored 0.17**, (2) a real tool-level/decision-level agent mechanism, (3) Research → running Agent → independently verified issue fixes → legal Kaggle ZIP → one official score, (4) reuse existing evidence/evaluation resources; no speculative user-managed retraining or repeated expensive GPU runs. The live plan is the **existing** [goal-aligned PI plan](docs/design/goal-aligned-replan-2026-11-10.md) (new 11:06 MYT directive). Do not start another replan file.

**Verified engineering truth:** Confirmed top Kaggle 0.17 is a **third-party Budget-Fit V2 31B reproduction** (`58019162`); it is the byte-pinned comparison control, **not our own new mechanism**. Historical `submission/` is E4B; `experiments/solver-v3/` remains a written design, **not implemented, tested or submitted**. Prior V2 31B 4-task pilot: four nonempty patches, **0/4 independently resolved**; Contract & Impact 0/4; reviewer scored 0.13; call/time-only variants do not prove semantic improvement. Toolcap60 8-minute ref `58164176` is COMPLETE with no score and user-reported Notebook Timeout. Toolcap60 5-minute recovery ref `58183466` was **PENDING** at latest authenticated check 2026-11-10 03:14:48 UTC ([read-only Action 42746055733](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42746055733)); recheck only via existing read-only ledger when needed.

**ONE NEXT IMPLEMENTATION:** Build `Solver V3-R` inside `experiments/solver-v3/`, sourced from immutable 31B V2 control. Develop supported decision/action behavior: use actual repository/requirement witnesses, one materialized edit, classify real targeted test outcomes, make one meaningful semantic repair or preserve tested candidate, then finalize/submit inside shared runtime. Must demonstrate native ADK **function-call + function-result** and contrasting action choice with scripted clean CPU fixture **before** private 31B; generic private Python callbacks are NOT registered in official Kaggle submissions. If the intended deterministic interface cannot run under official tools/Skills, close it as unsupported instead of writing extra instructions. Existing `scripts/candidate_history.py` is an **observer only**, not a submitted capability.

**M1** implement legal v3 builder + synthetic event-level ADK verification; **M2** matched V2-vs-V3 on preregistered fresh tasks, issue PASS/FAIL as primary metric, count rescues/regressions and total time; **M3** one immutable, valid, no-timeout `submission.zip`, one accepted official submission, score >0.17 required for claimed competitive win. If separate pilot GPU blocks, no endless polling: at most one explicitly exploratory official submission after full source validity and allowed quota, not a claim of quality. No new GPU, training, submit or run has been launched by this replan.

---
**Objective:** build a genuinely stronger Gemma 4 coding agent with *more independently resolved unseen GitHub issues under the official 12-hour aggregate agent+setup budget*, then deliver one legal, non-timeout, scored official Kaggle submission. **Target:** surpass our confirmed best Public **0.17** (external Budget-Fit V2 reproduction), with a defensible mechanism and resource cost. [Sole current PI replan](docs/design/goal-aligned-replan-2026-11-10.md).

**Verified Kaggle ledger (2026-11-10 02:55 UTC, [Action 42746055733](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42746055733)):** ref **58019162** scored **0.17**; ref **58045795** scored **0.15** (V2 5 minutes); ref **58112753** scored **0.13** (Recovery Reviewer); ref **58164176** = `COMPLETE` + blank score, with user-reported **Notebook Timeout** (Toolcap60 8 minutes); ref **58183466** = **PENDING** + blank score (Toolcap60 5-minute recovery). Accepted ZIP ≠ quality gain. No confirmed original V3 improvement.

**True current architecture:** `submission/` is historical **E4B** source, while scored 31B artifacts were built from pinned external Budget-Fit V2 sources. The public repo's ~102 Actions are mainly operational history, **not** 102 working solver features. No real Solver V3 is implemented. Official ADK supports a restricted native tool registry; arbitrary participant callback/submit wrappers are not supported by the existing scorer. Do not claim a hard deterministic verifier gate exists.

**PIC decision:** stop time/tool-call cap sweeps, new Reviewer copies, optional Skill instructions and extra submission wrappers. Freeze exact 0.17 V2 control and existing exposed denominators. The primary hypothesis is **semantic repair/diagnostic test feedback**, not more tool use; keep checkpoint/branch selection, coder adaptation and specialist roles as alternatives gated by genuine evidence. Private 31B kernel previously remained QUEUED; no duplicate GPU launching just to generate more process metrics.

**ONE next executable work item:** implement an *actual supported tool/action mechanism* for **Solver V3-R** under `experiments/solver-v3/`, prove its invocation and feedback handling in a minimal exposure-free CPU ADK fixture, build a reproducible competition ZIP, and test for **real issue-resolution lift** on disjoint tasks when inference is available. If private 31B remains unavailable, avoid infinite polling and consider one explicitly exploratory official scored test only after real execution/validity checks and quota; no leaderboard parameter grid. Don't mutate or promote historical `submission/` until a verified candidate exists. No user-managed training unless separately approved.

**Source of truth:** [PI roadmap](docs/design/goal-aligned-replan-2026-11-10.md), [timeout incident](docs/evaluation/toolcap60-notebook-timeout-recovery-2026-11-10.md), [ADK feasibility](docs/research/adk-lifecycle-probe-2026-10-31.md). Historical entries below retain prior evidence and decisions; **this header supersedes older 'next step' claims**.

---

# NOW — Toolcap60 Notebook Timeout → bounded recovery (2026-11-10)

**New verified incident:** User's Kaggle submission `58164176` reported **Notebook Timeout**. Authenticated [GitHub check 42648039124](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42648039124) at **2026-11-10 02:38 UTC** reported `SubmissionStatus.COMPLETE` with **blank Public and Private scores**; this matches the user-visible error. It is **not** evidence of poor patch correctness. The Kaggle main competition limits agent+setup time to **12 hours total**, independent of optional per-task cap. Earlier 28-call/8min V2 scored **0.17**, and 28-call/5min V2 scored **0.15**. We cannot prove which exact task or engine stall produced the new timeout without grader traces.

**One operational repair, not Solver V3:** new builder `scripts/build_toolcap60_timeout_recovery.py` retains original model/assistant/tool schema, sampling, 60 calls and 80 turns of the failed Toolcap60 ZIP, changing only per-task time **8→5 minutes**. Under an *assumed* 120 issues: 600 agent-task minutes versus 720-minute limit, providing 120 minutes of contingent setup/other buffer; task count/overhead may differ. This is NOT proof of timeout elimination or improvement over 0.17. [New one-shot official workflow 42744871831](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42744871831) passed CPU tests and quota/duplicate checks, started its official ADK preflight and remote ZIP verification; **no new receipt at this writing**. It will submit once if official checks pass and a slot is available. Existing score controls and canonical E4B `submission/` remain untouched.

**Incident report:** [Toolcap60 notebook timeout and scoped recovery](docs/evaluation/toolcap60-notebook-timeout-recovery-2026-11-10.md). **Research direction unchanged:** halt repeated tool/time cap tuning after this operational recovery and resume real Semantic Repair Solver V3 (repo-evidence → verified patch correctness) under matched compute. Never equate successful packaging or official acceptance with stronger agent quality.

---

# NOW — Goal-aligned Gemma 4 strategy RESET (2026-11-10)

**North star:** genuinely stronger *offline software-engineering issue repair*, independently resolved tasks per total competition compute; Kaggle is the external validation endpoint, not a prompt/leaderboard optimization loop. Read the complete [goal-aligned replan](docs/design/goal-aligned-replan-2026-11-10.md).

**Strategy decision:** retire Toolcap60 parameter sweeps and prompt-only Reviewer extensions. Current `experiments/solver-v3/README.md` (checkpoint-first concept) is **not a locked build specification**. First separate semantic candidate generation / meaningful verification feedback from demonstrable loss of an already-correct patch. Pursue one **executed** evidence-grounded semantic-repair candidate only when supported by the bounded diagnostic; B (branch/select), C (clean coder adaptation), and D (specialists) remain explicit alternative pivots. CPU checks establish legality/mechanics, **not quality**.

**Immediate executable research deliverable:** one bounded, evidence-linked F1–F9 diagnosis from **already exposed** development/31B traces (do not rerun known denominators), then implement **one** official-compatible 31B candidate with actual ADK tool/event verification and a frozen disjoint matched-budget correctness test. If Kaggle GPU remains QUEUED, do only source-level/CPU work, no duplicated private kernels. Do not train locally without explicit authorization, publish raw Competition Data, or tune to Public LB.

**Competition status (most recent authenticated result in prior update):** official submission `58164176` **PENDING** with no score at the last recorded Nov 9 check; previous scored reference **0.17** (externally attributed Budget-Fit V2). No verified original model improvement. Avoid duplicate submissions. Public repo README now distinguishes historical `submission/` E4B baseline from actual externally built 31B scored artifacts. Paper track optional, not an active target.

---

# NOW — Latest authenticated Kaggle score check (2026-11-09 23:46 MYT)

**Submission 58164176 remains PENDING, Public Score still blank** at 2026-11-09 15:46:40 UTC, confirmed through authenticated `kaggle competitions submissions -v` in [read-only GitHub Action 42648039124](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42648039124). Historical best scored Public remains **0.17**. Do not claim the new 60-call candidate wins or fails until the actual official result.

**No private 31B benchmark result:** the same authenticated Action still reports private Kernel `kolihhan/gemma4-toolcap-31b-42609260933` = `QUEUED`. The private pilot orchestrator [42609260933](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42609260933) failed after 360 polls and timeout without scoring; the older evidence-gated submit orchestrator [42610991463](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42610991463) likewise stopped after waiting for the queued Kernel. These **GitHub Actions failures were queue/polling timeouts, not evidence of bad solver quality**. The separate direct official submission [42617788829](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42617788829) succeeded and has authoritative ref **58164176**. Avoid retrying either older workflow because the official candidate is already accepted.

**Research continuation:** Stop 60-call parameter tuning. Do not launch duplicate official submission. Focus next implementation on executable Solver V3 with **one writer, actual snapshot/restore of candidate patches, diagnostic test feedback, and valid final submission**; verify official ADK/tool-registry support before introducing any new tool interface or claiming such a topology exists. Disjoint, independently graded patch correctness must drive promotion, not completed CI, token efficiency, or number of native calls. The V3 architecture [contract](experiments/solver-v3/README.md) is still a proposal, not a working contender.

---

# NOW — Official Kaggle Toolcap60 submission ACCEPTED, ref 58164176 (2026-11-09 20:35 MYT)

**Authenticated official Kaggle receipt:** [Explicit one-shot official workflow 42617788829](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42617788829) **SUCCESS**. Official code submission API returned `ref=58164176`; authenticated `competitions submissions -v` immediately confirmed `SubmissionStatus.PENDING`, description `v2-toolcap60-v1-20261109`, timestamp `2026-11-09 12:34:58.570000 UTC`, Public Score blank. **This is a real newly accepted official submission; it has NOT been scored yet.** Previous best confirmed Public remains **0.17**.

**Exact submitted bytes:** verified full private CPU Kaggle builder ZIP round-trip against SHA-256 `e05753aed22f360bfdc74942c0b1b432bc1aca8eeb0741804eb023f9714018f6`; official `adk-submission 0.2.13` compiler and `swegemma 0.2.11` directory/limit validation passed. Model `gemma-4-31b-it-qat-w4a16-ct`, V2 source baseline prompt/sampling/native tools unchanged, only `max_tool_calls` 28→60; task time stays 8 minutes and turn cap 80. No new training. The private CPU builder is `kolihhan/gemma4-v2-toolcap60-v1-20261109`.

**Why submitted without private pilot:** authenticated read-only Kaggle API [42617516719](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42617516719) established the already launched private 31B `kolihhan/gemma4-toolcap-31b-42609260933` was `QUEUED` at 12:30:11 UTC. The user's explicit request was for a new official submission, and the queue could not provide timely evidence. This is an *exploratory* official score check, not an evidence-supported claim of a stronger agent. Old [private pilot action 42609260933](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42609260933) and [earlier gated submit action 42610991463](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42610991463) may still be running/polling; their idempotent submission marker check must prevent duplicates if they resume. **Do not launch another official Toolcap60 submission.**

**Next verified action:** read the new submission's authenticated status and Public Score; if below 0.17 or errored, retain the failed result without tuning from the same public feedback. Design and separately evaluate real Solver V3 generation/repair/verification architecture; Toolcap60 is a budget experiment, not that redesign.

---

# NOW — Direct official submission route unblocked from queued private GPU (2026-11-09 20:32 MYT)

**Confirmed blocker:** authenticated read-only Kaggle CLI [Action 42617516719](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42617516719) reported `KernelWorkerStatus.QUEUED` at **2026-11-09 12:30:11 UTC** for `kolihhan/gemma4-toolcap-31b-42609260933`. The earlier GitHub pilot Action was polling but no model inference or derived score had started for this kernel by that check. Do not call queued model evaluation a successful runtime benchmark.

**User-authorized exploratory official submission:** the user explicitly requested a new Kaggle submission and said go. Instead of indefinitely blocking on the private GPU queue, [one-shot Action 42617788829](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42617788829) was launched using `scripts/submit_v2_toolcap60_official_once.py` and the already officially compiled candidate ZIP SHA-256 `e05753aed22f360bfdc74942c0b1b432bc1aca8eeb0741804eb023f9714018f6`. Tests and authenticated quota/preexisting-receipt checks passed. It verifies the official ADK/limits, publishes a **private CPU** builder Notebook, round-trips the exact ZIP from Kaggle output, and attempts the **single official** `competition_submit_code` call under idempotency marker `v2-toolcap60-v1-20261109`. At last check the Action was installing official compiler wheels. **No verified new submission ref or score yet.**

**Research status:** this deliberately relaxes the earlier *private-pilot-before-submission* gate for the one specific candidate because the user prioritized a new official submission despite GPU queue backlog. It does **not** establish improved solution capability. The unchanged V2 Public reference still scored 0.17; this toolcap candidate differs only in `max_tool_calls: 28 → 60`, with 8 minutes and 80 turns unchanged. Do not call it Solver V3. If the old evidence-gated workflow subsequently resumes, `check_slot()` and the unique description marker must prevent another duplicate official submission. Do not re-run either workflow to bypass quota.

---

# NOW — V2 Toolcap60 officially compiles; awaiting private 31B outcome (2026-11-09)

**Verified compiler gate:** [Independent official CPU Actions 42612471382](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42612471382) **SUCCESS**. The byte-pinned V2 source was downloaded; candidate ZIP passed official `swegemma 0.2.11` limits, `adk-submission 0.2.13`, `google-adk 1.36.1` compiler. The 60-tool-call setting is accepted while 8-minute time and 80 turns remain unchanged. Candidate ZIP SHA-256 `e05753aed22f360bfdc74942c0b1b432bc1aca8eeb0741804eb023f9714018f6`. No model execution or competition submission in this CPU verifier.

**Still running:** [private 31B paired experiment 42609260933](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42609260933) and [evidence-gated official submission workflow 42610991463](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42610991463). Both were running at latest verification. The official workflow passed CPU and authenticated slot prechecks but has not created an authenticated Kaggle submission reference. It must consume terminal independent outcome and stop if its evidence gate fails. Do not duplicate or bypass the active workflow.

---

# NOW — Official Kaggle candidate gated and staged; 60-call 31B proof still RUNNING (2026-11-09)

**Explicit user goal:** obtain a new, stronger official Gemma 4 submission, with substantive architecture reform rather than another prompt-only Reviewer. Do **not** conflate candidate staging with official acceptance.

**Current official candidate path:** [one-shot workflow 42610991463](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42610991463) is **IN PROGRESS**. Its CPU unit checks passed; authenticated Kaggle submission slot check passed. It is currently **waiting on the existing private 31B matched experiment** [42609260933](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42609260933), which has been launched and remains in Kaggle kernel status polling. There is **NO new authenticated official submission ref yet**. The workflow will not start any extra local-model training/inference for that gate. CPU builder `scripts/build_v2_toolcap_submission.py` changes only the V2 tool cap 28→60; prompt, native tools, model, sampling, task time 8 minutes and turns 80 stay unchanged. This is an **exploratory budget candidate**, not an end-to-end architecture breakthrough and not shown stronger yet.

**Fail-closed submission requirements:** `scripts/gate_v2_toolcap60_official.py` requires 8 completed, independently scored evaluations across four previously untested tasks; treatment non-regression on task resolved count; observable actual usage of additional calls or a rescue; total elapsed ≤125% of control. The official workflow then requires official wheelhouse/ADK CPU validation, exact pinned source ZIP equality except one field, successful private CPU Kaggle notebook round-trip SHA verification, an available official quota slot, and final authenticated submission receipt. If these gates fail, **there is no official submission**, by design. Prior authenticated best is Public **0.17**. Do not claim another Public score or new submission ref without an actual receipt.

**Substantial next refactor:** [Solver V3 contract](experiments/solver-v3/README.md) explicitly targets *root-cause repair generation vs candidate loss* through a single-writer model, deterministic versioned patch state, test-feedback-guided selection and validated ADK tool invocation. It is a research design, **not implemented nor submitted**. The previously rejected Contract & Impact optional Skill and Reviewer v0 are not promoted. A genuine V3 must demonstrate end-to-end independent correctness under matched global compute, not merely CPU package validity.

**Current evidence / caveats:** earlier 4-task V2 vs Contract Impact private 31B pilot resolved 0/4 vs 0/4; V2 made nonempty patches 4/4 yet did not solve issues. Tool-cap explanation is plausible because 3/4 V2 tasks reached 28, but is not proven. Separate V2 28-vs-60 test is resolving it. No training, no modification to canonical `submission/` or frozen scored control artifacts. The official Kaggle competition supports a 12-hour aggregate scoring budget. Recheck the experiment and the official pipeline receipts before claiming a stronger new submission.

---

# NOW — V2 tool-call ceiling hypothesis under REAL 31B test (2026-11-09 MYT)

**Competitive goal:** deliver an independently stronger SWE coding agent, not another CPU-valid architecture or prompt-only wrapper. Our best authenticated Kaggle Public Score remains **0.17**, so **no gain is claimed yet**.

**New evidence-led experimental decision:** In the completed 31B [Contract & Impact versus V2](experiments/architecture-contract-impact-v0/31b-paired-pilot-decision-2026-11-09.md) study, exact V2 hit the native tool cap **28/28 on 3 of 4 tasks** yet resolved **0/4**; the new optional-Skill arm resolved **0/4** and made fewer calls. The most direct next falsifiable engineering question is whether **call-cap truncation**, rather than insufficient model capability, caused failures on any tasks. This is not proof the cap is the dominant bottleneck or that additional calls necessarily improve correctness.

**NOW EXECUTING PRIVATE PAIRED 31B EXPERIMENT:** [GitHub Actions 42609260933](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42609260933) passed **5/5 preflight unit tests**, passed a fresh authenticated GPU quota gate (**17.77 hours remaining** at check), compiled an exact pinned source ZIP, and passed the **private Kaggle kernel launch step** (currently polled for actual results). Unique Kernel ref: `kolihhan/gemma4-toolcap-31b-42609260933`. No official competition submission and no training. [Manifest](experiments/v2-toolcap-31b/manifest.json) locks a disjoint SHA-selected **4-task FastAPI/Rich** development denominator, excluding 22 prior inspected/used tasks. The same 31B base model, V2 root prompt, sampling, native tools, **8-minute task time** and 80-turn cap remain unchanged. Only **max_tool_calls: 28 → 60** varies between V2 baseline and treatment; the evaluator's runtime `max_tool_calls` is separately overridden for treatment, not merely changed in a YAML file. Arm order alternates. Private task-level independent `swegemma` resolved score, patches, calls and elapsed seconds will decide this small hypothesis. **No scored result yet**.

**No local overfitting:** Do NOT retune using the four failed Contract & Impact tasks, redo the same denominator, or promote a treatment without an independently resolved task gain on new cases. Fewer calls or a smoother trace alone is not promotion. If 60 calls fail to rescue any tasks, stop call-cap tuning and revisit **generation capability / action-interface architecture / training** based on disjoint error evidence. If it rescues tasks, verify on another untouched denominator before any official Kaggle submission. Kaggle Staff reported a thinking-history interoperability fix in the current wheelhouse, so do not assume dropped thinking context without verifying the current wheel's behavior.

**Engineering status:** An initial experiment workflow failed at preflight metadata/version validation and a second run failed on the renderer module path; both aborted **before GPU push**. These were corrected on this research branch. The current run `42609260933` is the first validated private launched experiment. Canonical `submission/` and the frozen original control ZIP remain untouched.

---

# NOW — First real 31B architecture pilot COMPLETE; no promotion (2026-11-09 19:13 MYT)

**VERIFIED experiment:** [Private paired Kaggle Actions 42576094444](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42576094444) **COMPLETED SUCCESSFULLY**. Fixed [preregistered 4-task FastAPI/Rich public-development denominator](experiments/architecture-contract-impact-v0/31b-pilot-manifest.json); exact V2 vs Contract & Impact under the same 31B model/sampling/budget. Independent `swegemma` issue-resolution score: **V2 0/4; Contract & Impact 0/4**. No test case resolved by either arm. This is NOT a new Kaggle Public Score or an untouched generalization test.

**Mechanism diagnostics:** V2 produced **4/4 nonempty patches**, **107 native calls**, **1,470.36 agent seconds**, **40,961 completion tokens** in retained traces. Contract & Impact produced **3/4 nonempty patches**, **78 native calls**, **1,220.90 agent seconds**, **32,118 completion tokens**. In `rich_3064`, the new arm exhausted all **28 native calls** and ended with an **empty patch**, while V2 produced a nonempty unresolved patch. All eight `swegemma` evaluations completed without task-level execution exception; grader test statuses were 1/2. Faster and fewer calls did not deliver more correct solutions.

**Skill activation is UNVERIFIED, not proven zero:** four new-arm structured traces and four private `.log` files contain **zero exact `load_skill` and `run_skill_script` markers** ([read-only trace check 42607052760](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42607052760); [per-task log check 42607214238](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42607214238)). However official private structured traces report `thinking` / `system_instruction` / `task_prompt` / `final` events, **not a complete typed tool-call stream**. Do not claim a literal zero invocation count or that the deterministic Skill was causally harmful. This experiment changed the entire root prompt and added an **optional** Skill together; it never implemented a compulsory multi-stage architecture.

**RESEARCH DECISION: REJECT PROMOTION OF CURRENT LANE A v0, and stop local prompt tweaking.** Evidence does not justify a second Kaggle submission, another run on the same tasks, or a selection/training intervention. Preserve exact V2 as tested comparator. Next discriminating gate: on **synthetic exposure-free input**, instrument actual **ADK tool-call/tool-result events** to test whether Gemma 31B adopts structured tools and uses feedback. If optional Skill uptake is unreliable, consider a **genuinely governed tool/action interface** (or another coder policy) rather than more textual instructions. Any architecture must be validated on new matched-budget tasks before official submission. This does **not** permanently rule out branch-search, specialized multi-agent architecture or Coder adaptation.

**Full measured result / evidence / pivots:** [31B paired pilot decision](experiments/architecture-contract-impact-v0/31b-paired-pilot-decision-2026-11-09.md). [Per-task derived metrics 42606267763](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42606267763). No new model inference, training, or official Kaggle submission in this decision update. Canonical `submission/` and frozen ZIPs untouched.

---

# NOW — 31B paired private pilot LAUNCHED (2026-11-09 14:56 MYT)

**Verified LIVE Kaggle worker status:** Read-only authenticated Kaggle API returned `KernelWorkerStatus.RUNNING` at **2026-11-09 06:58:45 UTC / 14:58:45 MYT** for kernel `kolihhan/gemma4-contractpair-31b-42576094444`; [read-only proof](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42576357210). This confirms the private kernel is executing, not just GitHub Actions orchestration. No task-level resolved data yet.

**Real inference underway, no claimed quality result:** The independently preregistered Contract & Impact vs exact V2 31B comparison has passed the real GPU quota gate and the **private Kaggle kernel push gate** in [GitHub Actions 42576094444](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42576094444). GitHub step `Launch private paired 31B inference` concluded success; subsequent `Poll same private kernel` is in progress at verification. Kernel ref `kolihhan/gemma4-contractpair-31b-42576094444`. **No Kaggle competition submission**, no weights training, and no new Public Score yet.

**Frozen evaluation contract:** [31B pilot manifest](experiments/architecture-contract-impact-v0/31b-pilot-manifest.json) locks 2 deterministic salt-ranked eligible public development tasks from FastAPI and 2 from Rich, excluding 18 previously examined cases. Each task runs exact byte-pinned V2 and the Contract & Impact architectural candidate with the **same gemma-4-31b-it-qat-w4a16-ct service, sampling, 8-minute/28-native-call/80-turn budget and independent swegemma grading**. Arm order alternates per task; evaluator outputs use separate directories. This is a **4-task exploratory pilot**, not an untouched strong confirmation sample or hidden Kaggle leaderboard measurement. Actual Skill uptake and overhead are yet unmeasured.

**Verified before GPU:** [CPU preflight 42575786043](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42575786043) passed **5/5 structural tests**, downloaded the exact V2 source ZIP with SHA-256 `a4b10f6b8034fd7fffa144a7ee3fbd8faf9a84503ffb1349d1522ba048b534d3`, rendered and compiled both arms into one private 31B evaluator runtime. Derived per-task metrics only will be collected; raw competition data and patches are not published to GitHub. A separate [authenticated quota read](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42361825427) showed **19.51 GPU hours remaining** before launch. The new run independently passed a refreshed quota check.

**Decision not yet possible:** no resolved numerator, per-task traces, wall-time comparison or resource-feasibility verdict is available until the private kernel reaches a terminal state and the results JSON is inspected. Do not promote or dismiss this candidate on CPU checks alone. Frozen ZIPs and canonical `submission/` remain untouched.

---

# NOW — Architecture Lane A executable CPU prototype verified (2026-11-09 MYT)

**Changed research policy:** full architecture and training/representation pivots are permitted by user direction; patch-level tweaks are not compulsory. The original 31B Budget-Fit V2 Public **0.17** remains the *comparison control*, not a mandatory architectural base. Recovery Reviewer v0 official ref **58112753 COMPLETE Public 0.13** remains rejected for promotion. Score delta is not a causal diagnosis of dual agents.

**Concrete implementation:** Lane A, **Contract & Impact → Solver → Verification**, is now an independently buildable architecture under `experiments/architecture-contract-impact-v0/`. It completely replaces the root workflow prompt and introduces a real read-only **contract-impact ADK Skill** recording declared explicit requirements, unknown information, impacted edit paths, model-reported test evidence and actual git changes. Its status is deliberately NOT an independent correctness oracle. The original nine native tools, model **gemma-4-31b-it-qat-w4a16-ct**, original sampling, 8-minute/28-native-call/80-turn configuration, and source-license attribution remain. The tool does not add a second LLM agent or training. `scripts/build_contract_impact_candidate.py` generates a deterministic ZIP without mutating `submission/` or frozen candidates.

**Verified in [Actions 42551996131](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42551996131):** 9 focused CPU tests + 1 real official ADK compiler/Skill invocation CPU test passed; byte-pinned real-source package ZIP SHA-256 `4858587c922ae275417199d8c11c00abce2249e42992657e134ba8d6dc2df975`. Scripted test detects partial multi-file impact without altering source. No model inference, training, private task evaluation or Kaggle submission; **no competitive performance claim**.

**Next decision:** Lane A is engineering-valid, **not quality-validated**. Compare against exact V2 on preregistered clean same-budget 31B cases with independent final issue correctness, actual Skill uptake, coverage errors and overhead; retain noninvocations and failures. Reopen B (branch/select), C (Coder adaptation via clean SFT/LoRA/RL if separately authorized), or D (true specialist multi-agent) whenever their predicted failure mechanism has stronger evidence. See [architecture reset](docs/design/architecture-search-reset-2026-11-09.md) and [candidate contract](experiments/architecture-contract-impact-v0/README.md). The candidate has **not** been submitted; approval is required before any new official submission.

---

# NOW — Architecture search REOPENED (2026-11-09 MYT)

**Research direction corrected:** Small prompt or patch-level improvements are **not** a mandatory progression. The user explicitly permits full redesign of agent architecture, tool interfaces, topology, search and training when supported by evidence. Exact V2 is a scored **control/fallback (Public 0.17)**, not a fixed architectural foundation. Recovery Reviewer v0 ref 58112753 scored **0.13**, so that specific candidate remains rejected for promotion; one aggregate score cannot condemn all multi-agent designs.

**New decision artifact:** [Architecture search reset](docs/design/architecture-search-reset-2026-11-09.md) compares (A) structured **Contract & Impact → Solver → Verifier** end-to-end pipeline, (B) branching candidate search/selection, (C) Coder adaptation via SFT/LoRA and potentially RL, and (D) genuinely specialized multi-agent orchestration. Priority A is **provisional**, grounded in already-inspected E4B cases with incomplete multi-entrypoint repairs and missed semantics; no mechanism has been validated on thinking-on 31B yet. B becomes preferred if independent candidate histories show passing patches discarded; C moves up if correct patch generation is scarce; D must beat an equal-budget single Coder.

**Next engineering gate:** build an isolated, executable **CPU contract prototype** for A rather than adding another Reviewer prompt. It must represent grounded requirements, explicitly missing information, impacted call sites, verification coverage, and source state without fabricating a task oracle; then test the official ADK tool contract. Only thereafter run a preregistered matched-budget 31B study. This branch contains the architecture research decision, not an implemented A candidate or a competitive improvement. Do not mutate canonical `submission/` or frozen ZIPs; no training or new Kaggle submission without separate consent.

---

# NOW — Recovery Reviewer 0.13 terminal; submit-boundary observer CPU-verified (2026-11-09 MYT)

**Current authenticated Kaggle result:** Recovery Reviewer v0 submission **58112753**, marker `recovery-reviewer-v0:430e64d2c9a6`, **COMPLETE**, Public Score **0.13**, Private Score blank. Authenticated `kaggle competitions submission 58112753` read at **2026-11-09 02:09:53.483 UTC / 10:09:53 MYT** via [read-only Actions attempt 3](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42502184083/attempts/3). Exact V2 control remains verified Public **0.17**; the scored recovery arm was **0.04 points lower** in this run. **Reject promotion of this specific Reviewer v0**; do not infer a causal role effect, a general two-agent ceiling, invocation frequency, or per-task failure modes from one aggregate score. No repeat submission.

**Research decision:** return the main architecture priority to exact single-root V2 while evidence is gathered. Reviewer adds complexity and has not earned it. The most important unresolved causal split is **correct patch never generated / edit not materialized / correct intermediate patch lost before submit**. The 17 old E4B records do not contain complete independent patch histories, and official 31B Kaggle scores expose no task-level trajectories in the current evidence. External thinking-off results are supporting hypotheses, not measurements of our thinking-on 31B.

**Implemented, verified, private-only:** `scripts/candidate_history.py` now records a **pre-`submit_patch` request snapshot** and separate tool result/error, independently of the terminal workspace. It distinguishes "passing independent check at submit request", "passing candidate overwritten before submit", attempted-but-unconfirmed submit, reported tool failure and multiple ambiguous requests; the original `diagnosis` is explicitly scoped to the terminal tree. Official ADK Runner scripted CPU integration confirms the submit boundary and unchanged tool-facing response. [Actions run 42550027757](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42550027757): **33/33 focused tests passed**, including 6 new submission-boundary checks, Python compilation and official-wheel ADK fixture. [Design/test contract](experiments/candidate-history-v0/README.md). The code is experiment instrumentation, **not** an improvement of candidate agent or a scored result.

**Exact next experimental gate (not executed):** prelock an exposure-clean private development denominator, keep the 31B V2 model/sampling/native tools/budget unchanged, and instrument **actual** private evaluator task runs using the verified observer. Record final independently graded correctness, every materialized candidate, submit-request candidate, missed/failed edits, tool calls, wall-time and capture overhead. Preserve failures/noninvocations in the denominator. Only if correct candidates are repeatedly lost should a **single-writer candidate-retention/selection** intervention be implemented and compared at matched budget. If passing candidates rarely appear, pivot to issue understanding / patch generation, not more reviewers or prompts. The official `swegemma==0.2.11` source exposes `App(plugins=[...])` in its agent runner, but live observer attachment to real 31B sandbox is **not implemented or validated**. [Read-only evaluator source inspection](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42550388219). No new GPU inference, training or Kaggle submission in this turn; frozen candidates and canonical `submission/` untouched.

---

# NOW — Recovery Reviewer remains officially PENDING (2026-11-09 01:00 MYT)

**Fresh authenticated Kaggle status:** submission `58112753`, description `recovery-reviewer-v0:430e64d2c9a6`, status **PENDING**, Public Score blank, Private Score blank, checked **2026-11-08 17:00:36.747 UTC / 2026-11-09 01:00:36 MYT**. The already-configured read-only Kaggle CLI status workflow was re-run successfully, attempt 2. [Authenticated workflow receipt](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42502184083/attempts/2). **No new submission**; 0.17 remains the verified reference. Neither improvement nor regression can be inferred.

**Scope of what was actually submitted:** `scripts/build_recovery_decision_candidate.py` retains the external V2 native tool interface; an optional tool-free `AgentTool` is requested **only through root prompt instruction**, not a hard trigger. This submitted arm does **not** implement the proposed managed evidence ledger or automatic candidate checkpoint/selection. The `fresh_coder` counterfactual was CPU-packaged/compiled but never run against the model. An aggregate score, even when available, cannot isolate adviser invocation, role-specific benefit, or preserved good candidates.

**Evidence-led bottleneck ranking:** current thinking-on 31B task-level repair histories and reviewer invocation are **UNKNOWN**. The existing 17-task E4B archive has 12 unresolved nonempty finals, one resolved final, and four empty finals, but **all 17 lack complete independently graded intermediate histories**; it cannot distinguish failed candidate generation from wrong final selection or establish the dominant 31B failure. External thinking-off and E4B examples raise repair semantics, edit execution, and feedback use as competing hypotheses, not conclusions about this submission. The most consequential unresolved measurement is **whether the 31B ever produces a correct, materialized patch and whether it survives the final submission**, including exact wall-time/reviewer uptake.

**Decision while PENDING:** hold this frozen candidate; do not re-submit, train, add a helper, or tune prompts using the leaderboard. Next evidence gate: once Kaggle reaches a terminal state, record exact status and score; inspect task-level traces if legitimately available. If not, the smallest justified independent experiment is a **prelocked, matched-budget 31B observation** reusing `candidate-history-v0`, then compare the same evidence packet across ordinary Fresh Coder vs Recovery Reviewer and original V2. Count non-invocations and overhead. Implementation/promotion only after measured failures identify a target, with user approval before another official submission. No claim of a code-level improvement or model-quality gain in this status-only cycle.

---

# NOW — Official Kaggle Recovery Reviewer v0 submitted (2026-11-08 MYT)

**Official confirmed submission:** `58112753`, marker `recovery-reviewer-v0:430e64d2c9a6`, submission status `PENDING`, Public Score blank, created at **2026-11-08 03:03:39 UTC / 11:03 MYT**. The authenticated Kaggle API returned `{"ref":58112753}`, then a fresh authenticated submissions listing independently matched the same ref and description. [Successful official Actions run](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42440992059) / [job logs](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42440992059/job/128609982568). This is a real accepted official competition submission, **not yet a scored result**. Do not submit it again while pending.

**Exact candidate:** `recovery_reviewer` 31B variant, SHA-256 `430e64d2c9a60a737f197a5372afa33c4813526239828b71c5971eda283a743e`, built from attributed byte-pinned Budget-Fit V2. Preserves nine native tools, sampling and eight-minute/28-call/80-turn budget; adds optional short tool-free fresh-context Recovery Reviewer as an `AgentTool`. Root Coder alone edits and submits. Fresh Coder arm is a CPU control only, **not submitted**; baseline account Public 0.17 and previously scored frozen base-evidence helper Public 0.17.

**Gates passed:** 7 GitHub CPU unit tests; official wheel versions (`adk-submission==0.2.13`, `google-adk==1.36.1`, `adk-eval-core==0.1.0`); official `validate_directory` and `compile_submission` for BOTH matched roles using an inference-forbidden model stub; private Kaggle CPU Notebook generated an archive identical to expected SHA; authenticated quota `allowed_now=1`, `num_today=0` just before submission; official submit + receipt. A first private CPU notebook failed due missing `kernelspec`; corrected metadata using a fresh private notebook slug, without changing candidate ZIP. [First failed check](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42440733975); [read-only error trace](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42440915276); [successful fixed run](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42440992059).

**Scientific limitations:** official score pending; no real trajectory-level 31B evidence; helper uptake, independent correctness, gains/regressions, total 12-hour feasibility and Fresh Coder advantage are unmeasured. Do NOT infer recovery is effective from packaging or success of submission API. No training, extra submissions, frozen candidate changes, or canonical `submission/` changes.

**Next:** read official authenticated final status and score for `58112753`. If complete, compare Public 0.17 only as an aggregate signal; no score-based repeated prompt tuning. If pending, do not resubmit. Decide whether independent trajectory experiment is justified before claiming recovery-role benefit.

---

# NOW — Matched Recovery Decision v0 packaged on CPU (2026-11-08 MYT)

**Implementation progress:** built two candidate ZIPs from the exact byte-pinned external 31B Budget-Fit V2, preserving all nine native tools, original sampler, 8-minute/28-call/80-turn cap, and identical root call policy. The only difference between arms is a tool-free fresh helper instruction: ordinary Fresh Coder vs independent Recovery Reviewer. Root Coder alone edits/submits. The one-call conditional trigger is still a model instruction, **not an enforced automatic controller**.

**Verified:** [CPU Actions run 42438857122](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42438857122) succeeded: 3 Python unit tests, real public V2 ZIP hash validation, deterministic construction of both candidate ZIPs, ZIP integrity and strict arm-difference inspection. Hashes and exact implementation: [experiment README](experiments/recovery-decision-v0/README.md). This is CPU packaging evidence, **not scorer compilation or task-quality evidence**.

**Next gate:** no new submission or training. First CPU-compile both new ZIPs using the official ADK compiler with inference disabled; check AgentTool request/response and real budget semantics. Only then run a prelocked matched-budget comparison against V2, the scored frozen helper (ref 58081411 = 0.17), Fresh Coder and Recovery Reviewer using candidate-history as private observer. Measure actual invocation and final independent correctness; keep failures/overhead in denominator. Frozen candidate and canonical `submission/` unchanged.

---

# NOW — Frozen 31B recovery submission scored (2026-11-08 MYT)

**Official authenticated terminal result:** submission ref `58081411`, description `base-evidence-retry-v0:1944471ce983`, status `COMPLETE`, Public **0.17**, Private blank, checked 2026-11-08 07:31:18 MYT (2026-11-07T23:31:18Z) through `kaggle competitions submission 58081411` in [authenticated Actions receipt](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42409716117/job/128563104702). This is a **terminal scored result**, not a pending receipt. The frozen fresh-context helper **did not improve** the exact V2 public baseline of 0.17 in this single aggregate comparison; it does not prove the helper never fired or identify task-level failures. Do not resubmit or relabel this as an improvement.

**Research decision:** no justification for a second agent based on the score alone. Next intervention must test matched-budget fresh ordinary Coder vs recovery-specific Reviewer with identical current-diff/evidence handoff, and preserve the frozen helper as the third comparator. Keep native V2 tools, use candidate-history only as a private observer; don't replace the interface with managed Skill. Measure invocation/patch retention, total runtime, and independently graded resolved rate. No new Kaggle submission, training or frozen/canonical mutation authorized. The Recovery Decision implementation and CPU verification remain **not completed** at this checkpoint.

---

# NOW — Conditional recovery architecture research (2026-11-08 MYT)

**Research deliverable, not a new candidate.** The Chinese [architecture report](docs/research/dual-agent-recovery-architecture-2026-11-08.zh-CN.md) selects one experimental design: a single source-writing/submitting Coder, versioned execution evidence, and an optional short fresh-context Recovery Reviewer. Exact scored 31B Budget-Fit V2 (Public 0.17) remains the fallback/control. Conditional official graph navigation is retained; a new embedding service, always-on Analyzer/Critic, and immediate training/RL are deferred with explicit pivot triggers.

**Diagnosis and controls.** Current thinking-on 31B's dominant failure mix is unmeasured. Generation/feedback use and edit execution lead the hypotheses; existing E4B histories cannot establish candidate-selection loss. The frozen base-evidence retry already contains a fresh 31B helper, so that topology is not a new contribution. The report separates native-vs-managed bundle screening from a same-interface null ablation, and separates fresh context from role specialization using a fresh ordinary-Coder control. Hard repeated-action rules cover only fully observed source operations, not arbitrary shell state.

**Fresh runtime verification.** Official wheelhouse metadata reports v31. Re-downloaded adk_submission 0.2.13, google_adk 1.36.1 and swegemma 0.2.11; all bytes match the inspected cached wheels. The non-LlmAgent-root compaction exception remains present. Package hashes, source facts, limitations, prior scored receipts and 27 primary/repository references are recorded in the report.

**Next discriminating work, unexecuted.** Reuse candidate-history instrumentation with exact V2 on a prelocked, exposure-clean task denominator, grading immutable candidates only after the run. Then screen the managed single-role arm before testing any Reviewer. No new inference, GPU/TPU use, training, task/candidate grading, Kaggle submission, executor implementation or change to canonical submission/, frozen candidates, blind sets or existing experimental contracts occurred in this research turn. The latest account submission state was not refreshed; older PENDING receipts are not current-status claims.

---

# NOW — Candidate history CPU diagnostic implemented (2026-11-07 MYT)

**Concrete progress.** A private-evaluation observer now captures immutable source patches at tool boundaries and grades copied candidates only after the run. The official ADK Runner and sandbox API path passed with scripted CPU responses; the agent-facing tool results stayed unchanged. Twenty-seven focused tests passed. CPU controls distinguished a retained passing candidate, an overwritten passing candidate, a partial repair and an edit that never changed source. These are instrument checks, not model-quality results. [Implementation and scope](experiments/candidate-history-v0/README.md) · [CPU receipts](experiments/candidate-history-v0/cpu-verification.json).

**Existing-record result.** All 17 archived E4B development tasks were inventoried: 12 unresolved nonempty patches, one reported resolved, two empty patches with edit errors, two other empty patches. No complete independently graded intermediate history exists; the 16 unresolved cases cannot distinguish generation from selection. [Derived inventory and source hash](docs/evaluation/candidate-history-archive-inventory-2026-11-07.json). This does not establish our 31B's dominant failure class.

**Resources and execution boundary.** Authenticated read-only check at 17:56 MYT returned 28.99 GPU hours, reset November 14; frozen ref 58081411 remains PENDING. [Status receipt](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42361825427/job/128371635965). Quota is available, but this round retained the original prohibition on model inference. No new inference, training, official submission or candidate change. Actual 31B diagnostic, Docker overhead and task-level candidate grading remain unexecuted. The next actual diagnostic must preserve model, sampling and eight-minute allowance, retain failures, and separate candidate availability from final selection using independent grading.

---

# NOW — Bottleneck reassessment (2026-11-07 MYT)

**Priority revision.** The leading hypothesis is failure to turn available code/feedback into a correct, changed repair. Navigation efficiency remains a competing hypothesis. External 31B thinking-off records improved edit feedback and reduced repeats while staying at 14/33; a recovery-instruction screen showed little compliance and 7/33 versus baseline 9/33. These populations do not identify our thinking-on 31B hidden failure distribution. [Evidence, scope and updated decision](docs/research/flexon-budget-policy-review-2026-11-07.md#bottleneck-reassessment-after-the-comparator-review).

**Next measurement.** In the existing same-budget continuation/retry comparison, independently record whether a correct candidate ever appeared, whether it survived into the final patch, and whether intended edits reached the source tree. This separates generation, selection and malformed execution instead of treating every failure as missing verification. Model execution and independent candidate grading remain unexecuted. No new feature, training, inference, submission or frozen-candidate change was performed.

---

# NOW — Flexon public V10 comparator review (2026-11-07 MYT)

**Research finding.** Retrieved and CPU-rebuilt `flexonafft/gemma-4-budget-aware-coding-agent-v2`, explicitly pinned to Kaggle V10. The 3,713-byte local ZIP exactly matched its official output: SHA-256 `6ff73d104725cc31deadd18787f3f55e5ce534889cec82387e3b280637d34887`. Official compilation passed with an inference stub. Its agent, sampling and evaluation files are byte-identical to our 0.17 V2 control; only the root prompt differs. The public indexed page records 0.22 V10, which we have not independently reproduced or attributed to an individual behavior.

**Decision.** Retain this as an external policy comparator and execution-efficiency hypothesis. Early editing and failed-match recovery are already in our V2. More explicit search/read batching and a total graph-tool ban are differences; their effect on 31B decisions remains unexecuted. No automatic scheduler or executable recovery controller is implemented in the external package. [Source identity, exact comparison, CPU checks, uncertainty and falsifier](docs/research/flexon-budget-policy-review-2026-11-07.md).

**Effect on current work.** Keep the paired-check prototype and its matched control unchanged. Additional script/discovery/dual-execution cost must earn independent patch-quality gains; it has not yet done so. Our verified own best remains 0.17. This review performed no model inference, training, new submission or frozen-candidate change.

---

# NOW — Executable paired-check candidate (2026-11-07 MYT)

**Decision.** Continue with an agent-callable source comparison action, built on the exact attributed 31B Budget-Fit V2. The agent selects its Python check and decides its next action. The Skill script returns that check on original/current source; a matched control returns current/current. The original model, root prompt, sampling, 8-minute allowance, 28-call configuration and 80 turns are unchanged. ADK adds Skill discovery and script tools in both arms.

**Verified CPU result.** Twenty tests passed, including the official compiler, skill activation and script-execution adapter, with inference configured to raise. The standalone notebook schema passed and fresh CPU executions generated deterministic ZIPs. Two previously inspected Flask/SymPy programs also returned the recorded source differences through the new runner. These checks establish execution and packaging, not agent selection or patch quality. [Mechanism, evidence, commands, limitations and falsifier](experiments/paired-check-v0/README.md) · [Exact hashes and CPU results](experiments/paired-check-v0/cpu-verification.json).

**Artifacts.** One CPU notebook, `gemma4-paired-check-skill-v0.ipynb`, selects either arm. Treatment ZIP SHA-256 `df88261b4aa2a9f1337fb0f3860fd197266fae7ac16c7f38ba89ef7bfcbad729`; matched-control ZIP `0570da416031931d9cc7363d0a111a7c52e30dab1032138c4c54e8147f17236a`. Neither has been submitted. Canonical `submission/` and the frozen candidate are unchanged.

**Frozen submission update.** The original scheduled workflow succeeded and submitted the unchanged base-evidence ZIP, official ref **58081411**. Its authenticated receipt at 05:58:06 UTC / 13:58 MYT recorded PENDING and no score. [Exact receipt](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42344893898/job/128320398058). The authenticated read-only check at 07:33:24 UTC / 15:33 MYT still returned **PENDING**, with empty Public and Private scores. [Latest status](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42351756224/job/128341200017). The check did not submit or run inference.

**Still unexecuted.** 31B action uptake, selection quality, next-action effects and independent patch correctness. A causal comparison must start at the same selected-check checkpoint and preserve the remaining budget, with tasks locked before inference and missing checks retained. A notebook screen is weaker end-to-end outcome evidence. If useful observations fail to improve correctness at matched cost, retire this mechanism rather than tune on the 19 inspected external traces. No training, new model inference or submission of this candidate was performed.

---

# NOW — Paired execution feedback CPU experiment (2026-11-07 MYT)

**Decision.** Advance the narrower agent decision experiment. Show the base observation when the agent's own check reaches the relevant behavior and its trajectory lacks an equivalent base observation. This replay establishes when useful feedback is available. A matched 31B continuation is still required to measure its effect on decisions and independently correct patches.

**Protocol and evidence.** Locked 19 archived GPT-5 mini / mini-swe-agent SWE-bench Verified tasks before opening the trajectories. In each of Flask, Requests, pytest and SymPy, took up to six task IDs ordered by SHA-256 of `gemma4-decision-cpu-v0:` followed by the task ID. None overlapped the local Kaggle development task index. No replacements. Used the first eligible recorded agent command after its last relevant source write and the terminal patch printed from `patch.txt`. The archive's submission field was empty, so the displayed patch was recovered from its tool reply and checked against the before and after Git blob IDs. Each command ran twice on base and twice on the edited tree in a local CPU sandbox. Older checkouts received a compatibility replay with the same command and dependencies on both sides. The reference patch was excluded from probe selection and replay. [Pinned trajectories](https://huggingface.co/datasets/tarsur385/swebench-verified-trajectories/tree/773748a7c1222e8a642a7059821498e14293562a/swebench_verified_raw/gpt-5-mini) · [Pinned task data](https://huggingface.co/datasets/SWE-bench/SWE-bench_Verified/blob/78f471b/data/test-00000-of-00001.parquet)

| CPU result | Count of 19 | Issue IDs |
| --- | ---: | --- |
| Repeatable issue-relevant output change | 12 | Flask 5014. Requests 1142, 2931, 5414. pytest 5262, 7571, 10051. SymPy 11618, 24213, 24443, 24562, 24661. |
| No observable change from the recorded command | 4 | Requests 1724, 2317. pytest 8399. SymPy 17318. |
| Test blocked in setup | 1 | Requests 6028. The HTTP fixture was unavailable in the offline replay. |
| No eligible recorded post-edit check | 2 | pytest 6202, 7205. |

**What the feedback buys.** Eight of the 12 changed cases had identical exit codes on base and edit. Three of the 12 already had equivalent base observations in their original traces (Requests 5414 and SymPy 24443, 24562). The other nine would add a base observation relative to the recorded tool history under a compatible environment. Eleven changes moved the checked behavior toward the issue requirement, but three of those runs remained unresolved in the independent archive verdict (Requests 2931, pytest 10051, SymPy 24562). For example, the agent's Rational probe changed the requested value to 1/200, while the archived grader still recorded unresolved. The remaining change replaced an incorrect distance with an exception (SymPy 11618). Preserve behavior output and use independent grading to judge decisions.

**Next falsification.** Start both arms at the same 31B V2 checkpoint after the agent chooses a check. Use the same test command, model, prompt and time allowance. The control gets edited-tree results and the treatment gets base plus edited-tree results. Measure whether the model's next action and final independent correctness improve on cases locked before inference. Count the tasks where no useful difference can be returned. If previously unseen relevant feedback fails to improve correctness at the same cost, deprioritize this mechanism. The 12-of-19 CPU rate is descriptive of this external sample.

Protocol SHA-256 `f49e223e2009f14dcd3b4c9ec78f65b84e2ac53eb076c059548dd732061b5478`. Selected commands SHA-256 `c5bb7f771b0a6ecb7efb4a9a865628095c48fc962af19ed9624e389c413198e7`. This experiment used archived trajectories and CPU execution only.

---

# NOW — Agent decision research pivot (2026-11-07 MYT)

**Decision.** Archive the two-call assertion notebook as a CPU prototype. This supersedes the advancement decision below. The development cases showed that an auditor could construct two behavior checks. They supplied no independent evidence that the agent would choose a useful check or use its result to make a better decision.

**Research question.** Does giving the agent evidence of what its own edit changed improve its choice to keep, revise or revert the patch? The agent chooses the check and the next action. The proposed intervention changes the evidence returned by the sandbox. A matched control runs the same agent-chosen check twice on the edited tree. The treatment runs it once on the base tree and once on the edited tree. Match the checkpoint, model, prompt and total budget. Score on issues fixed in advance outside development and use independent correctness checks. Retain tasks without an eligible check in the denominator.

**Falsifier.** If informative paired observations occur but do not improve independent patch correctness at the same cost, set aside this feedback hypothesis and investigate edit generation and action selection. If informative observations are rare, the intervention has inadequate coverage. This is a research proposal. The frozen base-evidence retry retains its existing schedule.

---

# NOW — Two-call assertion selection audit (2026-11-07 MYT)

**Historical decision (superseded above).** Continue with one CPU packaging candidate for test selection. The existing conditional `base-evidence-retry-v0` schedule stays on its original plan. The 31B Budget-Fit V2 control `58019162` scored 0.17 Public at 8 minutes and the 5-minute variant `58045795` scored 0.15. [Frozen experiment state](https://github.com/kolihhan/gemma-4-kaggle/blob/fea90cd8233cbb49a713393e7071db091f9f8c7a/NOW.md#L1-L9)

**Evidence.** Locked four failures in the public faithful 31B development records before opening the issue text or reference. These runs had thinking off. A bounded search and one narrow read found a testable requirement on FastAPI #13713 and Rich #3278. After locking the assertions, the same CPU probes were run on the base and on independent reference-patched copies.

| Case | Result |
| --- | --- |
| FastAPI #13713 | The OpenAPI root field is absent on base and equals the supplied metadata on reference. The literal constructor spelling in the issue fails on both. The reference exposes `openapi_external_docs`. The predeclared root-only probe checks the output requirement and resolves the exposed slot by suffix. The historical run spent 37 calls paging the application file and recorded an empty patch. |
| Rich #3278 | Base retained all 16 tested private escape sequences. The reference removed all 16 and preserved surrounding text. The historical run repeated malformed edits 71 times and hit 80 turns. |
| FastAPI #15023 | Skip. The task lacks an expected change to a specific streaming example. The historical run made 35 searches and recorded an empty patch. Assertion unexecuted. |
| Rich #3942 | Skip. The task lacks target elements and expected styles. The historical record names 15 malformed edit repeats. Assertion unexecuted. |

[FastAPI development notes and call summaries](https://github.com/happyc0der/gemma-swe-agent/blob/88cfbc6dc9fdce17f90117e17c2ff8c365c7eb16/experiments/2026-10-14-faithful-v54-AB/notes.md#L25-L30) · [Rich development notes and call summaries](https://github.com/happyc0der/gemma-swe-agent/blob/88cfbc6dc9fdce17f90117e17c2ff8c365c7eb16/experiments/2026-10-21-faithful-bf-off-AB/notes.md#L24-L30) · [FastAPI base schema](https://github.com/fastapi/fastapi/blob/5c1f87c56387a96dbdddb2b1c4ec9ba48dcebc4e/fastapi/openapi/models.py#L423-L440) · [Rich base decoder](https://github.com/Textualize/rich/blob/4c5d305bb902ce97011666ada19e48d0b27b49e1/rich/ansi.py#L119-L165)

**CPU packaging.** `gemma4-budgetfit-v2-two-call-assertion.ipynb` generated identical `submission.zip` files in two local IPython executions. SHA-256 `fc828ec9253fc520f5f22e85943d73543be4154d6fb63761f2be3bc2b2e93e8d`. The source was lynnsakurai's Apache-2.0 V2 archive `a4b10f6b8034fd7fffa144a7ee3fbd8faf9a84503ffb1349d1522ba048b534d3`. Reversing the one test-selection replacement restored the exact original prompt. The other three archive members matched byte for byte, including model, tools, sampling, 8 minutes, 28 calls and 80 turns.

**Scope of the result.** Two requirements were recoverable in an auditor's two-call replay. Historical summaries identify navigation and editing bottlenecks, with incomplete tool timelines. Model compliance, patch resolution, and transfer to the hidden set remain unmeasured. No training, model inference or submission was performed in the audit. An independent follow-up would hold budgets fixed and compare how often the agent picks a grounded, runnable check within two calls and whether it improves correct patches.

---

# NOW — Base evidence retry v0 (2026-11-06 MYT)

**Ready for one conditional Kaggle submission.** The private CPU notebook `gemma4-base-evidence-retry-v0-20261106` v1 produced the pinned ZIP `1944471ce98386371ebe52a0d3e6a9cc211ff81803684eeaff5f344532234c1b`. A local CPU build matched that hash. The workflow is active and is scheduled for November 7 at 08:13 MYT. It verifies the notebook ZIP, checks for a prior receipt, and requires both an available slot and no active Kaggle entry on the account before submitting. Ten offline cases passed, including a pending entry, zero quota, a changed ZIP, and a missing response. [CPU build](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42202422197) · [Scheduled workflow](https://github.com/kolihhan/gemma-4-kaggle/actions/workflows/scheduled-gemma4-retry-nov07.yml)

**Latest Kaggle status at 00:40 MYT on November 7.** The five-minute cap audit `58045795` is COMPLETE at **0.15 Public**. The exact eight-minute Budget-Fit V2 control `58019162` is COMPLETE at **0.17 Public**. The observed five-minute score is 0.02 lower in one run per cap. The earlier active entry has finished. The scheduled retry will check the new day's allowance at launch. [Authenticated status](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42171026894/job/128018297926)

**Comparison.** The archive diff against the pinned V2 verified identical 31B model, sampling configuration, and evaluation limits. The candidate adds a read-only diagnosis helper for a relevant failed assertion, adds the conditions for calling it, and rewords the root agent's role line. Treat one official score as a screen of the combined change. Measuring the effect of base-only evidence requires an equal-cost helper with a conventional evidence handoff.

**Next.** Verify the official receipt and compare the terminal Public score to `58019162`. If the scheduled run reports an unavailable slot or an unconfirmed receipt, inspect that outcome before any further submission.

---

# NOW — Independent Research Verdict (2026-11-06 MYT)

**Research priority.** Test whether a fresh attempt can reuse repository observations that still hold on a clean checkout. Use the reproduced 31B Budget-Fit V2 as the practical comparator. The hypothesis concerns the information carried across a retry. The dominant bottleneck on the hidden set remains UNKNOWN.

## A. What we know

| Official entry | Public score | Existing authenticated record |
| --- | --- | --- |
| E4B baseline / E4B Reliability-v1 | 0.03 / 0.03 | [Kaggle receipts](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41585360688) |
| 31B, original Reliability-v1 policy | 0.08 | [Kaggle receipt and feedback check](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42003198673) |
| 31B, exact attributed public Budget-Fit V2 | 0.17 | [Kaggle receipt](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42160680339) |
| V2 with the existing five-minute cap audit | PENDING at 13:53 MYT on Nov 6 | [Last recorded receipt](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42171026894) |

- **FACT.** Reliability-v1 and the earlier single root each resolved 1/17 on the inspected E4B development set. Reliability-v1 was about 12% faster and produced about 20% smaller nonempty patches. The trace audit found five Reliability-v1 cases that submitted after a recognized nonzero test command without an intervening edit. The verifier LoRA was historically trained and the inspected development comparison went from 1/9 to 2/9, with two gains and one loss. Its matched blind effect is UNKNOWN. [E4B review](docs/research/why-reliability-v1-only-003-2026-11-04.md) · [Test-command audit](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41987818297) · [LoRA development run](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41447650864)
- **FACT.** The independent public [Mobius study](https://mobius.style/2026/10/31/kaggle-gemma4-scaffold-capacity/) measured model-dependent scaffold effects under a repaired local scorer (E4B 10.0% to 15.4%, 12B 25.2% to 23.1%, 104 issues per cell). I reconciled all six published cell rates and re-tabulated the released outcomes after excluding documented project diagnostics, verifier training samples and named reservations. The stricter slice contained 22 issues across three repositories and 660 min/max task-runs. Per issue and scaffold, I averaged all 20 ordered pairs of distinct seeds. A rescue means the first seed failed and the second solved. [Pinned run records](https://github.com/mobius-style/gemma4-scaffold-capacity/blob/7356b06b0f5c8b5cc185a03b8ac2b4b68d210425/data/runs.jsonl)

| Local model and scaffold | One draw | Oracle, either of two full draws | Added solves within 360s combined recorded time |
| --- | ---: | ---: | ---: |
| 12B minimal | 17.3% | 22.7% | 0 of 24 rescue pairs |
| 12B maximal | 17.3% | 24.1% | 0 of 30 rescue pairs |
| E4B minimal / maximal | 8.2% / 10.0% | 13.2% / 12.3% | 22 of 22 / 10 of 10 rescue pairs |

- **INFERENCE.** Candidate diversity exists, and its cost depends on the model. The 12B results challenge using a full second run by default. A wider 42-issue sensitivity slice, before additional training and diagnostic exclusions, also had zero fitting 12B rescues out of 120 rescue pairs. These are dependent pair counts on public tasks. The stricter slice is FastAPI-heavy (17 FastAPI, 3 Rich, 2 Requests). The recorded durations are from the local harness and the oracle assumes perfect selection.
- **UNKNOWN.** The split between 31B generation, selection, runtime and task-specification failures. The scored API receipt exposed aggregate status and scores. The 0.08 to 0.17 contrast changes several variables together. An external team also recorded 0.10 and 0.15 from the same ZIP within one observed host epoch. [Bundle comparison](docs/research/semantic-repair-gap-audit-2026-11-06.md#what-the-source-actually-shows-about-v2-vs-our-31b) · [External host study](https://pilkwangkim.github.io/posts/Gemma-4-Developer-Agent-Part-2-Measuring-an-Agent-While-Its-Evaluator-Moved/)

## B. Where the research went wrong

The F4/F5 diagnosis treated a nonzero command and the absence of a recognized pre-edit test as evidence of a dominant failure cause. A collection error, an irrelevant check and a wrong patch can produce the same observation. The repeated E4B denominator supplied diagnostics for that system. Its results cannot identify causes in the scored 31B system. The evidence-stage experiment stopped at eligibility (19/30 gold passes, all 19 fail no-op, too few eligible FastAPI tasks). Contrastive Contract Checking also lost priority because the later source audit found zero demonstrated repository-visible witnesses for competing specifications in the cases it reviewed. These are distinct negative findings about eligibility and support for a hypothesis. [Eligibility run](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42068107095) · [Case audit](docs/research/semantic-repair-gap-audit-2026-11-06.md#completed-case-level-falsification-audit--existing-trajectories-only-2026-11-06)

## C. Three competing hypotheses

1. **Restart with observations verified against the base checkout.** At a fixed checkpoint, give one fresh same-model attempt an observation packet containing matching source excerpts and reproducible, issue-relevant command results. Omit the previous diagnosis and diff. An observation that depends on the abandoned edits is stale after rollback. SWE-Replay reuses a trajectory prefix. RestartSmart can inherit edits and gained 3.0 points on Gemma 31B at 20.5% extra tokens in one setting, with inconclusive separation from its cold-restart control. The proposed distinction is the rule for which observations survive rollback and its value at equal cost. It is repo-independent in form. It could discard useful partial progress or cost more to check than it saves. Falsifier is no worthwhile resolution gain against both continuation and an equally short ordinary observation handoff. [SWE-Replay](https://arxiv.org/abs/2601.22129) · [FailFast/RestartSmart, Tables 3 and 8](https://arxiv.org/abs/2608.03222)
2. **Represent explicit requirements by the code paths they govern.** Tie each required behavior and preservation constraint to its public entry points and the implementation they share. Use dependency tools and source inspection to separate coverage gaps from locations that converge on the same fix. SpecRover already extracts intent, LocAgent already uses graph localization, and Working Set already models versioned dependencies. The narrower hypothesis is that explicit path coverage yields correct fixes under a matched context budget. This could transfer across repository layouts, although dynamic dispatch and single-path issues limit coverage. Falsifier is improved path coverage without improved held-out resolution or preservation at equal cost. [SpecRover](https://arxiv.org/abs/2408.02232) · [LocAgent](https://aclanthology.org/2025.acl-long.426/) · [Working Set](https://arxiv.org/abs/2608.16630)
3. **Train the editing policy on paired execution feedback.** At identical repository states, pair a behavior-relevant assertion with an infrastructure or irrelevant failure that has the same exit code. Supervise recovery choices by eventual independent correctness. SWE-Gym and newer trajectory training support learning agent behavior. Counterfactual Rollout Replay already learns from forks. The specific research question is whether controlling for the failure source teaches portable feedback use. Its value depends on realistic pairs and transfer across runner formats. Falsifier is better feedback classification without more correct final patches than matched outcome-only training on unseen repos. Same-base LoRA is allowed in principle. Data, compute, serving and transfer remain unverified for this approach. [SWE-Gym](https://proceedings.mlr.press/v267/pan25g.html) · [Teaching Agents to Code Reliably](https://arxiv.org/abs/2610.03984) · [Counterfactual Rollout Replay](https://arxiv.org/abs/2609.33875)

## D. Decision

Prioritize hypothesis 1. It addresses a measured gap between candidate diversity and the cost of redoing a full run. Its effect can be isolated without training or requiring agents to recover requirements absent from the task. Path coverage has a narrower demonstrated failure surface here. Policy training has stronger external results but greater validation cost. The distinctive claim is selective reuse of base-valid observations under a shared deadline. Originality and efficacy are provisional. If most stalled prefixes lack usable observations, or if all arms rarely generate any correct patch, redirect toward representation or the editing policy.

Kaggle permits one common Gemma 4 variant (31B, 12B, E4B or E2B) per submission, optional LoRA, and sandboxed tools. The 12-hour solver budget includes sandbox setup and excludes final validation. The design fits an offline workspace and one model in principle. The documented AgentTool creates a child session and copies parent state. Clean workspace, state isolation and budget accounting require validation before any harness adoption. [Kaggle rules](https://www.kaggle.com/competitions/gemma-4-developer-agent/overview/prizes) · [ADK AgentTool source](https://github.com/google/adk-python/blob/v1.36.1/src/google/adk/tools/agent_tool.py)

## E. Next discriminating research action

When authorized, run **one paired three-arm checkpoint trial** on a locked initial screen of 24 eligible issues from at least three repositories outside prior development, reserves and adapter data, with two seeds per issue. Check independent fail-to-pass and preservation tests and gold-pass/no-op-fail before inspecting model outcomes. Use the exact 31B V2 baseline, shared prefix, fixed halfway checkpoint at a tool boundary and identical remaining solver budget. A continues. B restarts on clean base with a short recency-ranked packet of observed facts. C uses the same clean restart and packet template, with records admitted only if their source bytes match the base or their read-only behavior reproduces there. Match packet length to the shorter eligible packet. Count early finishes identically and keep no-evidence cases in the denominator.

Interleave arms on the same pinned scorer and host. Charge packet checks, reset and setup to the budget and count tasks lost at a global cutoff as unresolved. Measure verified final resolutions, rescued and broken pairs, candidate availability and elapsed solver time. This screen budgets up to about 13 L4x4 host-hours inside the agent loop at V2's 8-minute per-task cap with a shared prefix, plus setup and grading. Judge deployment feasibility against 12 total solver hours on roughly 120 tasks, using measured scheduling overhead. [Kaggle task count](https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/746008)

Advance if C improves correct resolutions against both controls at equal cost. If B and C both beat A and their difference is tightly small, keep the simpler reset explanation. If the paired uncertainty excludes a worthwhile gain (prespecify 5 percentage points) against either control, retire the selective-transfer claim. Wide intervals mean INCONCLUSIVE. A correct draft already available to the same arm before the cutoff, followed by an incorrect final patch, identifies room for better selection or retention. Rare correct candidates across all arms shift attention upstream. This verdict used existing records and public research only.

---

# NOW — case-level research verdict (2026-11-06 MYT)

**RESEARCH-ONLY RESULT: CONTRASTIVE CONTRACT CHECKING DOWNRANKED.** Inspected the **existing** 17-task E4B topology single-root development trace artifact `13150931817` (Actions `41458804862`) and upstream original PR/issue evidence for ten concrete cases. The resulting [case-level audit](docs/research/semantic-repair-gap-audit-2026-11-06.md#completed-case-level-falsification-audit--existing-trajectories-only-2026-11-06) found **no demonstrated repository-recoverable competing-behavior witness (class B)** in reviewed concrete cases. This is **insufficient supporting evidence**, not a scored rejection of the method.

**Distinct, supported sources of failure:** explicit requirement with incomplete/wrong edit (e.g. `fastapi_14448`, `rich_3061`), explicit requirement but failing edit-tool/navigation (`fastapi_14873`), versus externally specified requirement missing from offline task text (`rich_3934`, `rich_4079`, `rich_3105`). One positive control `fastapi_9425` **resolved** with a patch different from upstream reference; gold-text equality is not correctness. **At least five of 17 issue statements are materially underspecified** without their offsite issue/PR detail. Do not generalize prevalence to hidden 31B tasks or imply no repository clue can ever exist.

**Next research direction (not authorized to implement or submit):** audit **specification sufficiency**, **multi-entry-point requirement coverage** and **edit semantic correctness** separately. Reopen class B / contrastive-contract intervention only after actual pre-edit repository evidence discriminates two legitimate interpretations in multiple independent examples. No benchmark runs, Kaggle submissions/status checks, model inference, training, or `submission/` edits in this research turn.

---

# NOW — mechanism-first research audit (2026-11-06 MYT)

**ACTIVE DIRECTION: RESEARCH ONLY.** User explicitly corrected course: do not use Kaggle submissions, repeated status probes, prompt/budget tweaks, or deployment as a surrogate for independent research. **No Kaggle submit, GPU/TPU run, model inference, training, or `submission/` changes in this work.**

**New independent source audit:** [Semantic Repair Gap — 2026-11-06](docs/research/semantic-repair-gap-audit-2026-11-06.md). It triangulates own 17-task E4B development evidence, scored 31B bundles, and the public Budget-Fit author's *different* exposed trace sample. Key limitation: 31B hidden task-level failures are not visible. The 0.08 → 0.17 displayed score is a multi-variable system contrast, **not proof that any component caused the gain**.

**Mechanism question:** on issues where the agent already finds relevant source, can a repository-visible discriminating witness resolve *two plausible competing interpretations of an underspecified behavior* before editing? Distinguish explicit requirements (A), repository-recoverable gaps (B), and genuinely unrecoverable gaps (C). This is a **hypothesis, not a proven new technique**. Plain test-first, graph localization, regression-test selection and more subagents overlap known prior art and cannot be claimed as novel.

**Next research action, before any implementation decision:** inspect a few *already inspected* development examples for actual source-visible A/B/C evidence (reference patches audit-only), then reject or refine this hypothesis. Do not invent case labels, train, re-evaluate models, or repurpose held-out sets. A pure prompt instruction to “verify more” is insufficient and was not selected.

**Previous submission receipt, historical only:** `58045795` was accepted, with status PENDING at last authenticated check 2026-11-06 05:53 UTC; there is no new result in this research audit. No new submission should be driven by that result.

---

# NOW — Kaggle-only audit / official cap5 submission accepted (2026-11-06 12:44 MYT)

**USER-SELECTED METHOD: Audit → official Kaggle code submission → read-only score verification. No self-run model/issue experiments.**

**OFFICIAL ENTRY ACCEPTED:** Kaggle ref **`58045795`**, `SubmissionStatus.PENDING` at authenticated read-back **2026-11-06 04:44:31 UTC**; Public Score and Private Score both empty. [Successful official recovery workflow 42164252901](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42164252901) independently fetched the already-built private CPU-only Kaggle artifact, verified ZIP SHA256 `c9eeb05c2b5c3c9a48689a6afd22ed48334efccd685999539c60567c8ef76551`, matched 3 unchanged original members byte-for-byte and the original `eval_config.yaml` after reversing exactly `max_time_minutes: 8 → 5`. The official submission API returned ref `58045795` and its existence in the authenticated Kaggle submission list was verified. **No score claim is yet possible.** This public V2 derivative is **not original novel research**.

**CONTROL:** exact attributed public Budget-Fit V2 `58019162` COMPLETE Public **0.17**, originally upstream ref `lynnsakurai/.../2` (Apache-2.0), ZIP `a4b10f6b8034fd7fffa144a7ee3fbd8faf9a84503ffb1349d1522ba048b534d3`. Original homegrown 31B `57983156` COMPLETE Public **0.08**. Only comparison `58045795` vs `58019162` is an identical-model/tool/prompt/sampling/budget-other-fields **single-variable cap change**, not a reliable task-level causal proof. Predeclared rationale and interpretive limits in [Research Reset](docs/research/independent-strategy-reset-2026-11-06.md).

**Operational failure diagnosed/resolved without a second builder:** original [submit workflow 42162206978](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42162206978) failed because it polled the metadata ID `kolihhan/gemma4-audit-cap5-42162206978`, while Kaggle automatically slugified the supplied **title** and created `kolihhan/gemma-4-public-v2-cap5-official-audit`. [Read-only inspection 42164107617](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42164107617) identified the real slug. The recovery workflow reused that exact pre-existing COMPLETE private CPU build. No retraining, new GPU notebook, raw competition-data mirror or duplicate Kaggle code submission.

**NEXT:** query **exact submission `58045795`** using authenticated Kaggle CLI until terminal; report score and difference versus 0.17 **without tuning/resubmitting based on Public LB**, and stop after this one candidate. The previously reported 0 GPU quota did not block this official code submission. Do not promote into canonical `submission/` solely from Public score.

---

# NOW — official 31B reference result and inference gate (2026-11-06 12:10 MYT)

**VERIFIED latest:** exact attributed public V2 reproduction Kaggle ref `58019162` is **COMPLETE, Public 0.17, Private empty**. Authenticated [read-only run 42160680339](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42160680339) at 2026-11-06 04:08:31 UTC. Prior scored 31B original baseline `57983156` Public 0.08; +0.09 displayed difference represents a *bundle* of configuration/tool/prompt/budget changes, not original research or a causal ablation. V2 is a **single-root pretrained 31B** and confirms no complex multi-agent topology is needed for this score, not that extra agents could never improve it.

**RESOURCE BLOCKER:** [authenticated `kaggle quota` run 42160889153](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42160889153) at 2026-11-06 04:10:34 UTC: **GPU 0.00h remaining, reset 2026-11-07 00:00 UTC / 08:00 MYT; TPU 19.97h remaining**. No GPU launch was attempted; do not claim a 31B experiment ran or switch hardware silently.

**NEXT:** pause the proposed 5-vs-8 minute diagnostic because the exact V2 system (8 minutes) scored 0.17 and differs from the 5-minute system in several settings. Both are under a global 12-hour/approx.120-task competition limit; a higher per-task cap need not mean higher average runtime. When legit GPU quota permits, first obtain/inspect **one private 31B V2 trajectory on already-inspected development issue(s)**, or reuse any existing uninspected V2 trajectories, to identify whether the bottleneck is patch semantics, tool/context loops, localization, or time. Choose ONE single-variable test only after a concrete failure mechanism is observed. Do not touch reserved cohorts, alter canonical `submission/`, train, LoRA, or submit another copy.

**REPORT:** [Independent Research Reset, updated Nov 6](docs/research/independent-strategy-reset-2026-11-06.md). Research decision is hypothesis review, not an improved original agent.

---

# NOW — Independent Gemma 4 research reset (2026-11-06 MYT)

**ACTIVE RESEARCH DIRECTION: REASSESS THE BOTTLENECK. Do not continue the evidence-before-mutation B/C lane or build more candidate-selection infrastructure by default.** This decision is documented in [Independent Research Reset](docs/research/independent-strategy-reset-2026-11-06.md) and is not a negative performance result for that candidate, which was never evaluated.

**Verified score evidence:** E4B Reliability-v1 Public 0.03 (`57921371`), same-policy 31B Public 0.08 (`57983156`); the attributed external V2 reproduction (`58019162`) was PENDING **at its last authenticated check 2026-11-05**; do not claim it scored without checking a fresh terminal response. The V2 package changes 5→8 minutes, tools, policy and turns; cannot attribute improvement to an individual factor.

**Research diagnosis:** Existing E4B 17-dev traces show poor solution reliability, and five tasks submitted after a nonzero test command without an edit, but they **do not demonstrate verification is the dominant reason 31B failed**. The original evidence-stage and 4+12 protocols stalled at eligibility, not at an actual model/causal test.

**Latest eligibility check, already completed:** [gold CPU run 42066105011](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42066105011), 19/30 reference-patch pass (Rich 13/14; FastAPI 6/16); [no-op CPU run 42067120930](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42067120930), **19/19 no-op fails** among gold-passing tasks; [final readiness 42068107095](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42068107095) SUCCESS as engineering check but **NO_GO_INSUFFICIENT_ELIGIBLE_TASKS** (4 pilot + only 10 exploratory). None measures agent quality.

**Next scientific decision, not another agent build:** distinguish capability/patch semantics, useful work per wall-time, localization, and harness reliability. The report proposes one conditional single-variable 31B **5-vs-8-minute dev diagnostic**, with the same model/config/tasks, global 12-hour budget normalization, and explicit interpretive limits. The external Agentless/SWE-agent research is counterevidence to automatically adding more agents, not a transplant recipe. No new model run is authorized here while private GPU quota blocks startup.

**Scope:** no new training/LoRA, Kaggle submission, model inference, GPU, raw data mirror, repo visibility/security changes, `submission/` edits, or modifications to any existing frozen cohort. Keep prior negative results and original contracts for historical provenance. Do not call research protocols a score improvement.

---

# NOW — discriminating-evidence 4+12 CPU eligibility checkpoint (2026-11-06 MYT)

**Research decision: NO-GO for balanced 4+12 exploratory A/B/C quality runs.** A separate, pre-outcome reduction from 4+24 reserved 4 pilot +12 exploratory IDs plus same-repo ordered replacements. [Exploratory contract](docs/research/discriminating-evidence-v0-exploratory-4plus12-2026-11-06.md), [frozen metadata-only manifest](docs/evaluation/discriminating-evidence-v0-exploratory-selection-2026-11-06.json). Neither contract certifies complete blindness.

**Actual no-model reference gold CPU result:** [Action 42066105011](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42066105011) SUCCESS, 30 screened, **Rich 13/14 gold pass; FastAPI 6/16 gold pass** (10 FastAPI failures report test exit 2, cause not classified). The preregistered balanced pilot+exploratory needs 8 FastAPI, so **NO-GO regardless of no-op outcome**. The candidate pool must not be resampled or strengthened based on outcome. Only safe result flags stored in [docs/evaluation/discriminating-evidence-v0-gold-screen-2026-11-06.json](docs/evaluation/discriminating-evidence-v0-gold-screen-2026-11-06.json).

**Verified static/compliance findings:**
- Deterministic 4+12 selection digest `20bca18b905161123ba0054d058a4f2b963cce6526c67b29e0175a81d17cc343`; original capacity-v0 4+12 remains reserved and untouched.
- [Action 42064561734](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42064561734) scanned 593 preselection Git source revisions and 14 refs, 0 tracked-ID historical mentions. This is NOT complete blind certification.
- [Action 42065388698](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42065388698) validated B/C YAML under fresh official 41-wheel scorer; 31B base, no adapters, frozen budget; both schema PASS. Runtime transfer, information isolation and quality remain UNTESTED; root LlmAgent -> AgentTool(SequentialAgent(evidence->coder)) is a proposal, not proven end-to-end.
- Private CPU no-op screening is linked to the exact passing gold set: [Action 42067120930](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42067120930). The eligibility-only frozen-order readiness check awaits it: [Actions workflow discriminating-evidence-ready-cpu](https://github.com/kolihhan/gemma-4-kaggle/actions/workflows/discriminating-evidence-ready-cpu.yml). These runs cannot reverse the FastAPI shortfall.

**Execution boundary:** no 31B model inference, no GPU use, training, LoRA, competition submission, new public raw Kaggle data mirror or edit to canonical `submission/` in this research lane. Scientific next decision: obtain independently eligible FastAPI tasks under a new prospectively justified data plan, or retire this lane and prioritize the existing separately reserved capacity-v0 E4B-vs-31B causal test when GPU startup is feasible; do not fabricate a small quality win from gold/no-op control results.

---

# NOW — discriminating-evidence research checkpoint (2026-11-05)

**This branch is research-only. Status: NO-GO for model inference, holdout evaluation and Kaggle submission.** No training or LoRA. The inherited capacity-v0 state is preserved below, but its open 31B hypothesis is not execution authorization for this branch.

- New experiment contract: [docs/research/discriminating-evidence-v0-gate-2026-11-05.md](docs/research/discriminating-evidence-v0-gate-2026-11-05.md).
- CPU-only reproducible gate: scripts/discriminating_evidence_preflight.py. Run python -m unittest -v tests.test_discriminating_evidence_preflight.
- **Verified CI:** [run 42060942156](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42060942156), success, 4/4 tests; selected metadata-only 4 pilot + 24 proposed confirmation, **Rich 14 candidates (zero replacements)**, FastAPI 16 candidates (two replacements). Selection fingerprint 13be4ff5205813de3ae869b65a7f7b5a37806589fa633f39dff8fd9dd265a137.
- **NO-GO reason:** an independent 24-task confirmation cannot yet have a robust eligibility replacement buffer; historical provenance and official gold-pass/no-op-fail checks remain undone. Not certified blind. The old capacity-v0 4+12 is still reserved and unmodified.
- The harness supports declarative LlmAgent subagents, output_key and include_contents: none in documentation, but a model-free *actual scorer-wheelhouse compiler check for B/C* and a dynamic evidence-isolation smoke have **NOT** been performed. Prior root-SequentialAgent compaction bug remains a design constraint.
- The scored 31B A baseline remains Kaggle ref 57983156, Public 0.08. At last authenticated query the attributed public Budget-Fit V2 ref 58019162 was PENDING; do not treat its author's reported score as ours.
- **Next allowed decision:** broaden/prove a genuinely uninspected replacement-safe denominator, OR explicitly freeze a smaller exploratory-only experiment with limited claims; then validate B/C against current official wheelhouse. Do not launch GPU, mutate submission/, train, or submit in this research branch.

---

# NOW — 2026-11-04

Updated: 2026-11-05 (new attributed public 31B V2 reference submitted ref 58019162 PENDING)

**Latest read-only scoring check: 2026-11-05 22:06 MYT / 14:06 UTC — submission 58019162 remains PENDING, Public/Private scores empty.** [Actions 42041728306](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42041728306) SUCCESS. No new submission, GPU use, or training. Do not infer an official score from the source author's 0.18.

## Attributed public 31B V2 reproduction officially submitted — 2026-11-05

**LATEST OWN SUBMISSION: Kaggle ref 58019162, PENDING (Public Score not yet available)**. Source: the openly published Apache-2.0 [Budget-Fit notebook by lynnsakurai](https://www.kaggle.com/code/lynnsakurai/gemma-4-budget-fit-agent-w-bounded-rescue), precisely **Version 2**, whose author reports Best Score **0.18 V2**. This is **not yet our result and not an original innovation**. Our prior independent 31B model-only scored ref **57983156 remains 0.08**.

- Actual version-aware public Kaggle API retrieval: [Actions 42007379647](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42007379647). V2 and V3 returned **different ZIP bytes**. Pinned V2 `submission.zip` SHA-256 `a4b10f6b8034fd7fffa144a7ee3fbd8faf9a84503ffb1349d1522ba048b534d3`.
- Contract and byte-identical private builder preflight: [Actions 42007948296](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42007948296), **SUCCESS, 4/4 tests**. Compiler sanity and exact output ZIP SHA pass. No training or GPU.
- **Official submission accepted**: [Actions 42008171687](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42008171687), Kaggle API returned `ref: 58019162`; authenticated submission listing returned `SubmissionStatus.PENDING` at **2026-11-05 10:09:09 UTC**. Description `attributed-public-budgetfit-v2-repro:no-train`. Private CPU builder ref `kolihhan/gemma4-budgetfit-v2-reference-42008171687`, version 1, produced the **same exact scored public V2 ZIP bytes**. Personal Kaggle GPU quota was not consumed; official scorer runs separately.
- No changes to canonical `submission/`, no LoRA, no additional scored submission or local holdout model evaluation. All source attribution, controls, thresholds and next original intervention gate: [public-budgetfit-v2-reproduction-2026-11-05.md](docs/research/public-budgetfit-v2-reproduction-2026-11-05.md).
- **Next**: query exact ref **58019162** read-only until terminal; never assume the author's 0.18 is ours. If it scores, compare our 0.08 with the reproduced bundle carefully; the bundle changes policy, tools, sampling and time budgets together and may be scored in a different host epoch. Do not launch another candidate while this submission is pending.

## Official Kaggle feedback availability probe — 2026-11-05

**Verified submission `57983156`: COMPLETE, Public LB 0.08, Private Score empty.** Authenticated read-only [GitHub Actions 42003198673](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/42003198673) checked the Kaggle competition submission-detail endpoint: the returned human-readable fields were reference, status, public/private score and description. **No per-issue failure labels, hidden tests, patches or grader traces were exposed by this detail response.** The Kaggle CLI episode query returned no recognized structured episode IDs; this endpoint is documented for simulation competitions, while Gemma 4 is a scored patch-resolution prediction competition, so it is not a supported route to hidden issue traces. Do not misinterpret the episode command returning exit 0 as usable episode logs. No new submission, GPU, or data download occurred.

**Interpretation:** Distinguish official hidden-issue aggregate LB from **private Kaggle local diagnostic kernel traces on already-inspected public development issues**. The latter are usable for process research but are not scoring feedback from submission 57983156. If Kaggle later adds a dedicated grader feedback download, verify it afresh. The official submission page is https://www.kaggle.com/competitions/gemma-4-developer-agent/submissions .

## Test-command evidence and repair audit — 2026-11-05

**Verified CPU-only, no-training read of previously completed E4B development traces.** This is a process diagnosis, **not** an explanation derived from 31B hidden task logs. Official 31B Kaggle Public LB remains **0.08** (ref 57983156); no new submission or GPU evaluation was launched.

- [Final read-only GitHub Actions 41987818297](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41987818297): **SUCCESS, 19 unit tests passed**, safe artifact 13397016902 (ZIP SHA-256 f962e9daaac457706786eb38cf42a52b9e832c76858cc065f20240ac8db21175). Outputs contain aggregate counts only; raw commands, issue text, task IDs and patches remain in ephemeral/private run inputs. Archived compact evidence: [trace-test-evidence-v0-2026-11-05.json](docs/evaluation/trace-test-evidence-v0-2026-11-05.json).
- **Reliability-v1 E4B, previously inspected 17 dev tasks:** 11/17 contain a classifier-confirmed test command, 6/17 contain neither a confirmed nor a plausible overlooked test command; 13 test command calls in total, **12 explicitly nonzero** exits, **1 zero** exit, **0 unknown** exits. **0/17** tasks contain a confirmed pre-edit test. **5/17** tasks submitted a patch after a nonzero test command exit with no intervening mutation. **3/17** attempted a subsequent mutation after a nonzero test exit. **One unresolved task's last recognized test command exited 0**, so local test success is not sufficient proof of issue resolution.
- **Predecessor single-root E4B, previously inspected same 17 dev tasks:** 11/17 confirmed a test command, 6/17 without candidate tests; 17 recognized test command calls, **16 nonzero**, 1 zero, no pre-edit test, **9/17** submitted after a nonzero test exit without a mutation, **1/17** attempted mutation after a nonzero exit.
- **Quality check:** The previous permissive analyzer could synthetically miscount echo pytest as testing. A new anchored-executable sensitivity audit excludes this and identifies possible unclassified invocations separately. In actual traces, **zero** legacy unsafe recognitions and **zero** plausible unclassified invocations; **zero** multi-tool trace steps, so no shared-observation ambiguity in these counts. This strengthens the process finding beyond earlier counts of targeted tests only.
- **Interpretation boundary:** A nonzero test *command* exit may reflect environment, import, or collection problems rather than a wrong patch; no per-test output cause classification was performed. These 17 dev tasks are not the hidden 31B scoring set, and one Public LB score does not prove capacity or architecture causality.
- **Next discriminating step:** Do not add more prompt text just to demand testing; the existing soft instruction already says not to submit known-failing patches. Test whether a feasible runtime and validated workflow can enforce or induce a meaningful **verify → interpret failure → repair/retest** transition on a separately untouched, pre-registered denominator. No GPU private Kaggle pilot while quota still rejects startup, and no speculative scored submission.

## After-0.08 diagnosis execution checkpoint — 2026-11-05

**Outcome: Existing E4B trace-mechanics finding survived a stronger parser audit; new private 31B task-level diagnosis is GPU-QUOTA BLOCKED, not attempted.** No training, LoRA, or new scored Kaggle submission was created. The official pretrained 31B Public LB remains **0.08** (submission `57983156`), E4B Reliability-v1 remains **0.03**.

- Verified frozen CPU preregistration/preflight after a minor source-audit regression fix: [Actions 41980757540](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41980757540) **SUCCESS**. The earlier check incorrectly considered the *later-created frozen cohort metadata* a pre-selection exposure. The exemption now validates exact structured fields, supported IDs, counts, no task/patch text, and `certifies_blind=false` before skipping the manifest in a present-tree source scan. Historical Git cutoff audit remains separate and strict; **do not claim fully certified blind**.
- One explicitly authorized private 31B L4×4 startup/array-tool feasibility attempt was rejected on push: [Actions 41980782896](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41980782896), **`BLOCKED_GPU_QUOTA`, GPU run NOT STARTED, zero task evaluations**. Private Kaggle GPU quota remains a blocker even though the official competition submission ran successfully. The startup workflow was restored to **manual-dispatch only**, preventing accidental repeated GPU pushes.
- Instead, audited **existing** (not newly generated) E4B 17-task traces with a conservative opt-in v2 parser recognizing only safe `cd ... && pytest target` or equivalent shell wrappers where the overall exit still reflects the test. [Actions 41981385025](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41981385025) **SUCCESS**; artifact `13393822468`, SHA-256 `dbbb61634f22d241a95607e4386dc31eee29e865ac4ea0fbb9b54df3258098f2`. **Every measured aggregate stayed unchanged** from v1 to v2 in both historical E4B arms.
- Reliability-v1 existing E4B dev: **1/17 resolved**, **14/17 no *classifier-recognized* targeted test**, **0/17 classifier-recognized pre-edit targeted evidence**, **2 observed post-edit targeted failures with no subsequent edit**, **2 submits after recognized failed targeted test**. This strengthens the *process* signal, but complex test commands may still be unrecognized. These are E4B data, **not 31B hidden or fresh local task diagnostics**. Do not pretend the same counts explain individual 31B Public LB failures.
- Evidence snapshot (metadata only): [docs/evaluation/gemma4-31b-postscore-diagnostic-checkpoint-2026-11-05.json](docs/evaluation/gemma4-31b-postscore-diagnostic-checkpoint-2026-11-05.json).
- **Next gate:** No new 31B GPU pilot while quota is exhausted. Preserve frozen 4-task pilot + 12-task independent confirmation untouched. Once a legitimate GPU/private scorer runtime is available, run fixed-policy paired feasibility before testing any architecture change. Do not train or submit merely to bypass quota.

## Untrained 31B scored result — 2026-11-05

**OFFICIAL RESULT: COMPLETE; PUBLIC LB 0.08.** Submission `57983156` (`untrained-31b-v0:same-policy-as-reliability-v1`) was checked read-only via authenticated Kaggle CLI on **2026-11-05 06:18:27 UTC / 14:18:27 MYT**. Returned `SubmissionStatus.COMPLETE`, `publicScore: "0.08"`, `privateScore: ""`. Primary verification: [successful GitHub Actions read-only probe 41979509173](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41979509173), job `127086109897`. No additional submission or training happened during this probe.

- **Control E4B Reliability-v1:** Kaggle ref `57921371`, displayed Public LB **0.03** (previously recorded COMPLETE).
- **Treatment pretrained 31B, no LoRA:** Kaggle ref `57983156`, displayed Public LB **0.08**. Difference **+0.05 points**, approximately **2.67×** the displayed control score. The 31B artifact changes only the root `agent.yaml` model name; prompt, tools, sampling and budgets remain unchanged.
- **Supported claim:** The submitted 31B variant achieved a better official Public score than the earlier E4B submission. **Not supported:** deterministic task-level improvement, causal proof that model capacity alone is responsible, fully equivalent scorer epochs, private-LB generalization, or significance claims. Public LB is a limited, potentially noisy comparison.
- **Decision:** Preserve these scored artifacts and IDs, do not re-submit the same ZIP, do not reintroduce self-training/LoRA. Next meaningful work is analysis of the bottleneck and controlled, uninspected evaluation (frozen 4+12 cohort if resource capacity and provenance allow); no automatic GPU or new leaderboard submissions authorized.

## Untrained Gemma 4 31B official Kaggle submission — 2026-11-04

**OFFICIAL SUBMISSION ACCEPTED; SCORING PENDING.** User explicitly authorized submitting an untrained pretrained Gemma 4 31B variant without running any self-training or LoRA, superseding the prior research-only no-submit hold. This is a **new untrained model-only comparison**, not completion of the frozen local 4+12 capacity experiment.

- **Kaggle submission ref:** `57983156`; accepted via Kaggle API at **2026-11-04 11:38:59.950 UTC**. Read-back from Kaggle CLI shows `SubmissionStatus.PENDING`, Public score blank and Private score blank at ~11:39 UTC.
- **Submission description:** `untrained-31b-v0:same-policy-as-reliability-v1`.
- [GitHub Actions successful workflow 41822538668](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41822538668), job `126548987873`. Kaggle private **CPU-only ZIP builder** kernel `kolihhan/gemma4-untrained-31b-submit-41822538668`, version **1**. No Kaggle notebook GPU was used to build the artifact. **Official scored runtime may use Kaggle GPUs**, as required by competition.
- **ZIP SHA-256:** `42ac2e15e42118b51a2e8835ad5fc5e51cbbdfb472e65e3b8720b38b69738820`. Workflow fetched the private builder's `submission.zip` and verified exact byte-for-byte SHA and every member against deterministic local build before calling `competition_submit_code`.
- Source E4B Reliability-v1 submission ref `57921371` was **COMPLETE, Public LB 0.03**. The new 31B submission changes **only `agent.yaml` root model field** from `gemma-4-e4b-it-qat-w4a16-ct` to `gemma-4-31b-it-qat-w4a16-ct`. All five frozen source files are hash-validated, remaining prompt/tools/sampling/budgets unchanged. **No adapters or self-training**. Static contract tests and Kaggle read-back passed.
- Relevant new sources: `scripts/render_untrained_31b_submission.py`, `tests/test_untrained_31b_submission.py`, `.github/workflows/submit-untrained-31b-once.yml`. First workflow attempt `41822409300` failed in local Python import before Kaggle kernel creation; fixed module entry, then accepted on second workflow run. The submit workflow includes pre-submit dedupe and pending-slot check to prevent duplicate submissions.
- **No scored result yet.** The Public LB may differ due to model class, model/runtime topology, throughput, and host epoch. No model-capacity causal claim or task-level correctness comparison can be made just from future LB delta. Do not create another 31B submission until this ID is terminal and reviewed; do not silently tune the E4B prompt to this outcome.
- Next read-only check: `kaggle competitions submission 57983156` or `kaggle competitions submissions gemma-4-developer-agent -v`. Record terminal public score, submission status, and elapsed time with exact probe timestamp. Keep frozen 4+12 preselected cohort unexposed unless independently authorized for a separate experiment.

## Capacity v0 double-eligibility + frozen 4+12 cohort — 2026-11-04

**Actual CPU-only execution completed (no model, no training, no GPU, no scored Kaggle submission).**

- [Private CPU replacement no-op run 41817822401](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41817822401): **SUCCESS**, 10/10 gold-passing replacements were **no-op-fail**, no no-op-pass or ambiguous records. Source artifact `13315174170`, verified ZIP SHA-256 `14b7d69c2afd5d04075e770cbf70215bded62b9b73156b5cf8aff19c6deb42c1`. Metadata-only [screen](docs/evaluation/capacity-v0-replacement-noop-2026-11-04.json), Rich 4 + FastAPI 6.
- Original frozen 16 had 10 gold-pass + independent no-op-fail. With this replacement pool, six missing positions can be filled by **frozen SHA rank, without task-text or model-result selection**.
- [CPU-only frozen allocation CI 41818760587](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41818760587): **SUCCESS** using actual vetted artifacts; manifest returned **feasibility 4** (Rich 2/FastAPI 2) + disjoint **confirmation 12** (Rich 6/FastAPI 6), six ranked replacements. Artifact `13315922648`, ZIP SHA-256 `5047248721f904fb99c792504d720737811fb842dddb9b6d7e9d5a7c8412bce9`.
- Frozen [cohort metadata](docs/evaluation/capacity-v0-paired-cohort-2026-11-04.json) and deterministic [allocator](scripts/freeze_capacity_paired_v0.py) are now versioned. A contract test verifies the committed cohort matches recomputation and fails closed on provenance/order/count/overlap drift.

**Limitations:** Gold-pass plus no-op-fail is **benchmark eligibility**, not agent task resolution, a leaderboard improvement, or proof of fully uninspected historical data. Git-source pre-exposure scanning found no earlier source mentions in 467 checked revisions, but past private artifacts/unrecorded views remain unverified. The four-task pilot is for model/runtime feasibility, not candidate promotion.

**Current execution boundary:** Follow the submission-first/no-new-training directive. The E4B and 31B comparison is still **NOT run** because of Kaggle weekly GPU quota and the separately paused Colab path. Do not automatically resume GPU runs, LoRA, or leaderboard submissions. The frozen E4B Reliability-v1 submission remains unchanged at recorded Public LB **0.03**.

## Submission-first audit completed — 2026-11-04 (read-only + metadata archive)

**Latest deliverable:** [submission-first research decision](docs/research/submission-first-no-training-decision-2026-11-04.md), based on scored baseline `57879765` and Reliability-v1 `57921371` (both displayed Public **0.03**), inspected development-trace mechanics, prior 12B one-task negative, and publicly scored **no-training** 31B comparators. No new model/GPU/LoRA/leaderboard run occurred.

**Bottleneck priority, not causality:** (1) issue semantics/root-cause/patch correctness; (2) targeted evidence plus repair transitions; (3) E4B capacity/policy; (4) harness/scorer epoch; (5) budget alone. The inspected 17-task trace classifier is conservative and can miss compound-shell verification. A larger model is not guaranteed to improve performance, and the two public 31B systems have different prompts, topologies, budgets and host epochs.

**Recovered prior CPU artifact, no new compute:** [gold-screen Actions 41803516800](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41803516800), artifact `13308702997`, ZIP SHA-256 `944b8acaac1e5f349f81bb0c941348dbc7c5694a57a48ce0ea843023a416711b`. Metadata-only [results](docs/evaluation/capacity-v0-replacement-gold-2026-11-04.json): **10/16 gold-pass**, Rich **4/4**, FastAPI **6/12**. These are **not** clean holdout replacements yet: independent no-op-fail screening is still missing. Do not confuse gold-check pass with model quality.

**Active instruction remains:** pause self-training, pause Colab/31B GPU execution and speculative submissions. The existing preregistered untrained same-policy E4B-vs-31B design is only a **conditional future experiment**, pending GPU feasibility and fully screened/provenance-clean paired tasks. No new candidate has been promoted; frozen `submission/` unchanged.

## Submission-first / no-new-training decision — 2026-11-04

**Current user directive:** Stop self-training/LoRA expansion and prioritize the existing scored Kaggle submissions. Put the optional Colab 31B feasibility notebook and Kaggle 31B GPU gate **on hold**, rather than treating them as required next steps. This is a priority change, not a deletion or a claim that all fine-tuning is intrinsically ineffective.

**Latest verified official per-user result**, from the read-only Kaggle CLI in [Actions 41585360688](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41585360688), 2026-11-04 03:13 UTC:
- Baseline E4B submission `57879765`: `COMPLETE`, displayed Public LB **0.03**.
- Reliability-v1 E4B submission `57921371`: `COMPLETE`, displayed Public LB **0.03**; predicted **0.08 [0.05, 0.12]**; improvement **0.00 displayed**; private scores unavailable.
- This is **no demonstrated leaderboard improvement**, not proof that the submissions solve identical hidden tasks or that a specific mechanism failed.

**Process evidence, nonblind inspected development diagnostic (17 Rich/FastAPI tasks):** **1/17 resolved**, 13 nonempty patches, 0/17 classifier-recognized pre-edit targeted witnesses, 14/17 without recognized targeted test, two observed targeted-test failures with no subsequent repair mutation, zero time/tool-cap exhaustions. These observations support a *hypothesis* of weak issue understanding → testing/repair decisions; they do not prove root-cause causality or characterize the hidden benchmark. See `docs/research/why-reliability-v1-only-003-2026-11-04.md`.

**Priority decision:**
1. **No additional self-trained verifier LoRA, no Colab training, no adaptation of the 9-example adapter into the scored submission.** Prior successful LoRA optimization is engineering evidence only; the tiny training set and lack of independent improvement do not justify promotion.
2. **No speculative new Kaggle submission** or re-submit of the 0.03 bundle. Preserve the frozen Reliability-v1 artifact and current baseline for comparison.
3. Focus on **submission evidence and untrained pretrained-Gemma agent design**: compare publicly reproducible successful submissions, trace evidence before edits, targeted tests and repair-after-fail; favor mechanism-first changes that can be independently checked. A 31B pretrained-model baseline remains an option *only after* a separate feasibility/compute decision; no GPU run is authorized by this status entry.
4. Do not chase 0.03 by patching inspected 17 task IDs. For any eventual new proposal, freeze a clean denominator and prediction before evaluation; do not claim generalization from one Public LB sample.
5. The optional Colab notebook remains committed but **not an active execution task**. Kaggle 31B quota remains blocked; no change to official submission.

**Next research-only step:** rank the actual submission failure hypotheses by evidence, compare public untrained 31B and E4B policies without training, and identify one low-compute, untouched evaluation whose result would change a real decision.

## Colab 31B synthetic-only feasibility alternative — 2026-11-04

**User-requested alternative to Kaggle GPU-quota blockade:** Added `notebooks/capacity_31b_colab_smoke.ipynb` on `exp/capacity-boundary-v0`. **Notebook created and statically validated; NOT executed on any Colab GPU yet.**

- [Static CI 41805674499](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41805674499): PASS; source/cell syntax and no-competition-data contract verified.
- Model checkpoint: `google/gemma-4-31B-it-qat-w4a16-ct`; frozen original synthetic probe code pinned at commit `b13087b402ceef0aa0aa2ce55d1f7aa2c99108c3` and verified with Git blob hash; 32K max context, 0.90 GPU-memory utilization, no LoRA.
- Fail-closed resource gate before installs/downloads: exactly one GPU with >=32 GiB **free** GPU memory, compute capability >=8.0, >=30 GiB free disk. These are screening heuristics and do not guarantee model fit. A 16 GiB Colab T4 fails by design; Colab GPU types/quotas are not guaranteed.
- For qualifying Colab runtimes, install vLLM, attempt one 31B TP=1 startup, then reuse original **plain / scalar tool / array tool synthetic probes**. Save only structured scalar metrics locally; do not mirror raw data or auto-upload logs.
- **Scientific boundary:** Colab uses a separate GPU topology (TP=1) and installed vLLM, not the four-L4 Kaggle official scorer wheelhouse. A successful Colab probe is merely supplementary model/parser feasibility evidence. It does not unblock the Kaggle quota, validate official scorer equivalence, score tasks, or authorize any 4+12 model A/B or leaderboard submission.
- A Colab account owner must attach/select a capable GPU and execute the notebook. No integrated Colab execution was available from this GitHub-only workflow. Future results must be recorded with GPU identity, versions, error classification, and whether they were reproduced in the official Kaggle environment.

**Next action:** User runs the notebook in Colab on a compatible GPU and shares the metrics JSON. On failure, distinguish insufficient hardware / installation / model initialization / parser errors. Keep Kaggle 31B blocked until an official compatible kernel can actually start.

## Capacity v0 replacement checkpoint — 2026-11-04 (CPU-only)

**Verified original eligibility (no model):** original 16 metadata-preselected IDs yielded **10/16 gold-pass** and, for those exact ten gold-pass IDs, **10/10 no-op-fail**. The per-ID no-op record was downloaded and checked against the original private [run 41786342489](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41786342489), artifact `13300818683`, then retained as metadata-only `docs/evaluation/capacity-v0-noop-screen-2026-11-04.json`. No raw patches, issue text, or hidden tests were committed.

**Frozen original gaps:** pilot Rich 0 / FastAPI 1; confirmation Rich 1 / FastAPI 4. Six replacements are needed in total (**Rich 1 + FastAPI 5**), all still subject to independent gold-pass AND no-op-fail screening.

**New deterministic metadata-only replacement gate:**
- `scripts/build_capacity_replacements_v0.py` preserves preregistered selector SHA `4abe73d79afcabd64795e7f2eedde5682732a85290f07a09e3f8a181594fd593`, excludes all original 16 and the original known-exposure corpus, and ranks additional candidates using the frozen source SHA namespace. No old holdout, training, or manually seen tasks are intentionally reassigned.
- [CPU Actions 41803046378](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41803046378): **11/11 tests PASS**; queue **Rich 18 + FastAPI 28**; preselection tracked Git-source history scan **467 revisions**, **0 mentions** among first **16** queued prospective screening candidates. Historical Git source cleanliness **does not certify blind status** across previous private artifacts or unrecorded inspections.
- The first screening cohort was frozen as **4 Rich + 12 FastAPI** (the exact first 16 Git-source-audited replacement-queue IDs), before seeing replacement task outcomes.
- [Private Kaggle CPU gold-control Actions 41803516800](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41803516800) was launched using a fail-closed Kaggle push guard and a metadata-only artifact policy. **Gold outcomes were not yet available at this checkpoint.** It has no GPU, model inference, or leaderboard submission.

**Next gate:** inspect the per-ID safe gold artifact on completion, run private CPU no-op verification **only on gold-pass replacement IDs**, then fill the missing Rich/FastAPI slots strictly in original ranked order. If the preregistered 16 replacement screens cannot fill six gaps, screen the next unexposed queue prefix without selecting on model results, or explicitly reduce/retire the planned comparison if clean source candidates run out. Do not pronounce blind certification from Git-source audit alone.

**31B GPU remains independently BLOCKED by Kaggle weekly quota**, not failed model inference. No new 31B run, no new LB score, and the frozen Reliability-v1 candidate remains unchanged. Verifier-LoRA's adapter artifact is a separate older research branch, not promoted.

## Latest PIC decision — 31B startup BLOCKED BY GPU QUOTA

**Verified external blocker:** GitHub Actions [41794811345](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41794811345), job 126456289520, attempted to push a *private synthetic-only* 31B L4x4 startup kernel. Kaggle printed **"Kernel push error: Maximum weekly GPU quota of 30.00 hours reached."** CLI exit code was nevertheless 0. The subsequent HTTP 404 was for a kernel that was never created. Read-only status probe [41795018386](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41795018386) confirmed no notebook/result. **NO model weights loaded, no GPU inference, no candidate issues tested and no new leaderboard submission.**

**Safeguards now implemented:** The 31B GPU workflow is **manual-only** (no auto-push on source commits); a new CLI push checker rejects zero-exit quota errors and requires an explicit successful push confirmation. CPU GitHub Action [41795366875](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41795366875) reports **9/9 tests PASS**, including the push-failure guard. Historical preselection Git-source audit scans **467 revisions** and found **0 pre-existing document/source mentions among the 16 candidate IDs**; this is stronger than checking only the current tree, but does *not* certify full blind status across past private artifacts/unrecorded views.

**Decision:** Do not launch or re-run 31B GPU until account quota availability is verified. Startup/tool-call behavior remains UNKNOWN (not failed). Do not fill all 16 tasks merely to keep busy if model feasibility is still blocked; the 10 gold-pass/no-op-fail tasks remain frozen and unused by a model. An E4B-only evidence/repair lane is a potential separate pivot, not authorized as an automatic fallback by the quota error.

Canonical report: docs/research/capacity-v0-31b-gpu-quota-blocker-2026-11-04.md

## North star

Build a competitive Gemma 4 software-engineering agent by learning which mechanisms transfer to Kaggle hidden evaluation, not by patching inspected tasks or chasing Public LB noise.

Research must remain anti-overfit, resource-aware, mechanism-first, and willing to reopen model/training/topology classes when evidence changes. Read `RESEARCH_DOCTRINE.md` before preserving or rejecting a major method class.

## Terminal scoring / active decision

**Reliability-v1 is terminal; its preregistered Public-LB prediction failed.**

Fresh read-only probe on **2026-11-04 03:13 UTC / 11:13 MYT**:
- baseline ref `57879765`: **COMPLETE**, Public LB **0.03**;
- Reliability-v1 ref `57921371`: **COMPLETE**, Public LB **0.03**, private score not available;
- frozen prediction: **0.08 [0.05, 0.12]**; observed result **0.03**, **-0.05** vs point, **0.02** below lower bound;
- observed displayed Public-LB gain over baseline: **0.00**.

Source: GitHub Actions run `41585360688`, latest job `126363546071`. Canonical calibration: `docs/evaluation/reliability-v1-terminal-calibration-2026-11-04.md`.

**Activated predeclared branch: Public LB < 0.05.** Do **not** automatically implement evidence-before-mutation-v0. Open an architecture/model-policy capacity discriminating lane, while explicitly preserving uncertainty about *which* mechanism failed.

Frozen Reliability-v1 submission remains untouched. No duplicate submission, no rerun of inspected 17-task denominator, and no task-specific prompt tuning.

## Root-cause investigation after the 0.03 miss

Research audit: `docs/research/why-reliability-v1-only-003-2026-11-04.md`.

**First-party evidence:** 1/17 resolved, 13/17 non-empty patches, 0/17 classifier-recognized pre-edit targeted witnesses, 14/17 without recognized targeted tests, 0 repairs after the two recognized failed targeted checks. Existing development result JSON shows **0/17 five-minute time-cap hits** (max ~201 sec) and **0/17 tool-cap exhaustions** (max 30 of 32).

**Main diagnostic hypothesis:** issue semantics/evidence → root cause → correct edit/repair is unreliable. Reliability-v1 reduced broad tests (14→10) without increasing recognized targeted tests (3→3), suggesting a possible verification-starvation trade-off rather than a knowledge gain.

**Not established:** hidden scorer task-level failure classes, same solved IDs across baseline/v1, model-capacity ceiling, partial hidden runtime/harness failures. The 17 development tasks are Rich/FastAPI-only and were inspected. Gold-pass/no-op-fail selection weakens blanket broken-harness explanations for that 17, not for hidden private-repo tasks.

**Decision correction:** the <0.05 pivot opens capacity as a *testable alternative*, not as the proven root cause. Before an expensive comparison, run a cheap scorer/model-source feasibility gate and freeze a genuinely untouched paired denominator. Do not assume that 5 minutes/32 calls caused the local 1/17 (neither limit was reached).

## Public leaderboard and open-method recon (2026-11-04)

Canonical evidence: `docs/research/public-leaderboard-vs-open-methods-2026-11-04.md`.

- Latest third-party CLIST Public LB snapshot: leader **0.29**, several teams **0.24**; **leader's method not publicly established**. Do not assign an unknown top agent a model or architecture.
- Disclosed scored stronger systems: **31B no-LoRA two-role v19 0.17**, with tracing/localization and thinking off; **31B single-root Budget-Fit 0.18**, using eight-minute cap, 28 tools and 4096 thinking budget. Neither proves multi-agent or thinking mode is universally superior.
- Factorial self-hosted study (3 model sizes × 2 scaffolds × 5 seeds × 104 public tasks): richer E4B scaffold improved local resolved rate **10.0% → 15.4%** while 12B min **25.2%** exceeded E4B max. The study used GGUF/llama.cpp and a repaired local verifier: **not official hidden LB**, not a directly controlled comparison with our E4B QAT.
- Caveat: identical public bundles have been observed scoring differently by up to 0.05 in hosted experiments; do not read a causal mechanism from single LB points.
- Our E4B 0.03 is lower than these 31B open systems, but the difference bundles model class, policy, budgets, harness epoch and hidden task draws. Stronger evidence for model capacity as a **candidate**, not a proven root cause.
- Official competition provides a **$10,000 E2B/E4B small-model prize**, but current filtered small-model standings have not been independently verified.

**Decision:** Preserve the planned capacity probe as a controlled falsification test; explicitly keep test-aware evidence/scaffold design as a competing hypothesis. Do not copy public leader configs without determining what mechanism is actually responsible.

## Capacity-v0 execution checkpoint — 2026-11-04

**Model-only CPU preflight: VERIFIED GREEN.** Run [41782383957](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41782383957), job 126416680873:
- 7/7 integrity/selection/exposure-scanning tests passed;
- old frozen E4B submission hash contract passed;
- E4B vs 31B exact file-set check passed; only one agent model declaration differs;
- Kaggle official model instance metadata found both E4B and 31B;
- 41 current official scorer wheels fetched;
- both model declarations passed the same scorer's submission schema checks;
- 149 repo research/source files scanned for the 16 candidates, zero unexpected mentions;
- candidate feasibility n=4 (2 Rich, 2 FastAPI); confirmation reserve n=12 (6 per repo);
- frozen selector SHA256: 4abe73d79afcabd64795e7f2eedde5682732a85290f07a09e3f8a181594fd593.

Source code/contract:
- scripts/capacity_preflight_v0.py; tests/test_capacity_preflight_v0.py;
- .github/workflows/capacity-preflight-v0.yml;
- docs/evaluation/capacity-boundary-v0-preregistration-2026-11-04.md.

**Gold eligibility:** 10/16 passed; **No-op eligibility:** 10/10 gold-passing candidates failed no-op verification, giving **10 doubly eligible tasks**. Private CPU actions: [gold 41782992381](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41782992381), [no-op 41786342489](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41786342489).

**Remaining gates before any expensive model run:** gold-pass + no-op-fail eligibility, prior-run/human exposure provenance limitations, and 31B runtime/startup resource feasibility on L4x4. Do not call the 16 candidates certified independent blind; the source-text audit cannot inspect private historical notebook artifacts or unrecorded human views. Do not alter frozen Reliability-v1 or publish competition data.

## Capacity eligibility update — 2026-11-04 14:28 MYT

**Gold reference screen completed successfully.** Private Kaggle CPU action [41782992381](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41782992381), metadata-only artifact `13299564669` (SHA256 `12a7ff7a377258eee08dd639ebd60726bdeb260649892c451c1d47d81e9e2f`):
- 16 preselected metadata IDs screened;
- **10/16 gold-pass**, 6 failed the official reference-patch verification;
- feasibility cohort 3/4 gold-pass; original confirmation reserve 7/12 gold-pass;
- Rich: 7 gold-pass out of 8, FastAPI: 3 gold-pass out of 8;
- source metadata preserved at `docs/evaluation/capacity-v0-gold-screen-2026-11-04.json`; contains no raw issue statements or patch bytes.

**No-op control now COMPLETE.** Private Kaggle CPU action [41786342489](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41786342489), job `126429235397`, completed successfully. The safe output reports `CAPACITY_NOOP_SCREENED=10` and `CAPACITY_NOOP_FAIL_COUNT=10`, artifact `13300818683`. All ten gold-passing tasks require a non-empty solution under the checked official no-op verifier. No model inference or GPU was used.

**Decision:** Continue gold-pass AND no-op-fail filtering, then replenish failed candidates using preregistered within-repo SHA-ranked metadata order before inspecting any A/B model results. Do not call the 16 raw candidates clean. Do not launch E4B/31B GPU while eligibility is incomplete. Do not change the frozen Reliability-v1 submission, sampler, prompts or budgets.

## PIC handoff — eligibility gate closed, replacements needed (2026-11-04)

**Verified:** CPU model/schema preflight GREEN (7/7); reference-patch gold pass 10/16; no-op fail 10/10 of gold pass; **10/16 total doubly eligible**. Gold and no-op remain separate controls. Private job `126429235397` and artifact `13300818683` establish the no-op gate; confirm exact per-task metadata from that artifact before finalizing a replacement manifest.

**Original frozen shape:** feasibility 4 = Rich 2 + FastAPI 2, currently gold/no-op eligible Rich 2 + FastAPI 1 (**missing FastAPI 1**). Confirmation 12 = Rich 6 + FastAPI 6, currently eligible Rich 5 + FastAPI 2 (**missing Rich 1 + FastAPI 4**). Overall **six replacement tasks needed: one Rich, five FastAPI**, from *new uninspected IDs* and fixed within-repo SHA ordering.

**PIC mandatory next steps:**
1. Verify the safe no-op artifact at the per-ID level and commit a vetted derived metadata-only eligibility record (no raw traces/test material).
2. Formally construct the next within-repo SHA-ranked replacement queue from the pre-existing 90-task source metadata; exclude the initial 16, previous training/holdout, known exposures and any ambiguous provenance. Freeze replacement order *before seeing model results*.
3. Run just enough private Kaggle CPU gold-pass AND no-op-fail screening to fill the **1 Rich + 5 FastAPI gaps**; stop early if provenance or eligible pool fails. Keep pilot and confirmation strata separate. If no clean replacements exist, **reduce/retire the preregistered comparison explicitly rather than silently changing the denominator**.
4. After a frozen eligible denominator, audit 31B vLLM startup on Kaggle L4×4 and command/tool/parser behavior, then run the *same-policy* four-task paired **E4B/31B feasibility** test only if justified by costs. That four-task pilot cannot promote 31B or establish a statistical win.
5. If feasible, use the untouched independent 12-task confirmation. Record resolved, unique solves, time, tool calls, empty patch rate, verifier exits and cost; follow the pre-registered threshold and pivot on genuine evidence.

**Not yet done:** clean replacement cohorts, GPU startup, paired model inference, any new competition LB score. **No submitted reliability-v1 artifacts changed.**

## Frozen control / development evidence

Reliability-v1 is the current frozen E4B single-root control.

Canonical development diagnostic:
- run `41485671952`;
- job `125417231948`;
- 17 / 17 completed;
- **1 / 17 resolved**;
- 13 non-empty patches, 4 empty;
- mean tool calls `10.41`;
- mean duration `89.21 s`;
- call-cap exhaustions `0`;
- 12 / 12 non-empty unresolved patches had non-zero evaluator verification exit.

Relative to the earlier single-root run on the same inspected denominator:
- resolved stayed **1 -> 1**;
- total evaluator runtime fell about **12%**;
- mean non-empty patch size fell about **20%**.

Interpretation: Reliability-v1 became more restrained/efficient, not demonstrably more capable on the inspected development set.

## Trace-mechanics audit

Canonical audit:
- run `41590900152`;
- job `125767140355`;
- artifact `13209917848`;
- no new model inference or Kaggle task execution;
- analyzer tests **8/8 PASS**;
- safe-output gate PASS.

Same-classifier earlier single-root -> Reliability-v1:
- resolved: `1 -> 1`;
- targeted behavioral evidence before first mutation: `0 -> 0` tasks;
- targeted-test calls: `3 -> 3`;
- tasks with no targeted test: `15 -> 14`;
- broad-test calls: `14 -> 10`;
- localization-tool calls: `0 -> 4`;
- mutations: `40 -> 39`;
- failed targeted check followed by repair mutation: `0 -> 0`;
- submit after latest classifier-recognized targeted failure: `1 -> 2`.

The analyzer is conservative; use these values for same-classifier mechanism comparison, not as exhaustive semantic labels.

## Current global hypotheses

### H-lifecycle — evidence before mutation

Status: **OPEN, but no longer the automatic first candidate after the <0.05 pivot trigger.**

Current mechanism:

> Obtain the cheapest discriminating behavioral witness before mutation when a concrete contract exists, then reuse that witness after editing where feasible.

Why it remains plausible:
- both inspected single-root variants show 0/17 classifier-recognized targeted pre-edit behavioral evidence;
- soft repair/submission lifecycle instructions were not reliably followed;
- simply reducing calls/runtime did not improve solved count.

Canonical design:
- `docs/design/evidence-before-mutation-v0-2026-11-03.md`

Implementation plan:
- `docs/superpowers/plans/2026-11-03-evidence-before-mutation-v0.md`

### H-capacity — E4B/model-policy ceiling

Status: **SELECTED for next discriminating research lane; not proven as the dominant bottleneck.**

External evidence includes a materially stronger public 31B-era no-LoRA system, but that comparison is confounded by model size, topology, prompts, budgets, and development history.

Important recovered repository evidence:
- old E4B/12B same-lineage `rich_3278` smokes already exist;
- E4B produced a wrong patch inside five minutes;
- 12B default-thinking timed out with 0 patch;
- 12B thinking-budget-1024 also timed out with 0 patch despite more tool activity.

Canonical note:
- `docs/research/recovered-12b-capacity-evidence-2026-11-03.md`

Therefore:
- do **not** repeat the old naive 12B-first experiment;
- capacity does **not** mean `swap E4B -> 12B`;
- if the capacity trigger fires, the next experiment must add new information, e.g. a preregistered 31B same-policy probe or a frozen strong-public model-policy reproduction.

Corrected fallback design:
- `docs/design/model-capacity-probe-v0-2026-11-03.md`

### H-training — trajectory/policy distillation or SFT

Status: **REOPENED for feasibility, not causally prioritized yet.**

Do not confuse this with historical verifier-LoRA v0. Verifier-LoRA remains **NOT TESTED**, not falsified. Broader policy/trajectory training becomes higher priority only if untouched evidence shows the lifecycle is correctly instantiated but E4B still systematically reasons/edits incorrectly, or a capacity probe shows a clear model-policy ceiling.

## Evidence-before-mutation causal guard

A simple comparison of:
- A: frozen Reliability-v1 single-root;
- C: two-role evidence -> coder;

is not enough to prove evidence transfer caused any gain because topology, independent model invocation, context partition, and latency also change.

Pre-register a conditional third arm:
- **A** — frozen Reliability-v1 incumbent;
- **B** — topology-matched null handoff: evidence root still runs, but coder is prevented from receiving its evidence/history;
- **C** — same topology, coder receives evidence/history.

Resource-aware rule:
1. freeze A/B/C plus untouched denominator before trace inspection;
2. run A and C first;
3. if C does not beat A by the practical promotion rule, stop and do not pay for B;
4. only if C > A, run already-frozen B before inspecting task-level traces;
5. strong evidence-mechanism claim requires C to beat B meaningfully as well as A.

Canonical review:
- `docs/research/evidence-before-mutation-v0-causal-identifiability-review-2026-11-03.md`.

## Current ADK / scorer runtime blocker

A cheap source probe against the current official scorer wheelhouse verified:
- `google_adk-1.36.1`;
- `adk_submission-0.2.13`;
- `swegemma-0.2.11`.

The historical compaction path still raises when the root agent is not an `LlmAgent` and no explicit summarizer model exists.

Therefore **do not use a root `SequentialAgent`** for evidence-v0 under the current wheelhouse.

Current safe provisional topology:

`root evidence LlmAgent -> coder LlmAgent`

Properties:
- root has no `edit_file`, `write_file`, or `submit_patch`;
- coder is the only mutation/submission role;
- zero-diff-before-coder remains mandatory because `run_command` can mutate;
- transfer is model-controlled, so successful transfer/compliance must be measured rather than assumed.

Canonical probe:
- `docs/research/current-compaction-probe-2026-11-03.md`;
- workflow run `41624178623`;
- job `125877217844`.

## Predeclared score fork — terminal branch now activated

### Public LB < 0.05 — TRIGGERED (observed 0.03)

The live candidate underperformed the preregistered interval.

Do **not** automatically implement evidence-v0 first. Reopen the architecture checkpoint and choose the smallest new experiment that separates lifecycle/policy limitations from model-policy capacity. Use the recovered 12B evidence; do not repeat it.

### Public LB 0.05–0.12

The live result is consistent with preregistration.

Evidence-before-mutation remains the first causal mechanism test. H-capacity stays explicitly open and second-line. If evidence-v0 forms high-quality pre-edit evidence but correctness does not improve, pivot rather than stacking more evidence prompts.

### Public LB > 0.12

Lifecycle/policy changes transferred better than expected.

Proceed with the untouched evidence-v0 causal test, but do not treat one LB score as proof of mechanism. Keep the A/B/C causal guard.

## Resource policy

- Existing artifact answers a question -> reuse it.
- Cheap GitHub Actions / source probes / static validation -> use freely in this public repo.
- Kaggle GPU/full task evaluations -> only when they can falsify a named hypothesis or change a decision.
- No duplicate active submissions/diagnostics.
- No compute to obtain another sample from an already-inspected denominator.
- No verifier-LoRA catch-up run merely for bookkeeping.
- No repeated 12B `rich_3278` smoke.

## Next action — revised after quota rejection

1. **Hard stop on GPU:** Do not push the 31B model again while Kaggle's weekly 30-hour quota is exhausted. The exact reset time is UNKNOWN. Future check must verify account quota and inspect active workloads before any manual dispatch.
2. **When quota is available, one explicit manual startup smoke:** use the now fail-closed workflow .github/workflows/capacity-31b-startup-smoke-v0.yml; record start, plain request, scalar tool, array-shaped tool, and total cost. This is zero-task feasibility only, not a model-capacity measurement.
3. **Before issue evaluation:** keep original selection immutable, verify historical exposure beyond Git where feasible, and replenish eligibility by preregistered within-repo SHA order (1 Rich, 5 FastAPI missing) if 31B startup actually works. The gold/no-op current result is 10/16 eligible; no task text/ref patches shared.
4. **If startup works and resources justify it:** execute the pre-registered four-task paired E4B/31B pilot; only then consider the 12-task independent confirmation. No changes to Reliability-v1, no per-task hyperparameter tuning, no leaderboard claims from pilot.
5. **If quota remains unavailable:** hold the capacity experiment; evaluate separately whether the 0.03 failure warrants a cheap, independent E4B evidence/test/repair mechanism hypothesis. Do not silently call a model-class limitation proven.

No new model inference or Public LB score has been produced by this checkpoint.
