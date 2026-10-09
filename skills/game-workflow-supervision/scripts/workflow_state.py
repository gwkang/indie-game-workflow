"""One project-owned workflow record; validates declared consistency, not authority."""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import sys

VERSION = '1.0.0'
RUN_FOLDER = 'planning/workflow-runs'
DASHBOARD_FOLDER = 'planning/workflow-dashboard'
OPEN_STATUSES = {'needs-clarification', 'needs-reconciliation', 'ready', 'running', 'blocked'}
STATUSES = OPEN_STATUSES | {'completed', 'cancelled'}
TASK_STATES = {'pending', 'ready', 'running', 'completed', 'failed', 'blocked', 'cancelled', 'skipped'}
EXECUTION_STATES = {'pending', 'running', 'completed', 'failed', 'cancelled'}
VERDICTS = {'pending', 'pass', 'fail', 'inconclusive'}
RECORD_KINDS = {'checkpoint', 'task', 'check', 'review', 'decision', 'skill', 'finding', 'measurement', 'scope'}
_MODULES = {}


class StateError(ValueError):
    pass


def module_at(name, filename):
    path = Path(filename).resolve()
    key = str(path)
    if key not in _MODULES:
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise StateError('공용 도구를 읽지 못했습니다.')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _MODULES[key] = module
    return _MODULES[key]


def dashboard_tool():
    return module_at('workflow_dashboard_support', Path(__file__).with_name('dashboard.py'))


def registry_tool(root):
    return module_at('workflow_registry_support', safe(root, '.agents/skills/game-workflow/scripts/workflow_run_registry.py'))


def project_root():
    return dashboard_tool().project_root(__file__)


def safe(root, relative, *, exists=True):
    return dashboard_tool().safe_path(root, relative, exists=exists)


