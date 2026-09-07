# U3 Order (+ Cart) — Functional Design Plan

**유닛**: U3 Order+Cart · **담당**: 최지영 · **의존**: U0(기반), U2(메뉴 조회·계약 A), U4(세션 시작/조회·계약 B, Realtime publish·계약 D)
**스토리**: US-C3(장바구니), US-C4(주문 생성·확정), US-C5(현재 세션 주문 내역), US-A3(주문 상세·상태 변경), US-A5(주문 삭제)
**소유 계약**: 계약 C(이력 이관 — U4가 호출) 제공.

병렬 개발 원칙(Q6-B): U2 조회(A)·U4 세션(B)·Realtime(D)는 **고정 계약에 대한 모킹/스텁**으로 대체해 독립 진행하고, 통합 단계에서 실제 구현으로 교체한다.

---

## 산출물 계획 (체크박스)
- [x] `domain-entities.md` — `Order`, `OrderItem` 엔티티(스토어 격리, 세션 연동, 단가 스냅샷) + 상태/생명주기
- [x] `business-logic-model.md` — OrderService/OrderRepository 로직: 주문 생성 오케스트레이션(계약 A 검증 → 계약 B 세션 → 저장 → 계약 D publish), 현재 세션 조회, 상세, 상태 변경, 삭제·총액 재계산, 계약 C(이력 이관) 제공, 대시보드 스냅샷
- [x] `business-rules.md` — BR-U3-* (검증·총액 계산·상태 전이·격리·이벤트 발행·삭제 규칙)
- [x] `frontend-components.md` — 고객 SPA(장바구니 store·주문 확정·현재 세션 내역) + 관리자 SPA(주문 상세/상태/삭제) 컴포넌트·상태·API 연동

## 확정 전제 (U0 계약 기반, 재확인 불필요)
- 인증/격리: 모든 라우터는 U0 `get_current_store_context`/`require_table`/`require_admin` 주입, `store_id`는 토큰에서만(BR-U0-3).
- 영속/격리: `Order`/`OrderItem`은 U0 `Base` 상속 + `store_id` 컬럼, `BaseRepository` 스토어 스코프(NFR-3/4).
- 이벤트: U0 `events.py` 팩토리(`order_created/updated/status_changed/deleted`) + `realtime.publish()` best-effort(BR-U0-13).
- 장바구니: **클라이언트 측 로컬 저장**, 서버 전송은 주문 확정 시에만(US-C3, NFR-5) — 서버 엔티티 없음.

## 사전 기본값 (질문 아님 — 명백한 설계, 이의 없으면 채택)
- **단가 스냅샷**: 주문 항목에 `menu_id` + 주문 시점의 `menu_name`·`unit_price`를 **복사 저장**한다(메뉴 변경/삭제에도 주문·이력 보존, US-C4/A3에 단가 표시 필요).
- **총액**: `Order.total = Σ(item.unit_price × item.qty)`, 서버에서 재계산(클라이언트 값 신뢰 안 함).
- **첫 주문 세션 시작**: 주문 생성 시 계약 B `start_or_get_active_session`으로 활성 세션 확보 후 `session_id` 연결(US-C4).

---

## 설계 질문 (인터랙티브로 수집 → 답변 기록)

### Q1. 주문번호(order_no) 체계
- [Answer]: A
- A. 매장별 일련번호(store-scoped, 1·2·3…) — 관리자가 인지하기 쉬움 (추천)
- B. 세션별 일련번호(세션 내 1·2·3…)
- C. 날짜기반(YYYYMMDD-#### 매장별 일자 리셋)
- D. 전역 UUID/난수

### Q2. 주문 삭제(US-A5) 방식
- [Answer]: B
- A. 하드 삭제(레코드 완전 제거) — 단순
- B. 소프트 삭제(`deleted_at`/`is_deleted` 플래그, 목록·총액·이력에서 제외) — 감사 추적 보존 (추천)

### Q3. 계약 C(이력 이관) 메커니즘 — 세션 종료 시 현재 목록에서 주문이 빠지는 방식
- [Answer]: A
- A. `Order.archived` 플래그 — U4가 `collect_active_session_orders`로 수집 후 `mark_orders_archived`로 플래그 set, `list_current_session_orders`는 `archived=false`만 반환(주문 레코드는 U3에 잔존, 이력 스냅샷은 U4가 보관) (추천)
- B. 주문 레코드를 U4 이력 테이블로 이동/삭제(현재 테이블에서 제거)

### Q4. `get_dashboard_snapshot`(테이블별 총액·최신 주문 n) 귀속
- [Answer]: A
- A. U3 Order가 조회 메서드로 제공, U4 대시보드(US-A2)가 소비 — `component-methods.md`가 Order에 배치 (추천)
- B. U4가 소유, U3는 원시 주문 조회 계약만 제공

### Q5. 주문 상태(대기중/준비중/완료) 전이 규칙
- [Answer]: A
- A. 자유 전이 — 관리자가 세 상태 중 임의로 변경 가능(직권 운영, 되돌리기 포함) (추천)
- B. 순방향 전용(대기중→준비중→완료, 역행 불가)

> 각 [Answer]: 에 A/B/C/D 중 하나를 기입하거나, 인터랙티브 질문에 응답하면 여기 기록 후 산출물 생성으로 진행합니다.
