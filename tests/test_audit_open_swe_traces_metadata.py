"""Synthetic data-contract tests; external raw trajectories never enter test output."""
import unittest

from scripts.audit_open_swe_traces_metadata import pick_splits, sample_grade


def row(**kwargs):
    base = {
        "resolved": 1,
        "repo": "example/clean-project",
        "language": "Python",
        "license": "MIT",
        "trajectory_id": "traj-private-synthetic-0001",
        "metadata": {"model_patch": {"patch": "diff --git a/a.py b/a.py\n+fix"}},
        "messages": [{"role": "user"}, {"role": "assistant"}, {"role": "tool"}],
    }
    base.update(kwargs)
    return base


class GateTests(unittest.TestCase):
    def test_known_good_and_reasons_for_rejection(self):
        self.assertEqual(sample_grade(row()), "candidate_for_private_deep_audit")
        self.assertEqual(sample_grade(row(resolved=0)), "not_verified_success")
        self.assertEqual(sample_grade(row(resolved=-1)), "not_verified_success")
        self.assertEqual(sample_grade(row(resolved=True)), "missing_resolved_label")
        self.assertEqual(sample_grade(row(repo="fastapi/fastapi")), "public_eval_repo_excluded")
        self.assertEqual(sample_grade(row(language="Java")), "non_python")
        self.assertEqual(sample_grade(row(license="unknown")), "unknown_repo_license")
        self.assertEqual(sample_grade(row(metadata={})), "no_verified_model_diff")
        self.assertEqual(sample_grade(row(messages=[{"role": "assistant"}])),
                         "no_complete_trace")
        self.assertEqual(sample_grade(row(messages=[{"role": "user"},{"role": "assistant"},{"role": "assistant"}])),
                         "no_observed_tool_feedback")
        self.assertEqual(sample_grade(row(trajectory_id=None)), "missing_trajectory_identity")
        self.assertEqual(sample_grade(row(model_patch={"patch": "diff --git a/ok b/ok"})),
                         "candidate_for_private_deep_audit")

    def test_one_per_train_config_no_future_label_dependence(self):
        splits=[
            {"config": "a", "split": "train", "num_examples": 11},
            {"config": "a", "split": "test", "num_examples": 3},
            {"config": "b", "split": "train", "num_examples": 0},
            {"config": "c", "split": "train", "num_examples": 12},
            {"config": "d", "split": "test", "num_examples": 7},
        ]
        self.assertEqual(pick_splits(splits, 3), [
            {"config": "a", "split": "train"},
            {"config": "c", "split": "train"}
        ])
        self.assertEqual(pick_splits([], 4), [])


if __name__ == "__main__":
    unittest.main()
