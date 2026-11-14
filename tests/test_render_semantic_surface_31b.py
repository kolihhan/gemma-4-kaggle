"""Frozen no-leak prospective selector regression for Gemma 31B surface pilot."""
import unittest

from scripts.render_semantic_surface_31b import EXCLUDED, SALT, select_ids


class SelectProspectiveTests(unittest.TestCase):
    def test_deterministic_balanced_and_excludes_previously_seen(self):
        ids = [f"fastapi_{n}" for n in range(16001,16012)]
        ids += [f"rich_{n}" for n in range(4200,4211)]
        ids += list(EXCLUDED)
        selected = select_ids(ids)
        self.assertEqual(selected, select_ids(list(reversed(ids))))
        self.assertEqual(len(set(selected)),4)
        self.assertEqual(sum(x.startswith("fastapi_") for x in selected),2)
        self.assertEqual(sum(x.startswith("rich_") for x in selected),2)
        self.assertFalse(set(selected) & set(EXCLUDED))
        self.assertTrue(len(SALT)>20)

    def test_insufficient_task_population_fails(self):
        with self.assertRaisesRegex(ValueError,"not enough unseen"):
            select_ids(["rich_4412","fastapi_15923"])


if __name__ == "__main__":
    unittest.main()
