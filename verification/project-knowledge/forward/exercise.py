from pathlib import Path
import hashlib, json, subprocess
r=Path('.tmp/knowledge-forward')
for p in ['comet-wiki','src','spec','test','evidence']:(r/p).mkdir(exist_ok=True)
def put(p,s): (r/p).write_text(s,encoding='utf-8')
put('profile.json',json.dumps({'knowledge':{'enabled':True,'projectName':'comet','root':'comet-wiki/','indexPath':'comet-wiki/README.md','policyPath':'policy.md'}},indent=2))
put('policy.md','''# 프로젝트 지식 정책
승인된 spec/save.md가 의도된 동작의 원본이며 코드는 관측 근거다. 이번 작업은 comet-wiki/save.md의 저장 성공 후 보상 확정 설명을 동기화할 권한이 있다. 다른 파일의 제품 변경이나 위키 이전은 허용하지 않는다. 문서 점검은 python -B check_docs.py, 동작 근거는 node --test --test-isolation=none test/save.test.mjs다. 마지막 검증 시점과 SHA-256으로 출처를 식별한다.
''')
put('comet-wiki/README.md','# comet 위키\n\n- [저장과 보상](save.md): 저장 실패와 보상 확정 계약.\n')
put('comet-wiki/save.md','# 저장과 보상\n\n과거 설명: 보상을 먼저 확정한 뒤 저장한다.\n출처: [이전 명세](../spec/save-v0.md).\n')
put('spec/save-v0.md','# 이전 명세 v0\n\n대체됨: 보상을 먼저 확정하고 저장한다.\n')
put('spec/save.md','# 저장 명세 v1\n\n상태: approved. SAVE-1: 저장 성공 후에만 보상을 확정한다. SAVE-2: 저장 실패 시 보상을 확정하지 않는다.\n')
put('src/save.mjs','export async function grant(save, confirm) { await save(); confirm(); }\n')
put('test/save.test.mjs','''import test from 'node:test';
import assert from 'node:assert/strict';
import { grant } from '../src/save.mjs';
test('SAVE-1: confirmation waits for save success', async () => {
  let release; let confirmed = 0;
  const pending = grant(() => new Promise(resolve => {release = resolve;}), () => confirmed++);
  assert.equal(confirmed, 0);
  release(); await pending; assert.equal(confirmed, 1);
});
test('SAVE-2: save rejection leaves reward unconfirmed', async () => {
  let confirmed = 0;
  await assert.rejects(grant(() => Promise.reject(new Error('disk')), () => confirmed++), /disk/);
  assert.equal(confirmed, 0);
});
''')
put('check_docs.py','''from pathlib import Path
import re
root=Path(__file__).parent
for p in (root/'comet-wiki').glob('*.md'):
    for target in re.findall(r'\\]\\(([^)#]+)(?:#[^)]*)?\\)', p.read_text(encoding='utf-8')):
        assert (p.parent/target).is_file(), (p, target)
print('PASS: local wiki links resolve')
''')
proc=subprocess.run(['node','--test','--test-isolation=none','test/save.test.mjs'],cwd=r,capture_output=True,text=True,encoding="utf-8")
put('evidence/verified-fix-tests.txt',proc.stdout+proc.stderr)
assert proc.returncode==0,proc.stdout+proc.stderr
def sha(p):return hashlib.sha256((r/p).read_bytes()).hexdigest()
inputs={p:sha(p) for p in ['profile.json','policy.md','spec/save.md','src/save.mjs','test/save.test.mjs']}
put('evidence/input-identities.json',json.dumps(inputs,indent=2))
put('evidence/wiki-before.md',(r/'comet-wiki/save.md').read_text(encoding='utf-8'))
assert all(sha(p)==v for p,v in inputs.items())
put('comet-wiki/save.md',f'''# 저장과 보상

## 현재 계약
- 승인된 결정: 저장 성공 후에만 보상을 확정한다. 실패하면 확정하지 않는다. [명세 v1](../spec/save.md)의 SAVE-1/SAVE-2가 규범이다.
- 확인된 구현: `grant`는 `save` 완료를 기다린 다음 `confirm`을 호출한다. [구현](../src/save.mjs), [지연 성공 및 실패 테스트](../test/save.test.mjs).
- 적용 범위: fixture comet의 grant 함수. 저장 장치나 실제 게임 통합까지 검증한 것은 아니다.
- 최종 확인: 2026-09-16. [출처 SHA-256](../evidence/input-identities.json), [실행 근거](../evidence/verified-fix-tests.txt). 변경된 출처를 재확인하기 전에는 현재 구현의 확정 사실로 재사용하지 않는다.

## 대체된 설명
[이전 명세 v0](../spec/save-v0.md)의 "보상을 먼저 확정한 뒤 저장" 설명은 v1로 대체되었다. 기존 설명은 [갱신 전 사본](../evidence/wiki-before.md)으로 추적한다.
''')
proc=subprocess.run(['python','-B','check_docs.py'],cwd=r,capture_output=True,text=True,encoding="utf-8")
put('evidence/docs-check.txt',proc.stdout+proc.stderr)
assert proc.returncode==0
put('evidence/candidate-identities.json',json.dumps({p:sha(p) for p in ['comet-wiki/save.md','comet-wiki/README.md','src/save.mjs','spec/save.md']},indent=2))
print('Fixture first update done; tests and local link checks PASS. Independent semantic review pending.')


