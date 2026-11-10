---
name: repair-witness
description: Run a real bounded targeted pytest witness before and after a code change, comparing actual pass/fail evidence; never claim hidden correctness.
---

# Repair Witness (V3-R)

Runs a **real pytest process** in the offline sandbox's actual git checkout (preferring SWE_WORKSPACE or PWD; the subprocess backend may remap /workspace). This is not
a hidden-test oracle and not a reason to generate speculative tests. Use only
a test file/node already found in the repository, not the full suite.

**Before an edit**, when a relevant test already exists, invoke
run_skill_script with:
  skill_name="repair-witness"
  file_path="scripts/witness.py"
  args={"phase":"before","target":"tests/test_example.py::test_case"}

**After the edit**, invoke the same script with:
  args={"phase":"after","target":"tests/test_example.py::test_case"}
using the **same exact target**. Optional timeout_seconds is 1..45, default 20.
If no pre-edit test existed, invoke only after and report baseline_unavailable.
For trivial issues without a relevant test, avoid unnecessary overhead.

Read the returned JSON, not assumptions:
- repair_demonstrated: specific targeted test failed before and passes after
- regression_introduced: same test passed before and now fails
- not_yet_fixed: still failing; inspect the actual traceback and revise
- baseline_unavailable, inconclusive, blocked: no improvement shown

A passing targeted test cannot certify the hidden issue. Collection errors,
missing pytest, a timeout or zero tests are blocked, never pass. The script
writes only small state under /tmp, not source files, and installs nothing.
