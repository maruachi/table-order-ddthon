# 서비스 정의 및 오케스트레이션 (Services)

3계층 아키텍처(Q3-A)에서 **서비스 계층**은 도메인 비즈니스 흐름을 오케스트레이션한다. 라우터는 요청 검증/컨텍스트 주입만, 리포지토리는 데이터 접근만 담당하고, 도메인 간 조율은 서비스에서 이뤄진다. 서비스 간 조율은 **직접 호출(동기)**(Q8-A) 방식이며, 실시간 전파만 Realtime 컴포넌트를 통한 발행/구독(Q2-A)으로 분리한다.

---

## 서비스 목록

| 서비스 | 소속 컴포넌트 | 책임 요약 |
|---|---|---|
| `AuthService` | Auth | 관리자/테이블 인증, 토큰 발급·검증, 테이블 설정 |
| `MenuService` | Menu | 메뉴/카테고리 CRUD·정렬, 고객 조회 |
| `OrderService` | Order | 주문 생성/조회/상태/삭제, 세션 시작 트리거, 이벤트 발행 |
| `TableSessionService` | TableSession | 세션 시작/종료·이력 이관, 과거 이력 조회 |
| `RealtimeService` | Realtime | 매장별 pub-sub 브로커, SSE 스트림 |
| `StoreService` (Common) | Platform | 매장/테이블 조회, 인증 컨텍스트 제공 |

모든 도메인 서비스는 `StoreContext`(store_id 포함)를 받아 멀티테넌시를 강제(Q5-A)한다.

---

## 핵심 오케스트레이션 시나리오

### S1. 주문 생성 (US-C4) — 세션 시작 + 실시간 전파
직접 호출로 여러 서비스를 조율하는 대표 흐름(Q8-A).

```
Customer SPA → POST /orders
  Router: verify_table_token → StoreContext(table)
  OrderService.create_order(ctx, items):
    1) MenuService로 menu 단가/유효성 확인, 총액 계산
    2) TableSessionService.start_or_get_active_session(ctx, table_id)  # 첫 주문이면 세션 생성
    3) OrderRepository.add(order with session_id, status=대기중)
    4) RealtimeService.publish(store_id, order.created)
    5) return Order{order_no, total, session_id}
```
- 트랜잭션 경계/실패 롤백 규칙은 Functional Design에서 확정(주문 실패 시 클라이언트 장바구니 유지 — FR-C4).

### S2. 주문 상태 변경 (US-A3)
```
Admin SPA → PATCH /orders/{id}/status
  OrderService.update_order_status(ctx, id, status):
    1) OrderRepository.update(status)
    2) RealtimeService.publish(store_id, order.status_changed)  # 대시보드 및 고객(US-C6) 전파
```

### S3. 주문 삭제 (US-A5)
```
Admin SPA → DELETE /orders/{id}
  OrderService.delete_order(ctx, id):
    1) OrderRepository.delete(id)
    2) 테이블 총액 재계산
    3) RealtimeService.publish(store_id, order.deleted)
```

### S4. 세션 종료 / 이용 완료 (US-A6) — 핵심 도메인 로직
```
Admin SPA → POST /tables/{id}/close-session
  TableSessionService.close_session(ctx, table_id):
    1) 활성 세션의 주문 조회
    2) OrderHistory로 이관(session_id + completed_at)
    3) 현재 주문/총액 리셋, 세션 상태=closed
    4) RealtimeService.publish(store_id, session.closed)  # 대시보드 & 고객 US-C5 목록 비움
```

### S5. 실시간 대시보드 구독 (US-A2)
```
Admin SPA → GET /realtime/admin (SSE)
  RealtimeService.subscribe_admin(ctx):
    - 초기: OrderService.get_dashboard_snapshot(ctx) 전송
    - 이후: 매장 브로커 이벤트를 스트림으로 push (2초 이내, NFR-1)
```

### S6. 인증 흐름
- **관리자**: `AuthService.admin_login` → JWT(16h) → 이후 요청은 `verify_admin_token`으로 `StoreContext(role=admin)` 주입.
- **테이블**: 관리자가 `setup_table` → 태블릿 `table_login` → 테이블 토큰 → 이후 `verify_table_token`으로 `StoreContext(role=table, table_id)` 주입.

---

## 오케스트레이션 경계 원칙
- **동기 직접 호출**(Q8-A): OrderService가 MenuService·TableSessionService를 직접 호출. 단순·명확, 로컬 SQLite/단일 프로세스에 적합.
- **실시간 전파만 pub-sub 분리**(Q2-A): 도메인 서비스는 상태 변경 후 `RealtimeService.publish`만 호출하고, SSE 커넥션 관리/브로드캐스트는 Realtime이 전담 → 도메인 로직과 전송 계층 분리.
- **의존 방향**: 상위 도메인(Order) → 하위/피어(Menu, TableSession, Realtime) → Platform. 순환 의존은 피하되, Order↔TableSession은 "주문 이관" 협력을 위한 제한적 상호 참조 허용(경계는 Functional Design에서 확정).
- **멀티테넌시**: 모든 서비스 메서드가 `store_id` 컨텍스트를 요구, 리포지토리가 쿼리에 강제 적용(NFR-3).
