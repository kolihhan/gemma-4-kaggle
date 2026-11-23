"""CPU-only tests for redacted private real-31B tool reliability audit."""
import json
import tempfile
import unittest
from pathlib import Path

from scripts import audit_gemma_edit_reliability_20261124 as a


class EditReliabilityTests(unittest.TestCase):
    def test_success_and_dispatch_failure_are_distinct(self):
        self.assertEqual(a._observe('{"status":"ok","filepath":"SECRET"}'), ("ok", "OK"))
        self.assertEqual(a._observe({"content": json.dumps({
            "status": "error", "error_type": "TypeError",
            "error_message": "Mandatory input parameters are not present: old_string"
        })}), ("error", "DISPATCH_MISSING_ARGS"))
        self.assertEqual(a._observe({"status":"error","error_type":"FileEditError"}),
                         ("error", "EDIT_MATCH_OR_VALIDATION"))
        self.assertEqual(a._observe("arbitrary private command output"), ("unknown","UNKNOWN"))

    def test_argument_shape_does_not_expose_text(self):
        ok={"filepath":"private/file.py","old_string":"very private code","new_string":"changed"}
        self.assertEqual(a._arg_shape("edit_file", ok), "apparently_valid")
        self.assertEqual(a._arg_shape("edit_file", {"filepath":"p.py"}), "invalid_missing_or_wrong_type")
        self.assertEqual(a._arg_shape("edit_file", dict(ok, tokenized_extra="private")), "unexpected_keys_present")
        self.assertEqual(a._arg_shape("edit_file", dict(ok, old_string="")), "invalid_empty_target")
        self.assertEqual(a._arg_shape("run_command", {"command": " "}), "invalid_empty_command")

    def test_trace_event_count_and_unambiguous_error(self):
        trace={"steps":[
            {"tool_calls":[{"function_name":"read_file","arguments":{"filepath":"private.py"}}],
             "observation":'{"status":"ok"}'},
            {"tool_calls":[{"function_name":"edit_file","arguments":{"filepath":"private.py"}}],
             "observation":'{"status":"error","error_type":"TypeError","error_message":"Mandatory input parameters are not present"}'},
            {"tool_calls":[{"function_name":"edit_file","arguments":{"filepath":"p","old_string":"a","new_string":"b"}}],
             "observation":'{"status":"ok","diff":"secret"}'},
            {"tool_calls":[{"function_name":"submit_patch","arguments":{}}],
             "observation":'{"status":"ok","patch_size":222}'},
        ]}
        x=a.reduce_trace(trace)
        self.assertEqual(x["edit_events"], 2)
        self.assertEqual(x["edit_argument_anomalies"], 1)
        self.assertEqual(x["edit_dispatch_missing_args"], 1)
        self.assertEqual(x["edit_confirmed_ok"], 1)
        self.assertEqual(x["submit_requests"], 1)
        self.assertEqual(x["submit_confirmed_ok"], 1)
        self.assertEqual(x["first_edit_event"], 2)
        self.assertEqual(x["first_submit_event"], 4)
        self.assertNotIn("secret", json.dumps(x))
        self.assertNotIn("private.py", json.dumps(x))

    def test_parallel_observation_cannot_be_misattributed(self):
        x=a.reduce_trace({"steps":[{
            "tool_calls":[
                {"function_name":"edit_file","arguments":{"filepath":"p","old_string":"x","new_string":"y"}},
                {"function_name":"read_file","arguments":{"filepath":"p"}}],
            "observation":'{"status":"error","error_type":"FileEditError"}'
        }]})
        self.assertEqual(x["edit_confirmed_error"], 0)
        self.assertEqual(x["edit_observation_unknown"], 1)

    def test_full_paired_integrity_required(self):
        def row(tid,arm):
            return {"arm":arm,"instance_id":tid,"resolved":False,"has_patch":True,
                    "tool_calls":12,"duration_seconds":200}
        data={"version":a.EXPECTED_VERSION,"status":"completed",
              "results":[row(f"rich_{k}",arm) for k in range(100,108) for arm in a.ARMS]}
        self.assertEqual(len(a.safe_result_rows(data)),16)
        data["results"][1]["arm"]=a.ARMS[0]
        with self.assertRaisesRegex(ValueError,"matched"):
            a.safe_result_rows(data)

    def test_missing_traces_are_unknown_not_zero_edit_calls(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            rows=[{"arm":arm,"instance_id":f"rich_{k}","resolved":False,
                   "has_patch":False,"tool_calls":8,"duration_seconds":120}
                  for k in range(100,108) for arm in a.ARMS]
            (root/a.SUMMARY).write_text(json.dumps({
                "version":a.EXPECTED_VERSION,"status":"completed","results":rows
            }))
            x=a.audit(root)
            self.assertEqual(x["results_by_arm"]["champion_4min"]["traces_found"],0)
            self.assertEqual(x["results_by_arm"]["behavioral_4min"]["traces_found"],0)
            self.assertFalse(x["raw_private_content_exported"])
            # One synthetic treatment-only trace should not leak to champion.
            target=root/"paired-behavioral-private-results"/"public-prompt"
            target.mkdir(parents=True)
            (target/"trace_rich_100.json").write_text(json.dumps({"steps":[{
                "tool_calls":[{"function_name":"edit_file","arguments":{}}],
                "observation":'{"status":"error","error_type":"TypeError","error_message":"Mandatory input parameters"}'
            }]}))
            x=a.audit(root)
            self.assertEqual(x["results_by_arm"]["behavioral_4min"]["traces_found"],1)
            self.assertEqual(x["results_by_arm"]["champion_4min"]["traces_found"],0)
            self.assertEqual(x["results_by_arm"]["behavioral_4min"]["from_traces_only"]["edit_dispatch_missing_args"],1)


if __name__=="__main__":
    unittest.main()
