"""Inspect seven required workflow preparations; never execute recorded commands."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path, PureWindowsPath
import re


SETTINGS = 'planning/workflow-requirements.json'
QUALITY = ('lint', 'format', 'analysis', 'coverage')
FEATURES = ('knowledge', 'models', 'roadmap', *QUALITY)
LABELS = dict(zip(FEATURES, ('프로젝트 위키', 'AI 모델 선택', '개발 목록',
                            '코드 규칙 검사', '형식 검사', '타입·의미 분석', '게임 코드 테스트 범위')))
BUNDLED_MODELS = 'bundle:game-workflow-supervision/references/model-routing-defaults.json'


class RequirementsError(ValueError):
    pass


def sibling(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def project_root():
    return sibling('dashboard').project_root(__file__)


def path(root, value, *, exists=True):
    if (not isinstance(value, str) or not value or value != value.strip()
            or '\\' in value or ':' in value or '..' in Path(value).parts
            or Path(value).is_absolute() or PureWindowsPath(value).is_absolute()):
        raise RequirementsError('프로젝트 안의 상대 파일 경로가 필요합니다.')
    root = Path(root).resolve(strict=True)
    target = root / value
    for part in (target, *target.parents):
        if part == root:
            break
        if part.is_symlink() or (hasattr(part, 'is_junction') and part.is_junction()):
            raise RequirementsError('연결된 파일·폴더는 준비 자료로 사용하지 않습니다.')
    resolved = target.resolve(strict=exists)
    if resolved == root or not resolved.is_relative_to(root):
        raise RequirementsError('프로젝트 밖의 자료는 사용하지 않습니다.')
    if exists and not resolved.is_file():
        raise RequirementsError('준비 자료가 파일이 아닙니다.')
    return resolved


def read(root, value):
    return json.loads(path(root, value).read_text(encoding='utf-8-sig'))


def text(value):
    return isinstance(value, str) and bool(value.strip()) and value == value.strip()


def object_shape(value, keys):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise RequirementsError('필수 설정의 항목이 없거나 알 수 없는 항목이 있습니다.')


def validate_manifest(config):
    object_shape(config, ('schemaVersion', 'projectName', 'profilePath', 'knowledge', 'models', 'roadmapPath', 'qualityPath'))
    if type(config['schemaVersion']) is not int or config['schemaVersion'] != 1 or not text(config['projectName']):
        raise RequirementsError('필수 설정 버전·프로젝트 이름을 확인하세요.')
    object_shape(config['knowledge'], ('enabled', 'state', 'owner', 'reason', 'indexPath', 'policyPath', 'sources'))
    object_shape(config['models'], ('policy', 'profilePath'))
    for key in ('profilePath', 'roadmapPath', 'qualityPath'):
        if not text(config[key]):
            raise RequirementsError('필수 자료의 파일 경로를 확인하세요.')
    return config


def source_paths(root, values, observe=None):
    if not isinstance(values, list) or not values:
        raise RequirementsError('실제 자료·검사 대상 파일을 연결해야 합니다.')
    for value in values:
        (observe or (lambda value: path(root, value)))(value)


def _inspect(root, *, scope_item=None, settings=SETTINGS, observed):
    """Configuration readiness only; semantics and actual results belong to reviewers."""
    rows = []

    def observe(value):
        data = path(root, value).read_bytes()
        observed.setdefault(value, hashlib.sha256(data).hexdigest())
        return data

    def document(value):
        return json.loads(observe(value).decode('utf-8-sig'))

    try:
        config = validate_manifest(document(settings))
        observe(config['profilePath'])
    except (RequirementsError, OSError, ValueError) as exc:
        return {'schemaVersion': 1, 'setupReady': False, 'checksExecuted': False,
                'overallProgressReady': False, 'items': [
                    {'id': key, 'label': LABELS[key], 'required': True, 'state': 'blocked',
                     'reason': str(exc)} for key in FEATURES]}

    def check(key, function):
        try:
            extra = function() or {}
            rows.append({'id': key, 'label': LABELS[key], 'required': True,
                         'state': 'configured', 'reason': '', **extra})
        except (RequirementsError, OSError, ValueError, KeyError, TypeError) as exc:
            rows.append({'id': key, 'label': LABELS[key], 'required': True,
                         'state': 'blocked', 'reason': str(exc)})

    def knowledge():
        value = config['knowledge']
        object_shape(value, ('enabled', 'state', 'owner', 'reason', 'indexPath', 'policyPath', 'sources'))
        if value['enabled'] is not True:
            raise RequirementsError('위키 연결은 필수입니다. 꺼진 설정으로 통과하지 않습니다.')
        if value['state'] != 'configured' or not text(value['owner']):
            raise RequirementsError('출처에 맞는 지식을 작성하고 담당자를 연결해야 합니다.')
        for key in ('indexPath', 'policyPath'):
            if not observe(value[key]).decode('utf-8-sig').strip():
                raise RequirementsError('위키의 내용과 관리 규칙이 필요합니다.')
        source_paths(root, value['sources'], observe)

    def models():
        value = config['models']
        object_shape(value, ('policy', 'profilePath'))
        if value['policy'] != 'capability-tier':
            raise RequirementsError('작업 난이도에 따른 공통 모델 선택 규칙이 필요합니다.')
        router = sibling('resolve_model_route')
        profile = None
        if value['profilePath'] is not None:
            profile = router.parse_profile(observe(value['profilePath']).decode('utf-8-sig'))
        if profile is None or 'skillTiers' not in profile:
            target = router.common_profile_path()
            project = Path(root).resolve(strict=True)
            if target.is_relative_to(project):
                data = observe(target.relative_to(project).as_posix())
            else:
                # Direct function fixtures may consume the exact trusted bundled asset.
                # Installed project assets still pass the ordinary in-project path checks.
                data = target.read_bytes()
                observed.setdefault(BUNDLED_MODELS, hashlib.sha256(data).hexdigest())
            common = router.validate_common_profile(router.parse_profile(data.decode('utf-8-sig')))
            if profile is None:
                profile = common
        return {'policySource': 'configured-profile' if value['profilePath'] is not None else 'common-profile',
                'profileRevision': profile['revision']}

    progress = {'ready': False}

    def roadmap():
        value = document(config['roadmapPath'])
        if (not isinstance(value, dict) or type(value.get('schemaVersion')) is not int
                or value['schemaVersion'] != 1 or not text(value.get('scopeRevision'))
                or value.get('scopeState') not in ('known', 'unknown')
                or not isinstance(value.get('items'), list)):
            raise RequirementsError('개발 범위 상태·목록·버전을 확인하세요.')
        if value['scopeState'] == 'unknown':
            if not text(value.get('reason')):
                raise RequirementsError('미정인 개발 범위의 이유를 기록하세요.')
            if scope_item is None:
                raise RequirementsError('전체 개발 범위 미정: 목록은 연결됐지만 전체 진행률은 계산할 수 없습니다.')
        else:
            if not value['items']:
                raise RequirementsError('확정한 개발 범위가 비어 있습니다.')
        ids = set()
        for item in value['items']:
            if not isinstance(item, dict) or not text(item.get('id')) or item['id'] in ids or not text(item.get('title')):
                raise RequirementsError('개발 항목 이름·번호가 없거나 중복되었습니다.')
            ids.add(item['id'])
            if not isinstance(item.get('criteria'), list) or not item['criteria']:
                raise RequirementsError('개발 항목마다 완료 기준이 필요합니다.')
            for criterion in item['criteria']:
                if not isinstance(criterion, dict) or not text(criterion.get('id')):
                    raise RequirementsError('완료 기준 번호가 필요합니다.')
        if scope_item is not None and scope_item not in ids:
            raise RequirementsError('이번 작업의 개발 항목을 먼저 연결해야 합니다.')
        progress['ready'] = value['scopeState'] == 'known'
        return {'scopeState': value['scopeState'], 'scopeItem': scope_item}

    def quality(key):
        value = document(config['qualityPath'])
        if (not isinstance(value, dict) or type(value.get('schemaVersion')) is not int
                or value['schemaVersion'] != 1 or not text(value.get('primaryRuntime'))
                or not isinstance(value.get('checks'), dict) or set(value['checks']) != set(QUALITY)):
            raise RequirementsError('주 제품의 언어·실행 환경과 네 가지 필수 검사를 연결하세요.')
        row = value['checks'][key]
        object_shape(row, ('state', 'owner', 'reason', 'tool', 'version', 'command',
                           'cwd', 'sourcePaths', 'configurationPaths', 'supportEvidencePaths', 'capabilities', 'runtime'))
        if row['state'] != 'configured':
            raise RequirementsError(f"준비 필요 ({row['state']}): {row['reason']}")
        if not text(row['owner']) or not text(row['tool']) or not text(row['version']):
            raise RequirementsError('담당자·실제 도구·버전이 필요합니다.')
        if not isinstance(row['command'], list) or not row['command'] or not all(text(x) for x in row['command']):
            raise RequirementsError('검사 명령을 인자 목록으로 연결하세요.')
        if row['cwd'] != '.':
            if not path(root, row['cwd'], exists=False).is_dir():
                raise RequirementsError('검사 실행 폴더가 없습니다.')
        source_paths(root, row['sourcePaths'], observe)
        source_paths(root, row['supportEvidencePaths'], observe)
        if not isinstance(row['configurationPaths'], list):
            raise RequirementsError('검사 설정 목록을 확인하세요.')
        for locator in row['configurationPaths']:
            observe(locator)
        if not isinstance(row['capabilities'], list) or key not in row['capabilities']:
            raise RequirementsError('구문 검사만으로 다른 필수 검사를 대신할 수 없습니다.')
        if not text(row['runtime']) or (key == 'coverage' and row['runtime'] != value['primaryRuntime']):
            raise RequirementsError('참조판의 테스트 범위를 주 제품의 측정으로 대신할 수 없습니다.')

    check('knowledge', knowledge)
    check('models', models)
    check('roadmap', roadmap)
    for key in QUALITY:
        check(key, lambda key=key: quality(key))
    return {'schemaVersion': 1, 'setupReady': all(x['state'] == 'configured' for x in rows),
            'checksExecuted': False, 'overallProgressReady': progress['ready'], 'items': rows}


def inspect(root, *, scope_item=None, settings=SETTINGS):
    for attempt in range(2):
        observed = {}
        result = _inspect(root, scope_item=scope_item, settings=settings, observed=observed)
        changed = []
        for locator, expected in observed.items():
            try:
                target = (sibling('resolve_model_route').common_profile_path()
                          if locator == BUNDLED_MODELS else path(root, locator))
                actual = hashlib.sha256(target.read_bytes()).hexdigest()
            except (OSError, ValueError):
                actual = None
            if actual != expected:
                changed.append(locator)
        if not changed:
            result['observation'] = 'configuration-only'
            result['sources'] = observed
            return result
    result.update(setupReady=False, checksExecuted=False, overallProgressReady=False,
                  observation='configuration-changed', changedSources=changed)
    for row in result['items']:
        row.update(state='blocked', reason='확인 중 자료가 바뀌었습니다. 쓰기가 끝난 뒤 다시 확인하세요.')
    return result


def _initialize(root, name, *, settings, written, preserved):
    if not text(name):
        raise RequirementsError('기존 프로젝트 설정에서 확인한 이름이 필요합니다.')
    slug = re.sub(r'[^a-z0-9-]+', '-', name.lower()).strip('-')
    if not slug or slug in ('con', 'prn', 'aux', 'nul'):
        raise RequirementsError('프로젝트의 안정된 영문 이름을 사용하세요.')

    def create(relative, value):
        target = path(root, relative, exists=False)
        if target.exists():
            preserved.append(relative)
            return
        target.parent.mkdir(parents=True, exist_ok=True)
        data = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2) + '\n'
        if target.exists():
            preserved.append(relative)
            return
        sibling('dashboard').atomic(target, data.encode('utf-8'))
        written.append(relative)

    if not path(root, settings, exists=False).exists():
        create(settings, {'schemaVersion': 1, 'projectName': name, 'profilePath': 'planning/game-workflow-profile.md',
                         'knowledge': {'enabled': True, 'state': 'pending', 'owner': 'game-knowledge-maintenance',
                                       'reason': '현재 출처에 맞는 지식을 준비해야 합니다.', 'indexPath': f'{slug}-wiki/index.md',
                                       'policyPath': f'{slug}-wiki/policy.md', 'sources': []},
                         'models': {'policy': 'capability-tier', 'profilePath': None},
                         'roadmapPath': 'planning/development-roadmap.json',
                         'qualityPath': 'planning/workflow-quality.json'})
    else:
        preserved.append(settings)
    config = validate_manifest(read(root, settings))
    if config.get('projectName') != name:
        raise RequirementsError('기존 프로젝트 연결을 보존합니다. 이름 충돌을 먼저 확인하세요.')
    create(config['knowledge']['indexPath'], f'# {name} 프로젝트 지식\n\n현재 출처를 확인한 뒤 규칙·결정·발견을 연결한다. 지식 준비는 아직 미완료다.\n')
    create(config['knowledge']['policyPath'], '# 지식 관리 규칙\n\n원본 규칙과 승인된 결정을 출처로 사용한다. 출처·확인 범위·미정 상태를 함께 기록한다. 감독이 허가된 갱신을 배정하고 별도 검토자가 의미와 출처를 확인한다.\n')
    create(config['roadmapPath'], {'schemaVersion': 1, 'scopeRevision': 'initial', 'scopeState': 'unknown',
                                'reason': '현재 출처에서 전체 개발 범위가 아직 정해지지 않았습니다.', 'items': []})
    create(config['qualityPath'], {'schemaVersion': 1, 'primaryRuntime': 'unresolved', 'checks': {
        key: {'state': 'pending', 'owner': 'game-test-infrastructure', 'reason': '실제 언어·도구·검사 대상을 확인하고 연결해야 합니다.',
              'tool': None, 'version': None, 'command': [], 'cwd': '.', 'sourcePaths': [],
              'configurationPaths': [], 'supportEvidencePaths': [],
              'capabilities': [], 'runtime': None} for key in QUALITY}})
    return {'written': written, 'preserved': preserved, 'readiness': inspect(root, settings=settings)}


def initialize(root, name, *, settings=SETTINGS):
    written, preserved = [], []
    try:
        return _initialize(root, name, settings=settings, written=written, preserved=preserved)
    except (RequirementsError, OSError, ValueError, KeyError, TypeError) as exc:
        return {'written': written, 'preserved': preserved, 'error': str(exc),
                'readiness': inspect(root, settings=settings)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--settings', default=SETTINGS)
    commands = parser.add_subparsers(dest='action', required=True)
    commands.add_parser('init').add_argument('--name', required=True)
    commands.add_parser('check').add_argument('--scope-item')
    args = parser.parse_args(argv)
    try:
        root = project_root()
        result = initialize(root, args.name, settings=args.settings) if args.action == 'init' else inspect(root, scope_item=args.scope_item, settings=args.settings)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if 'error' in result:
            return 1
        ready = result.get('readiness', result)['setupReady']
        return 0 if ready else 2
    except (RequirementsError, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({'error': str(exc), 'setupReady': False}, ensure_ascii=False))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
