# U4 Session + Realtime — Code Summary

**유닛**: U4 Session + Realtime (담당: 이재환) · **브랜치**: `feature/u4-session-realtime`
**구현 스토리**: US-A2(실시간 대시보드), US-A6(세션 종료·이력 이관), US-A7(과거 이력), US-C6(고객 상태 실시간)
**생성 방식**: AI-DLC Code Generation (17-step 계획 승인 후 Workflow 병렬 구현 + 적대적 검증)

## 생성 파일 (신규)

### 백엔드 — `backend/app/session/` (3계층: router → service → repository)
| 파일 | 역할 | 공개 심볼 |
|---|---|---|
| `models.py` | 소유 엔티티 3종 | `TableSession`(부분 유니크 `uq_active_session_per_table WHERE status='active'`), `SessionHistoryOrder`, `SessionHistoryOrderLine` |
| `provider.py` | 계약 C 디커플(레지스트리) | `OrderHistoryProvider`(Protocol), `NoOpOrderProvider`, `register_order_provider`/`get_order_provider` |
| `repository.py` | store 격리 영속(NFR-3) | `SessionRepository(BaseRepository[TableSession])`: `get_active`, `create_active`, `list_history_orders` |
| `service.py` | 계약 B/C/D 오케스트레이션 | `SessionService`: `start_or_get_active_session`, `get_active_session`, `close_session`, `get_dashboard`, `list_history` |
| `schemas.py` | API 응답(pydantic v2) | `RecentOrder`, `DashboardCard`, `CloseSessionRequest`, `ClosedSessionSummary`, `HistoryOrderLineOut`, `HistoryOrderOut` |
| `router.py` | REST 엔드포인트(require_admin) | `router`(prefix `/sessions`): `GET /dashboard`, `POST /close`, `GET /history` |

### 백엔드 — `backend/app/realtime/`
| 파일 | 역할 | 공개 심볼 |
|---|---|---|
| `broker.py` | 계약 D 구현, NFR-1 | `InMemoryBroker`(매장별 구독자·`asyncio.Queue(maxsize=1000)`·`bind_loop`/`subscribe`/`unsubscribe`/`publish`(스레드세이프)), 모듈 싱글턴 `broker` |
| `router.py` | SSE 스트림 | `router`(prefix `/realtime`): `GET /admin/stream`(매장 전체), `GET /table/stream`(서버측 table_id 필터, Q8=A) |

### 테스트 — `backend/tests/`
| 파일 | 커버리지 |
|---|---|
| `test_session.py` (9) | 멱등 시작(BR-U4-2), 부분유니크 활성세션(BR-U4-1), 종료·스냅샷·아카이브·총액(BR-U4-4/6), 주문0건 종료(BR-U4-5), NotFound, store 격리(BR-U4-3), 이력 정렬/날짜필터/Page(BR-U4-8/15), 대시보드 preview_n 보정(BR-U4-16) |
| `test_realtime.py` (10) | 브로커 구독/발행, store 격리(BR-U4-10), table 필터(Q8=A), 스레드→루프 핸드오프(NFR-1), best-effort(BR-U4-9), unsubscribe, **SSE 엔드포인트 인증(401)·역할(403)·admin 매장전체/table 서버측 필터 구독** |

### 프론트엔드
| 파일 | 역할 |
|---|---|
| `frontend-admin/src/api/session.js` | `getDashboard`, `closeSession`, `getHistory` (U0 client.js 재사용) |
| `frontend-admin/src/views/DashboardView.vue` | US-A2/A6: 초기 스냅샷 + `openSse('/realtime/admin/stream')` 라이브 갱신·강조, 테이블 필터, 세션 종료(확인), 재연결 재동기화(Q7=C), NFR-6 |
| `frontend-admin/src/views/HistoryView.vue` | US-A7: 이력 목록(closed_at 역순), 테이블/날짜 필터, 페이지네이션 |
| `frontend-customer/src/api/sse.js` | admin sse.js 미러링(신규) — 토큰 query, EventSource |
| `frontend-customer/src/stores/realtime.js` | US-C6: `openSse('/realtime/table/stream')` → `order.status_changed`로 `statusByOrderNo` 갱신 |

