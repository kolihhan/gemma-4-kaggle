"""Pure repo-disjoint grouping contract for future training-only sources."""
import unittest
from scripts.check_three_scale_cohorts_train_split import group_split,F2P_PROVEN_POSITIVE_INDICES

class SourceSplitTests(unittest.TestCase):
    def test_deterministic_no_cross_repo_split(self):
        repos={"owner/a","owner/b","owner/c","owner/d","owner/e","owner/f"}
        a,b=group_split(repos)
        a2,b2=group_split(repos)
        self.assertEqual((a,b),(a2,b2))
        self.assertEqual(len(b),3)
        self.assertEqual(a&b,set())
        self.assertEqual(a|b,repos)
    def test_frozen_verified_case_counts(self):
        self.assertEqual(sum(len(x) for x in F2P_PROVEN_POSITIVE_INDICES.values()),19)
        self.assertEqual(F2P_PROVEN_POSITIVE_INDICES["wave3_30"],
                         (1,3,4,5,6,7,9,10))

if __name__=="__main__":
    unittest.main()
