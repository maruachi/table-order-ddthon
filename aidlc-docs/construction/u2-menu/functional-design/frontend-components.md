# U2 Menu 프론트엔드 컴포넌트 (Frontend Components)

U0 앱 셸(라우팅·레이아웃·API 클라이언트·토큰 유틸) 위에 U2 화면을 **도메인 수직 귀속**(Q2-A, Units Generation)으로 추가. 고객 SPA(US-C2)·관리자 SPA(US-A8) 양쪽. 터치 친화 UI(NFR-6: 버튼 최소 44×44px, 카드 레이아웃, 명확한 시각 계층).

---

## A. 고객 SPA (`frontend-customer`) — US-C2 메뉴 조회·탐색

### 라우트
- `/menu` (기본 화면, `require_table` 가드) — `views/menu/MenuView.vue`.

### 컴포넌트 계층
```
MenuView (페이지, 기본 화면)
├─ CategoryNav        // 카테고리 탭/앵커, 빠른 이동
├─ CategorySection[]  // 카테고리별 섹션
│   └─ MenuCard[]     // 카드형 메뉴(이미지·이름·가격·품절 배지)
└─ MenuDetailModal    // 메뉴 상세(이름·가격·설명·이미지)
```

| 컴포넌트 | Props | 상태/이벤트 |
|---|---|---|
| `MenuView` | - | `menusByCategory`, `activeCategoryId`, `loading`, `error`, `selectedMenu` |
| `CategoryNav` | `categories`, `activeCategoryId` | emit `select(categoryId)` → 해당 섹션 스크롤 |
| `CategorySection` | `category`, `menus` | - |
| `MenuCard` | `menu` | emit `open(menu)`; `available=false`면 품절 배지 + 클릭 시 상세만(주문 X, 주문은 U3) |
| `MenuDetailModal` | `menu`, `open` | emit `close` |

### 데이터 흐름 / API
- 진입 시 `GET /api/menu` → `list_menus_for_customer` 그룹 구조(Q9:A) 수신 → `menusByCategory`에 저장.
- 품절(`available=false`) 메뉴는 표시하되 시각적으로 구분(흐림 + "품절" 배지). **장바구니 담기/주문 트리거는 U3(Order) 소유** — U2는 조회·표시까지.
- 이미지 로드 실패 시 플레이스홀더.
- 상태 관리: 화면 로컬 상태(간단). 필요 시 `stores/menu.js`(Pinia) 도입 가능하나 MVP는 뷰 로컬로 충분.

## B. 관리자 SPA (`frontend-admin`) — US-A8 메뉴 관리

### 라우트
- `/menus` (`require_admin`) — `views/menu/MenuManageView.vue`.

### 컴포넌트 계층
```
MenuManageView (페이지)
├─ CategoryPanel
│   ├─ CategoryList        // 목록 + 드래그 재정렬(reorder_categories)
│   ├─ CategoryFormModal   // 생성/수정(name)
│   └─ (삭제: 확인 모달, 활성 메뉴 있으면 차단 안내)
└─ MenuPanel (선택된 카테고리 기준)
    ├─ MenuList            // 메뉴 목록 + 드래그 재정렬(reorder_menus) + 품절 토글
    ├─ MenuFormModal       // 생성/수정 폼
    └─ ConfirmDialog       // 삭제 확인(소프트 삭제)
```

| 컴포넌트 | Props | 상태/이벤트 |
|---|---|---|
| `MenuManageView` | - | `categories`, `selectedCategoryId`, `menus`, `editing`, `formErrors`, `loading` |
| `CategoryList` | `categories`, `selectedId` | emit `select`, `reorder(orderedIds)`, `edit`, `delete` |
| `CategoryFormModal` | `model`(신규/기존) | emit `submit(name)`, `cancel` |
| `MenuList` | `menus` | emit `reorder(orderedIds)`, `edit`, `delete`, `toggleAvailable(id, value)` |
| `MenuFormModal` | `model`, `categories` | emit `submit(MenuInput)`, `cancel` |
| `ConfirmDialog` | `message` | emit `confirm`, `cancel` |

### 폼 검증 (클라이언트, 서버 BR-U2-1~5와 정합)
- `name`: 필수, 공백 불가.
- `price`: 필수, 정수, 0 이상(Q6:B). 숫자 외 입력 차단.
- `category`: 필수, 셀렉트에서 선택(기존 카테고리).
- `description`: 선택.
- `image_url`: 선택, 입력 시 `http(s)://` 형식(Q7:B). 서버 422도 폼 오류로 표시.
- 제출 실패(422) 시 필드별 오류 메시지 매핑, 입력값 유지.

### API 연동 (`api/menuAdmin.js`)
| 액션 | 호출 |
|---|---|
| 카테고리 목록 | `GET /api/admin/categories` |
| 카테고리 생성/수정/삭제 | `POST` / `PATCH /{id}` / `DELETE /{id}` |
| 카테고리 재정렬 | `POST /api/admin/categories/reorder` |
| 메뉴 목록 | `GET /api/admin/menus?category_id=` |
| 메뉴 생성/수정/삭제 | `POST` / `PATCH /{id}` / `DELETE /{id}` |
| 품절 토글 | `PATCH /api/admin/menus/{id}/availability` |
| 메뉴 재정렬 | `POST /api/admin/menus/reorder` |

- 모든 요청은 U0 API 클라이언트가 JWT 주입·401 처리. 재정렬은 드래그 종료 시 전체 `ordered_ids`를 전송(BR-U2-7).
- 삭제는 소프트 삭제(BR-U2-11)지만 관리 화면에서는 목록에서 즉시 사라지게 처리(재조회 또는 로컬 제거).

## 상호작용 흐름 (요약)
- **고객**: 앱 진입 → `/menu` 자동 → 카테고리 탐색 → 카드 클릭 → 상세 모달. (주문 담기는 U3.)
- **관리자**: `/menus` → 카테고리 선택 → 메뉴 CRUD/재정렬/품절 토글 → 변경은 고객 다음 조회 시 반영(실시간 push 아님).
