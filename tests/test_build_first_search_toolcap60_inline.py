"""CPU acceptance tests for native run_command retrieval candidate (not 31B scorer)."""
import unittest
import tempfile
import subprocess
from pathlib import Path
from scripts.build_first_search_toolcap60_inline import make_command, candidate_files

class TestInlineFirstSearch(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory()
        self.root = Path(self.d.name)
        (self.root / 'fastapi').mkdir()

    def tearDown(self):
        self.d.cleanup()

    def run_q(self, q):
        return subprocess.run(
            ['bash', '-lc', make_command(q)], cwd=self.root,
            text=True, capture_output=True, timeout=12, check=True
        ).stdout

    def test_exact_native_command_returns_production_function(self):
        (self.root/'fastapi'/'auth.py').write_text('def refresh_token(x):\n    return x\n')
        self.assertIn('"symbol": "refresh_token"', self.run_q('refresh_token'))

    def test_does_not_export_test_or_outside_roots(self):
        (self.root/'tests').mkdir()
        (self.root/'tests'/'secret.py').write_text(
            'def refresh_token():\n    return "SENSITIVE_SENTINEL"\n')
        (self.root/'fastapi'/'tests').mkdir()
        (self.root/'fastapi'/'tests'/'secret.py').write_text(
            'def refresh_token():\n    return "SENSITIVE_SENTINEL"\n')
        (self.root/'outside.py').write_text(
            'def refresh_token():\n    return "SENSITIVE_SENTINEL"\n')
        self.assertNotIn('SENSITIVE_SENTINEL', self.run_q('refresh_token'))

    def test_finds_late_symbol_after_first_160_lines(self):
        (self.root/'fastapi'/'late.py').write_text(
            '# header\n'*175+'def refresh_token():\n    return 1\n')
        self.assertIn('"symbol": "refresh_token"', self.run_q('refresh_token'))

    def test_truncation_must_not_be_reported_as_no_match(self):
        for i in range(320):
            (self.root/'fastapi'/f'a{i:04}.py').write_text('def irrelevant(): return 1\n')
        (self.root/'fastapi'/'z_auth.py').write_text('def refresh_token(): return 1\n')
        self.assertIn('FIRST_SEARCH_STATUS=TRUNCATED', self.run_q('refresh_token'))

    def test_rejects_shell_metacharacters(self):
        with self.assertRaises(ValueError):
            make_command('$(touch /tmp/evil)')

    def test_only_prompt_differs_from_control(self):
        original={
            'agent.yaml':'model: gemma-4-31b-it-qat-w4a16-ct\ntools:\n  - run_command\n  - submit_patch\n',
            'eval_config.yaml':'evaluation:\n  max_time_minutes: 5\n  max_tool_calls: 60\n  max_turns: 80\n',
            'configs/sampling.yaml':'temperature: 0.5',
            'prompts/system.md':'Fix the issue carefully.'
        }
        altered=candidate_files(original)
        self.assertEqual(
            {k for k in original if original[k]!=altered[k]},
            {'prompts/system.md'}
        )
        self.assertIn('SWE_QUERY=',altered['prompts/system.md'])

if __name__=='__main__':
    unittest.main()
