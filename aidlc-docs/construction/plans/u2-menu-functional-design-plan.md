# U2 Menu — Functional Design Plan

**유닛**: U2 Menu (메뉴) · **담당**: 이원종
**스토리**: US-A8(메뉴 CRUD·노출 순서, Must), US-C2(메뉴 조회·카테고리 탐색, Must)
**의존**: U0 Common(계약 E StoreContext, `BaseRepository` store 격리, 예외/스키마) · Auth(컨텍스트만)
**제공(소비 유닛)**: **계약 A** — U3 Order가 주문 생성 시 메뉴 단가/유효성 조회에 사용.

> 본 문서는 U2 Functional Design 단계의 계획 + 결정 질문지입니다. 아래 **질문**에 `[Answer]:` 태그로 답을 채워주시면, 그 결정을 바탕으로 산출물(`domain-entities.md` / `business-logic-model.md` / `business-rules.md` / `frontend-components.md`)을 생성합니다.

---

## 참고 — 상위 설계에서 이미 고정된 사항 (재확인용, 질문 아님)

- **서비스 메서드**(`component-methods.md`): `list_menus_for_customer(ctx)`, `list_categories(ctx)`, `create_menu(ctx, MenuInput)`, `update_menu(ctx, menu_id, MenuInput)`, `delete_menu(ctx, menu_id)`, `reorder_menus(ctx, category_id, ordered_ids)`.
- **MenuInput 필드**(초안): `{name, price, desc, category_id, image_url}`.
- **멀티테넌시**: 모든 조회/변경은 `store_id`로 격리(BR-U0-1~4), `store_id`는 `StoreContext`에서만 파생.
- **3계층**: Router → Service → Repository(`BaseRepository` 상속).
- **계약 A**(`unit-of-work-dependency.md`): `get_menu_items(store_id, menu_ids) -> [{id, name, price, available}]`.
- **엔티티 소유**: Menu·Category 엔티티는 U2가 소유, U0 `Base` 상속 + `store_id` 격리.
- **이미지**: URL 참조만(업로드/최적화 없음 — `constraints.md`).

---

## 산출물 계획 (체크박스 — 답변 확정 후 생성)

- [x] `domain-entities.md` — Category, Menu 엔티티(필드·제약·관계·ER), store 격리
- [x] `business-logic-model.md` — MenuService/MenuRepository 로직, 계약 A(`get_menu_items`) 정의, 고객 조회 정렬/그룹핑, CRUD·재정렬 알고리즘
- [x] `business-rules.md` — 검증(필수 필드/가격 범위/이미지 URL), 삭제/품절 정책, 노출 순서 규칙, 카테고리 규칙, 예외 매핑(BR-U0-10 준수)
- [x] `frontend-components.md` — 고객 메뉴 탐색/상세(US-C2), 관리자 메뉴 관리 CRUD·재정렬(US-A8) 컴포넌트 구조·상태·API 연동

---

## 질문 (Functional Design 결정)

각 질문의 `[Answer]:` 태그 뒤에 **letter(A/B/C…)** 를 채워주세요. 보기 중 맞는 게 없으면 마지막 **Other** 를 선택하고 설명을 적어주세요. 다 채우신 뒤 "완료" 라고 알려주시면 분석 후 산출물을 생성합니다.

### Question 1 — 카테고리(Category) 모델링
메뉴 카테고리를 어떻게 표현할까요? (US-C2 카테고리 탐색, `list_categories`, `category_id` 존재)

A) **별도 Category 엔티티**(테이블: id, store_id, name, display_order) — 메뉴가 `category_id`로 FK 참조. 카테고리 자체도 등록/순서 관리 가능.

B) **Menu의 문자열 필드**(category: str) — 별도 테이블 없이 메뉴에 카테고리명을 직접 저장, 조회 시 그룹핑.

C) Other (please describe after [Answer]: tag below)

[Answer]: A

### Question 2 — 카테고리 관리 범위 (Q1에서 A 선택 시)
카테고리를 관리자가 별도로 CRUD 하나요, 아니면 메뉴 등록 과정에서 암묵 생성하나요?

A) **명시적 카테고리 CRUD** — 관리자가 카테고리를 직접 생성/수정/삭제/순서조정하고, 메뉴는 기존 카테고리에서 선택.

B) **암묵 생성** — 메뉴 등록 시 카테고리명을 입력하면 없으면 자동 생성(별도 관리 화면 없음).

C) Q1에서 B(문자열)를 선택했으므로 해당 없음.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

