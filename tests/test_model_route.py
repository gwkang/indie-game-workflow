import importlib.util
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


PACKAGE = Path(__file__).resolve().parents[1]
MODULE = PACKAGE / "skills/game-workflow-supervision/scripts/resolve_model_route.py"
PROFILE = Path(__file__).resolve().parent / "fixtures/model-routing-profile.json"
spec = importlib.util.spec_from_file_location("resolve_model_route", MODULE)
router = importlib.util.module_from_spec(spec)
spec.loader.exec_module(router)


class ModelRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = router.load_profile(PROFILE)
        cls.available = ["model-judgment", "model-complex", "model-balanced", "model-volume"]

    def test_each_tier_resolves_to_project_preference(self):
        expected = {
            "highest-judgment": ("model-judgment", "high"),
            "complex-execution": ("model-complex", "high"),
            "balanced-execution": ("model-balanced", "medium"),
            "high-volume": ("model-volume", "low"),
        }
        for tier, (model, effort) in expected.items():
            with self.subTest(tier=tier):
                result = router.resolve(self.profile, tier, self.available, True)
                self.assertEqual("override", result["decision"])
                self.assertEqual(model, result["resolvedModel"])
                self.assertEqual(effort, result["reasoningClass"])

    def test_missing_preferred_model_uses_declared_fallback(self):
        result = router.resolve(self.profile, "balanced-execution", ["model-complex"], True)
        self.assertEqual("model-complex", result["resolvedModel"])
        self.assertEqual("preferred-model-unavailable", result["fallbackReason"])

    def test_no_available_candidate_preserves_host_default(self):
        result = router.resolve(self.profile, "high-volume", ["unmapped-model"], True)
        self.assertEqual("host-default", result["decision"])
        self.assertEqual("no-tier-candidate-available", result["fallbackReason"])

    def test_unsupported_override_preserves_host_default(self):
        result = router.resolve(self.profile, "highest-judgment", self.available, False)
        self.assertEqual("host-default", result["decision"])
        self.assertEqual("model-override-unsupported", result["fallbackReason"])

    def test_explicit_unavailable_model_blocks_dispatch(self):
        result = router.resolve(self.profile, "balanced-execution", self.available, True, "requested-model")
        self.assertEqual("blocked", result["decision"])
        self.assertEqual("explicit-model-unavailable", result["fallbackReason"])

    def test_available_explicit_model_is_preserved(self):
        result = router.resolve(self.profile, "high-volume", self.available, True, "model-complex")
        self.assertEqual("override", result["decision"])
        self.assertEqual("model-complex", result["resolvedModel"])
        self.assertEqual("explicit-user", result["resolutionSource"])
        self.assertIsNone(result["reasoningClass"])

    def test_explicit_model_blocks_when_override_is_unsupported(self):
        result = router.resolve(self.profile, "balanced-execution", self.available, False, "model-balanced")
        self.assertEqual("blocked", result["decision"])
        self.assertEqual("explicit-model-override-unsupported", result["fallbackReason"])
        self.assertEqual("explicit-user", result["resolutionSource"])

    def test_common_policy_without_profile_is_strict(self):
        for tier in router.TIERS:
            result = router.resolve(None, tier, [], False)
            self.assertEqual('blocked', result['decision'])
            self.assertIsNone(result['resolvedModel'])
            self.assertEqual('model-override-unsupported', result['fallbackReason'])

    def test_explicit_model_still_blocks_or_overrides_without_profile(self):
        self.assertEqual('blocked', router.resolve(None, 'high-volume', [], True, 'requested')['decision'])
        self.assertEqual('override', router.resolve(None, 'high-volume', ['requested'], True, 'requested')['decision'])

    def test_unknown_tier_is_rejected(self):
        with self.assertRaises(router.ProfileError):
            router.resolve(None, 'skip', [], False)

    def task(self, **kwargs):
        inputs = {'skill': 'game-technical-design', 'override_supported': True,
                  'host_support': {'gpt-6-astra': ['high', 'medium', 'low'],
                                   'gpt-6.1-sol': ['high', 'medium', 'low'],
                                   'gpt-6-luna': ['high', 'medium', 'low']}}
        inputs.update(kwargs)
        return router.resolve_task(**inputs)

    def test_common_table_matches_all_actual_bundled_skills(self):
        skills = {p.parent.name for p in (PACKAGE / 'skills').glob('*/SKILL.md')}
        self.assertEqual(39, len(skills))
        self.assertEqual(skills, set(router.load_profile()['skillTiers']))

    def test_common_design_implementation_and_repeat_task_spawn_arguments(self):
        cases = [({'skill': 'game-technical-design'}, 'gpt-6-astra', 'high'),
                 ({'skill': 'game-rule-implementation'}, 'gpt-6.1-sol', 'high'),
                 ({'skill': 'game-workflow', 'tier': 'high-volume',
                   'tier_reason': 'Extract fixed manifest IDs only'}, 'gpt-6-luna', 'low')]
        for inputs, model, effort in cases:
            with self.subTest(inputs=inputs):
                result = self.task(**inputs)
                self.assertEqual({'model': model, 'reasoning_effort': effort, 'fork_turns': 'none'}, result['spawnArgs'])
                self.assertTrue(result['hostSupportConfirmed'])

    def test_task_override_and_external_skill_require_reason(self):
        for inputs in ({'tier': 'high-volume'}, {'skill': 'external'},
                       {'skill': 'external', 'tier': 'balanced-execution'}):
            with self.subTest(inputs=inputs), self.assertRaises(router.ProfileError):
                self.task(**inputs)
        result = self.task(skill='external', tier='balanced-execution', tier_reason='Settled external task')
        self.assertIsNone(result['defaultTier'])
        self.assertEqual('balanced-execution', result['capabilityTier'])

    def test_common_allowed_fallback_and_ineligible_host(self):
        result = self.task(host_support={'gpt-6.1-sol': ['high']})
        self.assertEqual('gpt-6.1-sol', result['spawnArgs']['model'])
        self.assertEqual('preferred-model-unavailable', result['fallbackReason'])
        for support in ({}, {'gpt-6-luna': ['high']}):
            result = self.task(host_support=support)
            self.assertEqual('blocked', result['decision'])
            self.assertIsNone(result['spawnArgs'])

    def test_candidate_must_support_requested_effort(self):
        result = self.task(host_support={'gpt-6-astra': ['low'], 'gpt-6.1-sol': ['high']})
        self.assertEqual('gpt-6.1-sol', result['spawnArgs']['model'])
        self.assertEqual('preferred-model-effort-unsupported', result['fallbackReason'])
        result = self.task(host_support={'gpt-6-astra': ['low']})
        self.assertEqual('blocked', result['decision'])
        self.assertIsNone(result['spawnArgs'])

    def test_explicit_model_effort_preserved_or_blocked(self):
        result = self.task(explicit_model='older-user-choice', explicit_effort='xhigh',
                           host_support={'older-user-choice': ['xhigh']})
        self.assertEqual({'model': 'older-user-choice', 'reasoning_effort': 'xhigh', 'fork_turns': 'none'}, result['spawnArgs'])
        for inputs in ({'explicit_effort': 'xhigh'}, {'explicit_model': 'missing'},
                       {'explicit_model': 'gpt-6-astra', 'explicit_effort': 'xhigh'},
                       {'explicit_model': 'gpt-6-astra', 'override_supported': False}):
            result = self.task(**inputs)
            self.assertEqual('blocked', result['decision'])
            self.assertIsNone(result['spawnArgs'])

    def test_legacy_profile_inherits_common_skill_table_but_keeps_model_order(self):
        result = self.task(profile=self.profile, host_support={'model-judgment': ['high']})
        self.assertEqual('model-judgment', result['spawnArgs']['model'])
        self.assertEqual('highest-judgment', result['defaultTier'])
        result = self.task(profile=self.profile, host_support={})
        self.assertEqual('host-default', result['decision'])
        self.assertIsNone(result['spawnArgs'])

    def test_legacy_extra_metadata_is_preserved_without_changing_selection(self):
        data = copy.deepcopy(self.profile)
        data.update(description='Legacy project mapping', owner='fixture-owner')
        parsed = router.parse_profile(json.dumps(data))
        self.assertEqual('Legacy project mapping', parsed['description'])
        self.assertEqual('fixture-owner', parsed['owner'])
        for tier in router.TIERS:
            self.assertEqual(router.resolve(self.profile, tier, self.available, True),
                             router.resolve(parsed, tier, self.available, True))
        parsed['onUnavailable'] = 'silent'
        with self.assertRaises(router.ProfileError):
            router.validate_profile(parsed)

    def test_common_asset_still_rejects_extra_metadata_keys(self):
        data = router.load_profile()
        data['description'] = 'Unexpected bundled metadata'
        with self.assertRaises(router.ProfileError):
            router.validate_common_profile(data)

    def test_malformed_profiles_are_rejected_structurally(self):
        common = router.load_profile()
        mutations = [('schemaVersion', True), ('revision', ' '), ('tiers', []),
                     ('onUnavailable', []), ('onUnsupportedOverride', 'silent'), ('skillTiers', {})]
        for key, value in mutations:
            bad = copy.deepcopy(common)
            bad[key] = value
            with self.subTest(key=key), self.assertRaises(router.ProfileError):
                router.validate_profile(bad)
        for key, value in [('preferredModels', [{}]), ('reasoningEffort', [])]:
            bad = copy.deepcopy(common)
            bad['tiers']['high-volume'][key] = value
            with self.subTest(key=key), self.assertRaises(router.ProfileError):
                router.validate_profile(bad)
        with self.assertRaises(router.ProfileError):
            router.parse_profile('{"schemaVersion":1,"schemaVersion":1}')

    def test_missing_or_noncommon_default_asset_is_not_silent_fallback(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / 'default.json'
            with patch.object(router, 'common_profile_path', return_value=target):
                with self.assertRaises(OSError):
                    self.task()
                target.write_text(json.dumps(self.profile), encoding='utf-8')
                with self.assertRaises(router.ProfileError):
                    self.task()
                target.write_text('{broken', encoding='utf-8')
                with self.assertRaises(ValueError):
                    self.task()

    def test_host_metadata_types_are_checked(self):
        for support in ([], {'model': 'high'}, {'model': []}, {'model': ['high', 'high']}):
            with self.subTest(support=support), self.assertRaises(router.ProfileError):
                self.task(host_support=support)

    def test_relocated_cli_loads_relative_asset_and_reports_negative_exits(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            script = root / 'skills/game-workflow-supervision/scripts/resolve_model_route.py'
            script.parent.mkdir(parents=True)
            shutil.copyfile(MODULE, script)
            asset = script.parent.parent / 'references/model-routing-defaults.json'
            asset.parent.mkdir()
            shutil.copyfile(router.common_profile_path(), asset)
            support = root / 'host.json'
            support.write_text(json.dumps({'gpt-6-astra': ['high']}), encoding='utf-8')
            command = [sys.executable, '-B', '-X', 'utf8', str(script), '--skill', 'game-technical-design',
                       '--host-support', str(support), '--override-supported']
            result = subprocess.run(command, cwd=root.parent, capture_output=True, text=True, encoding='utf-8', timeout=20)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual('gpt-6-astra', json.loads(result.stdout)['spawnArgs']['model'])
            result = subprocess.run(command + ['--explicit-effort', 'xhigh'], capture_output=True, text=True, timeout=20)
            self.assertEqual(2, result.returncode, result.stderr)
            self.assertIsNone(json.loads(result.stdout)['spawnArgs'])
            asset.unlink()
            result = subprocess.run(command, capture_output=True, text=True, timeout=20)
            self.assertEqual(1, result.returncode)


if __name__ == "__main__":
    unittest.main()
