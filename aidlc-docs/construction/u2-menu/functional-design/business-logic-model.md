# U2 Menu 비즈니스 로직 모델 (Business Logic Model)

MenuService/CategoryRepository/MenuRepository의 로직, 계약 A(`get_menu_items`), 고객 조회 정렬·그룹핑, CRUD·재정렬 알고리즘을 정의한다. 3계층(Router → Service → Repository), Repository는 U0 `BaseRepository` 상속(store 격리 자동).

---

## 1. 계층 구성

```
[Customer SPA] GET /api/menu ─────────┐
[Admin SPA]    /api/admin/categories  ├─▶ [MenuRouter] ─(StoreContext 주입, 계약 E)─▶ [MenuService] ─▶ [Category/MenuRepository(BaseRepository)] ─▶ SQLite
               /api/admin/menus ──────┘
[U3 OrderService] ── get_menu_items(store_id, ids) ──▶ [MenuService] (동일 프로세스 직접 호출, 계약 A)
```

- 라우터는 `Depends(get_current_store_context)`로 `ctx`를 주입받아 서비스에 전달. `store_id`는 항상 `ctx.store_id`.
- 관리자 엔드포인트는 `require_admin`, 고객 조회는 `require_table` 가드(BR-U0-6).

## 2. 리포지토리

`CategoryRepository(BaseRepository[Category])`, `MenuRepository(BaseRepository[Menu])` — U0 `BaseRepository`의 store 스코프 CRUD 상속. 추가 조회:
- `CategoryRepository.list_ordered(store_id) -> [Category]` : `display_order, id` 오름차순.
- `MenuRepository.list_active(store_id, category_id?) -> [Menu]` : `is_deleted=false` 필터, `(category_id,) display_order, id` 정렬.
- `MenuRepository.list_by_ids(store_id, ids) -> [Menu]` : `id IN ids AND is_deleted=false`(계약 A용).
- `MenuRepository.max_order(store_id, category_id) -> int` : 신규 메뉴 append 시 순서 계산.

## 3. 서비스 메서드

### 3.1 카테고리 (관리자, `require_admin`) — Q2:A
| 메서드 | 로직 |
|---|---|
| `list_categories(ctx) -> [Category]` | `display_order` 순 조회 |
| `create_category(ctx, name, display_order?) -> Category` | name 검증·중복 검사(BR-U2-9), display_order 미지정 시 맨 뒤 |
| `update_category(ctx, category_id, name) -> Category` | 존재 확인(없으면 404), name 검증·중복 검사 |
| `delete_category(ctx, category_id) -> None` | 활성 메뉴 존재 시 `ValidationError`(BR-U2-8), 아니면 하드 삭제 |
| `reorder_categories(ctx, ordered_ids) -> None` | ordered_ids 유효성(해당 매장 전체 카테고리 집합) 검증 후 순번 재배정(BR-U2-7) |

### 3.2 메뉴 (관리자, `require_admin`) — US-A8
| 메서드 | 로직 |
|---|---|
| `list_menus_admin(ctx, category_id?) -> [Menu]` | 활성(미삭제) 메뉴, 품절 포함, 순서대로. 관리 화면용 |
| `create_menu(ctx, MenuInput) -> Menu` | 입력 검증(BR-U2-1~5), category_id 소속 확인, display_order=맨 뒤, available=true, is_deleted=false |
| `update_menu(ctx, menu_id, MenuInput) -> Menu` | 존재·미삭제 확인(없으면 404), 검증 후 갱신. category 변경 시 새 카테고리 맨 뒤로 |
| `delete_menu(ctx, menu_id) -> None` | **소프트 삭제**: `is_deleted=true`(Q3:B) |
| `set_menu_availability(ctx, menu_id, available) -> Menu` | 품절 토글(Q4:A) |
| `reorder_menus(ctx, category_id, ordered_ids) -> None` | ordered_ids가 해당 카테고리 활성 메뉴 전체 집합인지 검증 후 순번 재배정(BR-U2-7) |

