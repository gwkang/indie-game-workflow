import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

MODULE = Path(__file__).resolve().parents[1] / 'tools/install_bundle.py'
spec = importlib.util.spec_from_file_location('installer', MODULE)
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / 'bundle'
        self.target = self.base / 'target'
        self.target.mkdir()
        entries = []
        for name in ('core-one', 'core-two'):
            source = self.root / 'skills' / name
            source.mkdir(parents=True)
            (source / 'SKILL.md').write_text(name)
            (source / 'references').mkdir()
            (source / 'references/contract.md').write_text('required reference')
            entries.append({'id': name, 'source': f'skills/{name}',
                            'files': installer.inventory(source)})
        self.lock = {'lockVersion': 1, 'bundleVersion': 'test', 'entries': entries}
        self.write_lock()

    def write_lock(self):
        (self.root / 'bundle.lock.json').write_text(json.dumps(self.lock))

    def test_preview_has_no_side_effect(self):
        result = installer.install(self.root, self.target)
        self.assertEqual('preview', result['status'])
        self.assertEqual([], list(self.target.iterdir()))

    def test_install_and_repeat_reuse_whole_tree(self):
        result = installer.install(self.root, self.target, True)
        self.assertEqual('files-ready-activation-pending', result['status'])
        self.assertEqual('not-verified', result['runtimeDiscovery'])
        result = installer.install(self.root, self.target, True)
        self.assertEqual([], result['install'])
        self.assertEqual(['core-one', 'core-two'], result['reused'])
        self.assertEqual(2, len(list(self.target.iterdir())))

    def test_modified_reference_blocks_before_any_write(self):
        destination = self.target / 'core-two'
        destination.mkdir()
        (destination / 'custom.txt').write_text('user owned')
        with self.assertRaises(installer.InstallError):
            installer.install(self.root, self.target, True)
        self.assertFalse((self.target / 'core-one').exists())
        self.assertEqual('user owned', (destination / 'custom.txt').read_text())

    def test_source_reference_tamper_rejected(self):
        (self.root / 'skills/core-one/references/contract.md').write_text('changed')
        with self.assertRaises(installer.InstallError):
            installer.install(self.root, self.target, True)
        self.assertEqual([], list(self.target.iterdir()))

    def test_partial_commit_failure_rolls_back_owned_only(self):
        user = self.target / 'unrelated'
        user.mkdir()
        (user / 'file').write_text('keep')
        calls = []
        def mover(source, destination):
            calls.append(source)
            if len(calls) == 2:
                raise OSError('simulated failure')
            source.rename(destination)
        with self.assertRaises(installer.InstallError):
            installer.install(self.root, self.target, True, mover)
        self.assertEqual([user], list(self.target.iterdir()))
        self.assertEqual('keep', (user / 'file').read_text())

    def test_concurrent_change_preserved_during_rollback(self):
        def mover(source, destination):
            if destination.name == 'core-two':
                (self.target / 'core-one/SKILL.md').write_text('external change')
                raise OSError('simulated failure')
            source.rename(destination)
        with self.assertRaisesRegex(installer.InstallError, 'externally changed paths preserved'):
            installer.install(self.root, self.target, True, mover)
        self.assertEqual('external change', (self.target / 'core-one/SKILL.md').read_text())

    def test_traversal_and_source_overlap_rejected(self):
        self.lock['entries'][0]['source'] = '../outside'
        self.write_lock()
        with self.assertRaises(installer.InstallError):
            installer.install(self.root, self.target)
        self.lock['entries'][0]['source'] = 'skills/core-one'
        self.write_lock()
        with self.assertRaises(installer.InstallError):
            installer.install(self.root, self.root / 'skills')

    def test_guard_preserved(self):
        guard = self.target / '.indie-game-install.lock'
        guard.write_text('other process')
        with self.assertRaises(installer.InstallError):
            installer.install(self.root, self.target, True)
        self.assertEqual('other process', guard.read_text())

    def test_real_core_and_ui_bundle(self):
        root = MODULE.parents[1]
        manifest = json.loads((root / 'bundle.json').read_text(encoding='utf-8'))
        expected = set(manifest['skills']) | {item['id'] for item in manifest['uiDependencies']}
        lock, entries = installer.read_bundle(root)
        self.assertEqual(manifest['bundleVersion'], lock['bundleVersion'])
        self.assertEqual(expected, {name for name, _, _ in entries})
        self.assertEqual(set(manifest['skills']), {path.name for path in (root / 'skills').iterdir() if path.is_dir()})
        for dependency in manifest['uiDependencies']:
            self.assertEqual(dependency['skillSha256'], installer.digest(root / dependency['source'] / 'SKILL.md'))
        result = installer.install(root, self.target, True)
        self.assertEqual(expected, set(result['install']))
        self.assertTrue((self.target / 'game-project-profile/assets/profile-template.md').is_file())
        self.assertTrue((self.target / 'game-ui-component-system/scripts/validate_component_catalog.py').is_file())
        self.assertTrue((self.target / 'game-input-implementation/../game-task-planning/references/delivery-contract.md').is_file())
        self.assertTrue((self.target / 'game-test-design/../game-technical-design/references/runtime-concurrency.md').is_file())
        repeated = installer.install(root, self.target, True)
        self.assertEqual(expected, set(repeated['reused']))
        self.assertEqual([], repeated['install'])


if __name__ == '__main__':
    unittest.main()
