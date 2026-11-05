# Discriminating Evidence v0 — executable research gate (2026-11-05)

**Status: NO-GO for 31B inference, held-out A/B/C and Kaggle submission.** Static research preflight only. No training or LoRA permitted. This document is a new *mechanism-specific* hypothesis, not a rename of the earlier evidence-before-mutation architecture or a scored experiment.

## 0. Source of truth and preserved controls

Research branch: research/discriminating-evidence-v0, forked from exp/capacity-boundary-v0 at c669984cb196a639ccb5b15c54e49847d8137c0c.

Frozen practical baseline A: the exact no-training 31B scored artifact, Kaggle submission **57983156**, Public score **0.08**, source ZIP SHA-256 **42ac2e15e42118b51a2e8835ad5fc5e51cbbdfb472e65e3b8720b38b69738820**. It is produced by scripts/render_untrained_31b_submission.py from frozen Reliability-v1 five-file payload with only the model declaration substituted. Do not alter/recreate its byte contract. Do not use its Public LB as the primary experimental outcome.

Current reference settings: 31B QAT pretrained model, temperature 0.2, top_p 0.95, max_output_tokens 16384, thinking_budget 4096, max_time_minutes 5, max_tool_calls 32, max_turns 64, timeout_seconds 300. All arms must share total budgets (not per-stage multiplied budgets), tool environment, scorer/wheelhouse version, hardware, seed policy and problem statements. No adapters.

**Reserved untouched-by-model capacity-v0 denominator:** docs/evaluation/capacity-v0-paired-cohort-2026-11-04.json, 4 feasibility + 12 confirmation. NEVER reuse those sixteen IDs for this experiment; the metadata itself cautions that full historical blind certification has not been established.

Source evidence:
- docs/evaluation/trace-test-evidence-v0-2026-11-05.json: E4B historical development traces, 0/17 recognised pre-edit test, 5/17 submit-after-nonzero-test-without-mutation; not the 31B hidden distribution.
- docs/research/current-compaction-probe-2026-11-03.md: root SequentialAgent is unsafe with current ADK compaction. Use root LlmAgent.
- docs/research/evidence-before-mutation-v0-causal-identifiability-review-2026-11-03.md: a topology-matched evidence-withheld control is necessary for causal interpretation.
- HARNESS_README.md §§2.3 and 7.2: LlmAgent sub_agents, output_key, include_contents: none, fixed compaction; current scorer support must still be rechecked against a fresh wheelhouse.
- Kaggle Staff model announcement: https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/748287, overrides the stale old 31B-only statement in bundled HARNESS_README.

## 1. Precise scientific question

**Does passing genuinely discriminating pre-edit behavioural evidence to the same 31B coder cause additional correct repairs, beyond extra model work/topology alone, under the SAME total agent time/tool-call limits?**

Not tested here: whether an agent simply runs more tests; whether an increased budget improves performance; whether a public reference ZIP outperforms our score; whether adding a second agent generally helps.

The intervention does not deserve an originality claim merely for using tests, two roles, or an evidence handoff. The interesting falsifiable mechanism is: the evidence stage chooses between *competing causal hypotheses* through an observation whose predictions differ, and the coder updates its patch choice in response.

## 2. Frozen three-arm design (not implemented or run)

**A — exact practical baseline:** no-training 31B 57983156, identical ZIP, single-root coder.

**B — diagnostic-stage null handoff:** root evidence LlmAgent gathers exactly the same evidence as C, then delegates to an editing coder LlmAgent. The coder has include_contents: none and receives the original problem_description but **not** the diagnostic packet; no session-state interpolation or history may inadvertently leak the packet. A fixed non-informative placeholder may be used if required to preserve identical prompt layout.

**C — diagnostic-stage evidence handoff:** identical B topology, evidence-stage model/tools/budget/prompt and coder; coder also receives the evidence packet using a frozen output_key state variable. Both B and C must use include_contents: none to prevent uncontrolled conversation-history differences. The only intended informational difference is the packet body/absence. Test for implicit access through session state, shared files and ADK transfer events.

Evidence packet contract, max 350 words:
1. Two competing root-cause hypotheses, neither presented as established.
2. Specific code/test location supporting each.
3. One minimal *discriminating* executable command or assertion; say explicitly when unavailable.
4. The observed result, exit status, and which hypothesis it supports/weakens.
5. Remaining uncertainty and what would falsify the current leading explanation.
No gold/reference patch, hidden tests, task ID special cases, post-hoc hints or proposed final patch.

Root evidence stage may use read_file, run_command and inexpensive search tools; remove edit_file, write_file and submit_patch. This is NOT hard read-only isolation because run_command can modify the working tree. Require trace-audited zero working-tree diff before coder starts and reject any pre-coder mutation. Temporary scripts must not enter the submitted patch. Do not rely on unsupported Python callbacks or custom ToolRegistry wrappers. The root must demonstrably hand off to the coder and never resume unbounded analysis after a child returns.

**Critical runtime risk:** the extra 31B stage consumes the same 5 minutes and 32 tool calls; the coder may be starved even if B/C are schema-valid. CPU/static validation alone cannot prove a usable runtime.

## 3. Frozen metadata-only selection algorithm

