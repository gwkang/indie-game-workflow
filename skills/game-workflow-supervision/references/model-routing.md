# 작업별 공통 AI 모델 선택

모든 새 전문 작업 배정에서 [공통 기본표](model-routing-defaults.json)를 읽는다. 프로젝트에 같은 모델 표를 복제할 필요가 없다. 명시한 `modelRoutingProfilePath`는 이 기본값의 project override이며 실제 사용자 선택을 보존한다. 현재 작업의 입력·위험·검사 조건으로 선택하고 스킬 이름만으로 고정하지 않는다.

| 작업 | 기본 모델 | 생각하는 정도 |
| --- | --- | --- |
| 중요한 설계·의도/원인·완료 판단 | GPT-6 Astra | high |
| 복잡한 구현·깊은 검토 | GPT-6.1 Sol | high |
| 기준이 정해진 일반 작업 | GPT-6.1 Sol | medium |
| 기계적으로 확인 가능한 좁은 반복 작업 | GPT-6 Luna | low |

공통표가 39개 스킬의 기본 tier와 각 tier의 후보 순서를 소유한다. 모호한 요구, 저장/상태/공용 경계나 여러 근거 충돌은 적합한 높은 tier로 배정한다. 스킬의 기본과 다른 tier에는 현재 작업의 이유를 기록한다. 좁은 목록 추출은 high-volume으로 분리할 수 있으나 전문 최종 판정·불명확한 원인 분석을 반복 작업으로 포장하지 않는다. 공통표 밖의 외부 스킬에는 명시 tier와 근거가 필요하다.

공식 [OpenAI 모델 선택](https://developers.openai.com/api/docs/guides/model-selection)과 [Codex/Work 안내](https://learn.chatgpt.com/docs/models)를 2026-10-10 확인했다. Astra의 어려운 판단, Sol의 복잡한 작업, Luna의 좁은 반복 작업이라는 설명에 따른 운영 배치이며 실제 업무의 최적 모델·비용·속도 절감을 측정한 결론은 아니다. 현재 호스트 도구의 모델과 effort 지원을 매 배정에서 다시 확인한다. API의 모델 존재나 가격은 계정의 접근 권한·Codex 사용량을 증명하지 않는다.

## 선택과 실제 배정

사용자가 지정한 모델/effort를 먼저 보존한다. 지정한 값을 지원하지 않으면 해당 배정을 막으며 다른 값으로 조용히 바꾸지 않는다. 그다음 스킬 기본/이유 있는 작업 tier, 명시 project override 또는 공통 프로필, 현재 사용 가능한 모델과 effort를 대조한다. 적합한 후보 순서에서 선택하며 preferred 부재의 대체 이유를 기록한다. 대체가 같은 품질을 보장한다고 주장하지 않는다.

선택기는 설치 위치에서 공통 파일을 읽고 기존 explicit tier 호출도 유지한다. 모델 이름만 선택하고 끝내지 않는다. 현재 호스트에서 지원을 확인한 선택 결과로 `model`, `reasoning_effort`, `fork_turns:"none"`를 만들고 실제 새 `collaboration.spawn_agent`에 전달한다. task_name/message는 필요한 범위·원본·기준만 추가한다. 모델 override와 full-history fork를 함께 전달하지 않는다. resolver는 생성 요청을 준비하며 자동 agent 실행/외부 API 호출을 하지 않는다.

새 공통표의 `onUnavailable`/`onUnsupportedOverride`는 blocked다. 사용할 적합 모델·지원되는 effort·모델 지정 기능이 없으면 이유와 막힌 작업을 반환한다. 기존 schema1 project 프로필에서 이 정책 키를 생략하면 이전 host-default fallback을 보존한다. 이는 호환 이력이며 모델의 적합성이나 실제 적용 PASS가 아니다. 사용자 명시 모델의 부재/미지원 차단은 어느 경우에도 유지한다.

`followup_task`는 모델·effort를 바꾸는 도구가 아니다. 실제 생성에 기록된 이전 모델/effort가 새 결정과 같고 역할/쓰기 범위가 호환될 때만 재사용한다. 다르거나 모델 신원이 불명확하면 새 작업자를 만든다. 현재 root 모델은 바꾸지 않으며 다른 모델이 필요한 전문 결과를 새 작업자에게 맡긴다. 매핑 자체가 새 위임·제품 변경·외부 권한을 만들지는 않는다.

## 기록과 검증

기존 capabilityTier/reasoningClass/resolvedModel/resolutionSource/overrideSupported/fallbackReason을 유지한다. profile revision·skill·선택 사유·현재 host 지원과 제출한 생성 인자를 기존 배정 envelope에 연결한다. 호스트가 실제 응답한 actor/creation acknowledgement와 실제 런타임 model header는 별도로 기록한다. header가 없으면 unknown/null이며 요청 설정이나 자기소개로 만들어내지 않는다. creation 응답이 불명확하면 새 작업자를 중복 생성하지 않고 실제 상태를 확인한다.

공통 파일 누락/손상·스킬표 누락·잘못된 타입·효력 없는 effort·부재/미지원 후보는 생성 성공이 아니다. 현재 후보에서 정상·부정·legacy/명시 선택·대체·다른 cwd/설치 위치의 로드와 실제 작업자 요청을 확인한다. 별도 검토의 독립성·기능·UI·출처·승인·실패예산은 모델을 선택했다고 면제되지 않는다.

실제 생성 인자가 필요한 호출 예시는 아래와 같다. `현재-호스트.json`은 그 시점 도구 metadata의 모델 ID → 지원 effort 배열이며 프로젝트 고정 설정으로 복제하지 않는다.

```sh
python -B .agents/skills/game-workflow-supervision/scripts/resolve_model_route.py --skill game-rule-implementation --host-support 현재-호스트.json --override-supported
```

기본과 다른 실제 작업에는 `--tier high-volume --tier-reason "현재 작업의 좁은 범위와 검사 이유"`를 추가한다. 반환의 `spawnArgs`가 없거나 decision이 blocked이면 모델 지정 배정으로 기록하지 않는다. 모델 목록만 주는 기존 `--available-model` 호출은 선택 결과만 확인하며 effort 지원과 실제 생성 인자를 검증한 결과가 아니다.
