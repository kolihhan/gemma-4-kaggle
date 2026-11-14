import unittest
from scripts.check_scale_swe_model_patch_apply import safe_public_repo_url

class SourceCheckoutSafetyTests(unittest.TestCase):
    def test_owner_repo_allowlist(self):
        self.assertEqual(safe_public_repo_url("safe-owner","repo.name"),
                         "https://github.com/safe-owner/repo.name.git")
        for owner,repo in [
            ("../evil","thing"),("x","../../data"),("x","bad/name"),
            ("x\nGIT","repo"),("","repo"),("x",""),("x","repo@evil")]:
            with self.assertRaises(ValueError):
                safe_public_repo_url(owner,repo)

if __name__=="__main__":
    unittest.main()