### 3.3 고객 조회 (`require_table`) — US-C2, Q9:A
`list_menus_for_customer(ctx) -> [CategoryWithMenus]`
1. `CategoryRepository.list_ordered(store_id)` 로 카테고리를 순서대로 조회.
2. 각 카테고리별 활성 메뉴(`is_deleted=false`)를 `display_order` 순으로 조회. **품절(available=false)도 포함**(프론트가 품절 배지 표시).
3. 그룹 구조로 반환:
```jsonc
[
  { "category_id": 1, "name": "커피", "display_order": 0,
    "menus": [
      { "id": 10, "name": "아메리카노", "price": 4500, "description": "...",
        "image_url": "https://...", "available": true, "display_order": 0 },
      ...
    ] },
  ...
]
```
- 빈 카테고리(메뉴 0개)도 포함할지: **포함하되 프론트에서 숨김 판단** 가능(빈 배열 반환).

### 3.4 계약 A — `get_menu_items(store_id, menu_ids) -> [MenuItemDTO]` (U3가 직접 호출)
- **호출 방식**(Q8:A): 동일 프로세스 내 `MenuService` 메서드 직접 호출(HTTP 아님). `store_id`는 U3가 자신의 `ctx.store_id`를 전달.
- **반환**(Clarification:A):
  - `MenuRepository.list_by_ids(store_id, menu_ids)` — **미존재·소프트삭제 항목은 결과에서 제외**.
  - 존재하는 항목은 **실제 `available` 플래그를 실어 반환**:
    ```jsonc
    [ { "id": 10, "name": "아메리카노", "price": 4500, "available": true },
      { "id": 12, "name": "딸기라떼", "price": 5500, "available": false } ]  // 품절도 포함
    ```
- **U3의 판단 책임**(문서화된 계약): U3는 (a) 요청 `menu_ids` 대비 **반환 누락 = 무효(삭제/미존재)** → 주문 거부, (b) 반환 항목 중 `available=false` = 품절 → 주문 거부. U2는 상태 정보만 제공, 주문 성립 판정은 U3.
- **단가 신뢰 경계**: 주문 금액 계산의 단가는 **계약 A의 `price`(서버 값)** 를 사용. 클라이언트가 보낸 가격은 신뢰하지 않는다.

## 4. 순서(display_order) 재배정 알고리즘 (Q5:B)
`reorder(scope, ordered_ids)`:
1. scope의 활성 대상 전체 id 집합 `S`를 조회.
2. `set(ordered_ids) == S` 검증 — 불일치(누락/외부 id/중복) 시 `ValidationError`(BR-U2-7).
3. `ordered_ids` 순서대로 `display_order = 0,1,2,...` 재할당, flush.
- 카테고리 순서: scope=매장 전체 카테고리. 메뉴 순서: scope=`category_id`의 활성 메뉴.

## 5. 트랜잭션·이벤트
- 각 쓰기 메서드는 단일 DB 트랜잭션(라우터/세션 경계). 재정렬은 다건 update를 한 트랜잭션에서 flush.
- **U2는 Realtime 이벤트를 발행하지 않는다**(계약 D 발행자는 U3/U4). 메뉴 변경은 고객이 다음 조회 시 반영(실시간 push 대상 아님).

## 6. REST 엔드포인트 매핑
| 메서드 | 엔드포인트 | 가드 |
|---|---|---|
| list_menus_for_customer | `GET /api/menu` | require_table |
| list_categories | `GET /api/admin/categories` | require_admin |
| create_category | `POST /api/admin/categories` | require_admin |
| update_category | `PATCH /api/admin/categories/{id}` | require_admin |
| delete_category | `DELETE /api/admin/categories/{id}` | require_admin |
| reorder_categories | `POST /api/admin/categories/reorder` | require_admin |
| list_menus_admin | `GET /api/admin/menus?category_id=` | require_admin |
| create_menu | `POST /api/admin/menus` | require_admin |
| update_menu | `PATCH /api/admin/menus/{id}` | require_admin |
| delete_menu | `DELETE /api/admin/menus/{id}` | require_admin |
| set_menu_availability | `PATCH /api/admin/menus/{id}/availability` | require_admin |
| reorder_menus | `POST /api/admin/menus/reorder` | require_admin |
| get_menu_items (계약 A) | (HTTP 아님 — 인프로세스 호출) | 호출자 U3의 ctx |