The selector is scripts/discriminating_evidence_preflight.py. It reads *only existing metadata*, never tasks.jsonl, issue text, reference patches, stored raw traces, screenshots or hidden verifier logs.

It excludes all known records in the verifier split, training harvest, existing blind reservation, topology diagnostic, existing capacity-v0 4+12, *all* capacity gold/no-op screen inputs including rejected/replacement cases, and the original public-corpus diagnostic sample. Per repo, rank remaining IDs using SHA-256 of the constant namespace plus ID.

Provisional plan: pilot **2 Rich + 2 FastAPI**; confirmation **12 Rich + 12 FastAPI**; use remaining ranked candidates only as eligibility replacements, applied *before model outputs exist*. This denominator is not promoted until complete history/artifact exposure audit and official CPU gold-pass/no-op-fail checks. No replacements based on text, difficulty, reference patch, or model outcome.

**CPU metadata result as of 2026-11-05:** 14 Rich + 16 FastAPI candidates remain, after all known exclusions. The proposed 4+24 consumes all fourteen Rich candidates and fourteen FastAPI candidates, leaving **zero Rich and two FastAPI replacements**. Historical source exposure and eligibility failure rates are unknown. A precautionary minimum four replacements per repo was fixed here based on documented gold-control attrition (10/16 in the earlier initial and replacement screens), not based on future model results.

**Current gate: NO_GO_INADEQUATE_REPLACEMENT_BUFFER.** This does not assert that any selected task is ineligible; it means the intended 24-confirmation design has no robust backup pool. It also does not certify that any of the thirty metadata candidates are historically blind.

For a lower-cost *exploratory* follow-up, a smaller denominator may be preregistered, e.g. 4 pilot + 12 confirmation with explicitly weak inferential power. This must be a NEW frozen contract, not an on-the-fly change after seeing outcomes. No competition-useful performance claim is possible from such a small set without independent replication.

## 4. Pre-registered outcome and budget gates — only applicable after independent eligibility

- Gate 0, **CPU-only now**: source hashes; no overlap with any prior reserved/seen lists; stable deterministic selection; adequate replacements; exact baseline ZIP hash; official current schema support; null-handoff information-isolation design. No model run.
- Gate 1, **future 4-task feasibility**: each arm starts and terminates, root transfer is observed, B coder cannot read the evidence, C coder can, no pre-coder mutation, no parser/compaction errors. No success claim from pilot solves.
- Gate 2, **future 24-task independent paired outcome**: freeze A/B/C and all IDs before any model trace inspection. Run A/C together without peeking at one arm before finishing the other. Execute the preregistered B on the same denominator if C clears the practical A-vs-C gate. No post-hoc selection or task replacement.
- Gate 3, **future decision only**: proposed go-to-replication bar: C has >=4 net additional resolved tasks over A and >=3 net over B, <=1 B-only solve relative to C, no meaningful loss of completed task coverage, <=10% extra total agent execution time, and no 12-hour global competition budget overrun. These are design thresholds, NOT statistical confidence claims; compute paired uncertainty and independent replication before any promotion or Kaggle submission.

Measure paired issue resolution (official gold/no-op-eligible verification), A-only/B-only/C-only successes, task-level timed-out vs empty vs invalid patch, exact test exit/error class, time and tokens to first edit, total wall time, tool calls, diagnostic-witness validity, explicit coder use of that witness, repair-after-nonzero-test frequency and end-to-end cost per resolution.

Relevance of a witness cannot be scored merely by presence of a pytest command: a zero-exit unrelated test does not validate the patch. Witness relevance and actual coder use must be audited on predeclared annotation rules, blind to arm identity and final resolved outcome until labels are frozen.

## 5. Falsifiers and interpretation

- C <= A: two-stage evidence path does not meet the practical hurdle; do not pay for B.
- C > A but C ~= B: extra stage/context separation is a competing explanation; **do not claim evidence caused the gain**.
- C > A and C > B, with valid used witnesses: evidence transfer is supported on this denominator, not necessarily on hidden repositories.
- B > C: diagnostic packet may be misleading/harmful.
- Better witness formation but no better correction: abandon the evidence-information hypothesis and examine model reasoning, patch generation, alternative-patch search and weak-test selection.
- Any strong cost/timeout regression: stop under the fixed competition-wide budget.

Existing 17 E4B development traces can be used only to debug the instrumentation, never to select or promote C. No public LB sweeps.

## 6. Immediate execution boundary / next gate

**DONE (source-level):** read actual repo and harness instructions, inspect frozen model-only 31B renderer, inspect historical masks and capacity reservations, compute deterministic metadata-only candidate counts, make a CPU-only source gate.

**NOT DONE:** live official schema compilation of B/C, actual isolation smoke, eligibility and full historical audit for selected candidate IDs, any 31B runtime, independent A/B/C quality inference.

**NO-GO until:** (a) sufficient untouched replacement-safe data exists or a separately agreed exploratory contract is frozen, (b) historical/artifact exposures and gold/no-op eligibility clear, (c) current scorer supports verified B/C isolation without compaction failure, and (d) legitimate GPU resource is available.

Do not mutate submission/, any prior holdout manifests, prior experiment contracts, public Kaggle score artifacts or the verifier-LoRA branch. Do not train, use Kaggle GPU or submit to Kaggle under this contract.
