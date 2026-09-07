# U4 Session + Realtime — Code Generation Plan

**유닛**: U4 Session + Realtime (담당: 이재환). **단일 진실 소스** = 이 계획서.
**워크스페이스 루트**: `/Users/jwlee/workspace/claude/table-order-ddthon` (Greenfield 멀티유닛 모놀리식 → `backend/app/{도메인}/`, `frontend-*/`).
**브랜치**: `feature/u4-session-realtime`.

## 유닛 컨텍스트
- **구현 스토리**: US-A2(실시간 대시보드), US-A6(세션 종료·이력 이관), US-A7(과거 이력), US-C6(고객 상태 실시간).
- **제공 계약**: B(세션 시작/조회 — U3 소비), D(Realtime 브로커 구현·등록).
- **소비 계약**: C(이력 이관 — U3 제공, `OrderHistoryProvider` 레지스트리로 디커플, 스탠드얼론 Mock).
- **의존 계약**: E(StoreContext — U0). SSE는 query 토큰 검증(`verify_token` additive).
- **소유 엔티티**: `TableSession`, `SessionHistoryOrder`, `SessionHistoryOrderLine`.
- **공유 파일(additive만)**: `common/security.py`(verify_token 추가), `main.py`, `common/database.py`, 프론트 `router/index.js`.

## 생성 단계 (순차)

### 백엔드 — Repository/도메인 계층
- [x] **Step 1. Session 모델** — `backend/app/session/models.py`: `TableSession`(부분 유니크 활성세션), `SessionHistoryOrder`, `SessionHistoryOrderLine`. `BaseRepository` 호환(store_id). [엔티티]
- [x] **Step 2. Order History Provider(계약 C)** — `backend/app/session/provider.py`: `OrderHistoryProvider` 프로토콜 + `register_order_provider()`/`get_order_provider()` + `NoOpOrderProvider`(빈 목록). [계약 C 디커플]
- [x] **Step 3. Session Repository** — `backend/app/session/repository.py`: `SessionRepository(BaseRepository)` — active 세션 조회/생성/종료 전이, 이력 조회(closed_at 역순·table/날짜 필터·페이지). [NFR-3]

### 백엔드 — Realtime
- [x] **Step 4. In-memory Broker(계약 D)** — `backend/app/realtime/broker.py`: `InMemoryBroker`(`RealtimePublisher` 구현) — 매장별 구독자 집합, 구독자당 `asyncio.Queue(maxsize)`, `subscribe/unsubscribe`, threadsafe `publish`(`loop.call_soon_threadsafe`), 이벤트 루프 캡처. [NFR-1]

### 백엔드 — Service 계층
- [x] **Step 5. Session Service** — `backend/app/session/service.py`: 계약 B(`start_or_get_active_session`, `get_active_session`), `close_session`(US-A6: 계약 C 수집→스냅샷 저장→상태전이→archive 마킹→`publish(session.closed)`), `get_dashboard`(US-A2, preview_n=3), `list_history`(US-A7). [계약 B/C/D]

### 백엔드 — Schemas/API 계층
- [x] **Step 6. Session Schemas** — `backend/app/session/schemas.py`: 대시보드/세션종료/이력 응답 Pydantic. [API]
- [x] **Step 7. Session Router** — `backend/app/session/router.py`: `GET /sessions/dashboard`, `POST /sessions/close`, `GET /sessions/history` (모두 `require_admin`, StoreContext.store_id만 사용). [US-A2/A6/A7]
- [x] **Step 8. SSE 인증 헬퍼(공유·additive)** — `backend/app/common/security.py`에 `verify_token(token: str) -> StoreContext` 추가(계약 E 확장, 다른 코드 미변경). [BR-U4-11]
- [x] **Step 9. Realtime Router** — `backend/app/realtime/router.py`: SSE `GET /realtime/admin/stream`(매장 전체), `GET /realtime/table/stream`(store+table 필터), query 토큰 검증, `StreamingResponse` + keepalive + disconnect 정리. [US-A2/C6, NFR-1/3]

### 백엔드 — 통합(additive)
- [x] **Step 10. 앱/DB 통합** — `main.py` lifespan에 `register_publisher(InMemoryBroker())`(+ 루프 캡처), `include_router(session_router, realtime_router)`; `common/database.py init_db`에 `from app.session import models` import. [통합]

