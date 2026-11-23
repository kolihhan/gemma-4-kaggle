"""No-model tests for read-only Gemma tool/action checkpoints."""
import unittest

from scripts.gemma_action_funnel_20261123 import analyze


class ActionFunnelTests(unittest.TestCase):
    def test_call_16_and_20_track_revision_not_correctness(self):
        empty = "0" * 64
        changed = "a" * 64
        later = "b" * 64
        events = [{"tool": "<start>", "revision": empty}]
        for idx in range(1, 23):
            if idx == 16:
                tool, rev = "edit_file", changed
            elif idx >= 21:
                tool, rev = "read_file", later
            else:
                tool, rev = "read_file", changed if idx > 16 else empty
            events.append({"tool": tool, "revision": rev,
                           "patch_bytes": 10 if rev != empty else 0})
        events.append({"tool": "<final>", "revision": later})
        report = analyze({"events": events, "revisions": {empty: 0, changed: 10, later: 12},
                          "complete": True, "finished": True})
        self.assertEqual(report["tool_calls_observed"], 22)
        self.assertEqual(report["first_materialized_patch_call"], 16)
        self.assertEqual(report["first_explicit_edit_call"], 16)
        self.assertTrue(report["checkpoints"]["16"]["nonempty_patch_observed"])
        self.assertEqual(report["checkpoints"]["16"]["correctness"],
                         "UNKNOWN_without_independent_grader")
        self.assertGreater(report["checkpoints"]["20"]["revision_changes_after"], 0)

    def test_submit_callback_is_not_counted_twice(self):
        rev = "x" * 64
        data = {"events": [
            {"tool": "<start>", "revision": rev},
            {"tool": "submit_patch", "phase": "attempt", "revision": rev},
            {"tool": "submit_patch", "phase": "result", "revision": rev},
            {"tool": "<final>", "revision": rev}],
            "revisions": {rev: 4}, "complete": True, "finished": True}
        report = analyze(data)
        self.assertEqual(report["tool_calls_observed"], 1)
        self.assertEqual(report["first_submit_request_call"], 1)
        self.assertFalse(report["checkpoints"]["16"]["observed"])

    def test_incomplete_history_is_explicit(self):
        data = {"events": [{"tool": "<start>"}, {"tool": "run_command", "tool_failed": True}],
                "revisions": {}, "complete": False, "finished": False}
        result = analyze(data)
        self.assertFalse(result["history_complete"])
        self.assertEqual(result["opaque_command_calls"], 1)
        self.assertEqual(result["reported_tool_failures"], 1)
        self.assertIsNone(result["first_materialized_patch_call"])

    def test_malformed_events_fail_closed(self):
        with self.assertRaises(ValueError):
            analyze({"events": [None]})


if __name__ == "__main__":
    unittest.main()
