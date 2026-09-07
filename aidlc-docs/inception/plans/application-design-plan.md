# Application Design Plan — 테이블오더 서비스

**단계 목적**: 고수준 컴포넌트 식별 + 서비스 계층 설계. (상세 비즈니스 로직은 이후 Construction의 Functional Design에서 유닛별로 진행)

- 출처: `aidlc-docs/inception/requirements/requirements.md`, `aidlc-docs/inception/user-stories/stories.md`, `aidlc-docs/inception/user-stories/personas.md`
- 기술 스택(확정): FastAPI(Python) 백엔드, Vue SPA(고객/관리자), SQLite, 로컬 실행, 멀티테넌트(매장 식별자 격리)

---

## Part A. 설계 산출물 계획 (Mandatory Artifacts)

아래 산출물을 `aidlc-docs/inception/application-design/`에 생성한다.

- [x] `components.md` — 컴포넌트 정의, 책임, 인터페이스
- [x] `component-methods.md` — 컴포넌트별 메서드 시그니처, 입/출력 타입, 고수준 목적 (상세 비즈니스 규칙은 Functional Design)
- [x] `services.md` — 서비스 정의, 책임, 오케스트레이션 패턴
- [x] `component-dependency.md` — 의존 관계 매트릭스, 통신 패턴, 데이터 흐름
- [x] `application-design.md` — 위 문서 통합본
- [x] 설계 완전성/일관성 검증

### 예비 컴포넌트 후보 (질문 응답 후 확정)
도메인/에픽 기준 초안:
- **인증 (Auth)**: 관리자 로그인/JWT(US-A1), 테이블 태블릿 초기 설정/자동 로그인(US-A4, US-C1)
- **메뉴 (Menu)**: 메뉴/카테고리 CRUD·노출 순서(US-A8), 고객 메뉴 조회(US-C2)
- **주문 (Order)**: 주문 생성(US-C4), 현재 세션 주문 조회(US-C5), 주문 상세/상태 변경(US-A3), 주문 삭제(US-A5). 장바구니는 클라이언트 측(서버 없음).
- **세션 (TableSession)**: 세션 시작(첫 주문)/종료(이용 완료)·이력 이관(US-A6), 과거 이력 조회(US-A7)
- **실시간 (Realtime/SSE)**: 대시보드 실시간 업데이트(US-A2), 상태 전파(US-A3, US-C6)
- **매장/테이블 (Store/Table)**: 멀티테넌트 매장·테이블 엔티티, 초기 데이터

---

## Part B. 설계 결정을 위한 질문

각 질문의 `[Answer]:` 태그에 A/B/C… 중 하나를 적어주세요. 해당 없으면 마지막 옵션(Other)을 선택하고 설명을 덧붙여주세요.

## Question 1
컴포넌트 경계(모듈 구분)를 어떻게 나눌까요? (4명 병렬 개발을 위한 유닛 분해의 기반이 됩니다)

A) 도메인 5분할 — Auth / Menu / Order / TableSession(+Realtime) / Store·Table 공통. Realtime(SSE)은 Order·Session이 발행하는 이벤트를 구독하는 얇은 계층으로 Session 쪽에 포함

B) 도메인 4분할 (개발자 수 정렬) — Auth / Menu / Order+Cart / Realtime+Session. Store·Table 엔티티는 각 도메인이 공유하는 공통 모듈로 분리

C) 계층형 분할 — 프론트(고객 SPA) / 프론트(관리자 SPA) / 백엔드 API / 데이터 계층

D) Other (please describe after [Answer]: tag below)

[Answer]:B

## Question 2
Realtime(SSE) 기능을 독립 컴포넌트로 둘까요, 아니면 각 도메인 서비스에 내장할까요?

A) 독립 컴포넌트 — 중앙 이벤트 브로커/퍼블리셔(예: 매장별 인메모리 pub-sub)를 두고, Order/Session 서비스가 이벤트를 발행하면 SSE 컴포넌트가 관리자/고객 커넥션에 브로드캐스트

