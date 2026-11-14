"""Prove retrospective task exposure overlap and fail closed on malformed metadata."""
import json
from pathlib import Path
import tempfile
import unittest

from scripts.audit_semantic_surface_exposure import ROOT, MANIFESTS, PILOT, audit


class ExposureAudit(unittest.TestCase):
    def test_existing_repository_manifests_expose_two_selected_tasks(self):
        result=audit(ROOT)
        self.assertEqual(result["selected_count"],4)
        self.assertEqual(result["historically_exposed_ids"],
                         ["fastapi_14479","rich_3953"])
        self.assertEqual(result["historically_exposed_count"],2)
        self.assertFalse(result["clean_unseen_set_proven"])
        self.assertFalse(result["leakage_to_model_proven"])
        self.assertFalse(result["model_training_in_new_pilot"])
        self.assertIn("old_train_trace_harvest",result["manifest_hits"])
        self.assertIn("old_training_targeted_checks",result["manifest_hits"])

    def test_invalid_manifest_and_duplicate_tasks_stop(self):
        with tempfile.TemporaryDirectory() as place:
            base=Path(place)
            for _, rel, field in MANIFESTS:
                (base/rel).parent.mkdir(parents=True,exist_ok=True)
                (base/rel).write_text(json.dumps({field:[]}))
            self.assertEqual(audit(base)["historically_exposed_count"],0)
            with self.assertRaisesRegex(ValueError,"duplicate"):
                audit(base,("foo","foo"))
            _, bad, _ = MANIFESTS[0]
            (base/bad).write_text('{"tasks":{}}')
            with self.assertRaisesRegex(ValueError,"missing manifest"):
                audit(base)


if __name__=="__main__":
    unittest.main()
