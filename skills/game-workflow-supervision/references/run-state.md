# 한 기록으로 관리하는 작업 상태

프로젝트가 `workflow.stateToolPath`를 선택했을 때 새 감독 실행에 사용한다. [공용 도구](../scripts/workflow_state.py)는 설치된 위치로 소속 프로젝트를 찾는다. 폴더 입력이나 별도 서버·패키지 설치가 필요하지 않다. Python 3.12 표준 라이브러리를 사용한다. 프로젝트 설정·작업 데이터는 프로젝트에 둔다.

새 실행은 `planning/workflow-runs/<runId>/state.json` 하나를 원본으로 쓴다. 레지스트리의 `recordPath`는 이 JSON을 가리킨다. 대시보드와 `show --markdown`은 같은 데이터의 읽기용 출력이다. 같은 현재 상태를 Markdown에 다시 작성하지 않는다. 기존 Markdown 실행은 기존 방식으로 재개하며 자동 변환하지 않는다. 한 실행의 명시적 전환은 `supersedesRecordPath`에 원래 기록 경로를 제공하고, 이전 파일을 이력으로 보존한다.

## 사용 순서

감독은 실제 권한, 현재 목표, 고정 수용 기준, 작업·검사·검토·필수 승인 집합을 init 입력 JSON에 작성한다. 하나의 실제 감독이 상태와 pointer를 갱신한다. 미정 구조/제품, 정식 UI, 필수 T1–T4 조사·보류, 실패 예산을 작은 계약으로 면제할 수 없다. 필요한 선행 작업과 막힌 이유를 필수 집합 또는 완료를 막는 finding에 연결한다.

프로젝트 루트에서의 예시이며, `작업-id`와 입력 경로는 실제 실행의 값으로 바꾼다. 다른 폴더에서는 설치된 도구의 절대 경로로 실행해도 같은 프로젝트를 처리한다.

```powershell
python -B .agents/skills/game-workflow-supervision/scripts/workflow_state.py init --input planning/workflow-runs/작업-id/init.json
python -B .agents/skills/game-workflow-supervision/scripts/workflow_state.py show --run-id 작업-id --markdown
python -B .agents/skills/game-workflow-supervision/scripts/workflow_state.py freeze --run-id 작업-id --candidate-id 후보-1 --file 변경파일 --producer 실제작성자 --expect-revision 1
python -B .agents/skills/game-workflow-supervision/scripts/workflow_state.py record --run-id 작업-id --input planning/workflow-runs/작업-id/반환.json --expect-revision 2
python -B .agents/skills/game-workflow-supervision/scripts/workflow_state.py check --run-id 작업-id
python -B .agents/skills/game-workflow-supervision/scripts/workflow_state.py complete --run-id 작업-id --expect-revision 현재revision
python -B .agents/skills/game-workflow-supervision/scripts/workflow_state.py sync --run-id 작업-id
```

`record`는 checkpoint/task/check/review/decision/skill/finding/measurement/scope 이벤트를 받는다. 검사·검토 결과는 append하며 실패나 오래된 결과를 삭제하지 않는다. 동일 이벤트의 재시도는 revision을 다시 올리지 않고 sync한다. 같은 ID의 다른 내용은 거절한다. scope 변경은 더 큰 goalRevision과 새로운 명시적 권한·전체 계약을 받고, 이전 후보/결과를 이력으로 남긴 뒤 현재 후보를 비워 새 검사를 요구한다. 닫힌 실행은 새 실행으로 연결한다.

## 완료 확인

`check`는 파일을 쓰지 않는다. 현재 파일 지문, 필수 작업의 실제 종료 상태, 명시한 검사 항목의 정확한 완료 집합, 최신 판정, 원본 증거의 지문, 같은 목표/후보와 작성자와 다른 검토자를 확인한다. exit zero·빈 결과·과거 PASS·skipped/cancelled·작성자 자신의 검토는 완료 근거가 아니다. 마지막 결과가 실패면 앞의 통과를 가져오지 않는다. `complete`는 이 조건을 다시 확인하며 누락/오래됨/열린 필수 문제에서는 상태를 바꾸지 않는다.

검토자는 `check`의 evidenceDigest와 같은 후보/검사 근거를 읽고 반환한다. 검토 후 검사·필수 작업·승인·문제·근거가 바뀌면 검토가 오래된 결과가 된다. 결과의 actorId는 호스트 배정/반환에서 확인한 실제 실행 주체다. 역할 이름만 다르게 쓰는 것은 독립 검토가 아니다. JSON은 감독이 받은 기록이며, 도구가 실행의 의미·완료 기준의 충분성·승인 권한을 인증하지 않는다. 별도 전문 검토와 실제 증거는 계속 필요하다.

