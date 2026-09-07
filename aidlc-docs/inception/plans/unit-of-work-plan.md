# Unit of Work Plan — 테이블오더 서비스 (Units Generation · Part 1 Planning)

**단계 목적**: 시스템을 4명(임동규·이원종·최지영·이재환) 병렬 개발이 가능한 **유닛(Unit of Work)** 으로 분해한다. 각 유닛은 스토리·컴포넌트·화면의 논리적 묶음이며, 이후 Construction 단계(Functional Design → Code Generation)가 유닛별로 반복 실행된다.

- 출처: `aidlc-docs/inception/application-design/` (components, services, component-dependency), `aidlc-docs/inception/user-stories/stories.md`, `requirements.md`
- 확정 기술 스택: FastAPI(Python) · Vue SPA × 2(고객/관리자) · SQLite · 로컬 실행 · 멀티테넌트(store_id 격리)
- 배포 모델: **모놀리식 단일 백엔드**(로컬 실행). 유닛 = 배포 단위가 아니라 **논리적 개발 모듈**.

---

## Part A. 유닛 분해 산출물 계획 (Mandatory Artifacts)

아래 산출물을 `aidlc-docs/inception/application-design/`에 생성한다. (Part 2 Generation에서 승인된 결정에 따라 작성)

- [x] `unit-of-work.md` — 유닛 정의·책임·포함 컴포넌트/모듈 + Greenfield 코드 조직 전략(디렉터리 구조)
- [x] `unit-of-work-dependency.md` — 유닛 간 의존성 매트릭스·계약 지점·개발 순서
- [x] `unit-of-work-story-map.md` — 스토리 ↔ 유닛 매핑(모든 스토리 배정 검증)
- [x] 유닛 경계·의존성 일관성 검증(순환 의존 최소화, 모든 스토리 커버)

### 예비 유닛 분해안 (질문 응답으로 확정)

설계 문서 기준 초안 — **공통 기반 1 + 도메인 4**:

| 유닛 | 포함 컴포넌트 | 관련 스토리 | 담당(예정) |
|---|---|---|---|
| **U0. Platform/Common** (선행 공통) | Store·Table 엔티티, DB/세션, BaseRepository, StoreContext 인증 의존성, 공통 스키마 | (기반) NFR-3/4 | 공동/선행 |
| **U1. Auth** | Auth 서비스(관리자 JWT·테이블 토큰) + 관련 화면(관리자 로그인, 테이블 설정, 태블릿 자동 로그인) | US-A1, US-A4, US-C1 | 임동규 |
| **U2. Menu** | Menu 서비스(CRUD·노출 순서·고객 조회) + 관련 화면(메뉴 관리, 고객 메뉴 탐색) | US-A8, US-C2 | 이원종 |
| **U3. Order (+Cart)** | Order 서비스(생성/조회/상태/삭제) + 고객 장바구니(클라이언트)·주문 화면 + 관리자 주문 상세/상태/삭제 화면 | US-C3, US-C4, US-C5, US-A3, US-A5 | 최지영 |
| **U4. Session + Realtime** | TableSession 서비스(세션 라이프사이클·이력) + Realtime(pub-sub·SSE) + 관리자 대시보드·이력 화면 + 고객 실시간 반영 | US-A2, US-A6, US-A7, US-C6 | 이재환 |

> Realtime은 아키텍처상 독립 컴포넌트(Q2-A)지만, 병렬 편성에서는 이벤트 소비/전파가 밀접한 Session과 동일 유닛(U4)으로 묶는 초안. Q1에서 확정.

---

## Part B. 유닛 분해 결정을 위한 질문

각 질문의 `[Answer]:` 태그에 A/B/C… 중 하나를 적어주세요. 해당 없으면 마지막 옵션(Other)을 고르고 설명을 덧붙여주세요.

## Question 1 — 유닛 개수/경계 (Story Grouping · Team Alignment)
개발자 4명 병렬 편성을 위해 유닛을 어떻게 나눌까요?

A) **공통 기반(U0) + 도메인 4분할(U1~U4)** — 위 예비안 그대로. Realtime은 Session과 함께 U4. 4명이 U1~U4를 1:1로 담당, U0는 선행 공동 구축

B) **도메인 5분할** — Realtime을 별도 유닛(U5)으로 분리(5개 도메인 유닛 + U0). 4명이 분담(누군가 2개 담당 또는 Realtime을 공동)

C) **계층 분할** — 백엔드 / 고객 SPA / 관리자 SPA / 공통으로 나눠 담당

