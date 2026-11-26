# 2026-11-26 — 31B multi-surface repair: gate to Kaggle submission

> Operational plan for in-session owner-authorized execution. No generic prompt churn.

**Goal:** Deliver a legitimate official Kaggle submission if a single-variable candidate defeats the 0.18 Champion on the **17 pristine, gold/noop-certified** public development issues with no higher global-timeout risk. Otherwise return measured failure and preserve the Champion.

**Frozen baseline:** Full 31B Champion exact SHA256 \`ff08c10240a38e151a2ea1d0478e999ee5d2f437d2dad5571d912cf12859922b\`, 5 minutes / 60 native tool calls / 80 turns, 0.2 temperature, 4096 thinking tokens. The 17 identifiers are deterministically reconstructed from pinned third-party gold/noop version, 65 earlier exclusions and issue-text length, then verified by SHA256 \`231db5d504930562c4dc78f696a56009635f02bfcf4a79023531d2a3a7eb8bd2\`. Do not inspect 17 reference patches as agent input.

**Verified current Kaggle gold/noop:** [real 17-pair CPU #45748245882](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/45748245882): all 17 gold PASS, all 17 no-op FAIL. Distinct from prior invalid 6-task panel (only 2/6 clean).

**Single tested hypothesis, preregistered before new 31B inference:** A 31B agent facing an explicitly multi-entrypoint behavioral issue may patch only one named path. A *bounded scope-coverage* instruction might lead it to use a shared helper or verify both named code surfaces. This does not pretend to infer contracts absent from the actual benchmark issue. For a single-path issue do nothing extra. Keep all constraints and source prompt, append one short conditional clause. **Competing possibility:** the model already finds required paths and this intervention only delays editing, hurting score. Existing broad contract/test prompting was not validated; this is a narrower mechanism with a testable paired outcome, not a claim of novelty.

**Tasks:**
1. Unit-test candidate builder: exact source SHA, ZIP 4 members, sole prompt change; reject drift, no tool/model/budget modifications.
2. Reconstruct 17 IDs exactly by the original pre-inference frozen filter and hash; private runtime uses same issue IDs in both arms, alternating order, same wheelhouse, vLLM Gemma 31B, official evaluator and independent result dirs. No raw task text/gold/patch to public logs.
3. CPU-compile both bundles against current wheelhouse without inference. Check enough free L4 GPU, existing matching private kernel absent, no other active own experimental kernel. Launch exactly one private Kaggle GPU matched run, no official contest submission during evaluation.
4. On terminal COMPLETE retrieve verified 34 scorer rows and output paired both/control-only/candidate-only/neither, tool calls, task time, errors. Reject candidate if incomplete, if net rescues minus regressions <2, if regressions>1, if candidate mean task duration >control*1.15, or if any scorer errors. No cherry-picking/dropouts.
5. If accepted, separately materialize exact candidate ZIP as a private CPU-only Kaggle notebook, verify remote ZIP SHA byte-for-byte, check legal Kaggle slot, active receipts and dedup marker, then submit once. Check authenticated receipt. If API return unknown, do not retry blindly. Keep the output in a private audit log; do not claim a new public score until scoring completes.

**Time-risk:** 34 evaluations ×5 minutes = max ~170 min for agent budget plus scorer/setup overhead. Benchmark test/setup time may exceed that estimate; require full terminal result before any official action. Official hidden-run inference uses unchanged Champion 5-min/60-call caps, so there is no additional global timer exposure from changing caps.

**Decision caveat:** 17 already selected by independent gold/noop validity, not representative of the entire hidden distribution. A +2 net score is exploratory; Kaggle public result is the actual last measurement. Submission still has leaderboard risk. No forced submission if verification fails.
