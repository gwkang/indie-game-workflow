from pathlib import Path
import hashlib, json, subprocess
r=Path('.tmp/knowledge-forward')
def put(p,s): (r/p).write_text(s,encoding='utf-8')
def sha(p):return hashlib.sha256((r/p).read_bytes()).hexdigest()
before_wiki=sha('comet-wiki/save.md')
put('evidence/src-save-verified.mjs',(r/'src/save.mjs').read_text(encoding='utf-8'))
put('src/save.mjs','export async function grant(save, confirm) { confirm(); await save(); }\n')
inputs=json.loads((r/'evidence/input-identities.json').read_text())
assert sha('src/save.mjs') != inputs['src/save.mjs']
proc=subprocess.run(['node','--test','--test-isolation=none','test/save.test.mjs'],cwd=r,capture_output=True,text=True,encoding='utf-8')
put('evidence/second-read-tests.txt',proc.stdout+proc.stderr)
assert proc.returncode!=0
assert before_wiki==sha('comet-wiki/save.md')
put('evidence/second-read-identities.json',json.dumps({'current-source':sha('src/save.mjs'),'recorded-source':inputs['src/save.mjs'],'wiki-before':before_wiki,'wiki-after':sha('comet-wiki/save.md')},indent=2))
put('second-read-result.md','''# 두 번째 조회: SAVE-1/SAVE-2

조회 범위: 현재 보상 확정 시점을 위키에서 재사용해도 되는가. 읽기 전용이다.

출처 SHA-256 비교에서 src/save.mjs 내용 변경이 감지됐다. 따라서 위키의 관측된 구현 설명을 현재 사실로 재사용하지 않았다. 해당 함수와 승인 명세를 재확인하고 기존 두 테스트를 실행했다. 두 테스트 모두 실패했다(evidence/second-read-tests.txt). 현재 코드는 confirm을 save 전에 실행하며 승인 명세 v1은 여전히 저장 성공 후 확정을 요구한다.

승인된 결정은 유지된다. 현재 구현은 그 결정과 불일치한다. 구현 동작을 따라 위키나 명세를 고치는 권한은 없다. 제품/기술 소유자에게 원인·의도·수정 범위를 반환한다. 위키 내용은 읽기 전용 조회 전후 SHA-256이 같으며 변경하지 않았다(evidence/second-read-identities.json). 저장 성공 후 확정한다는 문장은 규범으로는 유효하지만 현재 구현의 확인된 사실로는 재확인이 실패했다.
''')
put('report.md','''# knowledge-forward 수행 기록

- artifact ID: KF-1; type: knowledge-delta@1; task: knowledge-forward; attempt: 1.
- executor: /root/knowledge_forward; role: game-knowledge-maintenance (공유 role-cards v1).
- context: dispatched parent /root. 언어: workflow-default ko.
- scope source: 상위 배정의 comet fixture만. 실제 제품 변경, 운영 위키 이전, 외부 상태 변경 제외.
- 입력: profile.json, policy.md, spec/save.md, src/save.mjs, test/save.test.mjs. 초기 revision: evidence/input-identities.json의 SHA-256. body rule: sharing/indie-game-workflow/skills/game-task-planning/references/artifact-contract.md의 knowledge-delta@1 및 knowledge-contract.md.
- 전문 외부 자료: 불필요. 실제 제공된 계약과 fixture 내부 명세·코드·테스트만으로 판정 가능.
- consumer: parent /root supervisor. 별도 verifier executor: 미배정, 부모가 별도 verifier에게 전달해야 함. 아래 자기 점검은 독립 검증이 아님.

## 고정 검증 범위와 결과

| 기준 | 관측 | 상태 |
| --- | --- | --- |
| KF-C1: required 갱신은 근거와 일치하며 원본을 보존 | comet-wiki/save.md를 실제 수정. 저장 성공 후 확정/실패 시 미확정으로 변경. 이전 원본과 설명의 연결 보존. 초기 테스트 2/2 통과 | 자기 점검 통과, 독립 검증 대기 |
| KF-C2: 입력 revision과 적용 범위 추적 | SHA-256 및 2026-09-16, fixture 함수 범위와 통합 미검증 명시 | 자기 점검 통과 |
| KF-C3: 갱신 전 source revision 재확인 및 설정 검사 | 올바른 comet-wiki/ 사용, 갱신 직전 hash 동일 확인. index 페이지 목록·요약은 불변이어서 수정하지 않음. python -B check_docs.py PASS | 자기 점검 통과 |
| KF-C4: 이후 source 변경 시 주장 재확인 | src/save.mjs만 고의 회귀 후 hash 차이 감지, 재실행 0/2 통과로 불일치 확인. second-read-result.md에 반환 | 자기 점검 통과 |
| KF-C5: 읽기 전용 재조회는 위키 수정 금지 | 변경된 코드에 위키를 맞추지 않음. 위키 전후 hash 동일 | 자기 점검 통과 |

첫 갱신 분류: requirement=required, outcome=applied. 위키 동기화 criterion은 독립 의미 검증 전 닫지 않는다. 이후 source 변경으로 최초 관측 근거의 현재 유효성이 소멸하였고 현재 통합 완료를 주장하지 않는다. 첫 검증 코드 스냅샷은 evidence/src-save-verified.mjs이다.

문서 체크 한계: fixture check_docs.py는 로컬 링크 존재만 검사한다. 내용 의미를 검증하지 않는다. 실제 읽기/수정/재조회는 수행했지만 자동 workflow 실행기나 게임 제품 E2E를 실행한 것은 아니다. node 기본 격리는 sandbox spawn EPERM이어서 --test-isolation=none으로 동일 test를 실행했다.

## 계약으로 판단한 추가 경계 사례

아래는 실제 workflow dispatch 실행이 아니라 계약 적용 검토다.

- knowledge.enabled=false 또는 설정 부재: 일반 workflow를 유지하고 위키를 만들지 않는다. 독립된 일반 작업을 차단하지 않는다.
- 읽기 전용 상담: 관련 위키와 source를 읽어 답변하며 유용한 결과가 있어도 위키 쓰기 권한을 얻은 것으로 취급하지 않는다. 두 번째 조회에서 실제로 이 경계를 적용했다.
- required delta를 deferred로 반환: requirement와 outcome을 별도로 기록하고 해당 필수 수용 기준은 미완료로 반환한다. no-change로 바꾸거나 전체 완료로 표시할 수 없다. 실제 supervisor 완료 제어는 이번 fixture에서 실행하지 않았다.
- 기존 legacy wiki/만 있는 경우: 기존 참조로 읽을 수 있으나 comet-wiki/를 자동 생성·복제·이전하지 않는다. 이름 불일치는 설정/이전 결정을 소유자에게 반환한다. knowledge 의존 작업만 조정한다. 실제 파일 이전은 실행하지 않았다.

## 검증 인계

별도 검증자는 KF-C1~KF-C5만 읽기 전용으로 검사한다. 필요한 읽기: 이 디렉터리와 위에 명시한 skill/contracts. 허용 수리 경로는 .tmp/knowledge-forward/ 내부뿐이며 수리자는 /root/knowledge_forward, 수정 예산 2회. 입력 current 상태는 고의 conflict이므로 첫 갱신은 evidence/src-save-verified.mjs와 input-identities를 대조해야 한다. 실제 게임 코드나 위키 전체 품질은 제외한다. 의미 검증 불가 또는 독립 executor 부재는 unverified로 반환한다.
''')
print('Second read detected changed source; both tests failed; wiki hash unchanged. See report.md.')
