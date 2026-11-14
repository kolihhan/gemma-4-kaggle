import unittest
from scripts.probe_sweagent_action_shapes import parse_call, summarize


class SWEAgentShapeProbeTests(unittest.TestCase):
    def test_only_metadata_keys_no_command_literals(self):
        event = {"function": {"name": "bash",
                              "arguments": '{"command":"SECRET_STRING_DONT_LOG"}'}}
        self.assertEqual(parse_call(event), ("bash", "json_object", ("command",)))
        data = summarize([{"row": {
            "resolved": 1, "repo": "safe/public-repo", "language": "python",
            "license": "MIT", "trajectory_id": "synthetic",
            "metadata": {"model_patch": {"patch": "diff --git a/a b/a"}},
            "messages": [
                {"role": "assistant", "tool_calls": [event]},
                {"role": "tool", "tool_call_id": "id", "content": "SECRET_STRING_DONT_LOG"},
                {"role": "assistant", "content": "SECRET_STRING_DONT_LOG"}
            ]
        }}])
        self.assertEqual(data["qualified_rows"], 1)
        self.assertEqual(data["observed_tool_names"], {"bash": 1})
        self.assertEqual(data["call_arg_key_shapes"], {"bash|json_object|command": 1})
        self.assertNotIn("SECRET_STRING_DONT_LOG", str(data))

    def test_reject_malformed_calls_without_exposing_values(self):
        self.assertEqual(parse_call({"function": {"name": "bash", "arguments": "{BAD"}}),
                         ("bash", "unparseable_json", ()))
        self.assertEqual(parse_call({}), ("unknown_tool", "not_dict", ()))
        self.assertEqual(parse_call(None), ("invalid_structure", "unknown", ()))


if __name__ == "__main__":
    unittest.main()
