# U3 NFR Design Patterns — Order (+ Cart)

U0가 확립한 패턴을 재사용/적용한다. U3 고유 관심사(오케스트레이션·스냅샷·채번·소프트 삭제)에 대한 패턴을 추가.

## 멀티테넌시 격리 (NFR-3) — 재사용
- **Scoped Repository**: `OrderRepository(BaseRepository[Order])` 상속으로 모든 쿼리에 `store_id` 강제. 별도 격리 코드 불필요.
- **Context-injected store_id**: 라우터는 `require_table`/`require_admin`로 `StoreContext` 주입, `store_id`는 토큰에서만(BR-U3-8, BR-U0-3).
- **Fail-closed**: 타 매장 주문 접근은 스코프 미스로 `NotFoundError`(404) 은닉.

## 도메인 오케스트레이션 (NFR-1 협력)
- **Gateway 인터페이스 + 의존성 주입**: 계약 A(`MenuLookup`)·계약 B(`SessionGateway`)를 `Protocol`로 정의하고 서비스 생성 시 주입. 단위 테스트는 모킹, 통합 시 실제 U2/U4 구현 주입(병렬 개발 Q6-B, 의존 역전).
- **Post-commit publish**: 주문 생성/상태변경/삭제는 DB 커밋 후 `realtime.publish` 호출(계약 D). 이벤트는 U0 `events.py` 팩토리로만 생성(스키마 단일 출처).
- **Best-effort 발행**: `realtime.publish`의 예외는 U0 헬퍼가 흡수(BR-U0-13/BR-U3-11) — 주문 정합 우선, 실시간은 부가.

## 데이터 무결성 패턴
- **Snapshot on write**: OrderItem에 주문 시점 `menu_name`·`unit_price` 복사(BR-U3-3). 참조 무결성을 스냅샷으로 대체 → 메뉴 변경/삭제와 디커플링(FK 미사용, 유닛 경계).
- **Soft delete**: `is_deleted`/`deleted_at` 필터링(BR-U3-9). 조회·집계는 `is_deleted=false` 기본 스코프.
- **Archive flag(계약 C)**: `archived`로 세션 종료 이력 이관 표시. 멱등 처리(이미 archived면 무시, BR-U3-14).
- **Server-authoritative 금액**: 총액·라인 금액은 서버 계산만 신뢰(클라이언트 값 무시, BR-U3-5).

## 동시성 패턴 (채번)
- **Unique constraint + retry**: `order_no`는 `max+1` 채번, `unique(store_id, order_no)`로 경합 방어. IntegrityError 시 1회 재채번 재시도. SQLite 단일 라이터라 실경합 낮음.
- **Single transaction**: Order+OrderItems 원자적 저장. 세션 확보(계약 B) 실패 시 저장 중단(BR-U3-4b).

## 성능 패턴 (로컬 규모)
- **Eager load**: `selectinload(Order.items)`로 상세·목록 N+1 회피.
- **Index**: `(store_id, session_id)`, `(store_id, table_id)`, unique `(store_id, order_no)`.
- **Pagination**: U0 `PageParams`/`Page[T]`(기본 limit 50, max 200)로 응답 크기 제한.

## 오류 처리 — 재사용
- 도메인 규칙 위반 시 U0 typed `AppError`(ValidationError/NotFoundError/ForbiddenError) raise → 중앙 핸들러가 표준 `ErrorResponse`로 변환.

## 관측
- 표준 로깅(publish 실패 warning, 채번 재시도 debug). 로컬 데모 — 별도 APM 없음.

## 확장 준수
- Security / Resiliency / Property-Based Testing 모두 Disabled → 관련 강제 패턴 **N/A**(결함 아님). 재시도·격리·best-effort는 기능 규칙으로 이미 반영.
