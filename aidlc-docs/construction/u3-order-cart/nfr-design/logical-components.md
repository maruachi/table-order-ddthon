# U3 논리 컴포넌트 (Logical Components) — Order (+ Cart)

U3가 추가하는 논리 컴포넌트와 NFR 매핑. 코드 위치는 `backend/app/order/`(3계층) + 프론트 화면.

## 백엔드 (`backend/app/order/`)

| 논리 컴포넌트 | 파일(예정) | 역할 | 관련 NFR / 계약 |
|---|---|---|---|
| Models | `order/models.py` | `Order`·`OrderItem` 엔티티(store 격리, 스냅샷, 소프트 삭제, archived) | NFR-3/4 |
| Schemas | `order/schemas.py` | `OrderInput`·`OrderItemIn`·`OrderOut`·`OrderDetailOut`·`TableTotals`·`TableCard`·상태 enum | - |
| Repository | `order/repository.py` | `OrderRepository(BaseRepository[Order])` + 채번·세션조회·집계·활성필터 | NFR-3, 동시성 |
| Service | `order/service.py` | 주문 오케스트레이션·상태변경·삭제·대시보드 스냅샷·계약 C 제공 | NFR-1, BR-U3-* |
| Router | `order/router.py` | REST 엔드포인트 + 역할 가드(require_table/admin) | NFR-2/3 |
| Gateways(계약) | `order/gateways.py` | `MenuLookup`(계약 A)·`SessionGateway`(계약 B) Protocol + 통합 시 실제 주입 | 계약 A/B, 병렬 |
| Contract C 제공 | `service.py` 내 | `collect_active_session_orders`·`mark_orders_archived` (U4 close_session 호출) | 계약 C |
| Realtime 사용 | (U0) `common/realtime.publish` + `common/events` | 이벤트 발행 | NFR-1, 계약 D |

**엔드포인트(예정)**
| 메서드/경로 | 서비스 | 권한 |
|---|---|---|
| `POST /orders` | create_order | table |
| `GET /orders/current` | list_current_session_orders | table |
| `GET /orders/{id}` | get_order | table(자기)/admin |
| `PATCH /orders/{id}/status` | update_order_status | admin |
| `DELETE /orders/{id}` | delete_order | admin |
| `GET /orders/dashboard` | get_dashboard_snapshot | admin |

## 프론트엔드

| 컴포넌트 | 위치 | 역할 | NFR |
|---|---|---|---|
| cartStore | `frontend-customer/src/stores/cart.js` | 장바구니 로컬 영속(Pinia+localStorage) | NFR-5 |
| Cart/OrderConfirm/CurrentOrders views | `frontend-customer/src/views/order/` | 장바구니·확정·현재 세션 내역 | NFR-6 |
| orderApi / orderAdminApi | `frontend-*/src/api/` | 주문 API 클라이언트 | - |
| OrderDetailModal / DeleteOrderAction | `frontend-admin/src/views/order/` | 상세·상태변경·삭제 | NFR-6 |

## 인프라 컴포넌트
- **없음(N/A)**: 큐/캐시/서킷브레이커/외부 브로커 불필요. 실시간은 U4 인메모리 pub-sub(계약 D)로 충분. 로컬 단일 SQLite.

## 통합 지점 (U0 슬롯 채우기)
- `app/main.py` create_app: `include_router(order_router)`.
- `app/database.py init_db`: `order.models` import 등록.
- 프론트 `router/index.js`: order 라우트 슬롯.
- 통합 단계: `MenuLookup`←U2 실제 구현, `SessionGateway`←U4 실제 구현으로 모킹 교체. U4 `close_session`이 계약 C 메서드 호출.
