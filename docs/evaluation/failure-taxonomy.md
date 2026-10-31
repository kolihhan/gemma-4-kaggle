# Baseline Failure Taxonomy

Use one primary terminal class per failed task. Add secondary notes when useful, but avoid inventing overlapping categories just to explain every detail.

## F1 — LOCATE

The agent fails to identify the relevant file, symbol, test, or subsystem.

Typical evidence:
- spends calls reading unrelated files;
- never reaches the code changed by the reference solution or an equivalent implementation point;
- broad scans consume the budget without narrowing candidates.

## F2 — UNDERSTAND

The agent reaches relevant code but forms the wrong root-cause/model of behavior.

Typical evidence:
- patch addresses a symptom but not the failing invariant;
- test output contradicts the stated hypothesis;
- correct component, wrong semantics.

## F3 — EDIT

The root cause is substantially correct but the implementation is invalid, incomplete, too broad, or breaks surrounding behavior.

Typical evidence:
- syntax/runtime error introduced;
- wrong API/return shape;
- misses one required call site;
- unnecessary refactor creates regression.

## F4 — TEST

The agent does not select, run, or correctly interpret a useful verification step.

Typical evidence:
- no verification despite available time;
- repeatedly runs irrelevant suite/command;
- misreads exit code/output;
- assumes success from compilation only.

## F5 — REPAIR

A useful failure signal exists, but the agent fails to turn it into a converging second attempt.

Typical evidence:
- repeats the same patch/action;
- ignores new traceback/assertion evidence;
- oscillates between two changes;
- gives up with repair budget remaining.

## F6 — CONTEXT

The agent loses or fails to preserve important constraints/evidence across turns.

Typical evidence:
- contradicts earlier observed code;
- forgets required behavior while editing;
- re-reads the same context because no compact working state survives.

## F7 — TOOL

Failure is primarily caused by invalid or poor tool use rather than the software reasoning itself.

Typical evidence:
- invalid paths/arguments;
- destructive or malformed edit calls;
- command timeouts from avoidably broad commands;
- graph query misuse or repeated empty queries.

## F8 — BUDGET

The task exceeds time/tool/turn limits before a credible patch is verified/submitted.

Typical evidence:
- high-value work starts too late;
- repeated low-information calls;
- large test commands dominate wall time;
- patch exists but cannot be verified/submitted before termination.

## F9 — SUBMIT

The solution work is substantially complete but the final patch/submission lifecycle fails.

Typical evidence:
- forgets `submit_patch`;
- submits empty/unintended diff;
- harness rejects layout/config;
- patch extraction/application fails for an avoidable submission reason.

## Run record

Record at minimum:

```text
task_id:
repo:
git_commit:
model:
resolved: true|false
elapsed_seconds:
tool_calls:
files_opened:
patch_files:
patch_bytes:
tests_run:
repair_count:
primary_failure: F1..F9 | NONE
notes:
```

## Decision rule

Do not add architecture based on one interesting failure. After the fixed diagnostic sample, count dominant classes and inspect representative traces.

Examples:

- F1/F2 dominant → test stronger navigation / graph policy.
- F4/F5 dominant → test targeted-test + repair policy.
- F6/F8 dominant → test context compression / budget policy.
- F3 dominant → inspect model capability and edit discipline before adding orchestration.
- F9 dominant → fix harness/submission mechanics before any model work.

A new intervention should predict which failure class it will reduce before we implement it.
