# U3 NFR Requirements — Order (+ Cart)

요구사항 NFR-1~6을 U3(Order+Cart) 관점으로 구체화한다. 기반은 U0가 제공하며, U3는 이를 **소비/준수**한다.

| NFR | 요구 | U3 책임 / 목표 |
|---|---|---|
| **NFR-1 실시간** | 신규 주문 2초 이내 SSE 반영 | 주문 생성/상태변경/삭제 시 **즉시** `realtime.publish`(계약 D) 호출. 발행은 커밋 후 동기 호출·best-effort. 전파(<2s)는 U4 브로커가 담당하나, U3는 지연 없이 발행할 책임. |
| **NFR-3 멀티테넌시** | 매장 간 데이터 완전 격리 | 모든 Order/OrderItem 쿼리는 `store_id` 스코프(U0 `BaseRepository`). `store_id`는 토큰(StoreContext)에서만. 이벤트 페이로드는 자기 매장 정보만. |
| **NFR-4 영속성** | SQLite 영속 저장 | Order/OrderItem은 SQLAlchemy 모델로 영속. 소프트 삭제·archived 플래그로 이력 보존(레코드 삭제 안 함). |
| **NFR-5 클라이언트 영속** | 장바구니 로컬 저장·새로고침 유지 | 장바구니는 **서버 미저장**, 브라우저 `localStorage`(`cartStore`). 서버 전송은 주문 확정 시에만. |
| **NFR-6 터치 UI** | 44×44px, 카드형 계층 | 주문/장바구니/상세 화면 버튼 ≥44×44px, 카드형 레이아웃(U0 셸 스타일 준수). |

## 성능 요구
- **주문 생성 응답**: 로컬 단일 SQLite + 동기 접근 기준 p95 < 300ms(계약 A 조회·계약 B 세션·저장·이벤트 포함). 워크샵 규모(매장당 수십 테이블)에서 충분.
- **현재 세션 조회 / 대시보드 스냅샷**: 인덱스 활용으로 < 200ms. 페이지네이션(U0 `PageParams`, 기본 limit 50)으로 응답 크기 제한.
- **N+1 회피**: 주문 상세·목록 조회 시 `OrderItem`을 `selectinload`로 즉시 로드.

## 동시성 / 정합성
- **order_no 채번**: 매장별 `max(order_no)+1`. `unique(store_id, order_no)` 제약으로 동시 주문 충돌을 방어하고, 충돌(IntegrityError) 시 **1회 재채번 재시도**. 로컬 SQLite 단일 라이터 특성상 실질 경합 낮음.
- **총액 재계산**: 삭제/조회 시점 활성 주문 합으로 계산(캐시 없음) — 항상 정합.
- **트랜잭션 경계**: 주문 생성(Order+Items)은 단일 트랜잭션. 이벤트 발행은 커밋 이후(발행 실패가 주문에 영향 없음).

## 신뢰성 / 오류 처리
- 계약 A(메뉴 없음/미노출) → `ValidationError`(422). 계약 B(세션 확보 실패) → 주문 미저장, 5xx/명시 오류.
- 이벤트 발행 실패는 삼켜서 로깅(U0 best-effort, BR-U0-13). 주 데이터 정합 우선.
- 표준 오류 응답(U0 `ErrorResponse`)로 일관.

## 가용성
- 로컬 실행 데모 — 고가용성/이중화 목표 없음. 재시작 시 SQLite 데이터 유지.

## 확장(Extension) 준수 요약
| 확장 | 상태 | 판정 |
|---|---|---|
| Security Baseline | Disabled | **N/A** (미적용). 단, 인증/격리는 기능 요구(NFR-2/3)로 U0/U1 통해 충족. |
| Resiliency Baseline | Disabled | **N/A**. best-effort 이벤트 발행은 기능 규칙(BR-U0-13)으로 이미 반영. |
| Property-Based Testing | Disabled | **N/A**. 표준 pytest 단위/통합 테스트 사용. |

> 확장 3종 모두 비활성 → 강제 blocking 규칙 없음. 위 판정은 비활성으로 인한 N/A이며 결함 아님.