모든 입력/후보/증거는 프로젝트 내부의 상대 파일 경로다. 바깥 경로·절대 경로·상위 폴더·외부 연결은 거절한다. state/registry/생성 대시보드처럼 스스로 바뀌는 파일을 후보나 실행 증거로 쓰지 않는다. 파일 지문은 일관성 근거이며 진실이나 권한의 인증이 아니다.

## 실패와 측정

저장은 state → 최신 registry의 자기 pointer → 대시보드 순서다. 명령 출력은 `stateSaved`, `registrySynced`, `dashboardUpdated`를 따로 알려준다. 상태 저장 후 registry/대시보드가 실패하면 앞 단계는 남으며 명령은 실패로 보고한다. `sync`로 다시 연결한다. 기존 수동 대시보드 설정과 다른 pointer를 보존한다. 설정된 registry와 입력 경로가 다르면 임의로 고르지 않는다. 최초 필수 대시보드 생성이 빠졌다면 적용 완료로 보고하지 않는다.

expected revision과 원본 바이트를 저장 전에 다시 확인한다. 단일 파일은 임시 파일·flush/fsync·교체로 저장한다. 이것은 여러 파일의 한 번 저장, 전역 잠금, 원자적 비교 후 저장, 작업자 감시나 자동 복구가 아니다. 확인된 단일 작성자 또는 격리 공간이 필요하며 소유권이 불확실하면 쓰기를 멈춘다. 서버는 원본·registry·저장 요약을 쓰지 않는다. JSON 읽기 실패와 개별 검증 근거의 오래됨을 구분한다.

measurement는 격리 행동 시험과 실작업, 관측값/추정/미측정을 구분한다. 실제 관측한 방법·조건·출처를 연결하고 미측정 value는 null로 둔다. 단계 시간·문서 읽기·담당자 교대·재작업 수는 관측한 범위만 기록한다. 문서 분량 감소나 격리 시험으로 전체 개발 시간 절감이나 모든 프로젝트 적용을 주장하지 않는다.

## 초기 입력의 최소 구성

init 입력에는 runId/title/goalRevision/supervisorId, registryPath, discovery, authority, checkpoint, contract를 넣는다. discovery에는 goalKeys/targetPaths와 선택적 conversationKey, authority에는 cursor/summary/scope/excluded, checkpoint에는 stage/summary/blocker/nextAction을 넣는다. contract는 아래 실제 ID 목록을 선언한다. 필수 기준과 필수 산출물 작업은 check와 별도 review에서 모두 다뤄야 한다.

| 목록 | 한 항목의 필드 |
| --- | --- |
| criteria | id, text |
| tasks | id, title, skillId, producerId, criterionIds, required |
| checks | id, criterionIds, taskIds, expectedNames, mode(command/observation) |
| reviews | id, criterionIds, taskIds |
| decisions | id, criterionIds; 필요한 승인만 선언, 없으면 빈 목록 |

검토 배정 자체는 checkpoint/event로 기록한다. review를 다시 작성자 산출물 task로 만들어 같은 검토자에게 자기 검토를 요구하지 않는다. revision·후보·초기 taskStates/results/events는 도구가 생성한다. 입력은 임의 JSON patch가 아니며 잘못된 타입·중복/미등록 ID·빈 필수 집합은 거절한다.

check/review/decision 반환에는 eventId/kind/contractId/goalRevision/candidateId/candidateDigest/actorId/criterionIds/taskIds/executionState/verdict/evidence(path,digest)를 제공한다. check는 completedNames/failedNames/timedOut과 command mode의 command/exitCode를 추가한다. review는 현재 evidenceDigest, decision은 authorityId/state와 현재 증거 지문을 추가한다. enum·필드의 실제 허용값과 추가 제약은 공용 도구가 검증하며, 원본 증거와 의미 판단은 해당 실행에서 제공한다.

완료된 실행과 그 원본 증거는 이력으로 보존한다. 공용 묶음에는 이 도구·참조·소비 연결만 포함하며, 프로젝트 이름·설정·작업 기록·증거·절대 경로는 포함하지 않는다. 실제 입력 형식과 반환 검증은 공용 도구의 schema와 해당 실행의 고정 계약을 따른다.