## 수정 파일 (Additive — 공유 파일, 다른 유닛 슬롯 미변경)
| 파일 | 변경 |
|---|---|
| `backend/app/common/security.py` | `verify_token(token) -> StoreContext` 추가(계약 E 확장, SSE query 인증). 기존 심볼 불변 — **팀 조율 대상** |
| `backend/app/main.py` | lifespan: `broker.bind_loop(asyncio.get_running_loop())` + `register_publisher(broker)`; create_app: `include_router(session_router, realtime_router)` |
| `backend/app/common/database.py` | `init_db`에 `from app.session import models` 등록 |
| `frontend-admin/src/router/index.js` | `/dashboard`·`/history` 라우트 슬롯 활성화 |

## 계약 / 스토리 트레이스
- **계약 B**(제공, U3 소비): `SessionService.start_or_get_active_session`/`get_active_session` — in-process 호출.
- **계약 C**(소비, U3 제공): `OrderHistoryProvider` 레지스트리 + `NoOpOrderProvider`(스탠드얼론). 종료 시 `collect_active_session_orders`→스냅샷, `mark_orders_archived`.
- **계약 D**(구현): `InMemoryBroker`가 U0 `RealtimePublisher` 구현, `main.py`에서 등록. domain service는 U0 best-effort `publish` 헬퍼 사용.
- **계약 E**(확장): `verify_token` — SSE query 토큰 인증.
- US-A2 → service.get_dashboard/router/realtime admin stream/DashboardView. US-A6 → close_session/DashboardView. US-A7 → repository.list_history_orders/HistoryView. US-C6 → realtime table stream/customer realtime store.

## 통합 지점 (U3/U1 완료 후 연결)
1. **계약 B/C 실연동**: U3(최지영)가 `register_order_provider(실제구현)` 등록 + 첫 주문 시 `start_or_get_active_session` 호출. 현재는 NoOp/Mock.
2. **SSE 라이브 검증**: 실제 `TokenVerifier`(U1) 등록 후 admin 토큰으로 `curl -N /realtime/admin/stream?token=` → 세션 종료 시 2초 내 `session.closed` 수신(NFR-1), cross-tenant 미수신(NFR-3).
3. **고객 실시간 화면**: `stores/realtime.js`의 `statusByOrderNo`를 U3 `OrderHistoryView`(US-C5)가 구독. 재연결 시 U3 현재세션 조회로 재동기화.
4. **대시보드 카드 클릭 → 주문 상세**: U3 `OrderDetailView` 라우트로 이동(현재 통합 지점 주석).
5. **admin 라우트 인증**: `/dashboard`·`/history` `requiresAuth:false`(단독 빌드용) → U1 로그인 랜딩 도입 시 `true`로 조정.

## 검증 결과
- `pytest -q` → **24 passed** (U0 5 + realtime 10 + session 9). 경고 2건(passlib/starlette deprecation) 무관.
- 앱 부팅(TestClient lifespan) → `/health` 200, `/openapi.json`에 5개 U4 라우트 노출.
- `frontend-admin`·`frontend-customer` `vite build` 성공.

## 적대적 리뷰(3 렌즈: 계약/멀티테넌시/실시간) — blocker 0, major 0, minor 4
- **반영**: (1) `start_or_get_active_session` 경합 시 `IntegrityError`→rollback→refetch 멱등 가드(BR-U4-2); (2) `list_history_orders` 조인 `TableSession.store_id` 심층방어(NFR-3); (3) `_now()` naive-UTC 통일로 `closed_at` 응답 형태 일치; (4) SSE 엔드포인트 인증/역할/필터 단위 테스트 4종 추가.
- **이월**: closed_at 날짜필터의 비-UTC(KST) day-boundary off-by-one은 로컬 데모 범위 밖(UTC 기준 필터로 문서화).
