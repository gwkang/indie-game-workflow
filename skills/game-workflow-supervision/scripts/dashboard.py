"""Project-owned workflow dashboard. Python 3.12+, standard library only."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path, PureWindowsPath
import re
import sys
import tempfile
import uuid
import webbrowser

VERSION = '1.0.0'
FOLDER = 'planning/workflow-dashboard'
ASSETS = Path(__file__).resolve().parents[1] / 'assets/dashboard'
STATES = {'pending', 'ready', 'running', 'completed', 'failed', 'blocked',
          'cancelled', 'skipped', 'needs-clarification', 'needs-reconciliation'}
SKILL_NAMES = {
    'game-workflow': '작업 시작', 'game-workflow-supervision': '전체 작업 관리',
    'game-task-planning': '작업 순서 정하기', 'game-technical-design': '구조 설계',
    'game-feature-spec': '기능 정하기', 'game-project-profile': '프로젝트 설정 정리',
    'game-code-review': '코드 검토', 'game-functional-verification': '동작 검사',
    'game-test-design': '검사 방법 정하기', 'game-test-infrastructure': '검사 도구 만들기',
    'game-workflow-audit': '작업 방식 점검', 'game-bug-reproduction': '문제 재현',
    'game-bug-diagnosis': '문제 원인 찾기', 'game-build-packaging': '실행 파일 만들기',
    'game-ui-implementation': '화면 제작', 'game-ui-ux-design': '화면 사용 흐름 설계',
    'game-ui-art-direction': '화면 스타일 정하기', 'game-ui-mockup': '화면 시안',
    'game-ui-screen-spec': '화면 내용 정하기', 'game-ui-handoff': '화면 제작 기준',
    'game-ui-runtime-validation': '실제 화면 검사', 'game-ui-acceptance-review': '화면 완료 검토',
    'game-ui-component-system': '공통 화면 요소', 'game-ui-asset-production': '그림 준비',
    'game-improvement-assessment': '개선 효과 검토', 'game-rule-implementation': '게임 규칙 제작',
    'game-save-implementation': '저장 기능 제작', 'game-session-implementation': '게임 상태 관리',
    'game-input-implementation': '입력 기능 제작', 'game-movement-implementation': '이동 기능 제작',
    'game-camera-implementation': '카메라 제작', 'game-content-loading': '자료 불러오기',
    'game-platform-integration': '외부 기능 연결', 'game-performance-profiling': '성능 측정',
    'game-knowledge-maintenance': '프로젝트 지식 정리', 'art-asset-review': '그림 검토',
    'indie-game-development': '기능 개발', 'indie-game-improvement': '품질 개선',
    'indie-game-bugfix': '문제 수정', 'skill-creator': '워크플로우 도구 제작',
}
SKILL_RE = re.compile(r'\b(?:game-[a-z][a-z-]+|indie-game-[a-z-]+|art-asset-review|skill-creator)\b')


class DashboardError(ValueError):
    pass


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def project_root(script=None):
    """Discover from the installed tool, never from the caller's working directory."""
    location = Path(script or __file__).resolve()
    for folder in location.parents:
        if folder.name == '.agents' and location.is_relative_to(folder / 'skills'):
            return folder.parent
    raise DashboardError('프로젝트에 설치된 도구를 실행하세요. 프로젝트 폴더 입력은 필요 없습니다.')


def safe_path(root, relative, *, exists=True):
    if not isinstance(relative, str) or not relative or '\\' in relative or ':' in relative:
        raise DashboardError('프로젝트 안의 상대 경로만 사용할 수 있습니다.')
    path = Path(relative)
    if path.is_absolute() or PureWindowsPath(relative).is_absolute() or '..' in path.parts:
        raise DashboardError('프로젝트 밖의 경로는 읽거나 쓰지 않습니다.')
    root = Path(root).resolve(strict=True)
    target = (root / path).resolve(strict=exists)
    if not target.is_relative_to(root) or target == root:
        raise DashboardError('연결된 파일이 프로젝트 밖에 있습니다.')
    return target


def atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.dashboard-', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def encode(data):
    return (json.dumps(data, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def load_config(root):
    path = safe_path(root, FOLDER + '/dashboard.config.json')
    config = json.loads(path.read_text(encoding='utf-8'))
    if config.get('schemaVersion') != 1:
        raise DashboardError('지원하지 않는 대시보드 설정입니다.')
    if Path(config.get('projectRoot', '')).resolve() != Path(root).resolve():
        raise DashboardError('다른 프로젝트의 설정입니다. init --rebind로 새 프로젝트에 연결하세요.')
    if not isinstance(config.get('projectId'), str) or not config['projectId']:
        raise DashboardError('프로젝트 고유 번호가 없습니다.')
    for key in ('profilePath', 'registryPath', 'roadmapPath'):
        if config.get(key) is not None:
            safe_path(root, config[key], exists=False)
    return config


def init(root, *, rebind=False, name=None, registry=None, profile=None):
    root = Path(root).resolve(strict=True)
    folder = safe_path(root, FOLDER, exists=False)
    path = safe_path(root, FOLDER + '/dashboard.config.json', exists=False)
    if path.exists() and not rebind:
        config = load_config(root)
    else:
        # Preserve manual settings on an explicit project move/copy.
        old = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
        if path.exists():
            atomic(folder / f'config-before-rebind-{uuid.uuid4().hex}.json', path.read_bytes())
        config = {
            **old, 'schemaVersion': 1, 'toolVersion': VERSION,
            'projectId': str(uuid.uuid4()), 'projectRoot': str(root),
            'displayName': name or (old.get('displayName') if old else None) or root.name,
            'profilePath': profile or old.get('profilePath', 'planning/game-workflow-profile.md'),
            'registryPath': registry or old.get('registryPath', 'planning/workflow-runs/active.json'),
            'roadmapPath': old.get('roadmapPath'),
        }
        for key in ('profilePath', 'registryPath', 'roadmapPath'):
            if config.get(key) is not None:
                safe_path(root, config[key], exists=False)
        atomic(path, encode(config))
    launcher = """\"\"\"Open this project's dashboard; working directory does not matter.\"\"\"
from pathlib import Path
import runpy
import sys

root = Path(__file__).resolve().parents[2]
tool = root / '.agents/skills/game-workflow-supervision/scripts/dashboard.py'
if not tool.is_file():
    raise SystemExit('이 프로젝트의 대시보드 도구가 없습니다. 워크플로우 설치를 확인하세요.')
sys.argv = [str(tool), *(sys.argv[1:] or ['serve'])]
runpy.run_path(str(tool), run_name='__main__')
"""
    launcher_path = safe_path(root, FOLDER + '/open.py', exists=False)
    if not launcher_path.exists():
        atomic(launcher_path, launcher.encode('utf-8'))
    for filename in ('index.html', 'app.js', 'style.css'):
        atomic(safe_path(root, FOLDER + '/' + filename, exists=False), (ASSETS / filename).read_bytes())
    return update(root)


def clean(value):
    return re.sub(r'[`*]', '', str(value)).strip()


def sections(text):
    result, heading, lines = [], '', []
    for line in text.splitlines():
        match = re.match(r'^#{1,6}\s+(.+)', line)
        if match:
            result.append((heading, '\n'.join(lines)))
            heading, lines = match[1], []
        else:
            lines.append(line)
    result.append((heading, '\n'.join(lines)))
    return result


def tables(text):
    lines = text.splitlines()
    result = []
    for pos in range(len(lines) - 1):
        if not lines[pos].lstrip().startswith('|') or not re.match(r'^\s*\|[\s:|-]+\|\s*$', lines[pos + 1]):
            continue
        headers = [clean(cell).lower() for cell in re.split(r'(?<!\\)\|', lines[pos].strip().strip('|'))]
        rows = []
        for line in lines[pos + 2:]:
            if not line.lstrip().startswith('|'):
                break
            cells = [clean(cell).replace('\\|', '|') for cell in re.split(r'(?<!\\)\|', line.strip().strip('|'))]
            if len(cells) == len(headers):
                rows.append(dict(zip(headers, cells)))
        result.append(rows)
    return result


def cell(row, needles):
    for key, value in row.items():
        if any(needle in key for needle in needles):
            return value
    return ''


def execution(value):
    tokens = re.findall(r'\b[a-z]+(?:-[a-z]+)*\b', value.lower())
    return next((token for token in tokens if token in STATES), 'unknown')


def parse_record(text, source):
    parts = sections(text)
    checkpoints = [body for heading, body in parts
                   if re.search(r'current checkpoint|현재.*체크포인트', heading, re.I)
                   and not re.search(r'histor|역사', heading, re.I)]
    checkpoint = checkpoints[-1].strip() if checkpoints else ''
    title = next((heading for heading, _ in parts if heading), source['path'])
    tasks, skills, findings = [], [], []
    for heading, body in parts:
        task_section = bool(re.search(r'^tasks|작업과|작업 목록|^작업$|tasks\s*/', heading, re.I))
        finding_section = bool(re.search(r'^repair|^findings|^문제|발견된 문제|수리.*관찰', heading, re.I))
        usage_section = bool(re.search(r'^consumed skills|^사용 기록|^사용 확인', heading, re.I))
        if task_section:
            for rows in tables(body):
                for row in rows:
                    task_id = cell(row, ('task', '작업',))
                    if not task_id:
                        continue
                    raw_state = cell(row, ('state', '상태'))
                    skill_text = cell(row, ('skill', 'owner', '소유자', '담당'))
                    tasks.append({'id': task_id, 'description': cell(row, ('output', '산출', '결과', 'contract')),
                                  'state': execution(raw_state), 'stateText': raw_state or '확인되지 않음',
                                  'verdict': cell(row, ('verdict', '판정', '검사 결과')) or None,
                                  'validity': cell(row, ('validity', '유효')) or None, 'sourceId': source['id']})
                    for skill_id in dict.fromkeys(SKILL_RE.findall(skill_text)):
                        skills.append({'id': skill_id, 'name': SKILL_NAMES.get(skill_id, '전문 작업'),
                                       'taskId': task_id, 'usage': 'assigned', 'sourceId': source['id']})
        if usage_section:
            for rows in tables(body):
                for row in rows:
                    raw = cell(row, ('skill', '스킬'))
                    status = cell(row, ('usage', '사용', 'state', '상태')).lower()
                    confirmed = status in ('consumed', '사용 확인', '실제 사용')
                    for skill_id in dict.fromkeys(SKILL_RE.findall(raw)):
                        skills.append({'id': skill_id, 'name': SKILL_NAMES.get(skill_id, '전문 작업'),
                                       'taskId': cell(row, ('task', '작업')), 'usage': 'consumed' if confirmed else 'planned',
                                       'sourceId': source['id']})
        if finding_section:
            for rows in tables(body):
                for row in rows:
                    description = cell(row, ('finding', 'observation', '문제', '관찰'))
                    if description:
                        findings.append({'description': description, 'state': cell(row, ('state', '상태', 'disposition')) or '확인되지 않음',
                                         'nextAction': cell(row, ('next', '다음', 'repair owner', '소유자')), 'sourceId': source['id']})
    # All record text remains available as evidence. No inference from historical prose.
    return {'title': title, 'checkpoint': checkpoint[:12000], 'tasks': tasks, 'skills': skills, 'findings': findings}


def parse_json_record(root, text, source, entry):
    """Adapt one canonical state; source routes expose only declared record files."""
    filename = Path(__file__).with_name('workflow_state.py')
    spec = importlib.util.spec_from_file_location('dashboard_workflow_state', filename)
    if spec is None or spec.loader is None:
        raise DashboardError('공용 상태 도구가 없습니다.')
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    state = tool.validate(json.loads(text))
    if state['runId'] != entry['runId']:
        raise DashboardError('연결된 상태의 작업 번호가 다릅니다.')
    checked = tool.inspect(root, state)
    pointer_current = state['status'] == entry.get('status') and state['goalRevision'] == entry.get('goalRevision')
    checkpoint = state['checkpoint']
    summary = (f'현재 단계: {checkpoint["stage"]}\n{checkpoint["summary"]}\n'
               f'막힌 이유: {checkpoint["blocker"] or "없음으로 기록됨"}\n'
               f'다음 행동: {checkpoint["nextAction"]}\n'
               f'완료 조건: {"충족" if checked["ready"] else "미충족"} · 후보 근거: '
               f'{ {"current": "현재 버전에 맞음", "stale": "이전 버전", "unknown": "미고정"}[checked["candidateValidity"]] }')
    if checked['issues']:
        summary += '\n확인 필요: ' + '; '.join(checked['issues'])
    outcomes_by_task = {task['id']: [] for task in state['contract']['tasks']}
    for kind in ('checks', 'reviews'):
        contracts = {item['id']: item for item in state['contract'][kind]}
        for outcome in checked[kind]:
            for task_id in contracts[outcome['id']]['taskIds']:
                outcomes_by_task[task_id].append(outcome)
    tasks = []
    for task in state['contract']['tasks']:
        applicable = outcomes_by_task[task['id']]
        task_state = state['taskStates'][task['id']]
        tasks.append({'id': task['id'], 'description': task['title'], 'state': task_state['state'],
                      'stateText': task_state['state'],
                      'verdict': 'pass' if applicable and all(item['ready'] for item in applicable) else
                                 'fail' if any(item['verdict'] == 'fail' for item in applicable) else 'pending',
                      'validity': 'current' if applicable and all(item['ready'] for item in applicable) else
                                  'stale' if any(item['validity'] == 'stale' for item in applicable) else 'unknown',
                      'sourceId': source['id']})
    skills = [{'id': item['skillId'], 'name': SKILL_NAMES.get(item['skillId'], '전문 작업'),
               'taskId': item['taskId'], 'usage': item['usage'], 'sourceId': source['id']} for item in state['skills']]
    findings = [{'description': item['description'], 'state': item['state'],
                 'nextAction': item['nextAction'], 'sourceId': source['id']} for item in state['findings']]
    if not pointer_current:
        findings.append({'description': '등록 상태와 현재 작업 기록이 다릅니다.', 'state': '기록 확인 필요',
                         'nextAction': '전체 감독이 자신의 pointer를 sync로 갱신합니다.', 'sourceId': source['id']})
        summary += '\n등록 상태와 현재 기록이 달라 갱신이 필요합니다.'
    return {'title': state['title'], 'checkpoint': summary[:12000], 'tasks': tasks, 'skills': skills,
            'findings': findings, 'canonicalState': state['status'], 'completionReady': checked['ready'],
            'candidateValidity': checked['candidateValidity'], 'pointerCurrent': pointer_current,
            'recordFormat': 'workflow-run@1'}


def valid_text(value):
    return isinstance(value, str) and bool(value) and value == value.strip()


def progress(roadmap):
    unknown = {'state': 'unknown', 'reason': '전체 범위 미정', 'percent': None, 'items': []}
    if roadmap is None:
        return unknown
    if not isinstance(roadmap, dict) or type(roadmap.get('schemaVersion')) is not int or roadmap.get('schemaVersion') != 1 or not roadmap.get('scopeRevision'):
        raise DashboardError('개발 항목 목록의 형식 또는 범위 번호를 확인하세요.')
    if roadmap.get('scopeState') not in (None, 'known', 'unknown'):
        raise DashboardError('개발 범위 상태를 확인하세요.')
    if roadmap.get('scopeState') == 'unknown':
        return unknown
    items = roadmap.get('items')
    if not isinstance(items, list) or not items:
        return unknown
    ids, result, all_criteria_ids = set(), [], set()
    criteria_count = 0
    passed_count = 0
    for item in items:
        if not isinstance(item, dict) or not item.get('id') or item['id'] in ids:
            raise DashboardError('개발 항목 번호가 없거나 중복되었습니다.')
        ids.add(item['id'])
        if not isinstance(item.get('inScope', True), bool):
            raise DashboardError('개발 항목의 범위 포함 여부가 확인되지 않습니다.')
        if item.get('inScope', True) is False:
            continue
        criteria = item.get('criteria')
        decisions = item.get('decisions')
        candidate = item.get('candidate') or {}
        if not isinstance(criteria, list) or not criteria or not isinstance(decisions, list):
            raise DashboardError('필수 검사 목록과 필요한 승인 목록을 명시하세요. 없으면 빈 승인 목록을 사용하세요.')
        digest = candidate.get('digest')
        identity_ok = isinstance(digest, str) and bool(re.fullmatch(r'[a-f0-9]{64}', digest)) and valid_text(candidate.get('id'))
        seen = set()
        passed = 0
        for criterion in criteria:
            if (not isinstance(criterion, dict) or not criterion.get('id')
                    or criterion['id'] in seen or criterion['id'] in all_criteria_ids):
                raise DashboardError('필수 검사 번호가 없거나 중복되었습니다.')
            seen.add(criterion['id'])
            all_criteria_ids.add(criterion['id'])
            valid = (identity_ok and criterion.get('verdict') == 'pass' and criterion.get('validity') == 'current'
                     and criterion.get('candidateDigest') == digest and valid_text(criterion.get('evidenceLocator'))
                     and valid_text(criterion.get('producerId')) and valid_text(criterion.get('verifierId'))
                     and criterion['producerId'] != criterion['verifierId'])
            passed += int(valid)
        decision_ok = all(isinstance(decision, dict) and decision.get('state') == 'approved'
                          and decision.get('candidateDigest') == digest and valid_text(decision.get('authorityLocator'))
                          for decision in decisions)
        complete = item.get('acceptanceState') == 'accepted' and passed == len(criteria) and decision_ok
        result.append({'id': item['id'], 'title': item.get('title', item['id']), 'complete': complete,
                       'state': item.get('acceptanceState', 'unknown'), 'passed': passed, 'total': len(criteria)})
        criteria_count += len(criteria)
        passed_count += passed
    if not result:
        return unknown
    completed = sum(item['complete'] for item in result)
    return {'state': 'known', 'scopeRevision': roadmap['scopeRevision'], 'items': result,
            'completed': completed, 'total': len(result), 'percent': round(100 * completed / len(result)),
            'criteriaPassed': passed_count, 'criteriaTotal': criteria_count, 'reason': '같은 비중'}


def collect(root):
    root = Path(root).resolve(strict=True)
    for attempt in range(2):
        config = load_config(root)
        blobs, sources = {}, []

        def read(relative, optional=False):
            path = safe_path(root, relative, exists=False)
            if not path.exists():
                if optional:
                    blobs[relative] = None
                    return None
                raise DashboardError(f'기록이 없습니다: {relative}')
            if not path.is_file():
                raise DashboardError('자료 경로가 파일이 아닙니다.')
            content = path.read_bytes()
            if len(content) > 4 * 1024 * 1024:
                raise DashboardError('기록 파일이 너무 큽니다. 4MiB 이하의 기록을 연결하세요.')
            blobs[relative] = content
            sources.append({'id': str(len(sources)), 'path': relative, 'digest': sha(content),
                            'updatedAt': datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()})
            return content.decode('utf-8-sig')

        config_relative = FOLDER + '/dashboard.config.json'
        if json.loads(read(config_relative)) != config:
            continue
        profile = read(config['profilePath'], optional=True) if config.get('profilePath') else None
        registry_text = read(config['registryPath'], optional=True)
        registry = json.loads(registry_text) if registry_text is not None else {'schemaVersion': 1, 'runs': []}
        if registry.get('schemaVersion') != 1 or not isinstance(registry.get('runs'), list):
            raise DashboardError('지원하지 않는 작업 목록 형식입니다.')
        runs, ids = [], set()
        for entry in registry['runs']:
            run_id = entry.get('runId')
            if not isinstance(run_id, str) or not run_id or run_id in ids:
                raise DashboardError('작업 번호가 없거나 중복되었습니다.')
            ids.add(run_id)
            raw = read(entry.get('recordPath'))
            source = sources[-1]
            if entry['recordPath'].endswith('.json'):
                parsed = parse_json_record(root, raw, source, entry)
            else:
                parsed = parse_record(raw, source)
            status = entry.get('status', 'unknown')
            display_state = ('needs-reconciliation' if parsed.get('pointerCurrent') is False else
                             parsed.get('canonicalState', status))
            runs.append({'id': run_id, 'state': display_state if display_state in STATES else 'unknown',
                         'registeredState': status, 'goalRevision': entry.get('goalRevision'),
                         'observation': 'recorded-only', 'sourceId': source['id'], **parsed})
            if status in ('blocked', 'needs-clarification', 'needs-reconciliation'):
                parsed['findings'].append({'description': '진행을 막는 상태가 등록되어 있습니다. 현재 기록을 확인하세요.',
                                          'state': '등록 상태 확인 필요', 'nextAction': '', 'sourceId': source['id']})
        roadmap = json.loads(read(config['roadmapPath'])) if config.get('roadmapPath') else None
        development = progress(roadmap)
        changed = False
        for relative, content in blobs.items():
            path = safe_path(root, relative, exists=False)
            current = path.read_bytes() if path.is_file() else None
            if current != content:
                changed = True
                break
        if changed:
            continue
        return {'schemaVersion': 1, 'toolVersion': VERSION,
                'project': {'id': config['projectId'], 'name': config['displayName']},
                'collectedAt': now(), 'sourceUpdatedAt': max((s['updatedAt'] for s in sources), default=None),
                'sourceDigest': sha(encode([(s['path'], s['digest']) for s in sources])),
                'freshness': 'current', 'readErrors': [], 'observation': 'recorded-only',
                'runs': runs, 'development': development, 'sources': sources,
                'limitations': ['화면은 작업 기록을 보여줍니다. 실제 작업자의 활동은 확인하지 않습니다.',
                                '표로 정리되지 않은 내용과 과거 결과는 원문에서 확인하세요.']}
    raise DashboardError('기록이 변경 중입니다. 잠시 뒤 다시 읽으세요.')


def update(root):
    data = collect(root)
    atomic(safe_path(root, FOLDER + '/snapshot.json', exists=False), encode(data))
    return data


class Reader:
    def __init__(self, root):
        self.root = Path(root)
        self.last = None
        try:
            config = load_config(root)
            saved = json.loads(safe_path(root, FOLDER + '/snapshot.json').read_text(encoding='utf-8'))
            if saved.get('project', {}).get('id') == config['projectId'] and saved.get('schemaVersion') == 1:
                self.last = saved
        except (ValueError, OSError, TypeError):
            pass

    def get(self):
        try:
            self.last = collect(self.root)
            return self.last
        except (ValueError, OSError, KeyError, TypeError) as exc:
            # A project-binding failure must not expose a previous project's records.
            try:
                config = load_config(self.root)
            except (ValueError, OSError, TypeError):
                raise DashboardError(str(exc)) from exc
            if self.last is None or self.last['project']['id'] != config['projectId']:
                raise DashboardError(str(exc)) from exc
            return {**self.last, 'freshness': 'stale', 'readErrors': [str(exc)]}


def create_server(root, port=0):
    reader = Reader(root)
    # Serve a frozen asset set, never the project directory.
    assets = {'/': ('text/html; charset=utf-8', (ASSETS / 'index.html').read_bytes()),
              '/app.js': ('text/javascript; charset=utf-8', (ASSETS / 'app.js').read_bytes()),
              '/style.css': ('text/css; charset=utf-8', (ASSETS / 'style.css').read_bytes())}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def reply(self, status, kind, body):
            self.send_response(status)
            self.send_header('Content-Type', kind)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            expected = f'127.0.0.1:{self.server.server_port}'
            origin = self.headers.get('Origin')
            if self.headers.get('Host') != expected or (origin and origin != f'http://{expected}'):
                self.reply(403, 'text/plain; charset=utf-8', '허용되지 않는 접근입니다.'.encode())
                return
            try:
                if self.path in assets:
                    self.reply(200, *assets[self.path])
                elif self.path in ('/snapshot.json', '/api/status'):
                    self.reply(200, 'application/json; charset=utf-8', encode(reader.get()))
                elif re.fullmatch(r'/source/\d+', self.path):
                    snapshot = reader.get()
                    source_id = self.path.rsplit('/', 1)[-1]
                    source = next((s for s in snapshot['sources'] if s['id'] == source_id), None)
                    # Local configuration contains binding paths; it is not an evidence page.
                    if source is None or source['path'] == FOLDER + '/dashboard.config.json':
                        self.reply(404, 'text/plain', b'Not found')
                        return
                    content = safe_path(root, source['path']).read_bytes()
                    if sha(content) != source['digest']:
                        self.reply(409, 'text/plain; charset=utf-8', '원본이 바뀌었습니다. 목록을 갱신하세요.'.encode())
                        return
                    self.reply(200, 'text/plain; charset=utf-8', content)
                else:
                    self.reply(404, 'text/plain', b'Not found')
            except (ValueError, OSError, KeyError, TypeError) as exc:
                self.reply(503, 'application/json; charset=utf-8', encode({'error': str(exc)}))

    return HTTPServer(('127.0.0.1', port), Handler)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('init', 'update', 'serve'), nargs='?', default='serve')
    parser.add_argument('--port', type=int, default=0)
    parser.add_argument('--no-browser', action='store_true')
    parser.add_argument('--rebind', action='store_true')
    parser.add_argument('--name')
    parser.add_argument('--registry')
    parser.add_argument('--profile')
    args = parser.parse_args(argv)
    try:
        root = project_root()
        if args.command == 'init':
            data = init(root, rebind=args.rebind, name=args.name, registry=args.registry, profile=args.profile)
            print(json.dumps({'project': data['project'], 'dashboard': str(root / FOLDER)}, ensure_ascii=False))
        elif args.command == 'update':
            data = update(root)
            print(json.dumps({'project': data['project'], 'sourceDigest': data['sourceDigest']}, ensure_ascii=False))
        else:
            if not safe_path(root, FOLDER + '/dashboard.config.json', exists=False).exists():
                init(root)
            load_config(root)
            server = create_server(root, args.port)
            url = f'http://127.0.0.1:{server.server_port}/'
            print(url, flush=True)
            if not args.no_browser:
                webbrowser.open(url)
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                pass
            finally:
                server.server_close()
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.exit(1, f'대시보드 오류: {exc}\n')


if __name__ == '__main__':
    main()
