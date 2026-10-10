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
        for name in ('workflow_requirements.py', 'dashboard.py', 'resolve_model_route.py', 'workflow_state.py'):
            shutil.copyfile(SCRIPT.with_name(name), target / name)
        asset = target.parent / 'references/model-routing-defaults.json'
        asset.parent.mkdir()
        small = self.root / '.agents/skills/game-task-planning/references/small-change.md'
        small.parent.mkdir(parents=True)
        shutil.copyfile(PACKAGE / 'skills/game-task-planning/references/small-change.md', small)
        shutil.copyfile(SCRIPT.parent.parent / 'references/model-routing-defaults.json', asset)
        result = subprocess.run([sys.executable, '-B', '-X', 'utf8', str(target / SCRIPT.name),
                                 'init', '--name', 'sample-game'], cwd=self.root.parent,
                                capture_output=True, text=True, encoding='utf-8', timeout=20)
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertTrue((self.root / requirements.SETTINGS).is_file())
        self.assertFalse(json.loads(result.stdout)['readiness']['setupReady'])

    def test_common_profile_is_observed_and_fingerprinted(self):
        self.configured()
        result = requirements.inspect(self.root)
        row = next(x for x in result['items'] if x['id'] == 'models')
        self.assertEqual('common-profile', row['policySource'])
        self.assertIn(requirements.BUNDLED_MODELS, result['sources'])
        self.assertEqual(64, len(result['sources'][requirements.BUNDLED_MODELS]))

    def test_legacy_explicit_profile_observes_common_table_as_well(self):
        config = self.configured()
        config['models']['profilePath'] = 'planning/models.json'
        self.write(requirements.SETTINGS, config)
        self.write('planning/models.json', json.loads((PACKAGE / 'tests/fixtures/model-routing-profile.json').read_text(encoding='utf-8')))
        result = requirements.inspect(self.root)
        self.assertTrue(result['setupReady'])
        self.assertIn('planning/models.json', result['sources'])
        self.assertIn(requirements.BUNDLED_MODELS, result['sources'])
        row = next(x for x in result['items'] if x['id'] == 'models')
        self.assertEqual('portable-test-fixture', row['profileRevision'])

    def test_full_custom_profile_does_not_require_unused_common_asset(self):
        config = self.configured()
        config['models']['profilePath'] = 'planning/models.json'
        self.write(requirements.SETTINGS, config)
        self.write('planning/models.json', requirements.sibling('resolve_model_route').load_profile())
        result = requirements.inspect(self.root)
        self.assertTrue(result['setupReady'])
        self.assertNotIn(requirements.BUNDLED_MODELS, result['sources'])

    def bundled_fixture(self):
        router = requirements.sibling('resolve_model_route')
        target = self.root / 'fixture-common.json'
        shutil.copyfile(router.common_profile_path(), target)
        original = requirements.sibling
        router.common_profile_path = lambda: target
        return target, lambda name: router if name == 'resolve_model_route' else original(name)

    def test_missing_and_malformed_bundled_asset_block_model_preparation(self):
        self.configured()
        target, modules = self.bundled_fixture()
        for value in (None, '{broken', json.dumps({'schemaVersion': 1, 'revision': 'bad', 'tiers': {}})):
            if value is None:
                target.unlink(missing_ok=True)
            else:
                target.write_text(value, encoding='utf-8')
            with patch.object(requirements, 'sibling', side_effect=modules):
                result = requirements.inspect(self.root)
            row = next(x for x in result['items'] if x['id'] == 'models')
            self.assertEqual('blocked', row['state'])
            self.assertFalse(result['setupReady'])

    def test_changed_bundled_asset_retries_then_blocks(self):
        self.configured()
        target, modules = self.bundled_fixture()
        original = requirements._inspect

        def change_after_read(*args, **kwargs):
            result = original(*args, **kwargs)
            value = json.loads(target.read_text(encoding='utf-8'))
            value['revision'] += '-changed'
            target.write_text(json.dumps(value), encoding='utf-8')
            return result

        with patch.object(requirements, 'sibling', side_effect=modules), patch.object(requirements, '_inspect', side_effect=change_after_read):
            result = requirements.inspect(self.root)
        self.assertEqual('configuration-changed', result['observation'])
        self.assertFalse(result['setupReady'])
        self.assertIn('fixture-common.json', result['changedSources'])

    def test_installed_cli_check_records_installed_asset_and_fails_if_missing(self):
        self.configured()
        target = self.root / '.agents/skills/game-workflow-supervision/scripts'
        target.mkdir(parents=True)
        for name in ('workflow_requirements.py', 'dashboard.py', 'resolve_model_route.py', 'workflow_state.py'):
            shutil.copyfile(SCRIPT.with_name(name), target / name)
        asset = target.parent / 'references/model-routing-defaults.json'
        asset.parent.mkdir()
        small = self.root / '.agents/skills/game-task-planning/references/small-change.md'
        small.parent.mkdir(parents=True)
        shutil.copyfile(PACKAGE / 'skills/game-task-planning/references/small-change.md', small)
        shutil.copyfile(SCRIPT.parent.parent / 'references/model-routing-defaults.json', asset)
        command = [sys.executable, '-B', '-X', 'utf8', str(target / SCRIPT.name), 'check']
        result = subprocess.run(command, cwd=self.root.parent, capture_output=True, text=True, encoding='utf-8', timeout=20)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn('.agents/skills/game-workflow-supervision/references/model-routing-defaults.json', json.loads(result.stdout)['sources'])
        config = requirements.read(self.root, requirements.SETTINGS)
        self.write('planning/cli custom.json', config)
        self.write(requirements.PROFILE, '| workflow.requirementsPath | planning/cli custom.json |\n')
        result = subprocess.run(command, cwd=self.root.parent, capture_output=True, text=True, encoding='utf-8', timeout=20)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual('planning/cli custom.json', json.loads(result.stdout)['settingsPath'])
        spaced_explicit = [*command[:-1], '--settings', 'planning/cli custom.json', 'check']
        result = subprocess.run(spaced_explicit, cwd=self.root.parent, capture_output=True, text=True, encoding='utf-8', timeout=20)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual('planning/cli custom.json', json.loads(result.stdout)['settingsPath'])
        self.assertEqual('explicit-settings', json.loads(result.stdout)['resolutionSource'])
        explicit = [*command[:-1], '--settings', requirements.SETTINGS, 'check']
        result = subprocess.run(explicit, cwd=self.root.parent, capture_output=True, text=True, encoding='utf-8', timeout=20)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual('explicit-settings', json.loads(result.stdout)['resolutionSource'])
        asset.unlink()
        result = subprocess.run(command, cwd=self.root.parent, capture_output=True, text=True, encoding='utf-8', timeout=20)
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertFalse(json.loads(result.stdout)['setupReady'])

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

    def test_profile_selects_manifest_and_explicit_settings_preserves_provenance(self):
        config = self.configured()
        self.write('planning/custom.json', config)
        self.write(requirements.PROFILE, '| `workflow.requirementsPath` | `planning/custom.json` |\n')
        result = requirements.inspect(self.root)
        self.assertTrue(result['setupReady'])
        self.assertEqual('planning/custom.json', result['settingsPath'])
        self.assertEqual('project-profile', result['resolutionSource'])
        self.assertIn(requirements.PROFILE, result['sources'])
        self.assertIn(requirements.PROFILE, requirements.resolve_settings(self.root)['sources'])
        explicit = requirements.inspect(self.root, settings=requirements.SETTINGS)
        self.assertEqual('explicit-settings', explicit['resolutionSource'])
        self.assertEqual('planning/custom.json', explicit['provenance']['profileRequirementsPath'])

    def test_invalid_selected_rows_never_fall_back(self):
        self.configured()
        for row in ('| workflow.requirementsPath | |', '| workflow.requirementsPath | [path](planning/workflow-requirements.json) |',
                    '| workflow.requirementsPath | planning/missing.json |', '| workflow.requirementsPath | TODO |',
                    '| workflow.requirementsPath | ../outside.json |',
                    '| workflow.requirementsPath | planning/workflow-requirements.json |\n| workflow.requirementsPath | planning/other.json |'):
            with self.subTest(row=row):
                self.write(requirements.PROFILE, row)
                result = requirements.inspect(self.root)
                self.assertFalse(result['setupReady'])
                self.assertTrue(all(x['state'] == 'blocked' for x in result['items']))
        self.write(requirements.PROFILE, '```markdown\n| workflow.requirementsPath | missing.json |\n```\n')
        self.assertTrue(requirements.inspect(self.root)['setupReady'])

    def test_profile_auto_selects_existing_manifest_with_internal_filename_space(self):
        config = self.configured()
        selected = 'planning/custom settings.json'
        self.write(selected, config)
        self.write(requirements.PROFILE, f'| workflow.requirementsPath | `{selected}` |\n')
        before = (self.root / selected).read_bytes()
        result = requirements.inspect(self.root)
        self.assertTrue(result['setupReady'])
        self.assertEqual(selected, result['settingsPath'])
        self.assertEqual('project-profile', result['resolutionSource'])
        self.assertIn(selected, result['sources'])
        initialized = requirements.initialize(self.root, 'sample-game')
        self.assertEqual([], initialized['written'])
        self.assertEqual(before, (self.root / selected).read_bytes())

    def test_custom_profile_discovery_and_live_mismatch(self):
        config = self.configured()
        (self.root / requirements.PROFILE).unlink()
        config['profilePath'] = 'planning/custom-profile.md'
        self.write(requirements.SETTINGS, config)
        self.write(config['profilePath'], '# Custom profile\n')
        self.assertEqual(config['profilePath'], requirements.inspect(self.root)['profilePath'])
        self.assertTrue(requirements.inspect(self.root, profile=config['profilePath'])['setupReady'])
        self.write(requirements.PROFILE, '# Another live profile\n')
        self.assertFalse(requirements.inspect(self.root)['setupReady'])
        self.assertFalse(requirements.inspect(self.root, profile='missing.md')['setupReady'])

    def test_init_uses_only_selected_missing_manifest_and_actual_profile(self):
        self.write('planning/custom-profile.md', '| workflow.requirementsPath | planning/custom.json |\n')
        result = requirements.initialize(self.root, 'sample-game', profile='planning/custom-profile.md')
        self.assertNotIn('error', result)
        self.assertEqual('planning/custom-profile.md', requirements.read(self.root, 'planning/custom.json')['profilePath'])
        self.assertFalse((self.root / requirements.SETTINGS).exists())
        self.assertFalse(result['readiness']['setupReady'])
        self.assertEqual('project-profile', result['readiness']['resolutionSource'])

    def test_defaults_and_exact_project_overrides(self):
        self.configured()
        defaults = requirements.inspect(self.root)['workflowDefaults']
        self.assertEqual(requirements.BUNDLED_SMALL, defaults['smallChangePolicy']['path'])
        self.assertTrue(all(x['available'] and x['source'] == 'bundled-default' for x in defaults.values()))
        self.write('policy.md', '# Project limits\n')
        self.write('state-tool.py', '# Project adapter\n')
        self.write(requirements.PROFILE, '| workflow.smallChangePolicyPath | policy.md |\n| workflow.stateToolPath | state-tool.py |\n')
        result = requirements.inspect(self.root)
        self.assertTrue(result['setupReady'])
        self.assertEqual('policy.md', result['workflowDefaults']['smallChangePolicy']['path'])
        (self.root / 'state-tool.py').unlink()
        result = requirements.inspect(self.root)
        self.assertFalse(result['setupReady'])
        self.assertTrue(all(x['state'] == 'configured' for x in result['items']))
        self.assertFalse(result['workflowDefaults']['stateTool']['available'])

    def test_profile_change_retries_and_blocks(self):
        self.configured()
        original = requirements._inspect
        def change(*args, **kwargs):
            result = original(*args, **kwargs)
            target = self.root / requirements.PROFILE
            target.write_text(target.read_text(encoding='utf-8') + '\nChanged\n', encoding='utf-8')
            return result
        with patch.object(requirements, '_inspect', side_effect=change):
            result = requirements.inspect(self.root)
        self.assertEqual('configuration-changed', result['observation'])
        self.assertIn(requirements.PROFILE, result['changedSources'])

    def test_selected_consumer_creates_new_json_run_and_preserves_markdown_source(self):
        from test_workflow_state import StateTests
        fixture = StateTests()
        fixture.setUp()
        self.addCleanup(lambda: shutil.rmtree(fixture.root))
        profile = fixture.root / requirements.PROFILE
        profile.parent.mkdir(parents=True, exist_ok=True)
        profile.write_text('# Consumer fixture\n', encoding='utf-8')
        requirements.initialize(fixture.root, 'fixture-game')
        for name in ('workflow_requirements.py', 'resolve_model_route.py'):
            shutil.copyfile(SCRIPT.with_name(name), fixture.scripts / name)
        asset = fixture.scripts.parent / 'references/model-routing-defaults.json'
        asset.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(SCRIPT.parent.parent / 'references/model-routing-defaults.json', asset)
        installed = fixture.import_file(fixture.scripts / 'workflow_requirements.py', 'selected_requirements_consumer')
        small = fixture.root / '.agents/skills/game-task-planning/references/small-change.md'
        small.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(PACKAGE / 'skills/game-task-planning/references/small-change.md', small)
        old = fixture.root / 'planning/workflow-runs/old/checkpoint.md'
        old.parent.mkdir(parents=True)
        old.write_bytes(b'# Existing Markdown source\n')
        before = old.read_bytes()
        selection = installed.inspect(fixture.root)['workflowDefaults']['stateTool']
        # This is the same exact selected tool locator passed to the supervisor's dispatch.
        self.assertTrue(selection['available'])
        selected = requirements.path(fixture.root, selection['path'])
        tool = fixture.import_file(selected, 'selected_state_consumer')
        result = tool.init(fixture.root, fixture.initial())
        self.assertTrue(result['stateSaved'])
        self.assertTrue((fixture.root / tool.state_relative('fixture-run')).is_file())
        self.assertEqual(before, old.read_bytes())


if __name__ == '__main__':
    unittest.main()
