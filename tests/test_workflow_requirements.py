import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


PACKAGE = Path(__file__).resolve().parents[1]
SCRIPT = PACKAGE / 'skills/game-workflow-supervision/scripts/workflow_requirements.py'
spec = importlib.util.spec_from_file_location('workflow_requirements', SCRIPT)
requirements = importlib.util.module_from_spec(spec)
spec.loader.exec_module(requirements)


class RequirementsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write(self, relative, value):
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(value, ensure_ascii=False) if isinstance(value, dict) else value,
                          encoding='utf-8')

    def configured(self):
        requirements.initialize(self.root, 'sample-game')
        self.write('rules.md', '# Rules\nA source fixture, not a production approval.\n')
        self.write('game.lua', 'return { value = 1 }\n')
        self.write('planning/game-workflow-profile.md', '# Fixture project profile\n')
        config = requirements.read(self.root, requirements.SETTINGS)
        config['knowledge']['state'] = 'configured'
        config['knowledge']['sources'] = ['rules.md']
        self.write(requirements.SETTINGS, config)
        self.write(config['roadmapPath'], {
            'schemaVersion': 1, 'scopeRevision': 'scope-1', 'scopeState': 'known', 'items': [
                {'id': 'feature-1', 'title': 'A settled fixture feature',
                 'criteria': [{'id': 'C1', 'text': 'Returns the agreed value'}]}]})
        self.write(config['qualityPath'], {'schemaVersion': 1, 'primaryRuntime': 'fixture-lua', 'checks': {
            key: {'state': 'configured', 'owner': 'fixture-owner', 'reason': '',
                  'tool': 'fixture-tool', 'version': 'fixture-1', 'command': ['fixture-check', key],
                  'cwd': '.', 'sourcePaths': ['game.lua'], 'capabilities': [key],
                  'configurationPaths': [], 'supportEvidencePaths': ['rules.md'],
                  'runtime': 'fixture-lua'} for key in requirements.QUALITY}})
        return config

    def test_missing_setup_blocks_all_seven(self):
        result = requirements.inspect(self.root)
        self.assertFalse(result['setupReady'])
        self.assertEqual(set(requirements.FEATURES), {x['id'] for x in result['items']})
        self.assertTrue(all(x['required'] and x['state'] == 'blocked' for x in result['items']))

    def test_initialization_creates_pending_data_not_acceptance(self):
        result = requirements.initialize(self.root, 'sample-game')
        self.assertEqual(5, len(result['written']))
        self.assertFalse(result['readiness']['setupReady'])
        self.assertFalse(result['readiness']['checksExecuted'])

    def test_existing_settings_and_files_are_preserved(self):
        self.configured()
        before = {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        result = requirements.initialize(self.root, 'sample-game')
        self.assertEqual([], result['written'])
        self.assertEqual(before, {p: p.read_bytes() for p in before})
        self.assertIn('error', requirements.initialize(self.root, 'different-game'))

    def test_configured_setup_does_not_claim_checks_were_executed(self):
        self.configured()
        result = requirements.inspect(self.root)
        self.assertTrue(result['setupReady'])
        self.assertFalse(result['checksExecuted'])

    def test_disabled_knowledge_and_unknown_model_policy_block(self):
        config = self.configured()
        config['knowledge']['enabled'] = False
        config['models']['policy'] = 'skip'
        self.write(requirements.SETTINGS, config)
        result = requirements.inspect(self.root)
        self.assertFalse(result['setupReady'])
        self.assertEqual({'knowledge', 'models'}, {x['id'] for x in result['items'] if x['state'] == 'blocked'})

    def test_unknown_scope_keeps_overall_progress_unknown_even_with_partial_items(self):
        config = self.configured()
        roadmap = requirements.read(self.root, config['roadmapPath'])
        roadmap.update(scopeState='unknown', reason='Only this feature is settled')
        self.write(config['roadmapPath'], roadmap)
        overall = requirements.inspect(self.root)
        scoped = requirements.inspect(self.root, scope_item='feature-1')
        self.assertFalse(overall['setupReady'])
        self.assertTrue(scoped['setupReady'])
        self.assertFalse(scoped['overallProgressReady'])
        self.assertFalse(requirements.inspect(self.root, scope_item='missing')['setupReady'])

    def test_each_unconfigured_quality_feature_blocks(self):
        config = self.configured()
        baseline = requirements.read(self.root, config['qualityPath'])
        for key in requirements.QUALITY:
            for state in ('pending', 'unsupported', 'unknown', 'not-applicable'):
                with self.subTest(key=key, state=state):
                    value = json.loads(json.dumps(baseline))
                    value['checks'][key].update(state=state, reason='Not connected')
                    self.write(config['qualityPath'], value)
                    self.assertFalse(requirements.inspect(self.root)['setupReady'])

    def test_syntax_cannot_replace_analysis_or_lint(self):
        config = self.configured()
        value = requirements.read(self.root, config['qualityPath'])
        for key in ('lint', 'analysis'):
            value['checks'][key]['capabilities'] = ['syntax']
        self.write(config['qualityPath'], value)
        self.assertFalse(requirements.inspect(self.root)['setupReady'])

    def test_reference_coverage_cannot_replace_primary_game_coverage(self):
        config = self.configured()
        value = requirements.read(self.root, config['qualityPath'])
        value['checks']['coverage']['runtime'] = 'reference-js'
        self.write(config['qualityPath'], value)
        self.assertFalse(requirements.inspect(self.root)['setupReady'])

    def test_false_required_switch_and_malformed_schema_cannot_bypass(self):
        config = self.configured()
        config['required'] = False
        self.write(requirements.SETTINGS, config)
        self.assertFalse(requirements.inspect(self.root)['setupReady'])
        del config['required']
        config['schemaVersion'] = True
        self.write(requirements.SETTINGS, config)
        self.assertFalse(requirements.inspect(self.root)['setupReady'])

    def test_external_missing_and_directory_sources_block(self):
        config = self.configured()
        for source in ('../outside.md', 'C:/outside.md', 'missing.md', 'planning'):
            with self.subTest(source=source):
                config['knowledge']['sources'] = [source]
                self.write(requirements.SETTINGS, config)
                self.assertFalse(requirements.inspect(self.root)['setupReady'])

    def test_installed_cli_uses_owning_project_from_another_cwd(self):
        target = self.root / '.agents/skills/game-workflow-supervision/scripts'
        target.mkdir(parents=True)
        for name in ('workflow_requirements.py', 'dashboard.py', 'resolve_model_route.py'):
            shutil.copyfile(SCRIPT.with_name(name), target / name)
        result = subprocess.run([sys.executable, '-B', '-X', 'utf8', str(target / SCRIPT.name),
                                 'init', '--name', 'sample-game'], cwd=self.root.parent,
                                capture_output=True, text=True, encoding='utf-8', timeout=20)
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertTrue((self.root / requirements.SETTINGS).is_file())
        self.assertFalse(json.loads(result.stdout)['readiness']['setupReady'])

    def test_existing_custom_manifest_is_reused(self):
        config = self.configured()
        self.write('planning/custom-required.json', config)
        before = (self.root / 'planning/custom-required.json').read_bytes()
        self.assertTrue(requirements.inspect(self.root, settings='planning/custom-required.json')['setupReady'])
        result = requirements.initialize(self.root, 'sample-game', settings='planning/custom-required.json')
        self.assertEqual([], result['written'])
        self.assertEqual(before, (self.root / 'planning/custom-required.json').read_bytes())

    def test_partial_initialization_reports_actual_saved_files(self):
        config = {'schemaVersion': 1, 'projectName': 'sample-game', 'profilePath': 'planning/profile.md',
                  'knowledge': {'enabled': True, 'state': 'pending', 'owner': 'fixture-owner', 'reason': 'Setup',
                                'indexPath': 'sample-game-wiki/index.md', 'policyPath': 'sample-game-wiki/policy.md', 'sources': []},
                  'models': {'policy': 'capability-tier', 'profilePath': None},
                  'roadmapPath': 'planning/roadmap.json', 'qualityPath': '../outside.json'}
        self.write(requirements.SETTINGS, config)
        result = requirements.initialize(self.root, 'sample-game')
        self.assertIn('error', result)
        self.assertEqual(3, len(result['written']))
        self.assertTrue(all((self.root / name).is_file() for name in result['written']))
        self.assertFalse(result['readiness']['setupReady'])

    def test_repeated_input_change_is_not_ready(self):
        self.configured()
        original = requirements._inspect
        calls = []

        def change_after_read(*args, **kwargs):
            result = original(*args, **kwargs)
            target = self.root / 'rules.md'
            target.write_text(target.read_text(encoding='utf-8') + 'changed\n', encoding='utf-8')
            calls.append(True)
            return result

        with patch.object(requirements, '_inspect', change_after_read):
            result = requirements.inspect(self.root)
        self.assertEqual(2, len(calls))
        self.assertFalse(result['setupReady'])
        self.assertEqual('configuration-changed', result['observation'])

    def test_malformed_existing_manifest_returns_structured_failure_without_writes(self):
        for value in ([], None, 'invalid', 7, True, {}, {'schemaVersion': True}):
            with self.subTest(value=value):
                target = self.root / requirements.SETTINGS
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(json.dumps(value), encoding='utf-8')
                before = target.read_bytes()
                result = requirements.initialize(self.root, 'sample-game')
                self.assertIn('error', result)
                self.assertEqual([], result['written'])
                self.assertEqual([requirements.SETTINGS], result['preserved'])
                self.assertFalse(result['readiness']['setupReady'])
                self.assertEqual(7, len(result['readiness']['items']))
                self.assertEqual(before, target.read_bytes())
                self.assertEqual([target], [p for p in self.root.rglob('*') if p.is_file()])


if __name__ == '__main__':
    unittest.main()
