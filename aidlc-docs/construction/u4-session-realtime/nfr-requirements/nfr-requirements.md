# U4 NFR Requirements — Session + Realtime

U4가 강제/지원하는 NFR. 출처 `requirements.md`(NFR-1~6), U0 NFR 기반 상속.

| NFR | 요구 | U4 책임 |
|---|---|---|
| **NFR-1 실시간** | 신규 주문/상태변경 2초 이내 SSE 반영 | **U4 핵심 책임** — 매장별 인메모리 pub-sub 브로커 + SSE 스트림(관리자/고객). 인메모리 fan-out으로 지연 최소화 |
| **NFR-3 멀티테넌시** | 매장 간 데이터 완전 격리 | 세션/이력 조회·변경은 `BaseRepository` store 스코프. SSE 구독은 `store_id`(+고객 `table_id`) 필터 격리 |
| **NFR-4 영속성** | SQLite 영속 저장 | `TableSession`·`SessionHistoryOrder`/`Line` SQLite 저장. 브로커 라이브 상태는 인메모리(휘발 허용) |
| **NFR-6 터치 UI** | 44×44px, 카드형, 시각 계층 | Admin DashboardView(그리드 카드)·HistoryView, U0 셸 스타일 상속 |

## 규모/성능
- 규모: 중간(다수 매장, 매장당 수십 테이블). 매장당 동시 SSE 구독자 = 관리자 소수 + 테이블 수십. 인메모리 fan-out으로 충분.
- 성능 목표(NFR-1): publish→구독자 수신 **2초 이내**. 인메모리 큐 전달로 통상 수십 ms.
- DB: 세션/이력 조회는 `store_id`·`table_id`·`closed_at` 인덱스로 스코프. 이력 페이지네이션(U0 `Page`).

## 가용성/신뢰성
- 로컬 실행 데모 — 고가용성 목표 없음. 서버 재시작 시 세션/이력(SQLite) 유지, SSE 구독은 클라이언트 자동 재연결 + REST 스냅샷 재동기화(Q7-C).
- publish 실패는 주 트랜잭션(세션 종료 등)에 영향 없음(best-effort, BR-U0-13/BR-U4-9).
- 세션 종료 이력 이관은 단일 트랜잭션 원자성(BR-U4-4).

## 보안
- SSE는 EventSource 헤더 제약으로 query param 토큰 검증(BR-U4-11). 유효 토큰만 구독 허용, store/table 격리.
- 관리자 전용 REST(`require_admin`): 대시보드/세션종료/이력.

## 확장(Extension) 준수
- Security / Resiliency / Property-Based Testing 확장 모두 **Disabled**(`aidlc-state.md`). 해당 강제 규칙 **N/A**.
