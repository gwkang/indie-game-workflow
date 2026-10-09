"""Observable workflow-dashboard behavior using isolated projects, no game data."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

TOOL = Path(__file__).resolve().parents[1] / 'skills/game-workflow-supervision/scripts/dashboard.py'
spec = importlib.util.spec_from_file_location('dashboard', TOOL)
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)


class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='workflow-dashboard-test-')
        self.root = Path(self.temp.name) / 'Project A'
        self.root.mkdir()
        d.init(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def config(self, **kwargs):
        path = self.root / d.FOLDER / 'dashboard.config.json'
        data = json.loads(path.read_text(encoding='utf-8'))
        data.update(kwargs)
        path.write_text(json.dumps(data), encoding='utf-8')
        return data

    def records(self, text, state='running'):
        folder = self.root / 'planning/workflow-runs'
        folder.mkdir(parents=True, exist_ok=True)
        (folder / 'run.md').write_text(text, encoding='utf-8')
        (folder / 'active.json').write_text(json.dumps({'schemaVersion': 1, 'runs': [
            {'runId': 'R1', 'recordPath': 'planning/workflow-runs/run.md', 'status': state, 'goalRevision': 1}
        ]}), encoding='utf-8')

    def test_empty_project_and_anchored_discovery(self):
        result = d.collect(self.root)
        self.assertEqual(result['runs'], [])
        self.assertIsNone(result['development']['percent'])
        self.assertEqual(d.project_root(self.root / '.agents/skills/game-workflow-supervision/scripts/dashboard.py'), self.root)
        self.assertTrue((self.root / d.FOLDER / 'open.py').is_file())

    def test_idempotence_preserves_manual_settings(self):
        config = self.config(displayName='내 이름', customSetting={'keep': True})
        d.init(self.root, name='덮어쓰지 않음')
        after = d.load_config(self.root)
        self.assertEqual(after, config)

    def test_copied_project_refuses_until_explicit_rebind(self):
        other = self.root.parent / 'Project B'
        shutil.copytree(self.root, other)
        with self.assertRaises(d.DashboardError):
            d.collect(other)
        old = d.load_config(self.root)['projectId']
        d.init(other, rebind=True, name='두 번째 프로젝트')
        self.assertNotEqual(d.load_config(other)['projectId'], old)
        self.assertTrue(list((other / d.FOLDER).glob('config-before-rebind-*.json')))

    def test_external_paths_and_symlink_escape(self):
        for path in ('../secret', '/etc/passwd', 'C:/secret', 'a\\b'):
            with self.subTest(path=path), self.assertRaises((d.DashboardError, OSError)):
                d.safe_path(self.root, path)
        outside = self.root.parent / 'outside'
        outside.mkdir()
        link = self.root / 'linked'
        try:
            link.symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest('Host does not allow symlink creation; other path cases executed')
        with self.assertRaises(d.DashboardError):
            d.safe_path(self.root, 'linked/file', exists=False)

    def test_completed_failed_check_and_usage_are_separate(self):
        self.records('''# 표시 검사
## Current checkpoint
- 현재 버전 검사 중
## Tasks
| Task ID | Skill/owner | State | Verdict | Validity |
| --- | --- | --- | --- | --- |
| T1 | game-functional-verification | completed | fail | stale |
## 사용 기록
| Skill | Task | Usage |
| --- | --- | --- |
| game-functional-verification | T1 | consumed |
| game-code-review | T2 | planned |
## Findings
| Finding | State | Next action |
| --- | --- | --- |
| 버튼 겹침 | open | 화면 수정 |
''')
        run = d.collect(self.root)['runs'][0]
        self.assertEqual((run['tasks'][0]['state'], run['tasks'][0]['verdict'], run['tasks'][0]['validity']), ('completed', 'fail', 'stale'))
        self.assertEqual([s['usage'] for s in run['skills']], ['assigned', 'consumed', 'planned'])
        self.assertEqual(run['findings'][0]['description'], '버튼 겹침')

    def test_history_not_promoted_and_unknown_preserved(self):
        self.records('''# 기록
## Current checkpoint
현재 미확인
## 역사
PASS, 100% 완료
## Tasks
| Task | owner | state |
| --- | --- | --- |
| T1 | game-code-review | strange-state |
''', 'invented-state')
        result = d.collect(self.root)
        self.assertEqual(result['runs'][0]['state'], 'unknown')
        self.assertEqual(result['runs'][0]['tasks'][0]['state'], 'unknown')
        self.assertEqual(result['runs'][0]['checkpoint'], '현재 미확인')
        self.assertIsNone(result['development']['percent'])

    def valid_roadmap(self):
        return {'schemaVersion': 1, 'scopeRevision': 'scope-1', 'items': [{
            'id': 'I1', 'title': '개발 목표', 'acceptanceState': 'accepted',
            'candidate': {'id': 'version1', 'digest': 'a' * 64}, 'criteria': [{
                'id': 'C1', 'verdict': 'pass', 'validity': 'current', 'candidateDigest': 'a' * 64,
                'evidenceLocator': 'planning/evidence.md', 'producerId': 'author', 'verifierId': 'reviewer'
            }], 'decisions': [{'state': 'approved', 'candidateDigest': 'a' * 64, 'authorityLocator': 'user-turn'}]
        }]}

    def test_completion_requires_current_independent_evidence_and_decisions(self):
        base = self.valid_roadmap()
        self.assertEqual(d.progress(base)['percent'], 100)
        for field, value in [('validity', 'stale'), ('candidateDigest', 'b' * 64),
                             ('verdict', 'fail'), ('verifierId', 'author'), ('evidenceLocator', '')]:
            wrong = copy.deepcopy(base)
            wrong['items'][0]['criteria'][0][field] = value
            self.assertEqual(d.progress(wrong)['percent'], 0, field)
        for state in ('skipped', 'cancelled', 'pending', 'unknown'):
            wrong = copy.deepcopy(base)
            wrong['items'][0]['acceptanceState'] = state
            self.assertEqual(d.progress(wrong)['percent'], 0)
        wrong = copy.deepcopy(base)
        wrong['items'][0]['decisions'][0]['state'] = 'pending'
        self.assertEqual(d.progress(wrong)['percent'], 0)

    def test_denominator_and_aggregate(self):
        base = self.valid_roadmap()
        second = copy.deepcopy(base['items'][0])
        second['id'] = 'I2'
        second['criteria'][0]['id'] = 'C2'
        second['acceptanceState'] = 'pending'
        base['items'].append(second)
        result = d.progress(base)
        self.assertEqual((result['completed'], result['total'], result['percent']), (1, 2, 50))
        self.assertEqual((result['criteriaPassed'], result['criteriaTotal']), (2, 2))
        base['items'][1]['inScope'] = False
        self.assertEqual(d.progress(base)['total'], 1)

    def test_malformed_identity_is_not_independent_evidence(self):
        for field, value in [('verifierId', ['author']), ('verifierId', {'id': 'reviewer'}),
                             ('verifierId', True), ('producerId', 42),
                             ('verifierId', 'author '), ('evidenceLocator', ['record'])]:
            case = self.valid_roadmap()
            case['items'][0]['criteria'][0][field] = value
            result = d.progress(case)
            self.assertEqual(result['percent'], 0, field)
            self.assertFalse(result['items'][0]['complete'], field)
        case = self.valid_roadmap()
        case['items'][0]['candidate']['id'] = ['version1']
        self.assertEqual(d.progress(case)['percent'], 0)
        case = self.valid_roadmap()
        case['items'][0]['decisions'][0]['authorityLocator'] = {'not': 'a-record'}
        self.assertEqual(d.progress(case)['percent'], 0)

    def test_duplicate_and_incomplete_scope_are_errors(self):
        base = self.valid_roadmap()
        for field in ('criteria', 'decisions'):
            wrong = copy.deepcopy(base)
            del wrong['items'][0][field]
            with self.assertRaises(d.DashboardError):
                d.progress(wrong)
        base['items'].append(copy.deepcopy(base['items'][0]))
        with self.assertRaises(d.DashboardError):
            d.progress(base)

    def test_refresh_failure_preserves_snapshot_and_last_good(self):
        self.records('# 처음 기록')
        snapshot = d.update(self.root)
        path = self.root / d.FOLDER / 'snapshot.json'
        before = path.read_bytes()
        reader = d.Reader(self.root)
        self.assertEqual(reader.get()['runs'][0]['title'], '처음 기록')
        self.records('# 새 기록')
        self.assertEqual(reader.get()['runs'][0]['title'], '새 기록')
        (self.root / 'planning/workflow-runs/active.json').write_text('{', encoding='utf-8')
        stale = reader.get()
        self.assertEqual((stale['freshness'], stale['runs'][0]['title']), ('stale', '새 기록'))
        self.assertTrue(stale['readErrors'])
        with self.assertRaises(ValueError):
            d.update(self.root)
        self.assertEqual(path.read_bytes(), before)

    def test_empty_existing_registry_is_not_missing(self):
        self.records('# 기록')
        (self.root / 'planning/workflow-runs/active.json').write_text('', encoding='utf-8')
        with self.assertRaises(ValueError):
            d.collect(self.root)

    def test_server_whitelist_origin_and_source_are_safe(self):
        self.records('# <script>window.injected=true</script>')
        record = self.root / 'planning/workflow-runs/run.md'
        before = hashlib.sha256(record.read_bytes()).hexdigest()
        server = d.create_server(self.root)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        base = f'http://127.0.0.1:{server.server_port}'
        try:
            with urlopen(base + '/snapshot.json') as response:
                data = json.load(response)
            source = next(s for s in data['sources'] if s['path'].endswith('run.md'))
            with urlopen(base + '/source/' + source['id']) as response:
                self.assertIn('text/plain', response.headers['Content-Type'])
                self.assertIn(b'<script>', response.read())
            for path in ('/../run.md', '/dashboard.config.json', '/.git/config', '/source/0'):
                with self.assertRaises(HTTPError) as raised:
                    urlopen(base + path)
                self.assertEqual(raised.exception.code, 404)
            with self.assertRaises(HTTPError) as raised:
                urlopen(Request(base + '/', headers={'Origin': 'https://example.com'}))
            self.assertEqual(raised.exception.code, 403)
            with self.assertRaises(HTTPError) as raised:
                urlopen(Request(base + '/', headers={'Host': 'example.com'}))
            self.assertEqual(raised.exception.code, 403)
            self.assertEqual(hashlib.sha256(record.read_bytes()).hexdigest(), before)
        finally:
            server.shutdown()
            server.server_close()
            worker.join()

    def test_partial_unknown_scope_has_no_overall_percent(self):
        value = {'schemaVersion': 1, 'scopeRevision': 'partial', 'scopeState': 'unknown',
                 'items': [{'id': 'partial-feature'}]}
        self.assertIsNone(d.progress(value)['percent'])


if __name__ == '__main__':
    unittest.main()
