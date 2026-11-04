# Capacity-v0 Gate B — 31B GPU quota blocker (2026-11-04)

**Status: BLOCKED BY EXTERNAL GPU QUOTA; NOT A MODEL-CAPACITY RESULT.**
No 31B weights were loaded. No model inference, issue task, patch, new competition submission, or new Public LB score was produced.

## Grounded execution

- Active branch: exp/capacity-boundary-v0.
- Model-only E4B-vs-31B payload + official scorer schema previously passed CPU checks: [41782383957](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41782383957).
- Preselection Git-source audit [41794198475](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41794198475) checked 467 historical revisions against 16 candidate IDs; zero prior tracked source/document mentions. **Not a certification of clean blind data**: old private artifacts, unrecorded human inspection and out-of-repo contexts remain unverified.
- Initial [41794612235](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41794612235) failed CPU static tests: a historical-audit test fixture accidentally contained two actual selected task IDs. This was corrected using synthetic IDs, with no weakening of the exposure scanner. No GPU ran.
- Second [41794811345](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41794811345), job 126456289520, passed static checks and rendered the private 31B L4x4 startup kernel. But the Kaggle CLI printed:

    Kernel push error: Maximum weekly GPU quota of 30.00 hours reached.

  Timestamp: 2026-11-04 07:48:32 UTC. **The Kaggle 2.2.5 command returned exit code 0 despite rejecting the push**; old workflow erroneously polled a nonexistent kernel and got HTTP 404.
- Read-only independent status probe [41795018386](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41795018386): kernel status HTTP 404; exact notebook not found in recent user listing; no result output. No new GPU submission.
- The failure is attributable to **weekly account GPU quota**, not demonstrated model OOM, tool parser failure, model reasoning or invalid submission schema.

## Corrective implementation

- Added scripts/check_capacity_31b_push_v0.py and tests/test_check_capacity_31b_push_v0.py to require an explicit successful kernel-version confirmation and fail closed on any printed push rejection, including zero-exit quota errors.
- Changed .github/workflows/capacity-31b-startup-smoke-v0.yml to MANUAL workflow_dispatch only, to avoid auto-launching GPU kernels on research commits.
- Startup kernel remains private, internet disabled, synthetic-only, no benchmark task hydration, and uses the official model source/wheelhouse.
- CPU validation [41795366875](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/41795366875): **9/9 tests pass** and 467-revision history audit still finds zero preselection source mentions.

Kaggle officially states L4x4 notebook quota is charged at twice the older T4x2/P100 rate:
https://www.kaggle.com/competitions/gemma-4-developer-agent/overview

## Unknowns

- Whether the 31B model actually loads with the frozen vLLM config on four Kaggle L4 GPUs.
- Whether ordinary generation and synthetic scalar/array tool calls work with the current scorer's model server.
- Model runtime cost, task success, and paired E4B-vs-31B benefit.
- Exact GPU-quota reset time and whether other active kernels consume it.
- Complete historical exposure across non-Git artifacts and human views.

## Next executable gate

1. Do not re-submit the blocked GPU kernel while account quota is exhausted.
2. Only after quota availability is confirmed, manually run the one-shot 31B startup/tool parser smoke. Its push-acceptance gate must explicitly pass BEFORE polling.
3. If the server runs, distinguish basic boot/plain inference from scalar-tool and array-tool success. Toy tool probes are runtime checks, not proof of repair competence.
4. Then finish model-independent task eligibility/replacement/provenance and consider the pre-registered four-task E4B-vs-31B feasibility-only paired experiment; no leaderboard submission, no promotion from four tasks.
5. If quota stays unavailable, open a separately justified E4B evidence/retrieval/repair mechanism lane, preserving the capacity test's untouched reserved denominator.

**Corrections to earlier narration:** A printed 404 was not evidence of a slow model start. The original kernel push was rejected due to quota; no 31B start occurred.
