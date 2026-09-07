# U0 NFR Requirements — Platform/Common

U0는 전 유닛의 NFR 기반을 제공한다. 요구사항(`requirements.md`)의 NFR-1~6 중 U0가 강제/지원하는 항목.

| NFR | 요구 | U0 책임 |
|---|---|---|
| **NFR-3 멀티테넌시** | 매장 간 데이터 완전 격리 | StoreContext + BaseRepository store_id 강제(단일 지점). **U0 핵심 책임** |
| **NFR-4 영속성** | SQLite 영속 저장 | 동기 SQLAlchemy 엔진·세션·create_all 제공 |
| **NFR-2 인증 보안(기반)** | JWT/토큰, bcrypt | StoreContext 주입 프레임 + bcrypt 유틸(검증 로직은 U1) |
| **NFR-1 실시간(기반)** | 신규 주문 2초 이내 SSE | 이벤트 스키마 + Publisher 계약 제공(브로커는 U4) |
| **NFR-5 클라이언트 영속(기반)** | 로컬 저장, 새로고침 유지 | 프론트 토큰 저장 유틸 + API 인터셉터 |
| **NFR-6 터치 UI(기반)** | 44×44px, 카드형 | 레이아웃 셸/스타일 기준 제공(화면은 유닛별) |

## 규모/성능
- 규모: 중간(다수 매장, 매장당 수십 테이블) — SQLite 단일 파일 + 동기 접근으로 충분(로컬/워크샵).
- 성능: 실시간 전파 2초 이내(NFR-1)는 U4 브로커 책임. U0 DB 접근은 인덱스(store_id, code) 제공.

## 가용성/신뢰성
- 로컬 실행 데모 — 고가용성 목표 없음. 재시작 시 SQLite 데이터 유지, 인메모리 구독은 재구독.
- publish 실패는 주 트랜잭션에 영향 없음(best-effort, BR-U0-13).

## 확장(Extension) 준수
- Security/Resiliency/Property-Based Testing 확장은 모두 **Disabled**(`aidlc-state.md`). 해당 강제 규칙 N/A.
