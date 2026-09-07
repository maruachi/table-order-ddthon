# U2 Menu — Code Generation Plan

**유닛**: U2 Menu · **담당**: 이원종 · **브랜치**: u2-menu
**입력(승인 완료)**: Functional Design(domain-entities/business-logic-model/business-rules/frontend-components), NFR Requirements, NFR Design(patterns/logical-components).
**성격**: Greenfield 멀티유닛(모놀리식 백엔드 + 2개 SPA). 이 계획이 코드 생성의 **단일 소스**다.

## 유닛 컨텍스트
- **구현 스토리**: US-C2(고객 메뉴 탐색/상세), US-A8(관리자 메뉴·카테고리 CRUD·정렬·품절토글).
- **의존**: U0 공통(BaseRepository, StoreContext, require_admin/require_table, AppError, Base/get_db/init_db). U1이 런타임에 TokenVerifier 등록(가드 소비만).
- **소유 엔티티**: `Category`, `Menu` (둘 다 store_id 격리).
- **제공 계약**: 계약 A `MenuService.get_menu_items(store_id, menu_ids) -> [{id,name,price,available}]` (U3 소비, 소프트삭제/미존재 제외, 품절 포함).
- **이벤트**: 없음(U2는 실시간 미발행).

## 코드 위치 (절대 aidlc-docs/ 아님)
- 백엔드: `backend/app/menu/` (models.py, schemas.py, repository.py, service.py, router.py, __init__.py)
- 백엔드 통합(U0 파일 수정): `backend/app/common/database.py`(init_db에 menu models import), `backend/app/main.py`(include_router)
- 시드(선택): `backend/seeds/seed.py`에 샘플 카테고리/메뉴 추가
- 테스트: `backend/tests/test_menu.py`
- 고객 SPA: `frontend-customer/src/views/MenuView.vue`, `src/api/menu.js`, `router/index.js` 수정
- 관리자 SPA: `frontend-admin/src/views/MenuAdminView.vue`, `src/api/menuAdmin.js`, `router/index.js` 수정
- 문서 요약: `aidlc-docs/construction/u2-menu/code/`

> **경로 정합성 결정**: U0 셸이 예약한 라우트 슬롯(고객 `/menu`→MenuView, 관리자 `/menu`→MenuAdminView.vue)을 그대로 사용한다. (Functional Design 문서의 관리자 `/menus`/`MenuManageView` 명칭 대신 U0 예약 슬롯을 따라 충돌을 피함.)

---

## 생성 단계 (순차 실행)

