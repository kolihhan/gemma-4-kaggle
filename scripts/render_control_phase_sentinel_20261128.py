"""Private CPU-only calibration, no model or submission. Select exact old task identities by hash."""
import ast
import hashlib
import json
from pathlib import Path
import sys

from scripts.render_budget_factorial_real31b_20261127 import meta
from scripts.render_six_gold_noop_cpu_20261126 import TEMPLATE

OLD_HASH = "58bc8f0fab67f9a7cd5a355068929dfb994c016e3ff41d0610617c3352611122"
CLEAN_HASH = "231db5d504930562c4dc78f696a56009635f02bfcf4a79023531d2a3a7eb8bd2"
SLUG = "kolihhan/gemma4-control-phase-sentinel-20261128-v1"


def ids(root, count, sha):
    found = []
    for p in root.rglob("*.py"):
        tree = ast.parse(p.read_text())
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "SELECTED_IDS" for t in node.targets):
                v = ast.literal_eval(node.value)
                if isinstance(v, list) and len(v) == count and len(set(v)) == count and hashlib.sha256("|".join(v).encode()).hexdigest() == sha:
                    found.append(v)
    if len(found) != 1:
        raise ValueError("private source membership not verified")
    return found[0]


def records(root, name, count):
    paths = list(root.rglob(name))
    if len(paths) != 1:
        raise ValueError("missing or ambiguous control output")
    d = json.loads(paths[0].read_text())
    assert d["tasks"] == count and not d["gpu"] and not d["model_inference"] and not d["competition_submission"]
    rows = sorted(d["rows"], key=lambda r: r["ordinal"])
    assert [r["ordinal"] for r in rows] == list(range(1, count + 1))
    return rows


def external(root, name):
    rows = [json.loads(l) for l in (root / name).read_text().splitlines() if l.strip()]
    d = {r["instance_id"]: r["resolved"] for r in rows}
    assert len(rows) == len(d) == 129 and all(type(x) is bool for x in d.values())
    return d


def build(root, out):
    old = ids(root / "old-source", 35, OLD_HASH)
    clean = ids(root / "clean-source", 17, CLEAN_HASH)
    assert not set(old) & set(clean)
    o = records(root / "old-output", "budget_factorial_eligibility.json", 35)
    c = records(root / "clean-output", "gemma31_fresh17_gold_noop_safe.json", 17)
    assert all(r["gold_pass"] is True and r["noop_pass"] is False for r in c)
    ff = [r for r in o if r["gold_pass"] is False and r["noop_pass"] is False]
    pp = [r for r in o if r["gold_pass"] is True and r["noop_pass"] is True]
    assert len(ff) == 33 and len(pp) == 2
    # Fixed diagnostic strata, never promotion tasks. Two failure cases with and without observed noop exit 1.
    actual_failure = next(r for r in ff if r.get("noop_actual_test_failure") is True)
    other_failure = next(r for r in ff if r.get("noop_actual_test_failure") is not True)
    cases = [
        ("previous_clean", clean[0]),
        ("both_false_noop_exit1", old[actual_failure["ordinal"] - 1]),
        ("both_false_noop_other", old[other_failure["ordinal"] - 1]),
        ("both_pass", old[pp[0]["ordinal"] - 1]),
    ]
    from collections import Counter
    g, n = external(root, "gold_runs.jsonl"), external(root, "empty_runs.jsonl")
    assert set(g) == set(n) and set(old + clean) <= set(g)
    cross = Counter()
    for tid, r in zip(old, o):
        cross["local_" + str(int(r["gold_pass"])) + str(int(r["noop_pass"])) + "_external_" + str(int(g[tid])) + str(int(n[tid]))] += 1
    print("SENTINEL_CROSS_ENV=" + json.dumps({"n":35,"pair_matrix":dict(cross),"external_clean":sum(g[t] and not n[t] for t in old),"external_source_commit":"f3b6d3ac4c532a2bf3745872fe171747d0bf3e31"},sort_keys=True),flush=True)
    src = Path(TEMPLATE).read_text().split('if __name__ == "__main__":', 1)[0]
    body = Path("kaggle/control_phase_sentinel_20261128.py").read_text()
    assert body.count("__PRIVATE_CASES__") == 1
    runtime = src + "\n" + body.replace("__PRIVATE_CASES__", repr(cases))
    compile(runtime, "main.py", "exec")
    out.mkdir(exist_ok=False, parents=True)
    (out / "main.py").write_text(runtime)
    m = meta(SLUG, False)
    assert m["is_private"] and not m["enable_gpu"] and not m["enable_tpu"] and not m["enable_internet"] and not m["model_sources"]
    (out / "kernel-metadata.json").write_text(json.dumps(m))
    print("SENTINEL_PREFLIGHT=4 tasks; 8 gold/noop controls; private CPU; no model",flush=True)


if __name__ == "__main__":
    build(Path(sys.argv[1]), Path(sys.argv[2]))
