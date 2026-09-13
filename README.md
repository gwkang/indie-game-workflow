# Indie Game Workflow

소규모 인디게임 개발에 사용하는 범용 에이전트 스킬 모음입니다. **워크플로우 26개 + 외부 UI 스킬 10개**로 구성합니다. 개발·개선·버그 수정을 분리하며 프로토타입 단계를 강제하지 않습니다.

## 주요 규칙

- 프로젝트 프로필에 엔진, 2D/3D, 대상 환경, 명령, 선호 언어를 기록합니다. 기본 언어는 한국어입니다.
- 사용자 의도와 확정·제안·위임·미정 상태를 보존합니다.
- 산출물마다 형식·소비 규칙·통과 기준·수정 범위를 고정합니다.
- 작성자와 다른 서브에이전트가 검증합니다. 오류는 작성자가 수정하고 별도 검증자가 재검증합니다.
- 검증 중 발견한 범위 밖 문제는 기록만 하며, 작업이나 필수 검사로 추가하지 않습니다.
- 필요한 역할만 실행합니다. 독립 작업만 병렬화하며 감독자는 입력·소유권·자원·합류를 관리합니다.

## 구성

| 영역 | 스킬 |
| --- | --- |
| 접수·진입·감독 | game-workflow, indie-game-development, indie-game-improvement, indie-game-bugfix, game-workflow-supervision |
| 설정·명세·분석·계획 | game-project-profile, game-feature-spec, game-improvement-assessment, game-bug-reproduction, game-bug-diagnosis, game-task-planning, game-technical-design |
| 구현 | game-rule-implementation, game-input-implementation, game-movement-implementation, game-camera-implementation, game-session-implementation, game-content-loading, game-save-implementation, game-platform-integration |
| 측정·검증·패키징 | game-performance-profiling, game-test-design, game-test-infrastructure, game-functional-verification, game-code-review, game-build-packaging |

UI는 [game-ui-production-skills](https://github.com/gwkang/game-ui-production-skills)의 10개 역할을 재사용합니다. 이 저장소에 UI 원본을 중복 포함하지 않습니다. 설치에는 아래 고정 버전의 UI 저장소도 필요합니다.

## 설치

**UI 의존성 공개 대기:** 아래 고정 UI 커밋은 아직 기존 공개 저장소에 업로드되지 않았습니다. 따라서 현재 이 저장소만으로 통합 설치를 완료할 수 없습니다. UI 의존성 공개 후 아래 절차를 사용할 수 있습니다. 워크플로우 26개 원본과 계약은 지금 열람할 수 있습니다.

Python 3.12 이상과 Git이 필요합니다. 두 저장소를 같은 상위 폴더에 받습니다.

```sh
git clone https://github.com/gwkang/indie-game-workflow.git
git clone https://github.com/gwkang/game-ui-production-skills.git
git -C game-ui-production-skills checkout 589d5ce3728e03172d8171f906bcd69b195b62f0
cd indie-game-workflow
python -B tools/install_bundle.py --target "ABSOLUTE_EXISTING_SKILL_DIRECTORY"
python -B tools/install_bundle.py --target "ABSOLUTE_EXISTING_SKILL_DIRECTORY" --apply
```

`ABSOLUTE_EXISTING_SKILL_DIRECTORY`는 대상 에이전트가 읽는 기존 스킬 폴더의 절대 경로로 바꿉니다. 첫 명령은 미리보기이고 `--apply`가 36개 스킬과 필요한 참조·양식을 설치합니다. 설치기는 네트워크 다운로드를 하지 않습니다.

전체 파일 해시가 맞아야 설치됩니다. 기존 스킬이 다르면 덮어쓰지 않고 중단합니다. 자동 업그레이드는 지원하지 않으며 사용자 변경을 별도로 조정해야 합니다. UI 저장소의 최신 main 대신 명시된 커밋을 사용하세요. `.gitattributes`는 운영체제별 줄바꿈 때문에 해시가 달라지는 일을 방지합니다.

설치 성공은 파일 배치 완료입니다. 대상 런타임에서 스킬을 발견하는지 별도로 확인해야 하며, 엔진·DCC·플랫폼 SDK는 이 설치기가 설치하지 않습니다.

## 사용

요청과 함께 `game-workflow`를 호출하거나 개발·개선·버그 수정 진입 스킬을 직접 선택합니다. 기존 문서와 코드를 먼저 사용하고, 필요한 제품 결정만 대화로 보충합니다. 사용자가 미리 긴 명세를 작성할 필요는 없습니다.

> 기존 저장 형식은 유지하면서 일시정지 기능을 추가해줘. 버튼 모양은 기존 UI 스타일 안에서 결정해도 돼. 검증은 일시정지·복귀와 해당 입력 경계로 제한해줘.

각 스킬 본문에는 핵심 책임을 두고 상세 규칙은 참조로 연결했습니다. 시작점은 [공통 역할 계약](skills/game-task-planning/references/role-contract.md), [산출물 양식](skills/game-task-planning/references/artifact-contract.md), [범위 제한 검증](skills/game-task-planning/references/verification-scope.md)입니다.

## 검증과 한계

현재 버전은 `0.5.0-role-contracts`입니다. 36개 스킬의 지침·인계 계약을 별도 서브에이전트로 검토했습니다. 이는 실제 게임 제작 품질이나 모든 엔진에서의 실행 성공을 보증하지 않습니다.

감독은 지침과 Markdown 기록으로 동작합니다. 트랜잭션 그래프 실행기, 원자적 자원 예약, 자동 장애 복구, 백그라운드 서비스는 포함하지 않습니다. 오디오·3D 에셋 제작 등 별도 전문 역할이 필요한 작업은 그 능력을 추가로 확인해야 합니다.

설치기 검증:

```sh
python -B -m unittest discover -s tests -v
```

프로젝트 코드·게임 에셋·개인 작업 로그는 배포에 포함하지 않습니다. MIT 라이선스입니다.