- [x] **Step 1 — 백엔드 패키지 스켈레톤**: `backend/app/menu/__init__.py` 준비, 패키지 확인.
- [x] **Step 2 — 도메인 모델 (Repository/Data 계층 모델)**: `menu/models.py` — `Category`(id, store_id FK+index, name, display_order, created_at; unique(store_id,name)), `Menu`(id, store_id FK+index, category_id FK, name, price int, description nullable, image_url nullable, display_order, available bool default true, is_deleted bool default false, created_at, updated_at; index(store_id,category_id,display_order)). *(domain-entities.md, BR-U2-0~5,11)*
- [x] **Step 3 — U0 통합(모델 등록)**: `common/database.py` `init_db()`에 `from app.menu import models` import 추가(주석 슬롯 대체). *(BR-U2-18)*
- [x] **Step 4 — Pydantic 스키마**: `menu/schemas.py` — `CategoryInput/CategoryOut`, `MenuInput`(name 필수, `price:int ge=0`, `image_url:HttpUrl|None`, description opt), `MenuOut`, `CategoryWithMenus`(고객 그룹 응답), `ReorderInput`(ordered_ids:list[int]), `AvailabilityInput`(available:bool). *(BR-U2-1~5, Q6:B/Q7:B/Q9:A)*
- [x] **Step 5 — Repository 계층**: `menu/repository.py` — `CategoryRepository`(list_ordered, exists_by_name), `MenuRepository`(list_active by category, list_all_active, list_by_ids, has_active_menus, max_display_order). 모두 `BaseRepository` 상속(store_id 자동 격리). *(NFR-3, logical-components.md)*
- [x] **Step 6 — Service 계층(비즈니스 로직)**: `menu/service.py` — 카테고리 CRUD(list/create/update/delete[활성 메뉴 없을 때만]/reorder), 메뉴 CRUD(list_admin/create/update/delete[soft]/set_availability/reorder), `list_menus_for_customer`(그룹 구조), **계약 A `get_menu_items`**. 검증 위반은 U0 ValidationError/NotFoundError raise. 재정렬은 전체집합 일치 검증 후 0..n 재할당. *(business-logic-model.md, business-rules.md 전체)*
- [x] **Step 7 — API(Router) 계층**: `menu/router.py` — 고객 `GET /api/menu`(require_table); 관리자(require_admin) `GET/POST/PUT/DELETE /api/admin/categories`, `PUT /api/admin/categories/reorder`, `GET/POST/PUT/DELETE /api/admin/menus`, `PUT /api/admin/menus/{id}/availability`, `PUT /api/admin/menus/reorder`. store_id는 ctx에서만. *(BR-U2-17, business-logic-model.md 엔드포인트 표)*
- [x] **Step 8 — U0 통합(라우터 등록)**: `main.py` `create_app()`에 `include_router(menu_router)` 추가(주석 슬롯 대체).
- [x] **Step 9 — 백엔드 단위 테스트**: `backend/tests/test_menu.py` — 멀티테넌시 격리, 카테고리/메뉴 CRUD, 소프트삭제(고객·계약A에서 제외), 품절 노출(available=false 포함), 재정렬 검증, 계약 A 반환 형태/타입. (실행은 Build&Test 단계)
- [x] **Step 10 — 시드 보강(선택)**: `seeds/seed.py`에 매장별 샘플 카테고리·메뉴 추가(멱등).
- [x] **Step 11 — 고객 프론트 API**: `frontend-customer/src/api/menu.js` — `fetchMenu()` → `GET /api/menu`.
- [x] **Step 12 — 고객 프론트 화면**: `frontend-customer/src/views/MenuView.vue` — 카테고리 네비 + 카테고리별 섹션 + 메뉴 카드(품절 배지) + 상세 모달. 터치 UI(카드형, 44px 타깃, NFR-6), `data-testid` 부여. 주문 담기는 U3 경계(미구현). `router/index.js`에 `/menu` 슬롯 활성화(고객 기본 진입).
- [x] **Step 13 — 관리자 프론트 API**: `frontend-admin/src/api/menuAdmin.js` — categories/menus CRUD·reorder·availability 호출.
- [x] **Step 14 — 관리자 프론트 화면**: `frontend-admin/src/views/MenuAdminView.vue` — 카테고리 패널 + 메뉴 패널, 생성/수정 폼(검증), 삭제 확인, 품절 토글, 순서 변경. `data-testid` 부여. `router/index.js`에 `/menu` 슬롯 활성화(require_admin 메타).
- [x] **Step 15 — 코드 요약 문서**: `aidlc-docs/construction/u2-menu/code/` 에 백엔드/프론트 생성물 요약 작성.

## 스토리 추적성
- [x] US-C2 ← Step 11, 12, (백엔드 Step 6~8 `GET /api/menu`)
- [x] US-A8 ← Step 13, 14, (백엔드 Step 6~8 admin 엔드포인트)
- [x] 계약 A(U3 제공) ← Step 6 `get_menu_items` + Step 9 테스트

## 범위 요약
- 신규 백엔드 파일 6 + U0 수정 2 + 테스트 1 + 시드 수정 1
- 신규 프론트 파일 4(고객 2 + 관리자 2) + 라우터 수정 2
- 문서 요약 1
- 총 15 스텝. Infrastructure Design은 로컬 개발로 스킵. 테스트 실행은 Build&Test 단계.
