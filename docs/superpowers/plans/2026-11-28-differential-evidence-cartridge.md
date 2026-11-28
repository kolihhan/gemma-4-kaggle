# Differential Evidence Cartridge Implementation Plan
> For agentic workers: use superpowers writing-plans, systematic-debugging, verification-before-completion; no GPU or submission in this phase.
**Goal:** identify whether useful missing visible evidence can be acquired cheaply, then prepare a legal candidate only after gates.
**Architecture:** single Champion LlmAgent, one bounded read-only evidence skill, native edit/verify/finalization. **Spec:** docs/design/2026-11-28-differential-evidence-cartridge.md. Python stdlib, pinned official wheelhouse, private runtime.
**Global constraints:** exact Champion SHA; no raw Competition Data in Git or logs; no GPU/training/inference/official submission now; no changes to current submission folder; no invented scorer equivalence; preserve failures and unknowns.

## Task 0: recover valid evaluation
- [ ] Inspect actual private 35-pair outputs (not just booleans) and wheelhouse/verify_task signature, retained snapshot/env provenance. Do not rerun 35 blindly.
- [ ] Implement private aggregate-only phase reporting in a new scripts/audit_control_phases_20261128.py. Record setup, apply, collection, execution, assertion, unknown separately; retain error codes privately. Do not output sensitive paths/test content.
- [ ] Use synthetic fixtures asserting setup error and timeout never classified as semantic fail; noop pass excludes, gold fail excludes, gold-pass/noop-fail qualifies only when controls execute validly. Run pytest new tests; expected all pass.
- [ ] Check one previously clean task under same environment to detect drift; then freeze small unused sentinels before private CPU qualification. Stop on setup failure; fix specific environment cause using actual stack, not label change. Keep raw materials private. No GPU.

## Task 1: blind trace/evidence audit
- [ ] Recover real retained patches/trace events using existing scripts/audit_four_arm_evidence_20261127.py and private artifacts; validate exact record identities/hash/patch sizes. Do not expose gold.
- [ ] Create issue-only rubric with visible original source, freeze expected behavior + necessary evidence before inspecting grade, trace, gold. Independent reviewer if available; if not report single-review limitation. Distinguish successful reads from requests.
- [ ] Compare stable failures, mixed, successes; label missing fact, adequate evidence but wrong inference, incorrect patch, blocked execution, ambiguous. No oracle paths fed to proposed agent.
- [ ] Write aggregate safe report; if inadequate evidence access, mark blocked, not fabricated. Mechanism gate in spec.

## Task 2: CPU-only cartridge prototype
- [ ] Create research-only scripts/dec_evidence.py (not submission yet) and tests/test_dec_evidence.py. Interface collect(root: Path, anchors: tuple[str,...], limits: Limits) -> Packet. No writes, no subprocess, no network. Use stdlib AST/tokenize; bounded files and bytes; deterministic sorting; avoid symlinks and traversal.
- [ ] Tests first: definition and caller in two files retained; branch alternatives included; same-named unrelated symbol marked ambiguous; invalid Python handled as PARTIAL; no anchors NO_ANCHOR; symlink skipped; bytes/file cap and deadline enforced; oversized packet explicitly truncated; no label file accessible. Run pytest tests/test_dec_evidence.py -q expected red then green.
- [ ] Compare three CPU prototype retrieval families on the same blind annotated snapshots: lexical top-k; AST symbol-only; diversity across definition/caller/alternative branch. Same output cap, no gold. Report real measured necessary-fact recall/precision, added facts vs actual Champion context, bytes, elapsed, error/blocked counts. At least five alternating runs for timing if claiming speed; no synthetic data as model result. Keep lowest complexity on ties.
- [ ] Apply mechanism gate from spec; if fail, stop and record.

## Task 3: build exact candidate (CPU only, conditional)
- [ ] Reconstruct exact Champion using scripts/build_behavioral_probe_timeout_safe_20261123.py _source_files; verify SHA before mutation. Fail closed on mismatch.
- [ ] Create new builder scripts/build_dec_candidate_20261128.py and tests/test_build_dec_candidate.py. Candidate extends only supported skill/tool declarations and instruction, retains model/budgets/sampling; assert unchanged original keys and file digests, no arbitrary host code. Tests include invalid base, duplicate root, traversal, raw data, wrong model and missing tool. Verify actual official wheelhouse compile in private CPU runtime; inspect exact legal skill invocation on fixture with no model using scripted replay if supported. No fake claim of real Gemma uptake.
- [ ] Candidate ZIP only as private immutable artifact, deterministic SHA and report. Do not touch historical submission/ or auto submission workflow.
- [ ] Review focus: model may never call script, context compaction, malformed anchors, deadline reserve, unavailable witness, no-op/blocked, stale grader, test scratch contamination; CPU tests for each feasible mechanical invariant; model/harness unknowns explicitly deferred.

## Task 4: prospective validation (not authorized now)
- [ ] Freeze independent eligible task set, hashes, budgets, exact seeds/config/order, test plan and stop rule in docs/research. Quota check and separate owner authorization required before any GPU.
- [ ] Interleave Champion/candidate, record actual resolved count, paired outcomes, uptake, cost and run failure reasons. No dropping tasks; no hidden scorer claims. Spec threshold + independent confirmation; reject or hold otherwise.
- [ ] Only after real-model gate and independent confirmation, verify current official rules, quota and conservative 12h forecast; explicit owner consent before one official submission. Preserve control and final-selection decisions separately.
