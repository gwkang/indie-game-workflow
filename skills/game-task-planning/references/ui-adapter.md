# 기존 UI 연결 · v1

원본 UI 스킬과 schema는 재사용한다. 작업 전에 선택한 화면·상태·target, 원본 SKILL/상세 규칙 locator와 hash, 역할 카드 ID/version, 공통 envelope, 문서 언어, 고정 검증 범위를 전달한다. UI 결과는 기존 표를 그대로 두고 envelope를 인계 기록으로 보충한다.

## 결정과 승인

| 기록할 값 | 소비 규칙 |
| --- | --- |
| decision ID, scope, candidate/revision, authority source | 현재 후보·범위와 일치하는 기존 결정만 재사용 |
| confirmed/delegated/proposed/unresolved, 선택 결과/이유 | delegated는 실제 위임 범위와 선택 결과 필요. proposed는 승인 아님 |
| 원본이 요구하는 PO gate, 충족 근거, 남은 독립 gate | 취향 선택 위임을 독립 리뷰 또는 실제 PO 승인으로 표기하지 않음 |

사용자의 명시 위임이 해당 선택을 허용하면 위임 선택으로 기록하고 진행 가능한 작업을 수행한다. 원본이 별도 실제 사람 승인을 요구하며 기존 결정으로 충족되지 않으면 그 gate만 미충족으로 유지한다. 감독이 필요한 승인 대상과 근거를 한 번에 제시한다. 원본 승인 제약을 묵시적으로 삭제하지 않는다.

각 산출물 검증은 작성자와 별도 서브에이전트가 맡는다. 필수 독립 art/UI review는 여전히 별개 판정이다. 화면 밖 발견은 추가 제작이나 검증을 유발하지 않으며, 공유 컴포넌트 수정도 배정 범위 안에서만 수행한다.
