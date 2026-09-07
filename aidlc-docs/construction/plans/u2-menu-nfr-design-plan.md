# U2 Menu — NFR Design Plan

**유닛**: U2 Menu · **담당**: 이원종
**입력**: `aidlc-docs/construction/u2-menu/nfr-requirements/*` (승인 완료), U0 NFR Design(patterns·logical-components).

> U2 NFR Requirements 결정(페이지네이션·캐싱·신규 의존성 **모두 없음**)에 따라, U2 NFR Design은 **U0가 정의한 패턴을 상속·적용**하는 것으로 충족된다. 신규 인프라 컴포넌트(큐/캐시/서킷브레이커 등)는 없다.

## 카테고리별 적용성 평가 (질문 필요 여부)

| 카테고리 | U2 적용 | 열린 결정? |
|---|---|---|
| Resilience(내결함성) | 단일 트랜잭션 + 표준 예외 핸들러(U0 상속). 재시도/서킷브레이커 불필요(로컬 데모) | ❌ 없음 |
| Scalability(확장) | 소량 데이터, 단일 프로세스. 스케일 메커니즘 불필요 | ❌ 없음 |
| Performance(성능) | 페이지네이션·캐싱 없음(NFR Req 확정), 인덱스로 충분 | ❌ 없음 |
| Security(보안) | `require_admin`/`require_table` 가드 + store 격리(U0 상속) | ❌ 없음 |
| Logical Components | Menu 패키지 3계층(router/service/repository) + 모델/스키마. 신규 인프라 컴포넌트 없음 | ❌ 없음 |

**→ 열린 질문 없음.** 모든 패턴이 U0에서 상속되거나 로컬 데모 범위로 N/A. 질문 게이트 생략(U0 NFR Design 선례와 동일). 산출물 바로 생성.

## 산출물 계획

- [x] `nfr-design-patterns.md` — U2에 적용되는 상속 패턴(멀티테넌시·인증가드·검증·소프트삭제/품절 조회·정렬·영속성) + 미적용(캐싱/실시간) 명시
- [x] `logical-components.md` — Menu 패키지 논리 컴포넌트(router/service/repository/models/schemas) + 프론트, 인프라 컴포넌트 N/A
