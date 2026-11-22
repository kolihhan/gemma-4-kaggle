---
name: evidence-channel
description: Mandatory bounded source localization, focused pytest, and patch integrity channel. Use instead of unrestricted shell commands.
---

# Evidence Channel

The coder has NO general `run_command`, graph search or free-form shell tool.
Use `run_skill_script` to locate source, verify narrowly, and check diff.
Tool call format:
- `skill_name="evidence-channel"`
- `file_path="scripts/evidence.py"`
- `args={"request":"<JSON STRING>"}`

Examples:
- `{"request":"{\"mode\":\"locate\",\"query\":\"error_code parser\"}"}`
- `{"request":"{\"mode\":\"test\",\"path\":\"tests/test_parser.py\"}"}`
- `{"request":"{\"mode\":\"test\",\"path\":\"tests/test_parser.py\",\"selector\":\"::test_case\"}"}`
- `{"request":"{\"mode\":\"diff\"}"}`
- `{"request":"{\"mode\":\"status\"}"}`

All evidence comes from the checked-out repository, never reference patches.
The `locate` action returns up to nine grounded, truncated **production**
code matches; a missing match is not evidence that the issue's target is
absent. Read those source files using native `read_file` before any edit.
You may call `locate` with one alternate identifier if necessary.

**Task workflow:** (1) locate using the most specific code symbol in the
actual issue; (2) read source and one relevant test; (3) edit with native
`edit_file`; (4) use `test` on the smallest available test node (if no
test can run, say so); (5) use `diff` to catch whitespace conflicts; (6)
call native `submit_patch` for a nonempty intended fix.

This Skill is the ONLY provided native command/search/test channel, not a
correctness oracle. Treat `status=nonzero` or `timeout` as failure,
and revise the code or narrow the test. Do not run an entire test suite,
install packages, invent tests, or repeat the same action without new evidence.
Budget is unchanged: 5 minutes, 60 tool calls, 80 turns. Stop early when the
issue is solved.
