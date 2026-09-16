# 저장과 보상

## 현재 계약
- 승인된 결정: 저장 성공 후에만 보상을 확정한다. 실패하면 확정하지 않는다. [명세 v1](../spec/save.md)의 SAVE-1/SAVE-2가 규범이다.
- 확인된 구현: `grant`는 `save` 완료를 기다린 다음 `confirm`을 호출한다. [구현](../src/save.mjs), [지연 성공 및 실패 테스트](../test/save.test.mjs).
- 적용 범위: fixture comet의 grant 함수. 저장 장치나 실제 게임 통합까지 검증한 것은 아니다.
- 최종 확인: 2026-09-16. [출처 SHA-256](../evidence/input-identities.json), [실행 근거](../evidence/verified-fix-tests.txt). 변경된 출처를 재확인하기 전에는 현재 구현의 확정 사실로 재사용하지 않는다.

## 대체된 설명
[이전 명세 v0](../spec/save-v0.md)의 "보상을 먼저 확정한 뒤 저장" 설명은 v1로 대체되었다. 기존 설명은 [갱신 전 사본](../evidence/wiki-before.md)으로 추적한다.
