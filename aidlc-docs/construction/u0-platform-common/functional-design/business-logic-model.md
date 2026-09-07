# U0 비즈니스 로직 모델 (Business Logic Model)

U0는 비즈니스 도메인 로직보다 **공통 인프라 계약**을 제공한다. 각 요소는 계약(A~E)의 소유/정의 지점.

## 1. 데이터베이스 (`common/database.py`)
- **동기** SQLAlchemy 엔진(`sqlite:///./table_order.db`), `check_same_thread=False`.
- `SessionLocal` 세션 팩토리, `Base` 선언적 베이스.
- `get_db()` — FastAPI 의존성(요청당 세션, 종료 시 close).
- `init_db()` — 모든 모델 import 후 `Base.metadata.create_all(engine)`. Alembic 미사용(결정).

## 2. StoreContext 주입 (`common/security.py`) — 계약 E
- `StoreContext` 값 객체(store_id, role, subject, table_id).
- `TokenVerifier` 프로토콜: `verify(token: str) -> StoreContext`.
- `register_token_verifier(fn)` / 내부 레지스트리 — Auth(U1)가 앱 시작 시 등록(U0→U1 역의존 방지).
- `get_current_store_context(authorization: Header) -> StoreContext` 의존성 — Bearer 토큰 추출→등록된 검증자 호출→실패 시 401.
- `require_admin` / `require_table` 편의 의존성(role 강제).

## 3. BaseRepository (`common/repository.py`) — 스토어 스코프 강제 (NFR-3)
- 제네릭 `BaseRepository[ModelT]`(`__init__(db, model)`).
- **모든 조회/변경 메서드는 `store_id: int`를 필수 인자로 받는다**. 내부 `_scoped_query(store_id)`가 `model.store_id == store_id` 필터를 항상 적용.
- 메서드: `get(store_id, id)`, `list(store_id, *, offset, limit, **filters)`, `create(store_id, **fields)`, `update(store_id, id, **fields)`, `delete(store_id, id)`.
- 크로스 테넌트 접근 시(다른 store의 row) `get`은 None → 라우터에서 404. 존재하나 store 불일치도 동일하게 은닉(정보 노출 방지).

## 4. 이벤트 스키마 (`common/events.py`) — 계약 D
- `Event` 베이스: `type: str`, `store_id: int`, `payload: dict`, `ts: datetime`.
- 상수 타입: `ORDER_CREATED`, `ORDER_UPDATED`, `ORDER_STATUS_CHANGED`, `ORDER_DELETED`, `SESSION_CLOSED`.
- 팩토리 헬퍼: `order_created(store_id, order)`, `session_closed(store_id, table_id, session_id)` 등 — 발행자(U3/U4)와 구독자(SSE)가 공유하는 단일 스키마 소스.

## 5. Realtime Publisher 계약 (`common/realtime.py`) — 계약 D
- `RealtimePublisher` 프로토콜: `publish(store_id: int, event: Event) -> None`.
- `register_publisher(pub)` / `get_publisher()` — U4가 실제 인메모리 pub-sub 브로커 등록.
- 기본값 `NoOpPublisher`(등록 전/테스트용) — 병렬 개발 중 U3/U4가 계약에 대고 독립 진행 가능.

## 6. 공통 응답/페이지네이션/예외
- `common/schemas.py`: `ErrorResponse`, `PageParams(offset, limit)`, `Page[T](items, total, offset, limit)`.
- `common/exceptions.py`: `AppError`(base), `NotFoundError`, `ForbiddenError`, `ValidationError`, `AuthError` + FastAPI exception handlers → 표준 `ErrorResponse` JSON.

## 7. 앱 조립 (`app/main.py`)
- FastAPI 앱 생성, CORS(고객/관리자 SPA origin 허용), 예외 핸들러 등록, `init_db()` 호출, 각 도메인 라우터 `include_router`(스텁 포함). 시작 시 U1이 `register_token_verifier`, U4가 `register_publisher` 등록.

## 계약 매핑 요약
| 계약 | U0 제공물 | 실제 구현 소유 |
|---|---|---|
| A Menu 조회 | (인터페이스는 U2에서 정의) | U2 |
| B Session 시작/조회 | (인터페이스는 U4에서 정의) | U4 |
| C 이력 이관 | (인터페이스는 U3에서 정의) | U3 |
| D Realtime publish + 이벤트 스키마 | `events.py` + `RealtimePublisher` 프로토콜/레지스트리 | U4(브로커) |
| E StoreContext | `security.py` StoreContext + 주입 의존성 + 검증자 레지스트리 | U1(검증자) |