B) 각 도메인 내장 — Order/Session 서비스가 직접 SSE 스트림을 관리 (별도 브로커 없음)

C) Other (please describe after [Answer]: tag below)

[Answer]:A

## Question 3
백엔드 아키텍처 스타일(계층 구조)을 어떻게 할까요?

A) 3계층 (Router/API → Service → Repository) — FastAPI 라우터가 서비스 계층을 호출하고, 서비스가 리포지토리를 통해 SQLite 접근. 명확한 관심사 분리, 병렬 개발에 유리

B) 2계층 (Router → Service, ORM 직접 사용) — 리포지토리 계층 생략, 서비스에서 ORM/쿼리 직접 사용. 더 간결

C) Other (please describe after [Answer]: tag below)

[Answer]:A

## Question 4
데이터 접근 방식은 무엇으로 할까요? (SQLite)

A) SQLAlchemy ORM (+ 선택적으로 Alembic 마이그레이션)

B) SQLModel (FastAPI 친화적, Pydantic+SQLAlchemy 통합)

C) 원시 SQL (sqlite3/aiosqlite + 직접 쿼리)

D) Other (please describe after [Answer]: tag below)

[Answer]:A

## Question 5
멀티테넌시(매장 격리)를 서비스/컴포넌트 계층에서 어떻게 강제할까요?

A) 인증 컨텍스트 주입 — JWT/세션에서 store_id를 추출해 요청 컨텍스트에 넣고, 모든 서비스 메서드가 store_id를 필수 인자로 받아 쿼리에 항상 포함(공통 의존성/미들웨어로 강제)

B) 리포지토리 계층에서 자동 필터 — 리포지토리가 현재 store_id를 자동 주입하여 모든 쿼리에 WHERE store_id 적용

C) Other (please describe after [Answer]: tag below)

[Answer]:A

## Question 6
고객용 테이블 인증(태블릿 자동 로그인)의 요청 인증 방식은?

A) 테이블 세션 토큰 — 초기 설정/로그인 성공 시 테이블 전용 토큰(JWT 또는 불투명 토큰) 발급, 이후 고객 요청은 이 토큰으로 인증(store_id·table 식별 포함)

B) 매 요청 자격증명 — 저장된 store_id/table/password를 요청마다 전송해 검증 (별도 토큰 없음)

C) Other (please describe after [Answer]: tag below)

[Answer]:A

## Question 7
프론트엔드(Vue SPA) 구성을 어떻게 할까요?

A) 앱 2개 분리 — 고객용 SPA와 관리자용 SPA를 별도 Vue 앱/빌드로 구성(라우팅·의존성 독립, 병렬 개발 용이)

B) 단일 SPA + 라우트 분리 — 하나의 Vue 앱 안에서 /customer, /admin 라우트로 분리

C) Other (please describe after [Answer]: tag below)

[Answer]:A

## Question 8
컴포넌트 간 통신에서 서비스 계층 오케스트레이션 경계는? (예: 주문 생성 시 세션 시작 트리거)

A) 서비스 간 직접 호출 — OrderService가 주문 생성 시 TableSessionService를 직접 호출해 세션 시작/이벤트 발행을 오케스트레이션 (동기, 단순)

B) 이벤트 기반 — OrderService는 이벤트만 발행하고, SessionService/RealtimeService가 구독해 반응 (느슨한 결합, 복잡도↑)

C) Other (please describe after [Answer]: tag below)

[Answer]:A

---

## Part C. 다음 단계
1. 위 질문에 모두 답변 → "완료" 알려주기
2. AI가 답변 분석(모호성/모순 검토), 필요 시 후속 질문
3. 승인된 결정에 따라 Part A 산출물 생성
4. 완료 메시지 및 승인 게이트