def standard(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def digest(value):
    return hashlib.sha256(standard(value)).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def fail(message):
    raise StateError(message)


def text(value, field, *, empty=False):
    if not isinstance(value, str) or (not empty and (not value or value != value.strip())):
        fail(f'{field}: 빈값이나 앞뒤 공백 없는 문자열이 필요합니다.')
    return value


def integer(value, field, *, minimum=1):
    if type(value) is not int or value < minimum:
        fail(f'{field}: 정수가 필요합니다.')
    return value


def boolean(value, field):
    if type(value) is not bool:
        fail(f'{field}: true/false가 필요합니다.')


def enum(value, allowed, field):
    if not isinstance(value, str) or value not in allowed:
        fail(f'{field}: 지원하지 않는 값입니다.')


def shape(value, required, optional=(), field='record'):
    if not isinstance(value, dict) or not set(required) <= set(value) or not set(value) <= set(required) | set(optional):
        fail(f'{field}: 필드가 없거나 지원하지 않는 필드가 있습니다.')


def strings(value, field, *, empty=True):
    if not isinstance(value, list) or (not empty and not value):
        fail(f'{field}: 문자열 목록이 필요합니다.')
    for item in value:
        text(item, field)
    if len(value) != len(set(value)):
        fail(f'{field}: 중복 항목입니다.')
    return value


def rows(value, field):
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        fail(f'{field}: 객체 목록이 필요합니다.')
    return value


def hashes(value, field):
    if not isinstance(value, str) or not re.fullmatch(r'[0-9a-f]{64}', value):
        fail(f'{field}: SHA256 지문이 필요합니다.')


def relative(value, field):
    text(value, field)
    # The same lexical and real-path contract is used by the dashboard.
    if '\\' in value or ':' in value or value.startswith('/') or '..' in Path(value).parts:
        fail(f'{field}: 프로젝트 내부 상대 경로만 사용합니다.')
    if Path(value).as_posix() != value or value in ('', '.'):
        fail(f'{field}: 정규 상대 경로가 필요합니다.')
    return value


def refs(value, allowed, field, *, empty=True):
    strings(value, field, empty=empty)
    if not set(value) <= set(allowed):
        fail(f'{field}: 등록되지 않은 ID입니다.')


def keyed(value, field):
    result = {}
    for item in rows(value, field):
        item_id = text(item.get('id'), field + '.id')
        if item_id in result:
            fail(f'{field}: 중복 ID입니다.')
        result[item_id] = item
    return result


def evidence_shape(value):
    seen = set()
    for item in rows(value, 'evidence'):
        shape(item, {'path', 'digest'}, field='evidence')
        relative(item['path'], 'evidence.path')
        hashes(item['digest'], 'evidence.digest')
        if item['path'] in seen:
            fail('evidence: 중복 경로입니다.')
        seen.add(item['path'])


def validate_contract(contract):
    shape(contract, {'criteria', 'tasks', 'checks', 'reviews', 'decisions'}, field='contract')
    criteria = keyed(contract['criteria'], 'criteria')
    tasks = keyed(contract['tasks'], 'tasks')
    checks = keyed(contract['checks'], 'checks')
    reviews = keyed(contract['reviews'], 'reviews')
    decisions = keyed(contract['decisions'], 'decisions')
    if not criteria or not tasks or not checks or not reviews:
        fail('필수 기준·작업·검사·별도 검토 집합이 비었습니다.')
    for item in criteria.values():
        shape(item, {'id', 'text'}, field='criterion')
        text(item['text'], 'criterion.text')
    for item in tasks.values():
        shape(item, {'id', 'title', 'skillId', 'producerId', 'criterionIds', 'required'}, field='task')
        for name in ('title', 'skillId', 'producerId'):
            text(item[name], 'task.' + name)
        boolean(item['required'], 'task.required')
        refs(item['criterionIds'], criteria, 'task.criterionIds', empty=False)
    for group, items in (('check', checks), ('review', reviews)):
        for item in items.values():
            required = {'id', 'criterionIds', 'taskIds'}
            if group == 'check':
                required |= {'expectedNames', 'mode'}
            shape(item, required, field=group)
            refs(item['criterionIds'], criteria, group + '.criterionIds', empty=False)
            refs(item['taskIds'], tasks, group + '.taskIds', empty=False)
            task_criteria = {criterion for task_id in item['taskIds'] for criterion in tasks[task_id]['criterionIds']}
            if not set(item['criterionIds']) <= task_criteria or any(
                    not set(tasks[task_id]['criterionIds']).intersection(item['criterionIds']) for task_id in item['taskIds']):
                fail(f'{group}: 작업과 기준의 연결이 다릅니다.')
            if group == 'check':
                strings(item['expectedNames'], 'check.expectedNames', empty=False)
                enum(item['mode'], {'command', 'observation'}, 'check.mode')
    for item in decisions.values():
        shape(item, {'id', 'criterionIds'}, field='decision')
        refs(item['criterionIds'], criteria, 'decision.criterionIds', empty=False)
    required_tasks = {key for key, item in tasks.items() if item['required']}
    if not required_tasks:
        fail('필수 산출물 작업이 없습니다.')
    for group, items in (('check', checks), ('review', reviews)):
        covered_criteria = {key for item in items.values() for key in item['criterionIds']}
        covered_tasks = {key for item in items.values() for key in item['taskIds']}
        if covered_criteria != set(criteria) or not required_tasks <= covered_tasks:
            fail(f'{group}: 필수 기준/작업의 커버리지가 없습니다.')
    return contract


def validate_result(result, contracts):
    common = {'eventId', 'kind', 'contractId', 'goalRevision', 'candidateId', 'candidateDigest',
              'actorId', 'criterionIds', 'taskIds', 'executionState', 'verdict', 'evidence'}
    kind = result.get('kind')
    enum(kind, {'check', 'review', 'decision'}, 'result.kind')
    extra = {'check': {'completedNames', 'failedNames', 'timedOut'},
             'review': {'evidenceDigest'}, 'decision': {'authorityId', 'state'}}[kind]
    shape(result, common | extra, {'command', 'exitCode', 'note'}, field='result')
    for name in ('eventId', 'contractId', 'candidateId', 'actorId'):
        text(result[name], 'result.' + name)
    integer(result['goalRevision'], 'result.goalRevision')
    hashes(result['candidateDigest'], 'result.candidateDigest')
    strings(result['criterionIds'], 'result.criterionIds', empty=False)
    strings(result['taskIds'], 'result.taskIds')
    enum(result['executionState'], EXECUTION_STATES, 'result.executionState')
    enum(result['verdict'], VERDICTS, 'result.verdict')
    evidence_shape(result['evidence'])
    if 'note' in result:
        text(result['note'], 'result.note', empty=True)
    if kind == 'check':
        strings(result['completedNames'], 'completedNames')
        strings(result['failedNames'], 'failedNames')
        boolean(result['timedOut'], 'timedOut')
        if 'exitCode' in result and result['exitCode'] is not None:
            if type(result['exitCode']) is not int:
                fail('exitCode: 정수가 필요합니다.')
        if 'command' in result:
            text(result['command'], 'command')
    elif kind == 'review':
        hashes(result['evidenceDigest'], 'evidenceDigest')
    else:
        text(result['authorityId'], 'authorityId')
        enum(result['state'], {'pending', 'approved', 'rejected'}, 'decision.state')
    # History from old goal revisions remains readable; only the current contract is matched below.
    if result['goalRevision'] == contracts.get('goalRevision'):
        contract = next((item for item in contracts[kind + 's'] if item['id'] == result['contractId']), None)
        if contract is None:
            fail('결과의 contractId가 현재 계약에 없습니다.')
        if set(result['criterionIds']) != set(contract['criterionIds']) or set(result['taskIds']) != set(contract.get('taskIds', [])):
            fail('결과의 기준/작업 집합이 현재 계약과 다릅니다.')


def validate_skills(skills, task_ids):
    for skill in rows(skills, 'skills'):
        shape(skill, {'skillId', 'taskId', 'usage', 'actorId'}, field='skill')
        for name in ('skillId', 'taskId', 'actorId'):
            text(skill[name], 'skill.' + name)
        if skill['taskId'] not in task_ids:
            fail('skill.taskId가 해당 범위의 계약에 없습니다.')
        enum(skill['usage'], {'planned', 'assigned', 'consumed'}, 'skill.usage')


def validate(state):
    required = {'schemaVersion', 'recordType', 'runId', 'title', 'revision', 'goalRevision', 'supervisorId',
                'status', 'registryPath', 'discovery', 'authority', 'checkpoint', 'contract', 'candidate',
                'taskStates', 'results', 'skills', 'findings', 'measurements', 'events', 'createdAt', 'updatedAt'}
    shape(state, required, {'supersedesRecordPath'}, field='state')
    if type(state['schemaVersion']) is not int or state['schemaVersion'] != 1 or state['recordType'] != 'workflow-run':
        fail('지원하지 않는 상태 형식입니다.')
    if not isinstance(state['runId'], str) or not re.fullmatch(r'[a-z0-9][a-z0-9-]*', state['runId']):
        fail('runId가 잘못되었습니다.')
    for name in ('title', 'supervisorId', 'createdAt', 'updatedAt'):
        text(state[name], name)
    integer(state['revision'], 'revision')
    integer(state['goalRevision'], 'goalRevision')
    enum(state['status'], STATUSES, 'status')
    relative(state['registryPath'], 'registryPath')
    if 'supersedesRecordPath' in state:
        relative(state['supersedesRecordPath'], 'supersedesRecordPath')
    shape(state['discovery'], {'goalKeys', 'targetPaths'}, {'conversationKey'}, field='discovery')
    strings(state['discovery']['goalKeys'], 'goalKeys')
    strings(state['discovery']['targetPaths'], 'targetPaths')
    if state['discovery'].get('conversationKey') is not None:
        text(state['discovery']['conversationKey'], 'conversationKey')
    shape(state['authority'], {'cursor', 'summary', 'scope', 'excluded'}, field='authority')
    text(state['authority']['cursor'], 'authority.cursor')
    text(state['authority']['summary'], 'authority.summary')
    strings(state['authority']['scope'], 'authority.scope', empty=False)
    strings(state['authority']['excluded'], 'authority.excluded')
    shape(state['checkpoint'], {'stage', 'summary', 'blocker', 'nextAction'}, field='checkpoint')
    for name in ('stage', 'summary', 'nextAction'):
        text(state['checkpoint'][name], 'checkpoint.' + name)
    text(state['checkpoint']['blocker'], 'checkpoint.blocker', empty=True)
    validate_contract(state['contract'])
    task_ids = {item['id'] for item in state['contract']['tasks']}
    if not isinstance(state['taskStates'], dict) or set(state['taskStates']) != task_ids:
        fail('taskStates 집합이 계약과 다릅니다.')
    for item in state['taskStates'].values():
        shape(item, {'state'}, {'resultPath'}, field='taskState')
        enum(item['state'], TASK_STATES, 'taskState.state')
        if item.get('resultPath') is not None:
            relative(item['resultPath'], 'resultPath')
    if state['candidate'] is not None:
        candidate = state['candidate']
        shape(candidate, {'id', 'digest', 'files', 'producerIds'}, field='candidate')
        text(candidate['id'], 'candidate.id')
        hashes(candidate['digest'], 'candidate.digest')
        strings(candidate['producerIds'], 'candidate.producerIds', empty=False)
        evidence_shape(candidate['files'])
        if not candidate['files']:
            fail('후보 파일이 없습니다.')
        expected = digest(sorted([[row['path'], row['digest']] for row in candidate['files']]))
        if expected != candidate['digest']:
            fail('후보 manifest의 지문이 다릅니다.')
    event_ids = set()
    for event in rows(state['events'], 'events'):
        shape(event, {'eventId', 'kind', 'payloadDigest', 'recordedAt', 'previousRevision', 'revision'}, {'previous'}, field='event')
        text(event['eventId'], 'eventId')
        text(event['kind'], 'event.kind')
        hashes(event['payloadDigest'], 'event.payloadDigest')
        text(event['recordedAt'], 'recordedAt')
        integer(event['previousRevision'], 'previousRevision', minimum=0)
        integer(event['revision'], 'event.revision')
        if event['eventId'] in event_ids:
            fail('중복 eventId입니다.')
        event_ids.add(event['eventId'])
        if event['kind'] == 'scope':
            previous = event.get('previous')
            if not isinstance(previous, dict) or not {'goalRevision', 'contract', 'skills'} <= set(previous):
                fail('scope 이전 사용 기록과 계약이 없습니다.')
            integer(previous['goalRevision'], 'scope.previous.goalRevision')
            validate_contract(previous['contract'])
            validate_skills(previous['skills'], {task['id'] for task in previous['contract']['tasks']})
    result_ids = set()
    contracts = {**state['contract'], 'goalRevision': state['goalRevision']}
    for result in rows(state['results'], 'results'):
        validate_result(result, contracts)
        if result['eventId'] in result_ids or result['eventId'] not in event_ids:
            fail('결과의 eventId가 중복되거나 이력에 없습니다.')
        result_ids.add(result['eventId'])
    validate_skills(state['skills'], task_ids)
    keyed(state['findings'], 'findings')
    for finding in state['findings']:
        shape(finding, {'id', 'description', 'state', 'blocksCompletion', 'nextAction'}, field='finding')
        text(finding['description'], 'finding.description')
        text(finding['nextAction'], 'finding.nextAction', empty=True)
        enum(finding['state'], {'open', 'resolved', 'deferred'}, 'finding.state')
        boolean(finding['blocksCompletion'], 'blocksCompletion')
    keyed(state['measurements'], 'measurements')
    for measurement in state['measurements']:
        shape(measurement, {'id', 'scope', 'metric', 'kind', 'value', 'unit', 'source'}, field='measurement')
        enum(measurement['scope'], {'behavior-test', 'real-work'}, 'measurement.scope')
        enum(measurement['kind'], {'measured', 'estimated', 'unmeasured'}, 'measurement.kind')
        for name in ('metric', 'unit', 'source'):
            text(measurement[name], 'measurement.' + name)
        value = measurement['value']
        if measurement['kind'] == 'unmeasured':
            if value is not None:
                fail('미측정 value는 null입니다.')
        elif type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            fail('측정 value는 유한한 음수 아닌 숫자입니다.')
    return state


def state_relative(run_id):
    if not isinstance(run_id, str) or not re.fullmatch(r'[a-z0-9][a-z0-9-]*', run_id):
        fail('runId가 잘못되었습니다.')
    return f'{RUN_FOLDER}/{run_id}/state.json'


def load_state(root, run_id):
    path = safe(root, state_relative(run_id))
    raw = path.read_bytes()
    state = validate(json.loads(raw.decode('utf-8-sig')))
    if state['runId'] != run_id:
        fail('상태의 runId와 요청이 다릅니다.')
    return state, raw


def file_digest(path):
    if not path.is_file():
        fail('파일이 없거나 일반 파일이 아닙니다.')
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def forbidden_paths(root, state):
    names = [state_relative(state['runId']), state['registryPath']]
    names += [DASHBOARD_FOLDER + '/' + name for name in
              ('dashboard.config.json', 'snapshot.json', 'index.html', 'app.js', 'style.css', 'open.py')]
    return [safe(root, name, exists=False) for name in names]


def inspect_files(root, state, references, observed):
    forbidden = forbidden_paths(root, state)
    seen, errors = set(), []
    for reference in references:
        path = safe(root, reference['path'], exists=False)
        physical = os.path.normcase(str(path))
        if physical in seen:
            fail('파일 참조가 같은 실제 경로를 중복 연결합니다.')
        seen.add(physical)
        for excluded in forbidden:
            if path == excluded or (excluded.is_file() and path.is_file() and os.path.samefile(path, excluded)):
                fail('상태·레지스트리·생성 대시보드는 후보/실행 증거가 아닙니다.')
        current = file_digest(path) if path.is_file() else None
        if path.exists() and not path.is_file():
            fail('파일 참조가 일반 파일이 아닙니다.')
        previous = observed.get(str(path))
        if previous is not None and previous[1] != current:
            fail('확인 중 같은 원본 파일이 변경되었습니다.')
        observed[str(path)] = (path, current)
        if current != reference['digest']:
            errors.append(reference['path'])
    return errors


def latest_results(state, kind):
    selected = {}
    for result in state['results']:
        if result['kind'] == kind and result['goalRevision'] == state['goalRevision']:
            selected[result['contractId']] = result
    return selected


def inspect(root, state):
    """Read-only consistency result. Raw files are hashed, never published as sources."""
    validate(state)
    issues, observed, checks, reviews, decisions = [], {}, [], [], []
    candidate = state['candidate']
    candidate_validity = 'unknown'
    if candidate is None:
        issues.append('현재 후보가 고정되지 않았습니다.')
    else:
        drift = inspect_files(root, state, candidate['files'], observed)
        candidate_validity = 'stale' if drift else 'current'
        if drift:
            issues.append('후보 파일이 변경되었습니다: ' + ', '.join(drift))
    required_tasks = [task for task in state['contract']['tasks'] if task['required']]
    for task in required_tasks:
        if state['taskStates'][task['id']]['state'] != 'completed':
            issues.append('필수 작업 미완료: ' + task['id'])
    for finding in state['findings']:
        if finding['blocksCompletion'] and finding['state'] != 'resolved':
            issues.append('완료를 막는 문제: ' + finding['id'])

    def result_current(result):
        return bool(candidate and result['candidateId'] == candidate['id'] and
                    result['candidateDigest'] == candidate['digest'] and
                    result['goalRevision'] == state['goalRevision'] and candidate_validity == 'current')

    for kind, output in (('check', checks), ('decision', decisions)):
        latest = latest_results(state, kind)
        for contract in state['contract'][kind + 's']:
            result = latest.get(contract['id'])
            evidence_drift = inspect_files(root, state, result['evidence'], observed) if result else []
            reason = None
            if result is None:
                reason = '실제 반환 없음'
            elif not result_current(result):
                reason = '이전 후보/범위의 결과'
            elif not result['evidence']:
                reason = '원본 증거 없음'
            elif evidence_drift:
                reason = '원본 증거 변경'
            elif result['executionState'] != 'completed' or result['verdict'] != 'pass':
                reason = '완료된 통과 결과 아님'
            elif kind == 'check':
                if result['timedOut'] or result['failedNames'] or set(result['completedNames']) != set(contract['expectedNames']):
                    reason = '완료 항목 누락/실패/시간 초과'
                elif contract['mode'] == 'command' and (result.get('exitCode') != 0 or type(result.get('exitCode')) is not int or not result.get('command')):
                    reason = '명령의 실제 성공 종료 정보 없음'
            elif result['state'] != 'approved':
                reason = '필수 승인 없음'
            stale = result and (not result_current(result) or reason == '원본 증거 변경')
            item = {'id': contract['id'], 'validity': 'current' if reason is None else 'stale' if stale else 'unknown',
                    'verdict': result['verdict'] if result else 'pending', 'ready': reason is None, 'reason': reason,
                    'result': result}
            output.append(item)
            if reason:
                issues.append(f'{kind} {contract["id"]}: {reason}')
    evidence_payload = {
        'goalRevision': state['goalRevision'], 'contract': state['contract'], 'candidate': candidate,
        'taskStates': {task['id']: state['taskStates'][task['id']] for task in required_tasks},
        'blockingFindings': [finding for finding in state['findings'] if finding['blocksCompletion']],
        'checks': [item['result'] for item in checks], 'decisions': [item['result'] for item in decisions],
        'currentRawEvidence': {reference['path']: observed[str(safe(root, reference['path'], exists=False))][1]
                               for item in checks + decisions if item['result']
                               for reference in item['result']['evidence']},
    }
    evidence_digest = digest(evidence_payload)
    latest = latest_results(state, 'review')
    for contract in state['contract']['reviews']:
        result = latest.get(contract['id'])
        reason = None
        authors = set(candidate['producerIds']) if candidate else set()
        authors.update(task['producerId'] for task in state['contract']['tasks'] if task['id'] in contract['taskIds'])
        if result is None:
            reason = '별도 검토 반환 없음'
        elif not result_current(result) or result['evidenceDigest'] != evidence_digest:
            reason = '검토한 후보/증거가 현재와 다름'
        elif result['actorId'] in authors:
            reason = '작성자와 검토자가 같음'
        elif not result['evidence']:
            reason = '검토 원문 없음'
        elif inspect_files(root, state, result['evidence'], observed):
            reason = '검토 원문 변경'
        elif result['executionState'] != 'completed' or result['verdict'] != 'pass':
            reason = '완료된 통과 검토 아님'
        stale = result and (not result_current(result) or reason in ('검토한 후보/증거가 현재와 다름', '검토 원문 변경'))
        item = {'id': contract['id'], 'validity': 'current' if reason is None else 'stale' if stale else 'unknown',
                'verdict': result['verdict'] if result else 'pending', 'ready': reason is None, 'reason': reason}
        reviews.append(item)
        if reason:
            issues.append(f'review {contract["id"]}: {reason}')
    for path, before in observed.values():
        if (file_digest(path) if path.is_file() else None) != before:
            fail('확인 중 파일이 변경되었습니다. 안정된 입력에서 다시 확인하세요.')
    return {'ready': not issues, 'candidateValidity': candidate_validity, 'evidenceDigest': evidence_digest,
            'issues': issues, 'checks': checks, 'reviews': reviews, 'decisions': decisions,
            'observation': 'declared-consistency-only'}


def verify_result_files(root, state, result):
    inspect_files(root, state, result['evidence'], {})
    if any(file_digest(safe(root, item['path'])) != item['digest'] for item in result['evidence']):
        fail('입력한 결과의 원본 증거 지문이 다릅니다.')


def append_event(state, event_id, kind, payload, previous=None):
    row = {'eventId': event_id, 'kind': kind, 'payloadDigest': digest(payload), 'recordedAt': now(),
           'previousRevision': state['revision'], 'revision': state['revision'] + 1}
    if previous is not None:
        row['previous'] = previous
    state['events'].append(row)
    state['revision'] += 1
    state['updatedAt'] = row['recordedAt']


def save_state(root, state, expected_raw):
    validate(state)
    path = safe(root, state_relative(state['runId']), exists=False)
    current = path.read_bytes() if path.is_file() else None
    if current != expected_raw:
        fail('상태가 다른 작성자에 의해 변경되었습니다. 다시 읽고 조정하세요.')
    safe(root, state_relative(state['runId']), exists=False)
    dashboard_tool().atomic(path, dashboard_tool().encode(state))


def expect_revision(state, expected):
    integer(expected, 'expect-revision')
    if state['revision'] != expected:
        fail('현재 revision과 다릅니다. 다시 읽고 조정하세요.')


def sync(root, state, *, state_saved=False):
    result = {'ok': True, 'runId': state['runId'], 'revision': state['revision'], 'status': state['status'],
              'stateSaved': state_saved, 'registrySynced': False, 'dashboardUpdated': False, 'errors': []}
    try:
        path = safe(root, state['registryPath'], exists=False)
        before = path.read_bytes() if path.is_file() else None
        registry = json.loads(before.decode('utf-8-sig')) if before is not None else {'schemaVersion': 1, 'runs': []}
        tool = registry_tool(root)
        tool.validate(registry)
        old = next((row for row in registry['runs'] if row['runId'] == state['runId']), None)
        record_path = state_relative(state['runId'])
        if old and old['recordPath'] != record_path:
            if old['recordPath'] != state.get('supersedesRecordPath') or old['status'] not in OPEN_STATUSES:
                fail('자신의 pointer 위치가 다릅니다. needs-reconciliation: 자동 전환하지 않습니다.')
            safe(root, old['recordPath'])
        pointer = {'runId': state['runId'], 'recordPath': record_path, 'status': state['status'],
                   'goalRevision': state['goalRevision'], **state['discovery']}
        if pointer.get('conversationKey') is None:
            pointer.pop('conversationKey', None)
        replacement = deepcopy(registry)
        if old:
            replacement['runs'] = [pointer if row['runId'] == state['runId'] else row for row in replacement['runs']]
        else:
            replacement['runs'].append(pointer)
        tool.validate(replacement)
        if (path.read_bytes() if path.is_file() else None) != before:
            fail('레지스트리가 변경 중입니다. 자신의 pointer만 다시 조정하세요.')
        safe(root, state['registryPath'], exists=False)
        dashboard_tool().atomic(path, dashboard_tool().encode(replacement))
        result['registrySynced'] = True
    except (ValueError, OSError, KeyError, TypeError) as exc:
        result['ok'] = False
        result['errors'].append({'stage': 'registry', 'message': str(exc)})
        result['dashboardStatus'] = 'skipped-registry-failure'
        return result
    try:
        config_path = safe(root, DASHBOARD_FOLDER + '/dashboard.config.json', exists=False)
        if not config_path.exists():
            result['dashboardUpdated'] = None
            result['dashboardStatus'] = 'skipped-unconfigured'
        else:
            config = dashboard_tool().load_config(root)
            if config['registryPath'] != state['registryPath']:
                fail('대시보드와 실행의 registryPath가 다릅니다. 설정 소유자에게 반환하세요.')
            dashboard_tool().update(root)
            result['dashboardUpdated'] = True
            result['dashboardStatus'] = 'current'
    except (ValueError, OSError, KeyError, TypeError) as exc:
        result['ok'] = False
        result['dashboardStatus'] = 'error'
        result['errors'].append({'stage': 'dashboard', 'message': str(exc)})
    return result


def init(root, data):
    required = {'runId', 'title', 'goalRevision', 'supervisorId', 'registryPath', 'discovery', 'authority', 'checkpoint', 'contract'}
    shape(data, required, {'supersedesRecordPath'}, field='init')
    timestamp = now()
    state = {**deepcopy(data), 'schemaVersion': 1, 'recordType': 'workflow-run', 'revision': 1,
             'status': 'ready', 'candidate': None,
             'taskStates': {task['id']: {'state': 'pending'} for task in data['contract']['tasks']},
             'results': [], 'skills': [], 'findings': [], 'measurements': [], 'events': [],
             'createdAt': timestamp, 'updatedAt': timestamp}
    validate(state)
    path = safe(root, state_relative(state['runId']), exists=False)
    if path.exists():
        fail('이 실행의 상태가 이미 있습니다. 덮어쓰지 않습니다.')
    registry_path = safe(root, state['registryPath'], exists=False)
    if registry_path.is_file():
        registry = registry_tool(root).load(registry_path)
        old = next((row for row in registry['runs'] if row['runId'] == state['runId']), None)
        if old and (old['recordPath'] != state.get('supersedesRecordPath') or old['status'] not in OPEN_STATUSES):
            fail('기존 실행 pointer가 있습니다. 명시적 동일 실행 전환 없이는 새 상태를 만들지 않습니다.')
    save_state(root, state, None)
    return sync(root, state, state_saved=True)


def freeze(root, run_id, candidate_id, files, producers, expected_revision):
    state, raw = load_state(root, run_id)
    expect_revision(state, expected_revision)
    if state['status'] not in OPEN_STATUSES:
        fail('닫힌 실행에는 새 후보를 고정하지 않습니다.')
    text(candidate_id, 'candidate-id')
    strings(files, 'files', empty=False)
    strings(producers, 'producerIds', empty=False)
    manifest, observed = [], {}
    for filename in files:
        relative(filename, 'file')
        manifest.append({'path': filename, 'digest': file_digest(safe(root, filename))})
    inspect_files(root, state, manifest, observed)
    for path, before in observed.values():
        if file_digest(path) != before:
            fail('후보 수집 중 파일이 변경되었습니다.')
    candidate = {'id': candidate_id, 'digest': digest(sorted([[row['path'], row['digest']] for row in manifest])),
                 'files': sorted(manifest, key=lambda row: row['path']), 'producerIds': sorted(producers)}
    prior_candidates = [state['candidate']]
    for event in state['events']:
        if event['kind'] == 'freeze':
            prior_candidates.append(event.get('previous'))
        elif event['kind'] == 'scope':
            prior_candidates.append(event.get('previous', {}).get('candidate'))
    if any(previous and previous['id'] == candidate_id and previous != candidate for previous in prior_candidates):
        fail('이력의 같은 후보 ID가 다른 내용을 가리킵니다. 새 ID를 사용하세요.')
    if state['candidate'] and state['candidate']['id'] == candidate_id:
        if state['candidate'] != candidate:
            fail('같은 후보 ID의 내용이 다릅니다. 새 ID를 사용하세요.')
        return sync(root, state)
    previous = state['candidate']
    state['candidate'] = candidate
    append_event(state, f'freeze-{state["revision"] + 1}', 'freeze', candidate, previous)
    save_state(root, state, raw)
    return {**sync(root, state, state_saved=True), 'candidate': candidate}


def record(root, run_id, event, expected_revision):
    shape(event, {'eventId', 'kind', 'data'}, field='record')
    text(event['eventId'], 'eventId')
    enum(event['kind'], RECORD_KINDS, 'record.kind')
    if not isinstance(event['data'], dict):
        fail('record.data는 객체입니다.')
    state, raw = load_state(root, run_id)
    prior = next((item for item in state['events'] if item['eventId'] == event['eventId']), None)
    if prior:
        if prior['payloadDigest'] != digest(event):
            fail('같은 eventId의 내용이 다릅니다.')
        return {**sync(root, state), 'alreadyRecorded': True}
    expect_revision(state, expected_revision)
    kind, data, previous = event['kind'], deepcopy(event['data']), None
    if state['status'] == 'cancelled' or (state['status'] == 'completed' and kind in {'scope', 'checkpoint', 'task'}):
        fail('닫힌 실행의 작업 범위를 바꾸지 않습니다. 새 실행으로 연결하세요.')
    if kind in {'check', 'review', 'decision'}:
        for key, expected in (('eventId', event['eventId']), ('kind', kind)):
            if key in data and data[key] != expected:
                fail('결과 신원과 event 신원이 다릅니다.')
        result = {**data, 'eventId': event['eventId'], 'kind': kind}
        validate_result(result, {**state['contract'], 'goalRevision': state['goalRevision']})
        if result['goalRevision'] != state['goalRevision']:
            fail('이전 goalRevision의 새 결과는 현재 실행에 기록하지 않습니다.')
        candidate = state['candidate']
        if not candidate or result['candidateId'] != candidate['id'] or result['candidateDigest'] != candidate['digest']:
            fail('결과가 현재 고정 후보와 다릅니다.')
        verify_result_files(root, state, result)
        state['results'].append(result)
    elif kind == 'checkpoint':
        previous = state['checkpoint']
        state['checkpoint'] = data
    elif kind == 'task':
        shape(data, {'taskId', 'state'}, {'resultPath'}, field='task event')
        if data['taskId'] not in state['taskStates']:
            fail('등록되지 않은 taskId입니다.')
        previous = state['taskStates'][data['taskId']]
        state['taskStates'][data['taskId']] = {key: value for key, value in data.items() if key != 'taskId'}
    elif kind == 'skill':
        state['skills'].append(data)
    elif kind in {'finding', 'measurement'}:
        collection = 'findings' if kind == 'finding' else 'measurements'
        previous = next((item for item in state[collection] if item['id'] == data.get('id')), None)
        state[collection] = [item for item in state[collection] if item['id'] != data.get('id')] + [data]
    elif kind == 'scope':
        shape(data, {'goalRevision', 'authority', 'contract', 'checkpoint'}, field='scope event')
        integer(data['goalRevision'], 'scope.goalRevision')
        if data['goalRevision'] <= state['goalRevision']:
            fail('scope는 더 큰 goalRevision이 필요합니다.')
        validate_contract(data['contract'])
        previous = {key: state[key] for key in ('goalRevision', 'authority', 'contract', 'checkpoint', 'candidate', 'taskStates', 'skills')}
        state.update(data)
        state['candidate'] = None
        state['status'] = 'running'
        state['skills'] = []
        state['taskStates'] = {task['id']: {'state': 'pending'} for task in data['contract']['tasks']}
    append_event(state, event['eventId'], kind, event, previous)
    save_state(root, state, raw)
    return sync(root, state, state_saved=True)


def complete(root, run_id, expected_revision):
    state, raw = load_state(root, run_id)
    expect_revision(state, expected_revision)
    checked = inspect(root, state)
    if state['status'] == 'cancelled' or not checked['ready']:
        return {'ok': False, 'runId': run_id, 'stateSaved': False, 'registrySynced': False,
                'dashboardUpdated': False, 'errors': [{'stage': 'completion', 'message': reason} for reason in
                                                    (checked['issues'] or ['취소된 실행입니다.'])], 'check': checked}
    if state['status'] == 'completed':
        return {**sync(root, state), 'check': checked}
    state['status'] = 'completed'
    append_event(state, f'complete-{state["revision"] + 1}', 'complete', {'evidenceDigest': checked['evidenceDigest']})
    save_state(root, state, raw)
    return {**sync(root, state, state_saved=True), 'check': checked}


def markdown(state, checked):
    lines = [f'# {state["title"]}', '', f'- 실행: {state["runId"]} · 기록 상태: {state["status"]}',
             f'- 현재 단계: {state["checkpoint"]["stage"]}', f'- 막힌 이유: {state["checkpoint"]["blocker"] or "없음으로 기록됨"}',
             f'- 다음 행동: {state["checkpoint"]["nextAction"]}', f'- 완료 조건: {"충족" if checked["ready"] else "미충족"}', '']
    lines.extend('- ' + issue for issue in checked['issues'])
    lines.append('\n기록 일치 확인이며 실제 실행 의미나 권한 인증이 아닙니다.')
    return '\n'.join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='operation', required=True)
    command = sub.add_parser('init')
    command.add_argument('--input', required=True)
    for name in ('show', 'freeze', 'record', 'check', 'complete', 'sync'):
        command = sub.add_parser(name)
        command.add_argument('--run-id', required=True)
        if name in ('freeze', 'record', 'complete'):
            command.add_argument('--expect-revision', required=True, type=int)
        if name == 'show':
            command.add_argument('--markdown', action='store_true')
        elif name == 'freeze':
            command.add_argument('--candidate-id', required=True)
            command.add_argument('--file', action='append', required=True)
            command.add_argument('--producer', action='append', required=True)
        elif name == 'record':
            command.add_argument('--input', required=True)
    args = parser.parse_args(argv)
    try:
        root = project_root()
        if args.operation in ('init', 'record'):
            raw_input = safe(root, args.input).read_text(encoding='utf-8-sig')
            data = json.loads(raw_input)
        if args.operation == 'init':
            result = init(root, data)
        elif args.operation == 'freeze':
            result = freeze(root, args.run_id, args.candidate_id, args.file, args.producer, args.expect_revision)
        elif args.operation == 'record':
            result = record(root, args.run_id, data, args.expect_revision)
        elif args.operation == 'complete':
            result = complete(root, args.run_id, args.expect_revision)
        else:
            state, raw = load_state(root, args.run_id)
            if args.operation == 'sync':
                result = sync(root, state)
            else:
                checked = inspect(root, state)
                if safe(root, state_relative(args.run_id)).read_bytes() != raw:
                    fail('상태가 확인 중 변경되었습니다. 다시 읽으세요.')
                if args.operation == 'show' and args.markdown:
                    print(markdown(state, checked))
                    return 0
                result = {'ok': checked['ready'] if args.operation == 'check' else True,
                          'state': state, 'check': checked, 'stateSaved': False}
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 0 if result['ok'] else 1
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(json.dumps({'ok': False, 'stateSaved': False, 'registrySynced': False,
                          'dashboardUpdated': False, 'errors': [{'stage': args.operation, 'message': str(exc)}]}, ensure_ascii=False))
        return 1


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    raise SystemExit(main())
