"""Capture actual UTC wall-clock intervals; emit events without changing run state.

Positive system-clock jumps cannot be reliably detected by this wall-clock helper.
Conditions must describe waiting and parallel work included in the measured phase.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re


class MeasureError(ValueError):
    pass


def support():
    spec = importlib.util.spec_from_file_location('measure_requirements', Path(__file__).with_name('workflow_requirements.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def slug(value):
    if not isinstance(value, str) or not re.fullmatch(r'[a-z0-9][a-z0-9-]*', value):
        raise MeasureError('실행·측정 ID는 소문자 영문 slug여야 합니다.')
    return value


def nonempty(value):
    if not isinstance(value, str) or not value or value != value.strip():
        raise MeasureError('앞뒤 공백 없는 문자열이 필요합니다.')
    return value


def strings(values):
    if not isinstance(values, list) or not values:
        raise MeasureError('하나 이상의 조건·출처가 필요합니다.')
    return [nonempty(value) for value in values]


def now():
    return datetime.now(timezone.utc)


def timestamp(value):
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise MeasureError('timezone-aware 실제 UTC 시각이 필요합니다.')
    return value.astimezone(timezone.utc)


def locations(root, run_id, measure_id):
    prefix = f'planning/workflow-runs/{slug(run_id)}'
    folder = support().path(root, prefix, exists=False)
    if not folder.is_dir():
        raise MeasureError('기존 실행 폴더가 필요합니다. 측정 도구는 실행을 만들지 않습니다.')
    raw = f'{prefix}/measurements/{slug(measure_id)}.json'
    event = f'{prefix}/measurements/{measure_id}.event.json'
    support().path(root, raw, exists=False)
    support().path(root, event, exists=False)
    return raw, event


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2) + '\n').encode('utf-8')


def save(root, relative, value, *, expected=None, writer=None):
    target = support().path(root, relative, exists=False)
    current = target.read_bytes() if target.exists() else None
    if current != expected:
        raise MeasureError('측정 자료가 확인 중 바뀌었습니다.')
    target.parent.mkdir(parents=True, exist_ok=True)
    support().path(root, relative, exists=False)
    (writer or support().sibling('dashboard').atomic)(target, encoded(value))


def validate(raw, run_id, measure_id, root):
    keys = {'schemaVersion', 'runId', 'id', 'phase', 'scope', 'conditions', 'sources',
            'startedAt', 'endedAt', 'clock', 'status', 'reason', 'value'}
    if not isinstance(raw, dict) or set(raw) != keys or type(raw['schemaVersion']) is not int or raw['schemaVersion'] != 1:
        raise MeasureError('측정 원본 schema가 잘못되었습니다.')
    if raw['runId'] != run_id or raw['id'] != measure_id or raw['clock'] != 'utc-wall-clock':
        raise MeasureError('측정 원본 신원·시계를 확인하세요.')
    nonempty(raw['phase'])
    strings(raw['conditions'])
    if raw['scope'] not in {'real-work', 'behavior-test'} or raw['status'] not in {'running', 'measured', 'unmeasured'}:
        raise MeasureError('측정 범위·상태가 잘못되었습니다.')
    timestamp(raw['startedAt'])
    if raw['endedAt'] is not None:
        timestamp(raw['endedAt'])
    if not isinstance(raw['sources'], list) or not raw['sources']:
        raise MeasureError('시작 당시 출처 지문이 필요합니다.')
    for source in raw['sources']:
        if (not isinstance(source, dict) or set(source) != {'path', 'digest'}
                or not isinstance(source['digest'], str) or not re.fullmatch(r'[0-9a-f]{64}', source['digest'])):
            raise MeasureError('출처 지문이 잘못되었습니다.')
        support().path(root, source['path'], exists=False)
    value = raw['value']
    if value is not None and (type(value) not in (int, float) or not math.isfinite(value) or value < 0):
        raise MeasureError('유한한 비음수 측정값이 필요합니다.')
    if raw['status'] == 'measured':
        if raw['endedAt'] is None or value is None or raw['reason'] != '':
            raise MeasureError('완료 측정의 시각·값이 없습니다.')
        if (timestamp(raw['endedAt']) - timestamp(raw['startedAt'])).total_seconds() != value:
            raise MeasureError('측정값과 원본 시각이 다릅니다.')
    elif value is not None or (raw['status'] == 'running' and (raw['endedAt'] is not None or raw['reason'] != '')):
        raise MeasureError('미측정·진행 상태와 값이 다릅니다.')
    if raw['status'] == 'unmeasured':
        nonempty(raw['reason'])
    return raw


def begin(root, run_id, measure_id, *, phase, scope, conditions, sources, clock=None, writer=None):
    raw_path, _ = locations(root, run_id, measure_id)
    nonempty(phase)
    if scope not in {'real-work', 'behavior-test'}:
        raise MeasureError('지원하지 않는 측정 범위입니다.')
    conditions, sources = strings(conditions), strings(sources)
    fingerprints = [{'path': locator, 'digest': hashlib.sha256(support().path(root, locator).read_bytes()).hexdigest()}
                    for locator in sources]
    target = support().path(root, raw_path, exists=False)
    if target.exists():
        raw = validate(json.loads(target.read_text(encoding='utf-8-sig')), run_id, measure_id, root)
        if any(raw[key] != value for key, value in {'phase': phase, 'scope': scope, 'conditions': conditions}.items()) or [x['path'] for x in raw['sources']] != sources:
            raise MeasureError('이미 사용한 측정 ID의 시작 인자가 다릅니다.')
        return {'rawPath': raw_path, 'measurement': raw}
    raw = {'schemaVersion': 1, 'runId': run_id, 'id': measure_id, 'phase': phase, 'scope': scope,
           'conditions': conditions, 'sources': fingerprints, 'startedAt': timestamp((clock or now)()).isoformat(),
           'endedAt': None, 'clock': 'utc-wall-clock', 'status': 'running', 'reason': '', 'value': None}
    save(root, raw_path, raw, writer=writer)
    return {'rawPath': raw_path, 'measurement': raw}


def end(root, run_id, measure_id, *, clock=None, clock_anomaly=None, writer=None):
    raw_path, event_path = locations(root, run_id, measure_id)
    target = support().path(root, raw_path)
    original = target.read_bytes()
    raw = validate(json.loads(original.decode('utf-8-sig')), run_id, measure_id, root)
    if raw['status'] == 'running':
        reason = nonempty(clock_anomaly) if clock_anomaly is not None else ''
        try:
            ended = timestamp((clock or now)())
            raw['endedAt'] = ended.isoformat()
            elapsed = (ended - timestamp(raw['startedAt'])).total_seconds()
            if elapsed < 0 or not math.isfinite(elapsed):
                reason = reason or 'UTC wall clock moved backward or produced an invalid interval.'
        except (ValueError, TypeError, OverflowError) as exc:
            elapsed = None
            reason = reason or f'Invalid UTC clock: {exc}'
        raw.update(status='unmeasured' if reason else 'measured', reason=reason,
                   value=None if reason else elapsed)
        save(root, raw_path, raw, expected=original, writer=writer)
    event_id = 'measurement-' + hashlib.sha256(f'{run_id}/{measure_id}'.encode()).hexdigest()[:32]
    event = {'eventId': event_id, 'kind': 'measurement', 'data': {
        'id': measure_id, 'scope': raw['scope'], 'metric': f"phase.{raw['phase']}.elapsed",
        'kind': raw['status'], 'value': raw['value'], 'unit': 'seconds', 'source': raw_path}}
    event_target = support().path(root, event_path, exists=False)
    if event_target.exists():
        if event_target.read_bytes() != encoded(event):
            raise MeasureError('기존 측정 이벤트 내용이 다릅니다.')
    else:
        save(root, event_path, event, writer=writer)
    state_path = f'planning/workflow-runs/{run_id}/state.json'
    revision = None
    if support().path(root, state_path, exists=False).exists():
        revision = support().sibling('workflow_state').load_state(root, run_id)[0]['revision']
    return {'rawPath': raw_path, 'eventPath': event_path, 'event': event, 'revision': revision,
            'recordArguments': ['record', '--run-id', run_id, '--input', event_path,
                                '--expect-revision', str(revision)] if revision is not None else None}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--id', required=True)
    commands = parser.add_subparsers(dest='action', required=True)
    start = commands.add_parser('begin')
    start.add_argument('--phase', required=True)
    start.add_argument('--scope', required=True, choices=('real-work', 'behavior-test'))
    start.add_argument('--condition', action='append', required=True)
    start.add_argument('--source', action='append', required=True)
    commands.add_parser('end').add_argument('--clock-anomaly')
    args = parser.parse_args(argv)
    try:
        root = support().project_root()
        result = (begin(root, args.run_id, args.id, phase=args.phase, scope=args.scope,
                        conditions=args.condition, sources=args.source) if args.action == 'begin'
                  else end(root, args.run_id, args.id, clock_anomaly=args.clock_anomaly))
        print(json.dumps(result, ensure_ascii=False, allow_nan=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({'error': str(exc)}, ensure_ascii=False))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