D) Other (please describe after [Answer]: tag below)

[Answer]:A

## Question 2 — 프론트엔드 화면의 유닛 귀속 (Story Grouping)
고객/관리자 SPA 화면을 어떻게 유닛에 배정할까요? (SPA는 앱 2개로 분리됨 — Q7-A)

A) **도메인 유닛에 수직 귀속** — 각 화면을 해당 도메인 유닛 담당자가 백엔드와 함께 개발(예: 메뉴 관리·고객 메뉴 화면 → U2 Menu). 앱 셸/공통 UI(라우팅·레이아웃·API 클라이언트)는 U0 공통에 포함

B) **프론트 전담 분리** — 고객 SPA·관리자 SPA를 별도 유닛으로 두고 프론트 담당자가 전 화면 개발(백엔드와 분리)

C) Other (please describe after [Answer]: tag below)

[Answer]:A

## Question 3 — 공통 기반(U0)의 범위와 선행 방식 (Dependencies · Technical)
U0(Platform/Common)을 어떻게 다룰까요? 병렬 개발의 결합 지점입니다.

A) **선행 스프린트 0 + 계약 고정** — U0(엔티티·DB·StoreContext·BaseRepository·이벤트 스키마·API 클라이언트 셸)를 먼저 완성/계약 확정한 뒤 U1~U4 병렬 착수. 가장 안전, 초기 직렬 구간 발생

B) **얇은 계약만 먼저, 이후 병렬** — 인터페이스/스키마 스텁만 합의하고 U0 구현과 U1~U4를 동시 진행(모킹 활용). 더 빠르나 계약 변경 리스크

C) Other (please describe after [Answer]: tag below)

[Answer]:B

## Question 4 — 유닛 간 계약 지점 명시 범위 (Dependencies · Business Domain)
유닛 간 결합 지점 중 이번 Units Generation에서 인터페이스 계약으로 **고정**할 대상은? (다중 선택 가능 — 해당 문자 나열)

A) Menu 조회(Order가 단가/유효성 확인) — Order↔Menu
B) Session 시작/현재 세션 조회(Order가 호출) — Order↔Session
C) 이력 이관(Session이 Order 데이터 수집) — Session↔Order
D) Realtime `publish(store_id, event)` + 이벤트 스키마(order.created/updated/deleted, session.closed 등)
E) StoreContext(인증→store_id 주입) — 전 유닛 공통
F) 위 전부(A~E 모두 계약 고정 권장)
G) Other (please describe after [Answer]: tag below)

[Answer]:F

## Question 5 — 코드 디렉터리 구조 (Code Organization · Greenfield)
워크스페이스 루트의 코드 조직 구조를 어떻게 할까요?

A) **backend/ + frontend-customer/ + frontend-admin/ 분리, 백엔드는 도메인 패키지** — 예: `backend/app/{common,auth,menu,order,session,realtime}/` 각 안에 router/service/repository/models, `frontend-customer/`, `frontend-admin/` 각각 Vue 앱. 유닛=백엔드 도메인 패키지 + 대응 프론트 화면

B) **레이어 우선 구조** — `backend/app/{routers,services,repositories,models}/` 아래에 도메인별 파일. 도메인보다 계층으로 먼저 분리

C) Other (please describe after [Answer]: tag below)

[Answer]:A

## Question 6 — 개발 착수 순서/우선순위 (Technical · Team)
병렬 개발 시 유닛 착수 우선순위(의존성 고려)를 어떻게 둘까요?

A) **U0 선행 → (U1 Auth, U2 Menu 우선) → U3 Order → U4 Session+Realtime** — Order는 Menu·Session 계약에 의존하므로 Auth/Menu가 계약을 먼저 제공. 의존성 순서 반영

B) **U0 선행 후 U1~U4 완전 동시 착수** — 모든 계약을 U0에서 고정했다는 전제로 4명이 동시 시작, 통합 시점에 결합

C) Other (please describe after [Answer]: tag below)

[Answer]:B

---

## Part C. 다음 단계
1. 위 질문에 모두 답변 → "완료" 알려주기
2. AI가 답변 분석(모호성/모순 검토), 필요 시 후속 질문
3. 승인 후 Part 2에서 `unit-of-work.md` / `unit-of-work-dependency.md` / `unit-of-work-story-map.md` 생성
4. 완료 메시지 및 승인 게이트 → CONSTRUCTION PHASE(유닛별 반복)
