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


if __name__ == '__main__':
    unittest.main()
