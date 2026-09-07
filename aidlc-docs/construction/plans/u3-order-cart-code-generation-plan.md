# U3 Order (+ Cart) — Code Generation Plan (SINGLE SOURCE OF TRUTH)

**유닛**: U3 Order+Cart · **담당**: 최지영 · **프로젝트**: Greenfield 모놀리식(코드=워크스페이스 루트, 문서=aidlc-docs/)

이 문서는 U3 코드 생성의 **단일 진실 원천**이다. Part 2 생성은 이 계획의 단계 순서를 그대로 따른다.

## 유닛 컨텍스트
- **구현 스토리**: US-C3(장바구니), US-C4(주문 생성·확정), US-C5(현재 세션 내역), US-A3(주문 상세·상태변경), US-A5(주문 삭제). US-C6(고객 실시간, Could)은 백엔드 이벤트 발행까지만 준비(프론트 SSE 구독은 선택).
- **소유 엔티티**: `Order`, `OrderItem`.
- **의존 계약**: A(Menu 조회·U2)·B(Session·U4)는 `Protocol`+모킹으로 병렬 개발. D(Realtime publish)는 U0 제공 사용. C(이력 이관)는 U3가 **제공**.
- **서비스 경계**: 주문 도메인(생성 오케스트레이션·조회·상태·삭제·대시보드 스냅샷). 장바구니는 클라이언트 전용.
- **코드 위치**: 백엔드 `backend/app/order/`, 테스트 `backend/tests/order/`, 프론트 `frontend-customer/src/{stores,views/order,api}`, `frontend-admin/src/{views/order,api}`.

---

## 생성 단계 (순차)

### Step 1 — 프로젝트 구조 셋업 (backend)
- [x] `backend/app/order/__init__.py` 확인/생성, `backend/tests/order/__init__.py` 생성.

### Step 2 — Repository Layer 생성 (US-C4/C5/A3/A5)
- [x] `backend/app/order/models.py` — `Order`, `OrderItem` SQLAlchemy 모델(엔티티 문서대로: store 격리, 스냅샷, status, total, archived, is_deleted, deleted_at, unique(store_id, order_no), 인덱스, relationship+cascade).
- [x] `backend/app/order/repository.py` — `OrderRepository(BaseRepository[Order])`: `next_order_no`, `list_active_by_session`, `list_active_by_store`, `sum_active_total`, `get_with_items`.

### Step 3 — Repository Layer 단위 테스트
- [x] `backend/tests/order/test_repository.py` — 채번 단조 증가·store 격리·활성 필터(archived/is_deleted) 검증.

### Step 4 — Business Logic Layer 생성 (US-C4/C5/A3/A5, 계약 A/B/C/D)
- [x] `backend/app/order/gateways.py` — `MenuLookup`(계약 A)·`SessionGateway`(계약 B) `Protocol` + 테스트/독립실행용 스텁(`StubMenuLookup`, `StubSessionGateway`).
- [x] `backend/app/order/schemas.py` — `OrderItemIn`·`OrderInput`·`OrderItemOut`·`OrderOut`·`OrderDetailOut`·`TableTotals`·`TableCard`·`OrderStatus`(enum).
- [x] `backend/app/order/service.py` — `OrderService`: create_order(검증→계약A→계약B→저장→계약D), list_current_session_orders, get_order, update_order_status, delete_order(소프트+총액재계산), get_dashboard_snapshot, collect_active_session_orders/mark_orders_archived(계약 C). BR-U3-1~14 반영.

### Step 5 — Business Logic 단위 테스트
- [x] `backend/tests/order/test_service.py` — 주문 생성(모킹 A/B)·빈 장바구니 거부·메뉴검증 실패·총액 계산·상태 자유전이·소프트 삭제 후 총액 재계산·현재 세션 격리·계약 C 멱등.

### Step 6 — API Layer 생성 (US-C4/C5/A3/A5)
- [x] `backend/app/order/router.py` — 엔드포인트: `POST /orders`(table), `GET /orders/current`(table), `GET /orders/{id}`(table/admin), `PATCH /orders/{id}/status`(admin), `DELETE /orders/{id}`(admin), `GET /orders/dashboard`(admin). 역할 가드·의존성 주입(service, gateways).

### Step 7 — API Layer 단위 테스트
- [x] `backend/tests/order/test_router.py` — TestClient + 토큰 검증기/게이트웨이 오버라이드로 201/422/403/404 경로 검증.

### Step 8 — U0 통합 배선 (모놀리식 조립)
- [x] `backend/app/main.py` — `include_router(order_router)` (기존 슬롯 채움, in-place 수정).
- [x] `backend/app/common/database.py` `init_db` — `order.models` import 등록(테이블 생성).
- [x] 통합 시 실제 U2/U4 주입을 위한 gateway provider 함수 자리 마련(기본은 스텁, 주석으로 교체 지점 표기).

### Step 9 — Frontend: Customer (US-C3/C4/C5)
- [x] `frontend-customer/src/stores/cart.js` — Pinia cartStore(localStorage 영속, add/inc/dec/remove/clear, total/count).
- [x] `frontend-customer/src/api/orderApi.js` — create/listCurrent/get.
- [x] `frontend-customer/src/views/order/CartView.vue`, `OrderConfirmView.vue`, `CurrentOrdersView.vue` (data-testid 부여).
- [x] `frontend-customer/src/router/index.js` — /cart, /order/confirm, /orders 라우트(테이블 가드) 슬롯 채움.

### Step 10 — Frontend: Admin (US-A3/A5)
- [x] `frontend-admin/src/api/orderAdminApi.js` — get/updateStatus/delete/dashboardSnapshot.
- [x] `frontend-admin/src/views/order/OrderDetailModal.vue`, `DeleteOrderAction.vue` (data-testid 부여).
- [x] `frontend-admin/src/router/index.js` — 주문 상세/관리 진입 슬롯(필요 시).

### Step 11 — 문서화 (code summary)
- [x] `aidlc-docs/construction/u3-order-cart/code/code-summary.md` — 생성 파일 목록·계약·NFR·통합 지점·검증 결과.

### Step 12 — 검증 (Build & Test 전 로컬 확인)
- [x] `pytest backend/tests/order` 통과.
- [x] 앱 부팅 + `/openapi.json`에 order 엔드포인트 노출 확인.
- [x] `npm run build`(frontend-customer / frontend-admin) 성공.

> 배포 아티팩트: 로컬 데모 — 별도 컨테이너/IaC 없음(U0 실행 방식 재사용). 해당 단계 N/A.

## 스토리 추적
- [x] US-C3 장바구니 → Step 9 (cartStore, CartView)
- [x] US-C4 주문 생성·확정 → Step 2,4,6,9
- [x] US-C5 현재 세션 내역 → Step 4,6,9
- [x] US-A3 주문 상세·상태변경 → Step 4,6,10
- [x] US-A5 주문 삭제 → Step 4,6,10
- [x] US-C6 고객 실시간(Could) → 백엔드 이벤트 발행(Step 4)까지; 프론트 SSE 구독 선택

## 확장 준수
- Security / Resiliency / Property-Based Testing: Disabled → N/A. 표준 pytest 사용.
