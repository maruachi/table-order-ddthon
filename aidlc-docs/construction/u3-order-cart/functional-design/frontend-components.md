# U3 프론트엔드 컴포넌트 (Frontend Components) — Order (+ Cart)

U0 앱 셸(라우팅·레이아웃·`api/client`(토큰 주입·401)·`api/token`·auth 스토어) 위에 U3 화면을 **수직 귀속**한다(Q2-A). 고객 SPA(`frontend-customer`)와 관리자 SPA(`frontend-admin`)에 각각 배치.

프레임워크: Vue 3 + Vite + Pinia(스토어) + Vue Router. 터치 친화(버튼 ≥44×44px, NFR-6).

---

## A. 고객 SPA (frontend-customer)

### 스토어: `cartStore` (Pinia, US-C3)
- **상태**: `items: [{menu_id, menu_name, unit_price, qty}]`.
- **게터**: `count`(총 수량), `total`(Σ unit_price×qty), `isEmpty`.
- **액션**: `add(menu)`, `increment(menu_id)`, `decrement(menu_id)`(0이면 제거), `remove(menu_id)`, `clear()`.
- **영속(NFR-5)**: `localStorage`에 저장(키: `cart:{store}:{table}`), 새로고침에도 유지. 서버 전송은 주문 확정 시에만.

### 뷰: `CartView` (US-C3)
- **역할**: 장바구니 항목 목록·수량 증감·삭제·비우기·실시간 총액.
- **Props/상태**: `cartStore` 구독.
- **상호작용**: +/− 버튼 → `cartStore.increment/decrement`; 항목 삭제; "장바구니 비우기". 총액 실시간 재계산 표시.
- **네비게이션**: "주문하기" → `OrderConfirmView`(빈 장바구니면 비활성, BR-U3-1 대응).

### 뷰: `OrderConfirmView` (US-C4)
- **역할**: 최종 확인 후 주문 확정.
- **상호작용**: "주문 확정" → `orderApi.create({items: cartStore.items.map(menu_id,qty)})`.
  - 성공: 주문번호 표시, `cartStore.clear()`, **5초 확인 화면 후 메뉴 화면 자동 리다이렉트**(US-C4).
  - 실패: 에러 메시지 표시, 장바구니 **유지**(clear 안 함).
- **검증**: 빈 장바구니 시 확정 비활성/안내.
- **상태**: `submitting`, `result{order_no,total}`, `error`.

### 뷰: `CurrentOrdersView` (US-C5)
- **역할**: 현재 세션 주문 내역(시간순), 상태 표시.
- **데이터**: `orderApi.listCurrent({offset,limit})` → 페이지네이션/무한 스크롤.
- **표시**: 주문번호·주문 시각·메뉴/수량·금액·상태 배지(대기중/준비중/완료).
- **실시간(US-C6, Could)**: 활성화 시 U0 `api/sse`(customer 구독)로 `order.status_changed` 수신 → 해당 주문 상태 갱신. 미구현 시 진입/새로고침 기준 표시.

### API 클라이언트: `api/orderApi.js`
| 메서드 | 호출 | 백엔드 |
|---|---|---|
| `create({items})` | 주문 확정 | `POST /orders` |
| `listCurrent(page)` | 현재 세션 내역 | `GET /orders/current` |
| `get(id)` | 주문 상세 | `GET /orders/{id}` |

### 라우트(customer router 슬롯)
- `/cart` → CartView, `/order/confirm` → OrderConfirmView, `/orders` → CurrentOrdersView. (모두 table 토큰 가드.)

---

## B. 관리자 SPA (frontend-admin)

> 실시간 대시보드 그리드(US-A2)·SSE 구독 자체는 U4 소유. U3는 **주문 상세/상태/삭제 상호작용**과 대시보드 **초기 스냅샷 소비**를 제공.

### 뷰/컴포넌트: `OrderDetailModal` (US-A3)
- **역할**: 대시보드 주문 카드 클릭 시 상세(메뉴명/수량/단가/총액) 열람 + 상태 변경.
- **데이터**: `orderAdminApi.get(order_id)`.
- **상호작용**: 상태 셀렉트(대기중/준비중/완료) → `orderAdminApi.updateStatus(id, status)`. 성공 시 카드/그리드 반영(SSE `order.status_changed`가 타 화면 전파).

### 컴포넌트: `DeleteOrderAction` (US-A5)
- **역할**: 주문 삭제(직권).
- **상호작용**: 삭제 클릭 → **확인 팝업** → 확인 시 `orderAdminApi.delete(id)`.
  - 성공: 성공 피드백, 반환 `TableTotals`로 테이블 총액 갱신(SSE `order.deleted` 전파).
  - 실패: 실패 피드백, 주문 유지.

### 대시보드 초기 스냅샷 소비 (US-A2 협력, Q4)
- U4 `dashboardStore`가 진입 시 `orderAdminApi.dashboardSnapshot({table_filter?})`(→ `GET /orders/dashboard`) 호출로 테이블 카드 초기 상태(총액·최신 주문 n·건수)를 로드하고, 이후 U4 SSE 증분으로 병합. **엔드포인트/집계는 U3 제공, 화면·SSE 병합은 U4.**

### API 클라이언트: `api/orderAdminApi.js`
| 메서드 | 호출 | 백엔드 |
|---|---|---|
| `get(id)` | 주문 상세 | `GET /orders/{id}` |
| `updateStatus(id, status)` | 상태 변경 | `PATCH /orders/{id}/status` |
| `delete(id)` | 주문 삭제 | `DELETE /orders/{id}` |
| `dashboardSnapshot(params)` | 대시보드 초기 스냅샷 | `GET /orders/dashboard` |

---

## 폼 검증 규칙 (프론트)
- 장바구니: `qty ≥ 1`, 빈 장바구니 시 주문 버튼 비활성(BR-U3-1/2와 정합).
- 상태 변경: 셀렉트 옵션은 3개 값으로 제한(BR-U3-10).
- 삭제: 확인 팝업 필수(US-A5).
- 서버 오류(422/404/403)는 U0 `ErrorResponse`(`error`,`detail`)를 표준 토스트/인라인으로 표시(`api/client` 401 자동 처리).

## 상태 관리 요약
- 고객: `cartStore`(로컬 영속) + 서버 조회는 `CurrentOrdersView` 로컬 상태.
- 관리자: 주문 상세/상태/삭제는 U4 `dashboardStore`와 상호작용(스냅샷 소비 + 액션 후 갱신).
