# U2 Menu — Code Generation Summary

**유닛**: U2 Menu · **담당**: 이원종 · **브랜치**: u2-menu
**스토리**: US-C2(고객 메뉴 탐색), US-A8(관리자 메뉴 관리) · **계약**: A(`get_menu_items`, U3 제공)

> 테스트/빌드 실행은 Build & Test 단계에서 수행. 본 문서는 생성물 요약(markdown).

## 백엔드 (`backend/app/menu/`)

| 파일 | 상태 | 내용 |
|---|---|---|
| `__init__.py` | Created | 유닛 패키지 docstring |
| `models.py` | Created | `Category`(unique(store_id,name)), `Menu`(price int, image_url, available, is_deleted, index(store_id,category_id,display_order)) |
| `schemas.py` | Created | `CategoryInput/Out`, `MenuInput`(price≥0, HttpUrl), `MenuOut`, `CategoryWithMenus`, `ReorderInput`, `AvailabilityInput` |
| `repository.py` | Created | `CategoryRepository`, `MenuRepository` (BaseRepository 상속, store 격리, is_deleted 필터) |
| `service.py` | Created | 카테고리/메뉴 CRUD·정렬·품절토글, 고객 그룹 조회, **계약 A `get_menu_items`** |
| `router.py` | Created | 고객 `GET /api/menu`(require_table) + 관리자 CRUD/reorder/availability(require_admin) |

**U0 통합 (수정)**
| 파일 | 상태 | 변경 |
|---|---|---|
| `common/database.py` | Modified | `init_db()`에 `from app.menu import models` 등록 |
| `main.py` | Modified | `create_app()`에 `include_router(menu_router)` |
| `seeds/seed.py` | Modified | 매장별 샘플 카테고리/메뉴(`_seed_menu`, 멱등) — 콜드브루는 품절 예시 |

**테스트**
| 파일 | 상태 | 커버리지 |
|---|---|---|
| `tests/test_menu.py` | Created | 멀티테넌시 격리, 카테고리/메뉴 CRUD·유니크, 소프트삭제 은닉, 품절 노출, 카테고리 삭제 제약, 재정렬 전체집합 검증, 계약 A(미존재/타매장 제외) |

## API 요약
| 메서드 | 경로 | 가드 | 설명 |
|---|---|---|---|
| GET | `/api/menu` | require_table | 카테고리별 그룹 메뉴(품절 포함) |
| GET/POST | `/api/admin/categories` | require_admin | 카테고리 목록/생성 |
| PUT | `/api/admin/categories/reorder` | require_admin | 카테고리 순서(전체집합) |
| PUT/DELETE | `/api/admin/categories/{id}` | require_admin | 수정/삭제(활성 메뉴 없을 때만) |
| GET/POST | `/api/admin/menus` | require_admin | 메뉴 목록/생성 |
| PUT | `/api/admin/menus/reorder?category_id=` | require_admin | 메뉴 순서(카테고리 내) |
| PUT/DELETE | `/api/admin/menus/{id}` | require_admin | 수정/소프트삭제 |
| PUT | `/api/admin/menus/{id}/availability` | require_admin | 품절 토글 |

## 프론트엔드
| 파일 | 상태 | 내용 |
|---|---|---|
| `frontend-customer/src/api/menu.js` | Created | `fetchMenu()` |
| `frontend-customer/src/views/MenuView.vue` | Created | 카테고리 네비 + 카드(품절 배지) + 상세 모달, 터치 UI(NFR-6). 담기=U3 경계(미구현) |
| `frontend-customer/src/router/index.js` | Modified | `/menu` 슬롯 활성화(requiresAuth) |
| `frontend-admin/src/api/menuAdmin.js` | Created | categories/menus CRUD·reorder·availability |
| `frontend-admin/src/views/MenuAdminView.vue` | Created | 카테고리/메뉴 패널, 폼 검증, 품절 토글, 삭제 확인 |
| `frontend-admin/src/router/index.js` | Modified | `/menu` 슬롯 활성화(requiresAuth) |

모든 상호작용 요소에 `data-testid` 부여(자동화 친화).

## 설계 준수 노트
- store_id는 항상 StoreContext에서만 (BR-U0-3/BR-U2-0). 리포지토리 store 격리 상속.
- 소프트삭제(is_deleted)와 품절(available)은 독립 상태 — 계약 A는 삭제/미존재 제외, 품절은 `available=false`로 포함(Q8:A).
- U2는 실시간 이벤트 미발행.
- 라우트 슬롯은 U0 예약(`/menu`)을 따름.
