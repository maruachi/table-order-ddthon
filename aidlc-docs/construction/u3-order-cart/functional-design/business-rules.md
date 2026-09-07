# U3 비즈니스 규칙 (Business Rules) — Order (+ Cart)

`OrderService`가 강제하는 규칙. U0 공통 규칙(BR-U0-*: 격리·예외·이벤트 best-effort)을 상속한다. 위반 시 U0 예외 계층(`ValidationError`/`NotFoundError`/`ForbiddenError`/`AuthError`)을 사용.

## 검증 규칙
- **BR-U3-1** 주문에는 최소 1개 항목이 있어야 한다. 빈 `items` → `ValidationError`(US-C4 빈 장바구니 방지).
- **BR-U3-2** 각 항목 `qty`는 1 이상의 정수. 위반 → `ValidationError`.
- **BR-U3-3** 모든 `menu_id`는 계약 A 조회 결과에 존재하고 `available=true`여야 한다. 단가·메뉴명은 **계약 A 응답을 신뢰원본으로 스냅샷** 저장하며, 클라이언트가 보낸 가격/이름은 무시한다.
- **BR-U3-10** `status`는 `{pending, preparing, done}` 중 하나여야 한다(그 외 → `ValidationError`). **자유 전이**: 이전 상태와 무관하게 변경 가능(Q5).

## 세션·오케스트레이션 규칙
- **BR-U3-4** 주문 생성 시 계약 B `start_or_get_active_session`으로 활성 세션을 확보하고 그 `session_id`에 주문을 연결한다. 테이블의 **첫 주문이 세션을 시작**한다(US-C4/도메인).
- **BR-U3-4b** 세션 확보(계약 B)가 실패하면 주문을 저장하지 않고 오류를 반환한다(세션 없는 주문 금지).
- **BR-U3-14** 계약 C(`collect_active_session_orders`/`mark_orders_archived`)는 U4 `close_session`이 오케스트레이션한다. U3는 멱등적으로 동작해야 한다(이미 archived면 재마킹 무시).

## 금액·번호 규칙
- **BR-U3-5** 라인 금액 = `unit_price(스냅샷) × qty`; 주문 총액 = Σ 라인 금액. 모든 계산은 서버에서 정수 원화 단위로 수행.
- **BR-U3-6** `order_no`는 매장별 단조 증가 일련번호이며 `unique(store_id, order_no)`. 채번은 주문 저장 트랜잭션 내에서 수행(동시성: per-store 최대값+1, 유니크 제약으로 충돌 시 재시도).
- **BR-U3-12** 주문 삭제 후 테이블 총액은 **활성 주문(archived=false, is_deleted=false)** 합으로 재계산한다.

## 조회·격리 규칙
- **BR-U3-7** `list_current_session_orders`는 **현재 활성 세션 + archived=false + is_deleted=false** 주문만, 주문 시각 순으로 반환한다. 이전/이용완료 세션 주문은 절대 노출하지 않는다(NFR-3 세션 격리).
- **BR-U3-8** 접근 권한: `role=table`은 자신의 매장·활성 세션 주문만 조회(주문 생성·현재 내역). `role=admin`은 자신의 매장 전체 주문 조회·상태변경·삭제·대시보드. 교차 매장 접근은 `store_id` 스코프로 원천 차단(BaseRepository, BR-U0-2).
- **BR-U3-13** 대시보드 스냅샷은 매장 내 활성 주문을 테이블별로 집계(총액·최신 n건·건수). `store_id` 격리 준수.

## 삭제 규칙
- **BR-U3-9** 주문 삭제는 **소프트 삭제**(`is_deleted=true`, `deleted_at` 기록). 삭제된 주문은 조회(`get_order`/목록)·총액·대시보드·이력 집계에서 제외되나 감사 목적상 레코드는 보존(US-A5, Q2). `delete_order`는 `require_admin`.

## 이벤트 발행 규칙 (계약 D)
- **BR-U3-11** 상태를 바꾸는 연산 후 대응 이벤트를 발행한다: 생성→`order.created`, 상태변경→`order.status_changed`, 삭제→`order.deleted`. 발행은 **best-effort**(U0 `realtime.publish`) — 실패해도 주 트랜잭션을 롤백하지 않는다(BR-U0-13). 이벤트 페이로드는 `store_id` 스코프 정보만 포함(타 매장 유출 금지).
- 이벤트는 U0 `events.py` 팩토리로만 생성(스키마 단일 출처, 계약 D). 전파(<2s, NFR-1)는 U4 Realtime가 담당.

## 권한 요약

| 연산 | 권한 | 관련 규칙 |
|---|---|---|
| create_order | role=table | BR-U3-1~6, 11 |
| list_current_session_orders | role=table | BR-U3-7 |
| get_order | table(자기 세션)/admin | BR-U3-8, 9 |
| update_order_status | role=admin | BR-U3-10, 11 |
| delete_order | role=admin | BR-U3-9, 12, 11 |
| get_dashboard_snapshot | role=admin | BR-U3-13 |
| 계약 C(collect/archive) | 내부(U4 호출) | BR-U3-14 |
