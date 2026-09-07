# U2 Menu NFR Design Patterns

U2는 U0가 확립한 패턴을 상속·적용한다. 신규 패턴/인프라는 없다.

## 멀티테넌시 격리 패턴 (NFR-3) — 상속
- **Context-injected tenant scoping**: Menu 라우터가 `Depends(get_current_store_context)`로 `ctx` 주입, `store_id=ctx.store_id`만 사용(클라이언트 store_id 불신, BR-U0-3).
- **Scoped Repository**: `MenuRepository`·`CategoryRepository`가 U0 `BaseRepository`를 상속 → 모든 쿼리에 `store_id` 필터 자동 강제(BR-U2-0). 별도 격리 코드 불필요.
- **Fail-closed**: 타 매장 카테고리/메뉴 접근은 404 은닉(BR-U0-4, BR-U2-10).

## 인증·인가 패턴 (NFR-2 소비) — 상속
- **Role guards**: 관리자 엔드포인트 `require_admin`, 고객 조회 `require_table`(BR-U2-17). 역할 불일치 403.
- 토큰 발급/검증은 U1 소관. U2는 가드 의존성만 소비.

## 입력 검증 패턴 — 상속·적용
- **Schema validation at boundary**: 라우터에서 Pydantic 스키마로 `MenuInput` 검증(name 필수, `price: int ge=0`, `image_url: HttpUrl|None`)(BR-U2-1~5, Q6:B·Q7:B).
- **Typed AppError → central handler**: 도메인/검증 위반은 U0 `ValidationError`/`NotFoundError`/`ForbiddenError` raise → 중앙 핸들러가 표준 `ErrorResponse`로 변환(BR-U0-10). U2는 예외만 raise.

## 조회 필터 패턴 (소프트삭제/품절) — U2 고유 적용
- **Soft-delete filter**: 고객 조회·관리 목록·계약 A는 리포지토리에서 `is_deleted=false` 필터(BR-U2-11).
- **Availability surfacing(불필터)**: 고객 조회는 품절(`available=false`)도 **포함**해 반환(프론트 품절 배지). 계약 A도 `available` 값을 실어 반환하고 주문 성립 판정은 U3에 위임(BR-U2-12/15/16).

## 노출 순서 패턴 — U2 고유 적용
- **Explicit order column + full-set reorder**: `display_order` 컬럼 정렬. 재정렬은 대상 전체 집합 일치 검증 후 0부터 재할당을 **단일 트랜잭션**으로 수행(BR-U2-6/7).

## 영속성 패턴 (NFR-4) — 상속
- **Session-per-request**: U0 `get_db` 의존성으로 요청당 세션 생성/정리. 쓰기 메서드는 단일 트랜잭션.
- **Declarative create_all**: Menu/Category 모델을 U0 `init_db`에 import 등록(BR-U2-18), 파괴적 변경 없음.

## 미적용 패턴 (명시)
- **캐싱**: 없음(Q2:A) — 매 요청 DB 조회.
- **페이지네이션**: 없음(Q1:A) — 전체 반환.
- **실시간(NFR-1)**: 없음 — U2는 이벤트 미발행. 메뉴 변경은 다음 조회 시 반영.
- **인프라(큐/캐시/서킷브레이커)**: N/A(로컬 데모).

## 관측(경량) — 상속
- 표준 로깅만. 검증 실패는 422 응답으로 충분, 별도 APM 없음.