### 백엔드 — 테스트
- [x] **Step 11. Session 테스트** — `backend/tests/test_session.py`: 세션 시작 멱등, 종료·이력 이관·총액 리셋(Mock provider), store 격리 fail-closed, US-A7 이력 조회/날짜 필터. [US-A2/A6/A7]
- [x] **Step 12. Realtime 테스트** — `backend/tests/test_realtime.py`: 브로커 구독/발행/store 격리, 스레드에서 publish→구독자 수신, best-effort(발행 실패 격리). [NFR-1/3]

### 프론트엔드 — Admin
- [x] **Step 13. Admin API + 라우트** — `frontend-admin/src/api/session.js`(getDashboard/closeSession/getHistory), `router/index.js`에 `/dashboard`·`/history` 슬롯 활성화(additive). [US-A2/A6/A7]
- [x] **Step 14. DashboardView** — `frontend-admin/src/views/DashboardView.vue`: 초기 스냅샷 + `openSse('/realtime/admin/stream')` 라이브 갱신·강조, 테이블 필터, 세션 종료 버튼(확인), 재연결 재동기화. `data-testid` 부여. [US-A2/A6, NFR-6]
- [x] **Step 15. HistoryView** — `frontend-admin/src/views/HistoryView.vue`: 이력 목록(closed_at 역순), 테이블/날짜 필터, 페이지네이션. `data-testid`. [US-A7]

### 프론트엔드 — Customer
- [x] **Step 16. Customer SSE + 실시간 반영** — `frontend-customer/src/api/sse.js`(신규, admin 미러링), 실시간 스토어/컴포저블(`stores/realtime.js`): `openSse('/realtime/table/stream')` → `order.status_changed` 반영. U3 주문내역 화면 연동은 통합 지점 주석. [US-C6]

### 문서
- [x] **Step 17. 코드 요약** — `aidlc-docs/construction/u4-session-realtime/code/code-summary.md`(생성/수정 파일, 계약/스토리 트레이스, 통합 지점, 검증 결과).

## 검증(생성 후) — 결과
- [x] `cd backend && pytest -q` → **24 passed** (기존 U0 5 + realtime 10 + session 9). 경고 2건은 passlib/starlette deprecation(무관).
- [x] 앱 부팅(TestClient lifespan: init_db + register_publisher(broker) + bind_loop) → `/health` 200, `/openapi.json`에 `/sessions/{dashboard,close,history}`·`/realtime/{admin,table}/stream` 노출 확인.
- [x] `frontend-admin`·`frontend-customer` `vite build` 성공(Dashboard/History/session 청크, customer 번들 정상).
- [~] SSE 라이브 curl 검증(2초 내 `session.closed` 수신, cross-tenant 미수신): 실제 `TokenVerifier`(U1) 등록이 필요하여 **통합 시점으로 이월**. 대신 SSE 엔드포인트 인증/역할/서버측 table_id 필터를 단위 테스트로 검증(test_realtime.py), 전파/격리/스레드-루프 핸드오프/best-effort는 브로커 테스트로 검증.

## 적대적 리뷰 반영(minor 4건)
- [x] `service.start_or_get_active_session`: 부분유니크 경합 시 `IntegrityError`→rollback→refetch로 멱등 보장(BR-U4-2).
- [x] `repository.list_history_orders`: 조인된 `TableSession.store_id == store_id` 조건 추가(NFR-3 심층방어).
- [x] `service._now()`: naive-UTC로 통일 — `/sessions/close`와 `/sessions/history`의 `closed_at` 형태 일치(SQLite tz strip 대응).
- [x] `tests/test_realtime.py`: SSE 엔드포인트 인증(401)·역할불일치(403)·admin 매장전체/table 서버측 필터 구독 4종 추가.
- (이월) closed_at 날짜필터의 비-UTC(KST) day-boundary off-by-one: 로컬 데모 범위 밖으로 문서화(UTC 기준 필터).

## 계약/스토리 트레이스
- 계약 B → Step 5; 계약 C → Step 2/5; 계약 D → Step 4/5/9/10; 계약 E 확장 → Step 8.
- US-A2 → Step 5/7/9/13/14; US-A6 → Step 5/7/14; US-A7 → Step 3/5/7/15; US-C6 → Step 9/16.
- NFR-1 → Step 4/9; NFR-3 → Step 3/9; NFR-4 → Step 1/3.
