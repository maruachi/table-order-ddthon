# U2 Menu 비즈니스 규칙 (Business Rules)

U0 규칙(BR-U0-*)을 상속·준수한다. 예외는 U0 표준 매핑(BR-U0-10): `ValidationError`→422, `NotFoundError`→404, `ForbiddenError`→403, `AuthError`→401. 결정 근거: Q1:A~Q9:A(계획서 참조).

## 멀티테넌시 (NFR-3, 상속)
- **BR-U2-0**: 모든 Category/Menu 조회·변경은 `BaseRepository`를 통해 `store_id`로 격리(BR-U0-2). `store_id`는 `StoreContext.store_id`에서만 파생(BR-U0-3). 타 매장 리소스 접근은 404(BR-U0-4).

## 입력 검증 (US-A8 "필수 필드/가격 범위 검증", Q6:B·Q7:B)
- **BR-U2-1**: `name`은 필수, 공백 trim 후 비어있지 않아야 함(1자 이상). 위반 시 `ValidationError`.
- **BR-U2-2**: `price`는 필수, **정수(원)**, `price >= 0`(무료 허용, 상한 없음 — Q6:B). 음수·비정수는 `ValidationError`.
- **BR-U2-3**: `category_id`는 필수이며 **같은 매장에 존재하는 카테고리**여야 함. 없거나 타 매장이면 `ValidationError`(생성/수정 입력 검증) — 리소스 조회가 아닌 입력값 검증 성격.
- **BR-U2-4**: `description`은 선택(nullable). 미입력 허용.
- **BR-U2-5**: `image_url`은 선택. 입력된 경우 `http://` 또는 `https://`로 시작하는 URL 형식만 허용(Q7:B). 위반 시 `ValidationError`. 이미지 업로드/최적화는 범위 외(constraints.md).

## 카테고리 규칙 (Q1:A·Q2:A)
- **BR-U2-9**: `(store_id, name)` 유일. 중복 카테고리명 생성/수정 시 `ValidationError`.
- **BR-U2-8**: 카테고리 삭제는 **활성(is_deleted=false) 메뉴가 없을 때만** 허용. 남아있으면 `ValidationError`(메뉴 이동/삭제 후 재시도 안내). 조건 충족 시 하드 삭제.
- **BR-U2-10**: 존재하지 않는 카테고리 조회/수정/삭제는 `NotFoundError`(404, 타 매장 포함 존재 미노출).

## 삭제 / 품절 정책 (Q3:B·Q4:A)
- **BR-U2-11**: `delete_menu`는 **소프트 삭제**(`is_deleted=true`). 레코드는 보존하되 고객 조회(`list_menus_for_customer`)·계약 A(`get_menu_items`)·관리 목록(`list_menus_admin`)에서 제외.
- **BR-U2-12**: `available`(품절 토글)은 `is_deleted`와 독립. `available=false`인 메뉴는 **고객 화면에 표시되나 주문 불가**(품절 배지). 계약 A는 이를 `available=false`로 반환.
- **BR-U2-13**: 이미 삭제된(`is_deleted=true`) 메뉴에 대한 수정/재삭제/품절토글은 `NotFoundError`.

## 노출 순서 규칙 (Q5:B)
- **BR-U2-6**: 신규 메뉴/카테고리는 해당 스코프의 **맨 뒤**(max display_order + 1)에 추가.
- **BR-U2-7**: `reorder_menus`/`reorder_categories`의 `ordered_ids`는 해당 스코프의 **활성 대상 전체 집합과 정확히 일치**(누락·외부 id·중복 금지)해야 함. 불일치 시 `ValidationError`. 검증 후 `display_order`를 0부터 순차 재할당.
- **BR-U2-14**: 고객·관리 조회의 기본 정렬은 카테고리 `display_order` → 메뉴 `display_order` → `id`.

## 계약 A 규칙 (Q8:A·Clarification:A)
- **BR-U2-15**: `get_menu_items(store_id, menu_ids)`는 **미존재·소프트삭제 항목을 결과에서 제외**하고, 존재하는 항목은 **실제 `available` 값과 서버 `price`를 포함**해 반환.
- **BR-U2-16**: 주문 성립 판정(누락=무효 거부, `available=false`=품절 거부)은 **U3의 책임**. U2는 상태 정보만 제공한다. 주문 단가는 계약 A의 서버 `price`가 신뢰 원천이며 클라이언트 전송 가격은 신뢰하지 않는다.

## 권한
- **BR-U2-17**: 카테고리·메뉴의 생성/수정/삭제/재정렬/품절토글은 `require_admin`. 고객 조회(`GET /api/menu`)는 `require_table`. 역할 불일치는 403(BR-U0-6).

## 영속성 (NFR-4, 상속)
- **BR-U2-18**: Category/Menu는 SQLite 영속(BR-U0-8). 스키마는 U0 `init_db()`의 `create_all`에 모델 import로 등록(BR-U0-9).
