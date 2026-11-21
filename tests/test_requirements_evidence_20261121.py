"""CPU-only unit tests for requirements evidence, not a grader metric."""
import tempfile
import unittest
from pathlib import Path
from scripts.requirements_evidence_20261121 import find_evidence


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / 'tests').mkdir()
        (self.root / 'src').mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def test_relevant_test_provides_behavior(self):
        (self.root/'tests'/'test_token.py').write_text(
            'def test_refresh_token_expiration():\n    assert refresh_token(expired) is None\n')
        r = find_evidence('refresh token expiration', self.root)
        self.assertEqual(r['status'], 'EVIDENCE')
        self.assertEqual(r['matches'][0]['path'], 'tests/test_token.py')
        self.assertIn('assert refresh_token', r['matches'][0]['excerpt'])

    def test_private_grader_excluded(self):
        (self.root/'tests'/'test_token.py').write_text(
            'def test_refresh_token():\n    assert True\n')
        for d in (self.root/'private', self.root/'tests'/'grader'):
            d.mkdir(parents=True)
            (d/'test_token.py').write_text(
                'def test_refresh_token():\n    assert "LEAK_SECRET"\n')
        self.assertNotIn('LEAK_SECRET', str(find_evidence('refresh token', self.root)))

    def test_no_match_is_not_invented(self):
        (self.root/'src'/'app.py').write_text('def render_hello(): return "hello"\n')
        self.assertEqual(find_evidence('zabqv trrz', self.root)['status'], 'NO_MATCH')

    def test_arbitrary_repo_name(self):
        (self.root/'src'/'widgets.py').write_text(
            'def normalize_widget_color(color):\n'
            '    """Return default when widget color is missing"""\n'
            '    return color or "default"\n')
        r = find_evidence('widget color default', self.root)
        self.assertEqual(r['status'], 'EVIDENCE')
        self.assertEqual(r['matches'][0]['path'], 'src/widgets.py')

    def test_truncated_not_misreported_as_no_match(self):
        for i in range(5):
            (self.root/'src'/f'a{i}.py').write_text(
                'def ignore_me():\n    return True\n')
        r = find_evidence('refresh token', self.root, max_files=1)
        self.assertEqual(r['status'], 'TRUNCATED')

    def test_stable_results(self):
        (self.root/'tests'/'test_alpha.py').write_text(
            'def test_refresh_token():\n    assert refresh_token(None) is None\n')
        a = find_evidence('refresh token', self.root)
        self.assertEqual(a, find_evidence('refresh token', self.root))
        self.assertLessEqual(len(a['matches']), 4)


    def test_sensitive_filenames_fail_closed_even_at_workspace_root(self):
        # These are normal .py files, so excluding only directory names leaks them.
        (self.root/'hidden_test.py').write_text(
            'def refresh_token():\n    assert "LEAK_ROOT_HIDDEN"\n')
        (self.root/'grader_case.py').write_text(
            'def refresh_token():\n    assert "LEAK_ROOT_GRADER"\n')
        (self.root/'src'/'reference_fix.py').write_text(
            'def refresh_token():\n    assert "LEAK_NESTED_REFERENCE"\n')
        (self.root/'tests'/'private_case.py').write_text(
            'def refresh_token():\n    assert "LEAK_NESTED_PRIVATE"\n')
        (self.root/'tests'/'test_api.py').write_text(
            'def test_refresh_token():\n    assert refresh_token(None) is None\n')
        result = find_evidence('refresh token', self.root)
        paths = {r['path'] for r in result['matches']}
        self.assertEqual(result['status'], 'EVIDENCE')
        self.assertIn('tests/test_api.py', paths)
        self.assertFalse({'hidden_test.py', 'grader_case.py',
                          'src/reference_fix.py', 'tests/private_case.py'} & paths)
        self.assertNotIn('LEAK_', repr(result))

    def test_sensitive_directory_names_and_symlink_remain_excluded(self):
        (self.root/'src'/'grader_snapshots').mkdir()
        (self.root/'src'/'grader_snapshots'/'api.py').write_text(
            'def refresh_token():\n    assert "LEAK_DIR_GRADER"\n')
        (self.root/'src'/'secret_case').mkdir()
        (self.root/'src'/'secret_case'/'api.py').write_text(
            'def refresh_token():\n    assert "LEAK_DIR_SECRET"\n')
        (self.root/'tests'/'test_public.py').write_text(
            'def test_refresh_token():\n    assert refresh_token(None) is None\n')
        (self.root/'tests'/'hidden_link.py').symlink_to(
            self.root/'src'/'grader_snapshots'/'api.py')
        result = find_evidence('refresh token', self.root)
        self.assertEqual([x['path'] for x in result['matches']], ['tests/test_public.py'])
        self.assertNotIn('LEAK_', repr(result))


if __name__ == '__main__':
    unittest.main()
