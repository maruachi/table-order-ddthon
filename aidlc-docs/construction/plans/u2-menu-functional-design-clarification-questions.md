# U2 Menu — Functional Design Clarification

답변(Q1:A, Q2:A, Q3:B, Q4:A, Q5:B, Q6:B, Q7:B, Q8:B, Q9:A) 검토 중 **Q4 ↔ Q8 상호작용**에서 계약 A(U3와 공유)의 동작이 확정되지 않아 1개 질문으로 해소합니다.

## 이슈: 계약 A `get_menu_items`에서 "품절(available=false)" 항목을 어떻게 다룰까
- Q4:A → 메뉴에 `available: bool`(품절 토글) 도입, 계약 A 시그니처는 `{id, name, price, available}` 반환.
- Q8:B → "무효 항목은 조용히 제외, 유효한 것만 반환, 누락은 U3가 판단".
- 충돌 지점: **품절(available=false)이 '제외 대상(무효)'인지, 아니면 반환하되 플래그로 알려줄 대상인지**가 미정.

### Clarification Question 1
`get_menu_items(store_id, menu_ids)`가 반환할 때, 각 항목의 상태별 처리는?

A) **삭제(소프트삭제)·미존재만 제외**하고, **품절 항목은 `available=false`로 포함해 반환**. → U3가 품절 주문 거부 여부를 판단(계약 A의 `available` 필드가 실제 의미를 가짐). *(권장 — Q4:A와 일관)*

B) **삭제·미존재·품절 모두 제외**하고 **주문 가능한(available=true) 항목만 반환**. → 반환 항목의 `available`은 항상 true(사실상 존재 확인용). U3는 요청 대비 누락으로 무효를 감지.

C) Other (please describe after [Answer]: tag below)

[Answer]: A
