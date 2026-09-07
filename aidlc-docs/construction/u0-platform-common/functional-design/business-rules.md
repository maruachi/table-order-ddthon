# U0 비즈니스 규칙 (Business Rules)

## 멀티테넌시 강제 (NFR-3) — 최우선 규칙
- **BR-U0-1**: store 격리가 필요한 모든 엔티티는 `store_id` 컬럼을 가지며 인덱싱한다.
- **BR-U0-2**: 모든 리포지토리 조회/변경은 `BaseRepository`를 통해 `store_id` 필터를 **항상** 적용한다. store_id 없는 직접 쿼리 금지.
- **BR-U0-3**: `store_id`는 클라이언트 입력이 아니라 **인증 토큰에서 파생된 `StoreContext.store_id`** 만 사용한다(요청 바디/쿼리의 store_id 신뢰 금지).
- **BR-U0-4**: 다른 매장의 리소스 접근 시도는 존재 여부를 노출하지 않고 404로 처리(타이밍/정보 노출 최소화).

## 인증 컨텍스트 (계약 E)
- **BR-U0-5**: 인증 필요한 모든 엔드포인트는 `get_current_store_context` 의존성을 통과한다.
- **BR-U0-6**: `role`이 `admin`/`table` 요건과 불일치하면 403.
- **BR-U0-7**: 토큰 검증자 미등록 상태에서 인증 요청 시 500이 아닌 명확한 구성 오류 로깅 + 401.

## 영속성 (NFR-4)
- **BR-U0-8**: 모든 도메인 데이터는 SQLite에 영속 저장. 인메모리 상태(Realtime 구독자)는 예외이며 재시작 시 재구독 허용.
- **BR-U0-9**: 스키마는 `init_db()`의 `create_all`로 생성. 기존 테이블은 보존(파괴적 마이그레이션 없음).

## 검증/예외
- **BR-U0-10**: 입력 검증 실패는 `ValidationError`→422, 미존재는 `NotFoundError`→404, 권한은 `ForbiddenError`→403, 인증은 `AuthError`→401. 모두 표준 `ErrorResponse` 형식.
- **BR-U0-11**: `Store.code`, `(store_id, table_number)`는 유일. 중복 생성 시 `ValidationError`.

## 이벤트/실시간 (계약 D)
- **BR-U0-12**: 이벤트 스키마는 `common/events.py` 단일 소스만 사용. 발행자는 임의 dict가 아닌 팩토리 헬퍼로 생성.
- **BR-U0-13**: `publish`는 실패해도 주 트랜잭션을 롤백하지 않는다(실시간 전파는 best-effort, 주문 저장 성공 우선).
