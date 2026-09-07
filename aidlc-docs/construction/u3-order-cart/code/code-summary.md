# U3 Order (+ Cart) — Code Generation Summary

**유닛**: U3 Order+Cart · **담당**: 최지영 · **프로젝트**: Greenfield 모놀리식
**생성일**: 2026-09-07 · **계획 원천**: `aidlc-docs/construction/plans/u3-order-cart-code-generation-plan.md`

---

## 1. 구현 스토리
| 스토리 | 설명 | 상태 |
|--------|------|------|
| US-C3 | 장바구니(담기/수량/삭제/총액) | ✅ 완료 |
| US-C4 | 주문 생성·확정 | ✅ 완료 |
| US-C5 | 현재 세션 주문 내역 | ✅ 완료 |
| US-A3 | 주문 상세·조리상태 변경 | ✅ 완료 (컴포넌트, U4 대시보드에서 진입) |
| US-A5 | 주문 삭제(확인 팝업·총액 재계산) | ✅ 완료 (컴포넌트, U4 대시보드에서 진입) |
| US-C6 | 고객 실시간(Could) | ⚙️ 백엔드 이벤트 발행까지 준비, 프론트 SSE 구독 미구현(선택) |

## 2. 생성 파일 목록

### 백엔드 (`backend/app/order/`)
| 파일 | 역할 |
|------|------|
| `models.py` | `Order`, `OrderItem` SQLAlchemy 2.0 모델. store 격리, 가격 스냅샷, status/total/archived/is_deleted/deleted_at, `UniqueConstraint(store_id, order_no)`, 인덱스, cascade relationship |
| `repository.py` | `OrderRepository(BaseRepository[Order])`: `next_order_no`, `get_with_items`, `list_active_by_session`, `count_active_by_session`, `list_active_by_store`, `list_active_session_orders`, `sum_active_total_for_table`, `soft_delete`, `mark_archived`(멱등), `_active_scope` |
| `gateways.py` | 계약 A `MenuLookup` / 계약 B `SessionGateway` `Protocol` + `StubMenuLookup`(catalog authoritative)·`StubSessionGateway`, `MenuItemInfo` |
| `schemas.py` | `OrderStatus`(enum), `OrderItemIn`(qty>0)·`OrderInput`(items min_length=1)·`OrderItemOut`·`OrderOut`·`OrderDetailOut`·`StatusUpdateIn`·`TableTotals`·`TableCard` |
| `service.py` | `OrderService`: `create_order`(검증→계약A→계약B→저장→계약D publish), `_persist_order`(order_no 재시도), `list_current_session_orders`, `get_order`, `update_order_status`(자유 전이), `delete_order`(소프트+총액 재계산), `get_dashboard_snapshot`, `collect_active_session_orders`/`mark_orders_archived`(계약 C 제공) |
| `router.py` | `APIRouter(prefix="/orders")`: POST ``·GET `/current`·GET `/dashboard`·PATCH `/{id}/status`·DELETE `/{id}`·GET `/{id}`. 역할 가드, gateway provider(`set_gateways()` 통합 훅) |

### 백엔드 통합 (in-place)
- `backend/app/main.py` — `include_router(order_router)`
- `backend/app/common/database.py` — `init_db`에 `order.models` 등록

### 백엔드 테스트 (`backend/tests/order/`)
- `conftest.py`(2개 스토어 시드), `test_repository.py`(5), `test_service.py`(8), `test_router.py`(4) → **17 passed**

### 프론트엔드 고객 (`frontend-customer/src/`)
- `stores/cart.js` — Pinia cartStore(localStorage 영속, 토큰 네임스페이스)
- `api/orderApi.js` — create/listCurrent/get
- `views/order/CartView.vue`, `OrderConfirmView.vue`(5초 후 /menu 리다이렉트), `CurrentOrdersView.vue`
- `router/index.js` — `/cart`, `/order/confirm`, `/orders` 라우트(requiresAuth)

### 프론트엔드 관리자 (`frontend-admin/src/`)
- `api/orderAdminApi.js` — get/updateStatus/delete/dashboardSnapshot
- `views/order/OrderDetailModal.vue`(상태 변경), `DeleteOrderAction.vue`(삭제 확인 팝업)

## 3. 계약 (Contract) 구현
| 계약 | 방향 | 구현 |
|------|------|------|
| A (Menu 조회, U2) | U3 **소비** | `MenuLookup` Protocol + `StubMenuLookup`. 통합 시 `set_gateways()`로 U2 구현 주입 |
| B (Session, U4) | U3 **소비** | `SessionGateway` Protocol + `StubSessionGateway`. 통합 시 U4 구현 주입 |
| C (이력 이관) | U3 **제공** | `collect_active_session_orders` + `mark_orders_archived`(멱등) |
| D (Realtime publish) | U3 **소비** | `app.common.events`/`realtime` 사용, best-effort 발행 |

## 4. NFR 반영
- **NFR-1 실시간(<2s)**: 주문 생성/상태변경 시 이벤트 best-effort 발행(SSE 채널). 발행 실패가 트랜잭션을 막지 않음.
- **NFR-3 멀티테넌시**: 모든 쿼리·유니크 제약이 `store_id` 스코프. 리포지토리 `_active_scope`로 강제.
- **가격 스냅샷**: 주문 시점 `menu_name`/`unit_price`를 OrderItem에 고정 → 메뉴 변경에 불변.
- **소프트 삭제**: `is_deleted`/`deleted_at`, 활성 필터에서 제외, 삭제 후 테이블 총액 재계산.

## 5. 통합 지점 (U0/U2/U4)
- `router.get_menu_lookup`/`get_session_gateway`는 기본 스텁 반환 → 통합 시 `set_gateways(menu_lookup=..., session_gateway=...)` 호출로 실제 U2/U4 주입.
- `OrderDetailModal.vue`/`DeleteOrderAction.vue`는 라우트 미연결 상태(현재 라우트 그래프 밖). U4 대시보드가 주문 카드 클릭 시 모달을 열도록 연결 예정.
- 계약 C(`collect_active_session_orders`/`mark_orders_archived`)는 U4 세션 종료 흐름이 호출.

## 6. 검증 결과
| 항목 | 결과 |
|------|------|
| `pytest backend/tests/order` | ✅ 17 passed (0.pydeps 격리 환경, SQLAlchemy 2.0.30) |
| 앱 부팅 + `/openapi.json` order 엔드포인트 | ✅ 6개 엔드포인트 노출 확인 |
| `npm run build` frontend-customer | ✅ built (97 modules, order 뷰 청크 포함) |
| `npm run build` frontend-admin | ✅ built (32 modules; 관리자 order 컴포넌트는 라우트 미연결이라 번들 미포함 — U4 연결 후 컴파일 대상) |

## 7. 확장 준수
- Security / Resiliency / Property-Based Testing: Disabled → N/A. 표준 pytest 사용.
