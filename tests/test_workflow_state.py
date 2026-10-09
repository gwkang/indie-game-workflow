"""Portable state-tool regression: isolated files, installed CLI and invalid result declarations."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

PACKAGE = Path(__file__).resolve().parents[1]
SOURCE_SKILLS = PACKAGE / 'skills'
DRAFT = SOURCE_SKILLS / 'game-workflow-supervision/scripts'
BASELINE = SOURCE_SKILLS
_FIXTURE_SCOPE = tempfile.TemporaryDirectory(prefix='workflow-state-')
ATTEMPT = Path(_FIXTURE_SCOPE.name)


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


class StateTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix=self._testMethodName + '-', dir=ATTEMPT))
        self.scripts = self.root / '.agents/skills/game-workflow-supervision/scripts'
        self.scripts.mkdir(parents=True)
        for name in ('workflow_state.py', 'dashboard.py'):
            shutil.copyfile(DRAFT / name, self.scripts / name)
        registry = self.root / '.agents/skills/game-workflow/scripts'
        registry.mkdir(parents=True)
        shutil.copyfile(BASELINE / 'game-workflow/scripts/workflow_run_registry.py', registry / 'workflow_run_registry.py')
        assets = self.root / '.agents/skills/game-workflow-supervision/assets/dashboard'
        shutil.copytree(BASELINE / 'game-workflow-supervision/assets/dashboard', assets)
        self.tool = self.import_file(self.scripts / 'workflow_state.py', 'state_test')
        self.dashboard = self.tool.dashboard_tool()
        self.counter = 0
        self.write('artifact/code.py', b'print(2 + 3)\n')
        self.data = self.initial()

    @staticmethod
    def import_file(path, name):
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def initial(self):
        return {'runId': 'fixture-run', 'title': '격리 상태 검사', 'goalRevision': 1, 'supervisorId': 'coordinator',
                'registryPath': 'planning/workflow-runs/active.json',
                'discovery': {'goalKeys': ['fixture'], 'targetPaths': ['artifact/code.py']},
                'authority': {'cursor': 'fixture-request', 'summary': '격리 도구 검사', 'scope': ['fixture only'], 'excluded': ['product']},
                'checkpoint': {'stage': '준비', 'summary': '격리 후보', 'blocker': '', 'nextAction': '검사'},
                'contract': {
                    'criteria': [{'id': 'C1', 'text': '계산 결과와 완료 증거'}],
                    'tasks': [{'id': 'A1', 'title': '격리 코드', 'skillId': 'game-test-infrastructure',
                               'producerId': 'author', 'criterionIds': ['C1'], 'required': True}],
                    'checks': [{'id': 'check-code', 'criterionIds': ['C1'], 'taskIds': ['A1'],
                                'expectedNames': ['arithmetic'], 'mode': 'command'}],
                    'reviews': [{'id': 'review-code', 'criterionIds': ['C1'], 'taskIds': ['A1']}], 'decisions': []}}

    def write(self, relative, content):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(encoded(content) if isinstance(content, dict) else content)
        return path

    def state(self):
        return self.tool.load_state(self.root, 'fixture-run')[0]

    def event(self, kind, data, event_id=None):
        self.counter += 1
        event = {'eventId': event_id or f'event-{self.counter}', 'kind': kind, 'data': data}
        return self.tool.record(self.root, 'fixture-run', event, self.state()['revision'])

    def raw_ref(self, relative, content):
        path = self.write(relative, content)
        return {'path': relative, 'digest': hashlib.sha256(path.read_bytes()).hexdigest()}

    def execute_arithmetic(self):
        result = subprocess.run([sys.executable, '-B', str(self.root / 'artifact/code.py')], cwd=self.root,
                                capture_output=True, timeout=30)
        reference = self.raw_ref('raw/arithmetic.stdout', result.stdout)
        self.write('raw/arithmetic.stderr', result.stderr)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.splitlines(), [b'5'])
        return reference

    def result_data(self, kind='check', actor='author'):
        candidate = self.state()['candidate']
        value = {'contractId': 'check-code' if kind == 'check' else 'review-code', 'goalRevision': 1,
                 'candidateId': candidate['id'], 'candidateDigest': candidate['digest'], 'actorId': actor,
                 'criterionIds': ['C1'], 'taskIds': ['A1'], 'executionState': 'completed', 'verdict': 'pass',
                 'evidence': [self.execute_arithmetic() if kind == 'check' else
                              self.raw_ref('raw/review.md', b'Isolated review declaration; adapter fixture only.\n')]}
        if kind == 'check':
            value.update({'completedNames': ['arithmetic'], 'failedNames': [], 'timedOut': False,
                          'exitCode': 0, 'command': 'python -B artifact/code.py'})
        else:
            value['evidenceDigest'] = self.tool.inspect(self.root, self.state())['evidenceDigest']
        return value

    def prepare(self, *, reviewed=True):
        self.assertTrue(self.tool.init(self.root, self.data)['ok'])
        self.event('task', {'taskId': 'A1', 'state': 'completed'})
        self.assertTrue(self.tool.freeze(self.root, 'fixture-run', 'candidate-1', ['artifact/code.py'],
                                         ['author'], self.state()['revision'])['ok'])
        self.event('check', self.result_data())
        if reviewed:
            self.event('review', self.result_data('review', 'verifier'))
        return self.state()

    def cli(self, args, expected=0):
        unrelated = self.root / 'unrelated-cwd'
        unrelated.mkdir(exist_ok=True)
        started = time.monotonic()
        result = subprocess.run([sys.executable, '-X', 'utf8', '-B', str(self.scripts / 'workflow_state.py'), *args],
                                cwd=unrelated, capture_output=True, text=True, encoding='utf-8', timeout=30)
        self.counter += 1
        folder = self.root / f'cli-attempts/{self.counter}'
        folder.mkdir(parents=True)
        (folder / 'stdout.txt').write_text(result.stdout, encoding='utf-8')
        (folder / 'stderr.txt').write_text(result.stderr, encoding='utf-8')
        (folder / 'attempt.json').write_bytes(encoded({'args': args, 'cwd': str(unrelated),
            'executable': sys.executable, 'exitCode': result.returncode, 'elapsedSeconds': time.monotonic() - started}))
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return json.loads(result.stdout) if '--markdown' not in args else result.stdout

    def test_normal_completion_preserves_other_pointer(self):
        self.write('legacy/run.md', b'# unrelated\n')
        other = {'runId': 'other-run', 'recordPath': 'legacy/run.md', 'status': 'blocked', 'goalRevision': 2,
                 'goalKeys': ['other'], 'targetPaths': ['other'], 'conversationKey': 'other-chat'}
        self.write(self.data['registryPath'], {'schemaVersion': 1, 'runs': [other]})
        self.prepare()
        checked = self.tool.inspect(self.root, self.state())
        self.assertTrue(checked['ready'])
        result = self.tool.complete(self.root, 'fixture-run', self.state()['revision'])
        self.assertTrue(result['ok'])
        self.assertTrue(result['stateSaved'])
        self.assertEqual(self.state()['status'], 'completed')
        registry = json.loads((self.root / self.data['registryPath']).read_text(encoding='utf-8'))
        self.assertEqual(next(row for row in registry['runs'] if row['runId'] == 'other-run'), other)
        self.assertTrue(self.tool.inspect(self.root, self.state())['ready'])

    def test_all_cli_commands_find_own_project_from_wrong_cwd(self):
        self.write('input/init.json', self.data)
        result = self.cli(['init', '--input', 'input/init.json'])
        self.assertTrue(result['stateSaved'])
        self.cli(['check', '--run-id', 'fixture-run'], 1)
        self.assertIn('실행', self.cli(['show', '--run-id', 'fixture-run', '--markdown']))
        self.cli(['freeze', '--run-id', 'fixture-run', '--candidate-id', 'candidate-1', '--file', 'artifact/code.py',
                  '--producer', 'author', '--expect-revision', str(self.state()['revision'])])
        self.write('input/task.json', {'eventId': 'cli-task', 'kind': 'task', 'data': {'taskId': 'A1', 'state': 'completed'}})
        self.cli(['record', '--run-id', 'fixture-run', '--input', 'input/task.json', '--expect-revision', str(self.state()['revision'])])
        self.write('input/check.json', {'eventId': 'cli-check', 'kind': 'check', 'data': self.result_data()})
        self.cli(['record', '--run-id', 'fixture-run', '--input', 'input/check.json', '--expect-revision', str(self.state()['revision'])])
        self.write('input/review.json', {'eventId': 'cli-review', 'kind': 'review', 'data': self.result_data('review', 'verifier')})
        self.cli(['record', '--run-id', 'fixture-run', '--input', 'input/review.json', '--expect-revision', str(self.state()['revision'])])
        self.cli(['check', '--run-id', 'fixture-run'])
        self.cli(['complete', '--run-id', 'fixture-run', '--expect-revision', str(self.state()['revision'])])
        self.cli(['sync', '--run-id', 'fixture-run'])
        self.assertEqual(self.cli(['show', '--run-id', 'fixture-run'])['state']['status'], 'completed')

    def test_denied_completion_does_not_write_any_state(self):
        self.tool.init(self.root, self.data)
        paths = [self.root / self.tool.state_relative('fixture-run'), self.root / self.data['registryPath']]
        before = [path.read_bytes() for path in paths]
        result = self.tool.complete(self.root, 'fixture-run', self.state()['revision'])
        self.assertFalse(result['ok'])
        self.assertEqual([path.read_bytes() for path in paths], before)

    def test_candidate_and_raw_drift_are_stale(self):
        self.prepare()
        self.write('artifact/code.py', b'print(2 + 4)\n')
        inspected = self.tool.inspect(self.root, self.state())
        self.assertFalse(inspected['ready'])
        self.assertEqual(inspected['candidateValidity'], 'stale')
        self.write('artifact/code.py', b'print(2 + 3)\n')
        self.write('raw/arithmetic.stdout', b'changed\n')
        inspected = self.tool.inspect(self.root, self.state())
        self.assertFalse(inspected['ready'])
        self.assertEqual(inspected['checks'][0]['validity'], 'stale')
        (self.root / 'raw/arithmetic.stdout').unlink()
        self.assertFalse(self.tool.inspect(self.root, self.state())['ready'])

    def test_current_raw_fingerprint_invalidates_review(self):
        self.prepare()
        previous = self.tool.inspect(self.root, self.state())
        self.assertTrue(previous['ready'])
        self.write('raw/arithmetic.stdout', b'changed source observation\n')
        checked = self.tool.inspect(self.root, self.state())
        self.assertEqual(checked['candidateValidity'], 'current')
        self.assertEqual(checked['checks'][0]['validity'], 'stale')
        self.assertEqual(checked['reviews'][0]['validity'], 'stale')
        self.assertNotEqual(checked['evidenceDigest'], previous['evidenceDigest'])
        state_path = self.root / self.tool.state_relative('fixture-run')
        before = state_path.read_bytes()
        self.assertFalse(self.tool.complete(self.root, 'fixture-run', self.state()['revision'])['ok'])
        self.assertEqual(state_path.read_bytes(), before)
        (self.root / 'raw/arithmetic.stdout').unlink()
        missing = self.tool.inspect(self.root, self.state())
        self.assertEqual(missing['checks'][0]['validity'], 'stale')
        self.assertEqual(missing['reviews'][0]['validity'], 'stale')
        self.assertNotEqual(missing['evidenceDigest'], checked['evidenceDigest'])

    def test_latest_failure_and_missing_completion_never_reuse_old_pass(self):
        self.prepare()
        for changes in ({'verdict': 'fail', 'failedNames': ['arithmetic']}, {'completedNames': []},
                        {'timedOut': True}, {'executionState': 'running'}, {'exitCode': 1}):
            with self.subTest(changes=changes):
                data = self.result_data()
                data.update(changes)
                self.event('check', data)
                self.assertFalse(self.tool.inspect(self.root, self.state())['ready'])
        self.assertGreater(len(self.state()['results']), 2)

    def test_wrong_sets_duplicate_names_and_malformed_types_rejected(self):
        self.prepare(reviewed=False)
        base = self.result_data()
        changes = [{'actorId': []}, {'actorId': ' author'}, {'actorId': ''}, {'goalRevision': True},
                   {'criterionIds': []}, {'taskIds': ['missing']}, {'completedNames': ['arithmetic', 'arithmetic']},
                   {'candidateDigest': '0' * 63}, {'timedOut': 0}, {'exitCode': False}]
        for change in changes:
            with self.subTest(change=change):
                value = deepcopy(base)
                value.update(change)
                with self.assertRaises(self.tool.StateError):
                    self.event('check', value)
        candidate = self.state()['candidate']
        self.assertFalse(self.tool.inspect(self.root, self.state())['ready'])
        self.assertEqual(candidate, self.state()['candidate'])

    def test_same_author_or_stale_review_cannot_complete(self):
        self.prepare(reviewed=False)
        self.event('review', self.result_data('review', 'author'))
        self.assertFalse(self.tool.inspect(self.root, self.state())['ready'])
        self.event('review', self.result_data('review', 'verifier'))
        self.assertTrue(self.tool.inspect(self.root, self.state())['ready'])
        self.event('check', self.result_data())
        checked = self.tool.inspect(self.root, self.state())
        self.assertFalse(checked['ready'])
        self.assertEqual(checked['reviews'][0]['validity'], 'stale')

    def test_required_decision_and_formal_check_hold(self):
        self.data['contract']['decisions'] = [{'id': 'formal-approval', 'criterionIds': ['C1']}]
        self.data['contract']['checks'].append({'id': 'visual-craft', 'criterionIds': ['C1'], 'taskIds': ['A1'],
                                               'expectedNames': ['representative-craft'], 'mode': 'observation'})
        self.prepare(reviewed=False)
        self.assertFalse(self.tool.inspect(self.root, self.state())['ready'])
        decision = {**self.result_data(), 'contractId': 'formal-approval', 'taskIds': [], 'authorityId': 'fixture-user', 'state': 'approved'}
        for name in ('completedNames', 'failedNames', 'timedOut', 'exitCode', 'command'):
            decision.pop(name)
        self.event('decision', decision)
        check = self.result_data()
        check.update({'contractId': 'visual-craft', 'completedNames': ['representative-craft']})
        check.pop('exitCode')
        check.pop('command')
        self.event('check', check)
        self.event('review', self.result_data('review', 'verifier'))
        self.assertTrue(self.tool.inspect(self.root, self.state())['ready'])

    def test_skipped_cancelled_tasks_and_blocking_findings_hold(self):
        self.prepare()
        for task_state in ('skipped', 'cancelled'):
            self.event('task', {'taskId': 'A1', 'state': task_state})
            self.assertFalse(self.tool.inspect(self.root, self.state())['ready'])
        self.event('task', {'taskId': 'A1', 'state': 'completed'})
        self.event('finding', {'id': 'audit-hold', 'description': 'required event unresolved', 'state': 'open',
                               'blocksCompletion': True, 'nextAction': 'separate audit'})
        self.assertFalse(self.tool.inspect(self.root, self.state())['ready'])
        self.event('finding', {'id': 'audit-hold', 'description': 'required event resolved', 'state': 'resolved',
                               'blocksCompletion': True, 'nextAction': ''})
        self.event('review', self.result_data('review', 'verifier'))
        self.assertTrue(self.tool.inspect(self.root, self.state())['ready'])

    def test_scope_preserves_previous_candidate_failure_and_lineage(self):
        self.prepare()
        failure = self.result_data()
        failure['verdict'] = 'fail'
        self.event('check', failure)
        old = self.state()
        self.event('scope', {'goalRevision': 2, 'authority': deepcopy(self.data['authority']),
                             'contract': deepcopy(self.data['contract']), 'checkpoint': deepcopy(self.data['checkpoint'])})
        state = self.state()
        self.assertIsNone(state['candidate'])
        self.assertEqual(state['results'], old['results'])
        self.assertEqual(state['events'][-1]['previous']['candidate'], old['candidate'])
        self.assertEqual(state['taskStates']['A1']['state'], 'pending')
        self.assertFalse(self.tool.inspect(self.root, state)['ready'])

    def test_skill_reference_rejects_unknown_task_without_write(self):
        self.prepare()
        state_path = self.root / self.tool.state_relative('fixture-run')
        registry_path = self.root / self.data['registryPath']
        before = (state_path.read_bytes(), registry_path.read_bytes())
        with self.assertRaises(self.tool.StateError):
            self.event('skill', {'skillId': 'game-test-infrastructure', 'taskId': 'undeclared-task',
                                 'usage': 'consumed', 'actorId': 'author'})
        self.assertEqual((state_path.read_bytes(), registry_path.read_bytes()), before)

    def test_skill_scope_keeps_legal_history_and_separates_current_use(self):
        self.prepare()
        skill = {'skillId': 'game-test-infrastructure', 'taskId': 'A1', 'usage': 'consumed', 'actorId': 'author'}
        self.event('skill', skill)
        self.dashboard.init(self.root, name='Fixture')
        before = self.dashboard.collect(self.root)
        self.assertEqual(before['runs'][0]['skills'][0]['taskId'], 'A1')
        contract = deepcopy(self.data['contract'])
        contract['tasks'][0]['id'] = 'A2'
        contract['checks'][0]['taskIds'] = ['A2']
        contract['reviews'][0]['taskIds'] = ['A2']
        self.event('scope', {'goalRevision': 2, 'authority': deepcopy(self.data['authority']),
                             'contract': contract, 'checkpoint': deepcopy(self.data['checkpoint'])})
        state = self.state()
        self.assertEqual(state['skills'], [])
        self.assertEqual(state['events'][-1]['previous']['skills'], [skill])
        self.assertEqual(state['events'][-1]['previous']['contract']['tasks'][0]['id'], 'A1')
        after = self.dashboard.collect(self.root)
        self.assertEqual(after['runs'][0]['skills'], [])
        self.assertEqual(after['runs'][0]['tasks'][0]['id'], 'A2')
        self.event('skill', {**skill, 'taskId': 'A2'})
        self.assertEqual(self.dashboard.collect(self.root)['runs'][0]['skills'][0]['taskId'], 'A2')
        tampered = deepcopy(self.state())
        scope_event = next(item for item in tampered['events'] if item['kind'] == 'scope')
        scope_event['previous']['skills'][0]['taskId'] = 'not-in-old-contract'
        with self.assertRaises(self.tool.StateError):
            self.tool.validate(tampered)

    def test_stale_revision_and_idempotent_retry(self):
        self.tool.init(self.root, self.data)
        event = {'eventId': 'one', 'kind': 'task', 'data': {'taskId': 'A1', 'state': 'completed'}}
        self.tool.record(self.root, 'fixture-run', event, 1)
        revision = self.state()['revision']
        retry = self.tool.record(self.root, 'fixture-run', event, 1)
        self.assertTrue(retry['alreadyRecorded'])
        self.assertEqual(self.state()['revision'], revision)
        with self.assertRaises(self.tool.StateError):
            self.tool.record(self.root, 'fixture-run', {**event, 'data': {'taskId': 'A1', 'state': 'failed'}}, revision)
        with self.assertRaises(self.tool.StateError):
            self.tool.freeze(self.root, 'fixture-run', 'candidate-1', ['artifact/code.py'], ['author'], 1)
        self.tool.freeze(self.root, 'fixture-run', 'candidate-1', ['artifact/code.py'], ['author'], revision)
        self.write('artifact/code.py', b'print(7)\n')
        self.tool.freeze(self.root, 'fixture-run', 'candidate-2', ['artifact/code.py'], ['author'], self.state()['revision'])
        with self.assertRaises(self.tool.StateError):
            self.tool.freeze(self.root, 'fixture-run', 'candidate-1', ['artifact/code.py'], ['author'], self.state()['revision'])

    def test_registry_failure_after_saved_state_recovers_without_duplicate(self):
        self.tool.init(self.root, self.data)
        registry_path = self.root / self.data['registryPath']
        registry_path.write_bytes(b'{broken')
        event = {'eventId': 'partial', 'kind': 'task', 'data': {'taskId': 'A1', 'state': 'completed'}}
        result = self.tool.record(self.root, 'fixture-run', event, 1)
        self.assertFalse(result['ok'])
        self.assertTrue(result['stateSaved'])
        self.assertFalse(result['registrySynced'])
        self.assertEqual(self.state()['taskStates']['A1']['state'], 'completed')
        registry_path.write_bytes(encoded({'schemaVersion': 1, 'runs': []}))
        result = self.tool.record(self.root, 'fixture-run', event, 1)
        self.assertTrue(result['alreadyRecorded'])
        self.assertTrue(result['ok'])
        self.assertEqual(len(self.state()['events']), 1)

    def test_state_write_and_registry_concurrent_change_are_detected(self):
        self.tool.init(self.root, self.data)
        state, raw = self.tool.load_state(self.root, 'fixture-run')
        path = self.root / self.tool.state_relative('fixture-run')
        path.write_bytes(raw + b' ')
        with self.assertRaises(self.tool.StateError):
            self.tool.save_state(self.root, state, raw)
        path.write_bytes(raw)
        registry_path = self.root / self.data['registryPath']
        original = registry_path.read_bytes()
        calls = 0
        real_read = Path.read_bytes
        def changing_read(target):
            nonlocal calls
            if target == registry_path:
                calls += 1
                if calls == 2:
                    registry_path.write_bytes(original + b' ')
            return real_read(target)
        with patch.object(Path, 'read_bytes', changing_read):
            result = self.tool.sync(self.root, state)
        self.assertFalse(result['registrySynced'])
        self.assertEqual(registry_path.read_bytes(), original + b' ')

    def test_self_changing_and_external_paths_are_forbidden(self):
        self.prepare(reviewed=False)
        bad_paths = ['../outside.py', 'C:/outside.py', '\\server/share/file', 'artifact\\code.py',
                     self.tool.state_relative('fixture-run'), self.data['registryPath']]
        self.write('planning/workflow-dashboard/snapshot.json', b'{}')
        bad_paths.append('planning/workflow-dashboard/snapshot.json')
        for filename in bad_paths:
            with self.subTest(filename=filename):
                with self.assertRaises((self.tool.StateError, ValueError, OSError)):
                    self.tool.freeze(self.root, 'fixture-run', 'bad-candidate', [filename], ['author'], self.state()['revision'])

    def test_actual_external_junction_or_symlink_is_rejected(self):
        self.prepare(reviewed=False)
        outside = Path(tempfile.mkdtemp(prefix='outside-', dir=ATTEMPT))
        (outside / 'file.py').write_bytes(b'print(9)\n')
        link = self.root / 'linked'
        if sys.platform == 'win32':
            script = "$ErrorActionPreference='Stop'; New-Item -ItemType Junction -Path $env:WF_LINK -Target $env:WF_TARGET | Out-Null"
            import os
            environment = {**os.environ, 'WF_LINK': str(link), 'WF_TARGET': str(outside)}
            result = subprocess.run(['powershell', '-NoProfile', '-Command', script], env=environment,
                                    capture_output=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr.decode('utf-8', errors='replace'))
        else:
            link.symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.tool.freeze(self.root, 'fixture-run', 'external', ['linked/file.py'], ['author'], self.state()['revision'])

    def test_read_stability_detects_changed_input(self):
        self.prepare()
        code_path = self.root / 'artifact/code.py'
        original_digest = self.tool.file_digest
        calls = 0
        def changed_digest(path):
            nonlocal calls
            value = original_digest(path)
            if path == code_path:
                calls += 1
                if calls == 1:
                    code_path.write_bytes(b'print(999)\n')
            return value
        with patch.object(self.tool, 'file_digest', changed_digest):
            with self.assertRaises(self.tool.StateError):
                self.tool.inspect(self.root, self.state())

    def test_json_dashboard_legacy_config_and_failure_retention(self):
        self.prepare()
        self.dashboard.init(self.root, name='Fixture project')
        config_path = self.root / 'planning/workflow-dashboard/dashboard.config.json'
        config = json.loads(config_path.read_text(encoding='utf-8'))
        config['manualSetting'] = 'preserve'
        config_path.write_bytes(encoded(config))
        self.write('legacy/run.md', b'# Legacy\n\n## Current checkpoint\nOld record stays\n')
        registry_path = self.root / self.data['registryPath']
        registry = json.loads(registry_path.read_text(encoding='utf-8'))
        registry['runs'].append({'runId': 'legacy', 'recordPath': 'legacy/run.md', 'status': 'blocked',
                                 'goalRevision': 1, 'goalKeys': [], 'targetPaths': []})
        registry_path.write_bytes(encoded(registry))
        snapshot = self.dashboard.update(self.root)
        current = next(run for run in snapshot['runs'] if run['id'] == 'fixture-run')
        self.assertTrue(current['completionReady'])
        self.assertEqual(current['tasks'][0]['validity'], 'current')
        self.assertEqual(next(run for run in snapshot['runs'] if run['id'] == 'legacy')['checkpoint'], 'Old record stays')
        self.assertNotIn('artifact/code.py', [source['path'] for source in snapshot['sources']])
        self.assertNotIn('raw/arithmetic.stdout', [source['path'] for source in snapshot['sources']])
        self.assertEqual(json.loads(config_path.read_text(encoding='utf-8'))['manualSetting'], 'preserve')
        reader = self.dashboard.Reader(self.root)
        saved_path = self.root / 'planning/workflow-dashboard/snapshot.json'
        saved = saved_path.read_bytes()
        state_path = self.root / self.tool.state_relative('fixture-run')
        original = state_path.read_bytes()
        state_path.write_bytes(b'{malformed')
        with self.assertRaises(ValueError):
            self.dashboard.update(self.root)
        self.assertEqual(saved_path.read_bytes(), saved)
        self.assertEqual(reader.get()['freshness'], 'stale')
        state_path.write_bytes(original)
        self.write('artifact/code.py', b'print(8)\n')
        current_snapshot = reader.get()
        self.assertEqual(current_snapshot['freshness'], 'current')
        self.assertEqual(current_snapshot['runs'][0]['candidateValidity'], 'stale')

    def test_dashboard_sync_failure_is_partial_and_canonical_survives(self):
        self.prepare()
        self.dashboard.init(self.root, name='Fixture')
        before = (self.root / 'planning/workflow-dashboard/snapshot.json').read_bytes()
        with patch.object(self.tool.dashboard_tool(), 'update', side_effect=OSError('injected snapshot write failure')):
            result = self.event('checkpoint', {'stage': '완료 준비', 'summary': 'same data', 'blocker': '', 'nextAction': 'complete'})
        self.assertFalse(result['ok'])
        self.assertTrue(result['stateSaved'])
        self.assertTrue(result['registrySynced'])
        self.assertFalse(result['dashboardUpdated'])
        self.assertEqual((self.root / 'planning/workflow-dashboard/snapshot.json').read_bytes(), before)
        self.assertEqual(self.state()['checkpoint']['stage'], '완료 준비')
        self.assertTrue(self.tool.sync(self.root, self.state())['ok'])

    def test_explicit_one_run_adoption_and_unsupported_registry_are_separate(self):
        self.write('legacy/own.md', b'# prior owned record\n')
        pointer = {'runId': 'fixture-run', 'recordPath': 'legacy/own.md', 'status': 'running', 'goalRevision': 1,
                   'goalKeys': [], 'targetPaths': []}
        self.write(self.data['registryPath'], {'schemaVersion': 1, 'runs': [pointer]})
        with self.assertRaises(self.tool.StateError):
            self.tool.init(self.root, self.data)
        self.data['supersedesRecordPath'] = 'legacy/own.md'
        self.assertTrue(self.tool.init(self.root, self.data)['ok'])
        self.assertEqual((self.root / 'legacy/own.md').read_bytes(), b'# prior owned record\n')
        registry_path = self.root / self.data['registryPath']
        registry_path.write_bytes(encoded({'schemaVersion': 2, 'runs': []}))
        self.assertFalse(self.tool.sync(self.root, self.state())['ok'])

    def test_measurements_preserve_unmeasured_and_do_not_invalidate_review(self):
        self.prepare()
        before = self.tool.inspect(self.root, self.state())['evidenceDigest']
        self.event('measurement', {'id': 'real-work-time', 'scope': 'real-work', 'metric': 'elapsed',
                                  'kind': 'unmeasured', 'value': None, 'unit': 'seconds', 'source': 'not yet observed'})
        checked = self.tool.inspect(self.root, self.state())
        self.assertEqual(checked['evidenceDigest'], before)
        self.assertTrue(checked['ready'])
        with self.assertRaises(self.tool.StateError):
            self.event('measurement', {'id': 'bad', 'scope': 'real-work', 'metric': 'elapsed',
                                      'kind': 'unmeasured', 'value': 0, 'unit': 'seconds', 'source': 'not measured'})

    def test_invalid_contract_cannot_remove_coverage(self):
        for mutation in ('no-criteria', 'no-task-review', 'bool-goal', 'duplicate-criterion', 'unknown-task'):
            with self.subTest(mutation=mutation):
                value = deepcopy(self.data)
                if mutation == 'no-criteria':
                    value['contract']['criteria'] = []
                elif mutation == 'no-task-review':
                    value['contract']['reviews'][0]['taskIds'] = []
                elif mutation == 'bool-goal':
                    value['goalRevision'] = True
                elif mutation == 'duplicate-criterion':
                    value['contract']['criteria'] *= 2
                else:
                    value['contract']['checks'][0]['taskIds'] = ['missing']
                with self.assertRaises((self.tool.StateError, ValueError)):
                    self.tool.init(self.root, value)
        self.assertFalse((self.root / self.tool.state_relative('fixture-run')).exists())


if __name__ == '__main__':
    unittest.main()
