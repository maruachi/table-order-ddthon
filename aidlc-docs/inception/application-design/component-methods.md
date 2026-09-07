# 컴포넌트 메서드 시그니처 (Component Methods)

각 컴포넌트의 **서비스 계층** 메서드 시그니처(고수준 목적 + 입/출력)를 정의한다. 시그니처는 언어 중립적 의사표기이며, 구현 세부(예외/트랜잭션 경계)와 **상세 비즈니스 규칙은 Functional Design(유닛별, Construction)** 에서 확정한다.

**공통 규약** (Q5-A): 모든 도메인 서비스 메서드는 첫 인자로 인증 컨텍스트에서 주입된 `store_id`를 받는다. 아래에서는 `ctx: StoreContext`(store_id, 선택적 table_id, 주체 role 포함)로 표기한다.

DTO는 요약 표기이며 상세 필드는 Functional Design에서 확정.

---

## 1. Platform / Common

| 메서드 | 목적 | 입력 | 출력 |
|---|---|---|---|
| `get_current_store_context(request) -> StoreContext` | 토큰 검증 후 요청 컨텍스트 생성(FastAPI 의존성) | Request(Authorization 헤더) | `StoreContext{store_id, table_id?, role}` |
| `Store.get(store_id) -> Store` | 매장 조회 | store_id | Store |
| `Table.list(ctx) -> list[Table]` | 매장 테이블 목록 | ctx | Table[] |
| `Table.get(ctx, table_id) -> Table` | 테이블 단건 조회 | ctx, table_id | Table |

> `BaseRepository[T]`: `get/list/add/update/delete` 제네릭 CRUD, 모든 쿼리에 `store_id` 조건 강제.

## 2. Auth

| 메서드 | 목적 | 입력 | 출력 |
|---|---|---|---|
| `admin_login(store_id, username, password) -> AdminToken` | 관리자 로그인·JWT 발급(16h), bcrypt 검증, 시도 제한(US-A1) | store_id, username, password | `AdminToken{access_token, expires_at}` |
| `verify_admin_token(token) -> StoreContext` | 관리자 JWT 검증 | token | StoreContext(role=admin) |
| `setup_table(ctx, table_no, password) -> Table` | 테이블 초기 설정(번호/비밀번호 해싱, 자동 로그인 활성)(US-A4) | ctx(admin), table_no, password | Table |
| `table_login(store_id, table_no, password) -> TableToken` | 테이블 태블릿 로그인·테이블 세션 토큰 발급(US-C1, Q6-A) | store_id, table_no, password | `TableToken{token}` |
| `verify_table_token(token) -> StoreContext` | 테이블 토큰 검증 | token | StoreContext(role=table, table_id) |

## 3. Menu

| 메서드 | 목적 | 입력 | 출력 |
|---|---|---|---|
| `list_menus_for_customer(ctx) -> list[CategoryWithMenus]` | 고객용 메뉴 조회(카테고리별·노출 순서)(US-C2) | ctx | CategoryWithMenus[] |
| `list_categories(ctx) -> list[Category]` | 카테고리 목록 | ctx | Category[] |
| `create_menu(ctx, MenuInput) -> Menu` | 메뉴 등록(검증: 필수/가격 범위)(US-A8) | ctx, MenuInput{name, price, desc, category_id, image_url} | Menu |
| `update_menu(ctx, menu_id, MenuInput) -> Menu` | 메뉴 수정 | ctx, menu_id, MenuInput | Menu |
| `delete_menu(ctx, menu_id) -> None` | 메뉴 삭제 | ctx, menu_id | - |
| `reorder_menus(ctx, category_id, ordered_ids) -> None` | 노출 순서 조정 | ctx, category_id, ordered_ids[] | - |

## 4. Order

| 메서드 | 목적 | 입력 | 출력 |
|---|---|---|---|
| `create_order(ctx, OrderInput) -> Order` | 주문 생성: 메뉴/가격 검증, 총액 계산, **첫 주문 시 TableSession 시작**, 저장 후 Realtime 이벤트 발행(US-C4) | ctx(table), OrderInput{items:[{menu_id, qty}]} | `Order{order_no, total, status, session_id, created_at}` |
| `list_current_session_orders(ctx) -> list[Order]` | 현재 세션 주문만 시간순 조회(US-C5) | ctx(table), pagination | Order[] |
| `get_order(ctx, order_id) -> OrderDetail` | 주문 상세(메뉴/수량/단가/총액)(US-A3) | ctx, order_id | OrderDetail |
| `update_order_status(ctx, order_id, status) -> Order` | 상태 변경(대기중/준비중/완료), 이벤트 발행(US-A3) | ctx(admin), order_id, status | Order |
| `delete_order(ctx, order_id) -> TableTotals` | 주문 삭제(직권), 총액 재계산, 이벤트 발행(US-A5) | ctx(admin), order_id | `TableTotals{table_id, total}` |
| `get_dashboard_snapshot(ctx) -> list[TableCard]` | 대시보드 초기 스냅샷(테이블별 총액·최신 주문 n)(US-A2) | ctx(admin), table_filter? | TableCard[] |

## 5. TableSession

| 메서드 | 목적 | 입력 | 출력 |
|---|---|---|---|
| `start_or_get_active_session(ctx, table_id) -> TableSession` | 활성 세션 조회, 없으면 새 세션 시작(주문 생성이 호출, Q8-A) | ctx, table_id | TableSession |
| `get_active_session(ctx, table_id) -> TableSession?` | 현재 활성 세션 조회 | ctx, table_id | TableSession or None |
| `close_session(ctx, table_id) -> ClosedSessionSummary` | 이용 완료: 세션 주문을 완료 시각과 함께 이력 이관, 현재 주문/총액 리셋, 이벤트 발행(US-A6) | ctx(admin), table_id | ClosedSessionSummary |
| `list_history(ctx, table_id, date_filter?) -> list[OrderHistory]` | 과거 이력(시간 역순, 날짜 필터)(US-A7) | ctx(admin), table_id, date_filter? | OrderHistory[] |

## 6. Realtime

| 메서드 | 목적 | 입력 | 출력 |
|---|---|---|---|
| `publish(store_id, event)` | 매장 브로커에 이벤트 발행(Order/TableSession이 호출) | store_id, `Event{type, payload}` | - |
| `subscribe_admin(ctx) -> SSEStream` | 관리자 대시보드 SSE 구독(US-A2) | ctx(admin) | SSE 스트림 |
| `subscribe_customer(ctx) -> SSEStream` | 고객 주문 상태 SSE 구독(US-C6, 선택) | ctx(table) | SSE 스트림 |

> 이벤트 타입(초안): `order.created`, `order.status_changed`, `order.deleted`, `session.closed`. 상세 페이로드/필터링 규칙은 Functional Design에서 확정.

---

## 프론트엔드(참고, 상위 상호작용)
- **Customer SPA**: `authStore`(테이블 토큰), `cartStore`(로컬 영속), `menuApi`, `orderApi`, `sse(customer)`.
- **Admin SPA**: `authStore`(JWT 16h), `dashboardStore`(SSE 구독+스냅샷 병합), `menuAdminApi`, `orderAdminApi`, `sessionApi`.
> 프론트 상태/컴포넌트 상세는 각 유닛 Functional Design/Code Generation에서 정의.
