# U2 Menu 논리 컴포넌트 (Logical Components)

Menu 도메인 패키지의 3계층 구성 + 프론트. 모두 U0 기반을 상속하며 신규 인프라 컴포넌트는 없다.

## 백엔드 (`backend/app/menu/`)

| 논리 컴포넌트 | 파일(예정) | 역할 | 관련 NFR |
|---|---|---|---|
| MenuRouter | `menu/router.py` | 고객(`GET /api/menu`)·관리자(categories/menus CRUD·reorder·availability) 엔드포인트, role guards, Pydantic I/O | NFR-2, NFR-3 |
| MenuService | `menu/service.py` | 비즈니스 로직: 카테고리 CRUD, 메뉴 CRUD·품절토글, 고객 그룹 조회, 재정렬, **계약 A `get_menu_items`** | - |
| MenuRepository | `menu/repository.py` | Menu store-scoped 쿼리(`BaseRepository` 상속): `list_active`, `list_by_ids`, `max_order` | NFR-3 |
| CategoryRepository | `menu/repository.py` | Category store-scoped 쿼리: `list_ordered` | NFR-3 |
| Models | `menu/models.py` | `Category`, `Menu` 엔티티(U0 `Base` 상속, store_id 격리) | NFR-3, NFR-4 |
| Schemas | `menu/schemas.py` | `MenuInput`/`MenuOut`/`CategoryInput`/`CategoryOut`/`CategoryWithMenus`/`ReorderInput`/`AvailabilityInput` (Pydantic; `HttpUrl`, `int ge=0`) | - |
| (등록) | `main.py`/`database.py` | U0 통합 슬롯에 `include_router(menu)`, `init_db` 모델 import | - |

## 프론트엔드

| 논리 컴포넌트 | 위치(예정) | 역할 | 관련 NFR |
|---|---|---|---|
| Customer Menu 화면 | `frontend-customer/src/views/menu/` (MenuView, CategoryNav, MenuCard, MenuDetailModal) | US-C2 메뉴 탐색/상세, 품절 배지 | NFR-6 |
| Customer Menu API | `frontend-customer/src/api/menu.js` | `GET /api/menu` | - |
| Admin Menu 화면 | `frontend-admin/src/views/menu/` (MenuManageView, CategoryList, MenuList, MenuFormModal, ConfirmDialog) | US-A8 CRUD·재정렬·품절토글, 폼 검증 | - |
| Admin Menu API | `frontend-admin/src/api/menuAdmin.js` | categories/menus CRUD·reorder·availability | - |

- 라우트: 고객 `/menu`(require_table), 관리자 `/menus`(require_admin) — U0 라우터 슬롯에 추가.

## 인프라 컴포넌트
- **없음(N/A)**: 큐/캐시/서킷브레이커 등 불필요(로컬 데모, 소량 데이터, 캐싱·페이지네이션 미적용). DB는 U0 SQLite 공유.
