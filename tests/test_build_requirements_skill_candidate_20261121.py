import unittest
from scripts.build_requirements_skill_candidate_20261121 import files_for_candidate

BASE = {
    'agent.yaml': 'agent_class: LlmAgent\nname: real_31b\nmodel: gemma-4-31b-it-qat-w4a16-ct\ninstruction: !include prompts/system.md\ntools:\n  - run_command\n  - submit_patch\ngenerate_content_config: !include configs/sampling.yaml\n',
    'prompts/system.md': 'Repair correctly.\n',
    'configs/sampling.yaml': 'temperature: 0.2\n',
    'eval_config.yaml': 'evaluation:\n  max_time_minutes: 5\n  max_tool_calls: 60\n  max_turns: 80\n',
}

class PackageTests(unittest.TestCase):
    def test_stages_single_skill_in_scored_31b(self):
        out = files_for_candidate(BASE)
        self.assertEqual(set(out)-set(BASE), {
            'skills/requirements-evidence/SKILL.md',
            'skills/requirements-evidence/scripts/requirements_evidence.py',
        })
        self.assertIn('skills/requirements-evidence',out['agent.yaml'])
        self.assertIn('run_skill_script',out['prompts/system.md'])
        self.assertIn('def find_evidence',out['skills/requirements-evidence/scripts/requirements_evidence.py'])

    def test_preserves_tools_sampling_and_budgets(self):
        out = files_for_candidate(BASE)
        self.assertEqual(out['configs/sampling.yaml'], BASE['configs/sampling.yaml'])
        self.assertEqual(out['eval_config.yaml'], BASE['eval_config.yaml'])
        self.assertEqual(out['agent.yaml'].split('tools:\n')[1], BASE['agent.yaml'].split('tools:\n')[1])

    def test_rejects_wrong_model(self):
        v=dict(BASE)
        v['agent.yaml']=v['agent.yaml'].replace('gemma-4-31b-it-qat-w4a16-ct','gemma-4-e4b-it-qat-w4a16-ct')
        with self.assertRaises(ValueError): files_for_candidate(v)

    def test_rejects_budget_drift_and_existing_skill(self):
        v=dict(BASE)
        v['eval_config.yaml']=v['eval_config.yaml'].replace('max_tool_calls: 60','max_tool_calls: 200')
        with self.assertRaises(ValueError): files_for_candidate(v)
        v=dict(BASE)
        v['agent.yaml'] += 'skills: [skills/other]\n'
        with self.assertRaises(ValueError): files_for_candidate(v)

if __name__ == '__main__':
    unittest.main()
