# U4 Session + Realtime — Functional Design Plan

**유닛**: U4 Session + Realtime (담당: 이재환)
**스토리**: US-A2(실시간 대시보드·SSE), US-A6(세션 종료·이력 이관), US-A7(과거 이력), US-C6(고객 상태 실시간 — 포함 확정)
**의존/계약**: U0(계약 D publish·E StoreContext·BaseRepository), U3(계약 C 이력 이관 — 상호 협력). 계약 B(세션 시작/조회)는 U4가 제공.
**참조**: `unit-of-work.md`(U4 정의), `unit-of-work-dependency.md`(계약 A~E), `stories.md`(US-A2/A6/A7/C6), U0 코드(`common/{events,realtime,security,repository}.py`).

## 산출물 계획 (Step 6에서 생성)
- [x] `domain-entities.md` — `TableSession`(+ 이력 스냅샷 엔티티) 필드/제약/ER, U0 `Store`/`Table` 관계
- [x] `business-logic-model.md` — 세션 라이프사이클(시작/조회/종료·이력 이관), 계약 B/C/D 상호작용, 대시보드 스냅샷 로직, 브로커/SSE 개념 모델(기술중립)
- [x] `business-rules.md` — 세션 유일성·store 격리·이력 자립성·total_amount 소유권·best-effort 발행 규칙(BR-U4-*)
- [x] `frontend-components.md` — Admin DashboardView/HistoryView(+세션 종료), Customer 실시간 반영 헬퍼/스토어, props/state/상호작용/API 연동 지점

## 확정 대상 설계 결정 (계약 시그니처 동결 포함)
- **계약 B (U4 제공)**: `start_or_get_active_session(store_id, table_id) -> session_id`, `get_active_session(store_id, table_id) -> session|None`
- **계약 C (U3 제공, U4 소비)**: `OrderHistoryProvider` 프로토콜 + `register_order_provider()` 레지스트리(U0 `register_publisher` 패턴). `collect_active_session_orders(store_id, session_id) -> [orders]`, `mark_orders_archived(store_id, session_id)`. 병렬 개발 중 NoOp/Mock.
- **계약 D (U4 구현)**: `InMemoryBroker`가 `RealtimePublisher` 구현, `register_publisher`로 등록. 세션 종료 시 `session_closed` 발행.

---

## 질문 (Step 3 — `[Answer]:` 태그에 답변 기입)

### Q1. 세션-테이블 활성 유일성 강제 위치
테이블당 `active` 세션은 하나만 존재해야 한다(US-A6: 종료 후 새 세션 시작). 어떻게 강제할까?
- A) DB 부분 유니크 인덱스(`unique(store_id, table_id) where status='active'`) — DB 레벨 보장(SQLite 부분 인덱스 지원)
- B) 서비스 레벨 가드만(조회 후 없으면 생성, 트랜잭션 내) — 단순, 로컬 단일 프로세스 전제
- C) 둘 다(A + B 방어적)
[Answer]: C

### Q2. 과거 이력(US-A7) 저장 형태
세션 종료 시 계약 C로 수집한 주문을 US-A7 조회가 U3에 런타임 의존하지 않도록 자립 저장한다. 형태는?
- A) 별도 테이블 `SessionHistoryOrder`(정규화: 주문/메뉴라인 스냅샷 행) — 쿼리·날짜 필터 용이
- B) 세션 레코드에 주문 스냅샷을 JSON 컬럼으로 denormalize — 단순, 조회 시 통째 반환
- C) 세션 요약(총액·주문 수·closed_at)만 저장하고 상세는 U3 조회(런타임 의존 허용)
[Answer]: A

### Q3. 이력 조회 반환 상세 수준
US-A7은 "주문번호, 시각, 메뉴, 총액, 이용완료 시각"을 시간 역순 표시. 상세 메뉴 라인(메뉴명/수량/단가)까지 스냅샷에 포함할까?
- A) 포함(주문별 메뉴 라인까지 스냅샷) — 정산·상세 확인 완전 지원
- B) 주문 단위 요약(주문번호/시각/총액)만, 메뉴 상세는 생략
[Answer]: A

### Q4. 대시보드(US-A2) 초기 스냅샷 데이터 범위
대시보드 진입 시 초기 상태. SSE 라이브 갱신 전 "테이블별 총액 + 최신 주문 n개 미리보기"를 어떻게 채울까?
- A) U4가 active 세션 목록 제공 + 테이블별 현재 주문/총액은 계약(U3)로 조회(스탠드얼론은 mock) — 정확한 초기 상태
- B) U4는 active 세션 목록만 제공, 주문 미리보기는 SSE 이벤트 누적으로만 채움(진입 시점엔 비어있고 이후 채워짐)
- C) A + 미리보기 개수 n 파라미터화
[Answer]: A

### Q5. "최신 주문 n개 미리보기"의 n 기본값
US-A2 카드에 표시할 테이블별 최신 주문 미리보기 개수 기본값은?
- A) 3
- B) 5
- C) 파라미터(쿼리)로 조정, 기본 3
[Answer]: A

### Q6. US-A7 날짜 필터 기준 필드
과거 이력 날짜 필터의 기준 시각은?
- A) `closed_at`(이용 완료 시각) — "이용완료 시각" 표시와 일관
- B) 세션 `started_at`(이용 시작 시각)
[Answer]: A

### Q7. SSE 재연결·keepalive 정책 (NFR-1 관련)
- A) 서버 주기적 keepalive 코멘트(예: 15초) + 클라이언트는 브라우저 EventSource 기본 자동재연결에 위임 — 단순, MVP 적합
- B) 서버가 `Last-Event-ID`/이벤트 id로 재전송 지원(재연결 시 놓친 이벤트 복구) — 구현 복잡
- C) A + 재연결 시 클라이언트가 REST 스냅샷 재조회로 상태 재동기화
[Answer]: C

### Q8. 고객 실시간(US-C6) 스트림 분리 방식
고객 태블릿은 자기 테이블 주문 상태만 필요하다. 스트림을 어떻게 줄까?
- A) 별도 엔드포인트 `/realtime/table/stream` — 서버가 `StoreContext.table_id`로 해당 테이블 이벤트만 필터해 전송
- B) 관리자와 동일 매장 스트림을 주고 클라이언트가 table_id로 필터 — 서버 단순하나 타 테이블 이벤트가 태블릿에 노출(격리 약화)
[Answer]: A

### Q9. 세션 종료 시 "진행 중 주문이 없는" 빈 세션 처리
활성 세션은 있으나 주문이 0건일 때 종료 요청 시?
- A) 정상 종료(이력엔 주문 0건 세션 기록) 
- B) 종료하되 이력에 남기지 않음(주문 없는 세션은 통계 제외)
- C) 활성 세션이 없거나 주문 0이면 종료 대상 없음으로 안내(no-op)
[Answer]: A
