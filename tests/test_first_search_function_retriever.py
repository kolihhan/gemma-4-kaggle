"""CPU tests for bounded first-search production evidence."""
import tempfile
import unittest
from pathlib import Path
from scripts.first_search_function_retriever import retrieve

class RetrieverTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.root=Path(self.tmp.name)
        (self.root/'pkg').mkdir()
        (self.root/'pkg'/'auth.py').write_text('def validate_token(token):\n    """Check authentication token expiration."""\n    return token\n\ndef parse_message(msg):\n    return msg\n')
        (self.root/'pkg'/'utils.py').write_text('def render_table(rows):\n    return rows\n')
        (self.root/'tests').mkdir(); (self.root/'tests'/'test_auth.py').write_text('def validate_token(token):\n    return None\n')
    def tearDown(self):self.tmp.cleanup()
    def test_top_match(self):
        x=retrieve('validate_token authentication expiration',self.root)
        self.assertEqual(x[0]['symbol'],'validate_token');self.assertEqual(x[0]['path'],'pkg/auth.py')
    def test_no_test_leak(self):self.assertTrue(all(not x['path'].startswith('tests/') for x in retrieve('validate_token',self.root)))
    def test_deterministic(self):self.assertEqual(retrieve('token authentication',self.root),retrieve('token authentication',self.root))
    def test_no_match(self):self.assertEqual(retrieve('xyzqwerty',self.root),[])
    def test_cap(self):self.assertLessEqual(len(retrieve('token rows message',self.root)),3)
    def test_bad_limit(self):
        with self.assertRaises(ValueError):retrieve('token',self.root,4)
    def test_syntax_error_isolated(self):
        (self.root/'pkg'/'broken.py').write_text('def not_valid(\n')
        self.assertEqual(retrieve('validate_token',self.root)[0]['symbol'],'validate_token')
    def test_symlink_ignored(self):
        (self.root/'pkg'/'linked.py').symlink_to(self.root/'pkg'/'auth.py')
        self.assertEqual(len([x for x in retrieve('validate_token',self.root) if x['symbol']=='validate_token']),1)
    def test_251st_relevant_file_not_lost(self):
        for i in range(250):
            (self.root / f'a{i:03}.py').write_text('def irrelevant():\\n    return 1\\n')
        (self.root / 'z_auth.py').write_text('def refresh_token():\\n    return 1\\n')
        found = retrieve('refresh token', self.root)
        self.assertEqual(found[0]['symbol'], 'refresh_token')
        self.assertEqual(found[0]['path'], 'z_auth.py')
    def test_hidden_fixture_not_visible(self):
        (self.root / 'fixtures').mkdir()
        (self.root / 'fixtures' / 'auth.py').write_text('def refresh_token():\\n    return "PRIVATE_FIXTURE_SENTINEL"\\n')
        self.assertNotIn('PRIVATE_FIXTURE_SENTINEL', repr(retrieve('refresh token', self.root)))
    def test_root_test_file_is_not_model_visible(self):
        (self.root/'test_auth.py').write_text('def validate_token():\n    return "HIDDEN_TEST_SENTINEL"\n')
        self.assertNotIn('HIDDEN_TEST_SENTINEL',repr(retrieve('validate_token',self.root)))
if __name__=='__main__':unittest.main()
