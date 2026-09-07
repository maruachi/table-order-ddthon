# User Stories Generation Plan (스토리 생성 계획)

> **역할**: Product Owner
> **목적**: `requirements.md`의 기능/비기능 요구사항을 INVEST 원칙에 부합하는 사용자 스토리와 페르소나로 변환한다.
> **상태**: PART 1 — Planning (아래 질문에 답변해 주세요). 모든 `[Answer]:` 태그가 채워지면 계획 승인 후 PART 2(생성)로 진행합니다.

---

## A. 스토리 개발 방법론 (Execution Checklist)

- [x] A1. `requirements.md`의 기능 요구사항(FR-C1~C5, FR-A1~A4)과 도메인 개념(테이블 세션, 주문 이력)을 스토리 후보로 분해
- [x] A2. 페르소나 정의 (고객 / 관리자, 필요 시 세분화)
- [x] A3. 아래 승인된 브레이크다운 방식(§C)에 따라 스토리 그룹화(에픽/그룹)
- [x] A4. 각 스토리를 INVEST(Independent, Negotiable, Valuable, Estimable, Small, Testable) 기준으로 작성
- [x] A5. 각 스토리에 승인된 형식(§D)의 인수 조건 부여
- [x] A6. 비기능 요구사항(NFR-1~8)을 관련 스토리의 인수 조건 또는 제약으로 반영
- [x] A7. 페르소나 ↔ 스토리 매핑 표 작성
- [x] A8. `stories.md`, `personas.md` 산출 및 상호 참조 검증

- 임동규, 이원종, 최지영, 이재환 4명이 나눠서 병렬 개발 진행할 예정. 유닛별로 나눠줘.

## B. 필수 산출물 (Mandatory Artifacts)

- [x] B1. `aidlc-docs/inception/user-stories/stories.md` — INVEST 기반 사용자 스토리
- [x] B2. `aidlc-docs/inception/user-stories/personas.md` — 사용자 원형 및 특성
- [x] B3. 스토리는 Independent/Negotiable/Valuable/Estimable/Small/Testable 준수
- [x] B4. 각 스토리에 인수 조건 포함
- [x] B5. 페르소나-스토리 매핑 포함

## C. 스토리 브레이크다운 방식 옵션 (트레이드오프)

| 방식 | 설명 | 장점 | 단점 |
|---|---|---|---|
| **User Journey-Based** | 사용자 워크플로우/여정 흐름 순서로 스토리 구성 | 실제 사용 흐름 반영, UX 검증 용이 | 기능 중복·경계 모호 가능 |
| **Feature-Based** | 시스템 기능/능력 단위로 구성 | 요구사항(FR) 추적성 우수, 구현 매핑 명확 | 여정 전체 흐름이 흩어질 수 있음 |
| **Persona-Based** | 사용자 유형(고객/관리자)별로 그룹화 | 페르소나별 범위·우선순위 명확 | 공통 기능 중복 서술 가능 |
| **Domain-Based** | 비즈니스 도메인(메뉴/주문/세션/인증)별 구성 | 도메인 응집도, 후속 Units 매핑 유리 | 사용자 관점보다 시스템 관점 |
| **Epic-Based** | 상위 에픽 → 하위 스토리 계층 | 대규모 범위 정리·우선순위화 용이 | 초기 오버헤드 |
| **Hybrid** | 최상위 페르소나 → 하위 기능/도메인 | 사용자 관점 + 추적성 균형 | 규칙을 명확히 정의해야 함 |

**PO 추천**: 페르소나가 뚜렷하고 FR 추적성이 중요하므로 **Hybrid(Persona → Feature/Domain)**를 권장합니다. 아래 질문 Q2에서 선택해 주세요.

---

## D. 계획 확정을 위한 질문 (아래 `[Answer]:`에 선택지 문자를 기입)

## Question 1
페르소나(사용자 원형)를 어느 수준으로 정의할까요?

A) 2개 — 고객(테이블 태블릿 이용자), 매장 관리자 (요구사항에 명시된 최소 구성)

B) 3개 — 고객, 매장 관리자, 시스템 운영자(초기 시드/매장·계정 설정 담당) 분리

C) 4개 — 고객, 홀 직원(주문 모니터링/상태 변경), 매장 매니저(메뉴·테이블·계정 관리), 시스템 운영자

D) Other (please describe after [Answer]: tag below)

[Answer]:A

## Question 2
스토리 브레이크다운(구성) 방식을 무엇으로 할까요? (§C 참고)

A) Hybrid — 페르소나(고객/관리자) → 하위 기능/도메인 (PO 추천)

B) Feature-Based — FR 항목 단위로 구성(추적성 최우선)

C) Persona-Based — 페르소나별 순수 그룹화

D) User Journey-Based — 사용자 여정 흐름 순서로 구성

E) Other (please describe after [Answer]: tag below)

[Answer]:A

## Question 3
스토리의 세분화(granularity) 수준은?

A) 세분화 — 하나의 화면/동작 단위로 작게 분할(예: "장바구니에 메뉴 추가", "수량 변경"을 별도 스토리로). 스토리 수는 많아짐

B) 중간 — 응집된 기능 단위로 묶음(예: "장바구니 관리" 하나로, 인수 조건에서 세부 동작 명시). PO 추천

C) 굵게 — FR 단위(FR-C3 등) 그대로 하나의 스토리로

D) Other (please describe after [Answer]: tag below)

[Answer]:B

## Question 4
인수 조건(Acceptance Criteria) 형식은?

A) Gherkin 스타일 (Given / When / Then) — 테스트 자동화 매핑에 유리 (PO 추천)

B) 체크리스트 스타일 (충족해야 할 조건 목록)

C) 서술형 (자연어 문단)

D) Other (please describe after [Answer]: tag below)

[Answer]:A

## Question 5
스토리에 우선순위(MVP 필수 vs 선택)를 표기할까요?

A) 예 — MoSCoW(Must/Should/Could/Won't) 또는 MVP/Optional 라벨을 각 스토리에 표기 (PO 추천)

B) 아니오 — 우선순위 없이 스토리만 나열(요구사항의 MVP 범위를 그대로 필수로 간주)

C) Other (please describe after [Answer]: tag below)

[Answer]:A

## Question 6
요구사항에서 "선택사항"으로 표시된 기능(예: FR-C5의 고객 화면 주문 상태 실시간 업데이트)은 스토리로 어떻게 다룰까요?

A) 별도의 "Could/Optional" 스토리로 포함하되 우선순위를 낮게 표기 (PO 추천)

B) MVP 범위에서 제외하고 스토리로 만들지 않음

C) 필수 스토리에 통합

D) Other (please describe after [Answer]: tag below)

[Answer]:A

## Question 7
비기능 요구사항(NFR-1 실시간 2초, NFR-3 멀티테넌시, NFR-6 터치 UI 등)을 스토리에 어떻게 반영할까요?

A) 관련 기능 스토리의 인수 조건/제약으로 인라인 반영 (PO 추천)

B) 별도의 NFR/기술 스토리 그룹으로 분리 작성

C) 두 방식 병행(핵심 NFR은 인라인, 시스템 전역 NFR은 별도)

D) Other (please describe after [Answer]: tag below)

[Answer]:A

---

> **안내**: 위 7개 질문의 `[Answer]:` 태그에 선택지 문자(예: `A`)를 채운 뒤 알려주시면, 답변을 분석하고(모호한 부분이 있으면 후속 질문) 계획 승인 후 스토리를 생성합니다.
