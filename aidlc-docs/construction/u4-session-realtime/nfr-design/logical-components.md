# U4 논리 컴포넌트 (Logical Components)

| 논리 컴포넌트 | 파일(예정) | 역할 | 관련 NFR/계약 |
|---|---|---|---|
| Session Models | `app/session/models.py` | `TableSession`, `SessionHistoryOrder`, `SessionHistoryOrderLine` | NFR-3/4 |
| Session Repository | `app/session/repository.py` | `SessionRepository(BaseRepository)` — active 조회/생성/종료, 이력 쿼리 | NFR-3 |
| Session Service | `app/session/service.py` | 계약 B(시작/조회), 종료+이력이관(US-A6), 대시보드(US-A2), 이력(US-A7) | 계약 B/C/D |
| Order History Provider | `app/session/provider.py` | `OrderHistoryProvider` 프로토콜 + 레지스트리 + NoOp | 계약 C(소비) |
| Session Schemas | `app/session/schemas.py` | 세션/대시보드/이력 응답 Pydantic | - |
| Session Router | `app/session/router.py` | `/sessions/{dashboard,close,history}` (require_admin) | NFR-3 |
| Realtime Broker | `app/realtime/broker.py` | `InMemoryBroker`(RealtimePublisher 구현), 매장별 구독자·asyncio.Queue·subscribe/unsubscribe·threadsafe publish | **NFR-1**, 계약 D |
| Realtime Router | `app/realtime/router.py` | SSE `/realtime/admin/stream`·`/realtime/table/stream`(query 토큰) | NFR-1/3 |
| Security(공유·additive) | `app/common/security.py` | `verify_token(token)->StoreContext` 추가(SSE query 인증) | 계약 E 확장, BR-U4-11 |
| App 통합(additive) | `app/main.py` | `register_publisher(InMemoryBroker())`, `include_router(session/realtime)` | - |
| DB 등록(additive) | `app/common/database.py` | `init_db`에 session 모델 import | NFR-4 |
| Admin 화면 | `frontend-admin/src/views/{DashboardView,HistoryView}.vue`, `api/session.js` | US-A2/A6/A7, SSE 소비(`api/sse.js` 재사용) | NFR-1/6 |
| Customer 실시간 | `frontend-customer/src/api/sse.js`(신규), 실시간 스토어/컴포저블 | US-C6, table 스트림 소비 | NFR-1 |

## 공유 파일 편집(머지 안전)
- `main.py`·`database.py`·`router/index.js`는 U1~U4 공유 → **additive만**(다른 유닛 슬롯 미변경).
- `common/security.py` `verify_token` 추가는 유일한 공유 로직 편집 → 팀 조율 대상(계약 E 확장).

## 인프라 컴포넌트
- 큐/캐시/서킷브레이커 등 외부 인프라 **N/A** — 로컬 단일 프로세스 인메모리 브로커로 NFR-1 충족.
