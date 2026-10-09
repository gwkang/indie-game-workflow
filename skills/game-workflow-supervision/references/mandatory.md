# 모든 프로젝트의 필수 준비

위키, 작업별 AI 모델 결정, 개발 목록과 진행률, 코드 규칙(lint)·형식(format)·타입 또는 의미 분석(analysis)·주 제품 코드 테스트 범위(coverage)를 필수로 확인한다. 스킬의 설치만으로 준비나 검사 통과를 주장하지 않는다. 다른 프로젝트의 이름·엔진·명령·제품 결정을 공통 기본값으로 복사하지 않는다.

허가된 워크플로우 적용·갱신에서 프로젝트 설정 담당자는 실제 출처에서 이름을 확인하고 아래 도구로 필요한 연결을 준비한다. 설치된 도구가 프로젝트 폴더를 찾는다. 기존 설정·위키·개발 목록을 먼저 재사용하며 덮어쓰거나 이동하지 않는다. 상담·읽기 전용 리뷰는 설정을 확인해 답하고 파일을 쓰지 않는다. 새 절차는 다음 영향받는 배정/재개에서 적용하며 기존 고정 후보와 판정을 소급 변경하지 않는다.

```sh
python -B .agents/skills/game-workflow-supervision/scripts/workflow_requirements.py init --name "실제 프로젝트 이름"
python -B .agents/skills/game-workflow-supervision/scripts/workflow_requirements.py check
```

프로필의 `workflow.requirementsPath`는 기본 `planning/workflow-requirements.json` 또는 보존한 정확한 설정 경로다. 다른 설정은 `--settings 프로젝트/상대경로.json`을 명령 앞쪽에 전달한다. manifest는 projectName/profilePath, knowledge의 enabled/state/owner/reason/indexPath/policyPath/sources, models의 policy/profilePath, roadmapPath/qualityPath를 연결한다. 필수성을 끄는 키는 없다.

init은 없는 설정·지식 초안·개발 목록·품질 준비 파일만 만든다. 기본 위키와 검사 준비는 pending, 전체 범위는 unknown이다. 준비가 남으면 exit2와 항목별 blocked를 반환한다. 파일 저장 성공은 준비 완료가 아니다. check는 명령을 실행하지 않고 연결·타입·출처 파일 지문만 확인한다. `setupReady`와 `checksExecuted:false`, 각 항목과 원본을 읽는다. 실제 의미·지원·실행·별도 검토는 기존 실행 기록에 연결한다. 한 파일의 저장과 여러 파일의 부분 성공을 구분하며 단일 작성자/안정된 입력을 유지한다. check 중 입력 변경은 한 번 재읽고 다시 바뀌면 차단한다.

위키는 실제 규칙·승인된 결정·재사용할 발견을 출처와 함께 정리한다. 관련 지식 조회는 필수이고, 변경으로 설명이 달라지면 허가된 갱신과 별도 의미 검토도 필수다. 내용 변화가 없으면 근거 있는 no-change를 기존 기록에 남기며 불필요한 새 페이지를 만들지 않는다. 빈 초안이나 플래그만으로 준비 완료를 만들지 않는다.

모델 선택은 매 실제 배정에서 [공통 난이도 규칙](model-routing.md)을 사용한다. 구체 모델 매핑이 없으면 공통 host-default 결정과 이유를 반드시 기록한다. 명시한 모델이 불가능하면 해당 배정을 막는다. 실행 주체와 실제 모델 확인은 호스트가 준 증거만 사용한다.

개발 목록은 파일과 이번 작업의 정확한 항목·완료 기준을 필수로 연결한다. 새 제품 작업 전 확정된 해당 항목으로 `check --scope-item 항목-id`를 실행한다. 전체 범위 unknown은 일부 항목이 있어도 전체 percent=null이다. 비어 있는 목록·누락된 해당 항목은 다음 제품 작업의 준비 대상이며 기능과 수치를 발명하지 않는다. [대시보드의 실제 완료 조건](dashboard.md)은 유지한다.

품질 준비 JSON은 schemaVersion1, 실제 primaryRuntime과 checks의 정확한 lint/format/analysis/coverage4개를 가진다. 각 항목은 state/owner/reason/tool/version/command(인자 목록)/cwd/sourcePaths/configurationPaths/supportEvidencePaths/capabilities/runtime을 기록한다. configured는 실제 지원·설정의 선언이고 PASS가 아니다. 설정 없이 쓰는 도구는 configurationPaths 빈 목록을 명시하되 실제 지원 근거와 검사 대상은 반드시 연결한다. 부재·미선택·미지원·미확인은 blocked이고 optional/N/A로 우회하지 않는다. analysis는 실제 타입 또는 의미 분석이며 syntax와 다르다. coverage는 주 제품 언어/환경을 계측하며 참조판으로 대신하지 않는다.

제품 코드 변경 전 필요한 네 가지 도구와 대상이 준비되어야 한다. 변경 후 영향 범위의 실제 명령·결과·원본·분모를 [품질 계약](../../game-task-planning/references/quality-tools.md)과 기존 독립 검토에 연결한다. 도구 설치나 전체 자동 재포맷 권한은 설정 문서가 만들지 않는다. 이미 받은 권한을 사용하고 부족한 권한만 정확히 반환한다.

감독은 부족한 준비를 기존 profile/knowledge/test-infrastructure/feature 담당에 배정하고 관련 소비자만 막는다. 위키·도구·개발 목록을 준비하는 작업과 공통 워크플로우 유지보수는 진행할 수 있지만 이를 전체 프로젝트 준비 완료·제품 검사 PASS로 확대하지 않는다. 완료 전 이번 작업에 적용되는 필수 준비/실행/별도 검토를 한 기존 근거 목록에서 확인한다. 공통 절차 게시 완료, 프로젝트 준비 상태, 제품 검증, 실작업 효과는 구분해서 보고한다.
