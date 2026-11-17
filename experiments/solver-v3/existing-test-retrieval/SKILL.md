---
name: existing-test-retrieval
description: Find exact existing assertions and edge cases for identifiers explicitly mentioned in a reported issue.
---

Once, before editing, extract one to four exact symbols from the issue, such as a method, class or exception name. Call `run_skill_script` with skill_name `existing-test-retrieval`, file_path `scripts/retrieve.py`, and args `{"anchors": "parse_value ValueError"}` using those exact symbols. It lists up to three existing tests with matching assertion context. Inspect a matched assertion only when it constrains the proposed repair. Skip this lookup when the issue contains no concrete identifier.
