"""Evidence-budget decision policy for SWE agents (mechanism prototype, not grader).
State is built from observed events. Unlike prompt reminders, each decision is
computed by a deterministic transition function, with explicit saturation and
verification reserves. It NEVER edits code or reads hidden tests.

The competition compiler cannot execute arbitrary Python callbacks from
submission.yaml, so this is only deployable as an optional Skill script (the
model must call it), or an offline/private diagnostic. No success claim.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import argparse
import json
from pathlib import PurePosixPath


class Next(str, Enum):
    FIND_TARGET = "FIND_TARGET"
    READ_TARGET = "READ_TARGET"
    CHANGE_SEARCH_CHANNEL = "CHANGE_SEARCH_CHANNEL"
    EDIT = "EDIT"
    VERIFY = "VERIFY"
    REVISE = "REVISE"
    SUBMIT = "SUBMIT"
    STOP_FAILED_CHECK = "STOP_FAILED_CHECK"


ALLOWED = {"search", "read", "edit", "test", "status"}
TESTS = {"pass", "fail", "blocked", "unknown"}


def normal_path(path: str) -> str:
    p = path.removeprefix("/workspace/").removeprefix("./")
    obj = PurePosixPath(p)
    if not p or p.startswith("/") or ".." in obj.parts or chr(0) in p:
        raise ValueError("unsafe source path")
    return str(obj)


@dataclass
class Budget:
    remaining_calls: int
    remaining_seconds: int
    seen_paths: set[str] = field(default_factory=set)
    recent_novelty: list[bool] = field(default_factory=list)
    observed_source_evidence: bool = False
    patch_changed: bool = False
    focused_test: str = "unknown"
    failed_revisions: int = 0
    observations: int = 0
    invalid_reports: int = 0

    def observe(self, action: str, *, paths=(), patch_changed=None,
                test_outcome="unknown", source_evidence=False):
        if action not in ALLOWED or test_outcome not in TESTS:
            raise ValueError("unknown event")
        if patch_changed is not None and type(patch_changed) is not bool:
            raise TypeError("patch_changed must be a strict boolean")
        canonical = {normal_path(p) for p in paths}
        if len(canonical) > 40:
            raise ValueError("unbounded path event")
        new = canonical - self.seen_paths
        if action in {"search", "read"}:
            self.recent_novelty.append(bool(new))
            self.recent_novelty = self.recent_novelty[-3:]
        self.seen_paths |= canonical
        self.observed_source_evidence |= bool(source_evidence)
        if patch_changed is True:
            if action == "edit" or not self.patch_changed:
                self.focused_test = "unknown"
            self.patch_changed = True
        elif patch_changed is False:
            self.patch_changed = False
            self.focused_test = "unknown"
        if action == "test" and test_outcome != "unknown":
            if test_outcome == "fail":
                self.failed_revisions += 1
            self.focused_test = test_outcome
        self.observations += 1
        return len(new)

    def choose(self) -> Next:
        if self.remaining_calls < 0 or self.remaining_seconds < 0:
            raise ValueError("negative budget")
        # A passing targeted test plus a changed patch is strongest observable
        # completion evidence; a random syntax/check pass is NOT sufficient.
        if self.patch_changed:
            if self.focused_test == "pass":
                return Next.SUBMIT
            if self.focused_test == "fail":
                if self.failed_revisions > 1 or self.remaining_seconds < 50:
                    return Next.STOP_FAILED_CHECK
                return Next.REVISE
            if self.remaining_seconds >= 20:
                return Next.VERIFY
            return Next.STOP_FAILED_CHECK
        if self.remaining_calls <= 2 or self.remaining_seconds < 25:
            return Next.STOP_FAILED_CHECK
        if len(self.recent_novelty) == 3 and not any(self.recent_novelty):
            return Next.CHANGE_SEARCH_CHANNEL
        if self.observed_source_evidence:
            if len(self.seen_paths) > 0:
                return Next.EDIT
            return Next.READ_TARGET
        if self.seen_paths:
            return Next.READ_TARGET
        return Next.FIND_TARGET

    def safe_summary(self):
        return {
            "recommendation": self.choose().value,
            "observed_actions": self.observations,
            "unique_paths": len(self.seen_paths),
            "last_three_new_path_flags": self.recent_novelty,
            "source_evidence": self.observed_source_evidence,
            "patch_changed": self.patch_changed,
            "focused_test": self.focused_test,
            "remaining_calls": self.remaining_calls,
            "remaining_seconds": self.remaining_seconds,
        }


def self_test():
    b = Budget(28, 250)
    assert b.choose() == Next.FIND_TARGET
    b.observe("search", paths=["pkg/a.py"])
    assert b.choose() == Next.READ_TARGET
    b.observe("read", paths=["pkg/a.py"], source_evidence=True)
    assert b.choose() == Next.EDIT
    b.observe("edit", patch_changed=True)
    assert b.choose() == Next.VERIFY
    b.observe("test", test_outcome="pass")
    assert b.choose() == Next.SUBMIT
    stalled = Budget(28, 220)
    stalled.observe("search", paths=["pkg/a.py"])
    for _ in range(3):
        stalled.observe("search", paths=["pkg/a.py"])
    assert stalled.choose() == Next.CHANGE_SEARCH_CHANNEL
    failed = Budget(10, 200)
    failed.observe("edit", patch_changed=True)
    failed.observe("test", test_outcome="fail")
    assert failed.choose() == Next.REVISE
    failed.observe("edit", patch_changed=True)
    assert failed.choose() == Next.VERIFY
    failed.observe("test", test_outcome="fail")
    assert failed.choose() == Next.STOP_FAILED_CHECK
    try:
        failed.observe("search", paths=["../secret"])
    except ValueError:
        pass
    else:
        raise AssertionError("path traversal accepted")
    assert Budget(1, 200).choose() == Next.STOP_FAILED_CHECK
    print("GEMMA_EVIDENCE_BUDGET_POLICY_SYNTHETIC=PASS")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--events-json", type=str, default="[]")
    parser.add_argument("--calls-left", type=int, default=28)
    parser.add_argument("--seconds-left", type=int, default=240)
    args = parser.parse_args()
    if args.test:
        self_test()
        return
    raw = json.loads(args.events_json)
    if not isinstance(raw, list) or len(raw) > 60:
        raise ValueError("expected <=60 events")
    state = Budget(args.calls_left, args.seconds_left)
    for event in raw:
        if not isinstance(event, dict) or not isinstance(event.get("action"), str):
            raise ValueError("invalid event")
        state.observe(**event)
    print(json.dumps(state.safe_summary(), sort_keys=True))


if __name__ == "__main__":
    main()