### Question 3 — 메뉴 삭제(delete) 시맨틱
`delete_menu`는 어떻게 동작할까요? (계약 A가 `available` 플래그를 반환하는 점 고려)

A) **하드 삭제** — 레코드를 실제 삭제. (주문은 생성 시점에 메뉴명/단가를 스냅샷으로 저장하므로 과거 주문에 영향 없음 — U3와 계약으로 전제.)

B) **소프트 삭제** — `is_deleted`(또는 `active=false`)로 숨김 처리, 레코드 보존. 고객 조회/계약 A에서 제외.

C) Other (please describe after [Answer]: tag below)

[Answer]: B

### Question 4 — 품절/판매중지(availability) 토글
"지금 주문 불가" 상태(품절 등)를 메뉴별로 토글하는 기능을 MVP에 포함할까요? (계약 A `available` 필드의 의미를 결정)

A) **포함** — 메뉴에 `available: bool` 필드. 관리자가 토글, 고객 화면엔 표시되나 주문 불가 처리, 계약 A는 실제 available 값을 반환.

B) **미포함** — MVP 범위 아님. 계약 A의 `available`은 "존재하고 삭제되지 않음"을 의미하는 상수(항상 true 또는 소프트삭제 여부)로 채운다.

C) Other (please describe after [Answer]: tag below)

[Answer]: A

### Question 5 — 노출 순서(display order) 범위
`reorder_menus(ctx, category_id, ordered_ids)`의 정렬 단위와 범위는?

A) **카테고리 내 메뉴 순서만** — 메뉴는 자신의 카테고리 안에서만 순서를 가짐. 카테고리 자체 순서는 (Q1-A 시) Category.display_order로 별도 관리.

B) **메뉴·카테고리 모두 순서 관리** — 카테고리 순서 + 각 카테고리 내 메뉴 순서 둘 다 조정 가능.

C) **전역 단일 순서** — 카테고리 구분 없이 메뉴 전체에 하나의 노출 순서.

D) Other (please describe after [Answer]: tag below)

[Answer]: B

### Question 6 — 가격(price) 타입·검증 범위
가격 필드의 타입과 유효 범위 검증 규칙은? (US-A8 "가격 범위 검증")

A) **정수(원, KRW)** — 최소 0 초과, 최대 1,000,000원. 소수점 없음.

B) **정수(원, KRW)** — 최소 0 이상(무료 허용), 상한 없음.

C) Other (please describe after [Answer]: tag below — 타입/최소/최대 명시)

[Answer]: B

### Question 7 — 필드 필수/선택 및 이미지 URL 검증
`MenuInput` 필드의 필수 여부와 image_url 검증 수준은?

A) **name·price·category 필수, desc·image_url 선택**. image_url은 형식 검증 없이 문자열로 저장(빈 값 허용).

B) **name·price·category 필수, desc·image_url 선택**. image_url은 입력 시 http(s):// URL 형식만 검증.

C) Other (please describe after [Answer]: tag below)

[Answer]: B

### Question 8 — 계약 A(`get_menu_items`) 노출 방식 및 미존재/삭제 처리
U3 Order가 주문 생성 시 사용할 계약 A를 U2가 어떻게 제공하고, 요청한 menu_id가 없거나 삭제/품절이면?

A) **동일 프로세스 내 서비스 메서드**(`MenuService.get_menu_items`) 직접 호출. 존재하지 않거나 주문 불가한 메뉴가 포함되면 **해당 항목을 오류로 표시**(유효 항목만 반환하지 않고, 잘못된 요청은 검증 실패로 U3가 처리하도록 정보 반환).

B) **동일 프로세스 내 서비스 메서드** 호출. 유효한 메뉴만 반환하고 무효 항목은 조용히 제외(누락은 U3가 판단).

C) Other (please describe after [Answer]: tag below)

[Answer]: A

### Question 9 — 고객 메뉴 조회 응답 구조
`list_menus_for_customer`의 반환 형태는? (US-C2 카테고리별 표시)

A) **카테고리별 그룹 구조** — `[{category, display_order, menus:[...정렬됨]}]`. 프론트가 그대로 렌더.

B) **평면 메뉴 배열** — `[{...menu, category_name, category_order, menu_order}]`. 프론트가 그룹핑.

C) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## 답변 후 진행
- 모든 `[Answer]:` 확인 → 모순/모호성 검사 → (필요 시 clarification) → 산출물 4종 생성 → REVIEW 게이트.
