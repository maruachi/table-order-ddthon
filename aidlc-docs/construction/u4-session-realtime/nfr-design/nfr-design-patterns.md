# U4 NFR Design Patterns — Session + Realtime

## 실시간 패턴 (NFR-1)
- **매장별 인메모리 pub-sub 브로커**: `store_id → set[Subscriber]`. 각 구독자는 `asyncio.Queue`. `publish(store_id, event)`는 해당 매장 구독자 큐에 fan-out. 인메모리 전달로 2초 이내 충족(통상 수십 ms).
- **스레드→이벤트루프 핸드오프**: 동기 요청 핸들러(FastAPI 스레드풀)에서 호출되는 `publish()`는, 앱 시작 시 캡처한 메인 이벤트 루프에 `loop.call_soon_threadsafe(queue.put_nowait, event)`로 안전하게 넣는다. asyncio 객체를 스레드에서 직접 만지지 않는다.
- **SSE 스트림(async generator)**: 구독자 큐에서 이벤트를 `await`로 꺼내 `data: {json}\n\n` 프레임 전송. 주기적 keepalive 코멘트(`: ping\n\n`, ~15s)로 유휴 연결 유지(BR-U4-14). 클라이언트 disconnect 시 `finally`에서 구독 해제(리소스 정리).
- **큐 백프레셔**: 구독자 큐에 `maxsize` 설정, 초과 시 가장 오래된 이벤트 드롭(라이브 뷰는 최신 우선, 이력은 DB로 보정). 느린 구독자가 전체를 막지 않게 함.
- **재동기화(Q7-C)**: 재연결 시 클라이언트가 REST 스냅샷(대시보드/현재 세션)을 재조회 → 놓친 이벤트 보정. 서버 재전송 버퍼 불필요(단순).

## 멀티테넌시 격리 패턴 (NFR-3)
- **Scoped Repository 상속**: `SessionRepository(BaseRepository)` — 모든 세션/이력 쿼리 `store_id` 강제(U0 단일 강제 지점 재사용).
- **SSE 구독 격리**: 구독은 검증된 `StoreContext.store_id`로만. 관리자=매장 전체, 고객=`store_id`+`table_id` 필터(BR-U4-10). 클라이언트 입력 store_id 불신(BR-U0-3).

## 인증 패턴 (SSE)
- **Query-token 검증**: `verify_token(token) -> StoreContext`(U0 security.py additive). SSE 라우터가 `token` query를 검증 후 구독. 실패 시 401/연결 거부(BR-U4-11).

## 디커플링 패턴 (계약 C)
- **Provider 인터페이스 + 레지스트리**: `OrderHistoryProvider` 프로토콜 + `register_order_provider()` + NoOp 기본값(U0 `register_publisher` 패턴 미러링). U3 미구현 시 Mock, 통합 시 실제 등록. U4→U3 런타임 의존 제거(의존 역전).

## 영속성 패턴 (NFR-4)
- **Session-per-request**: U0 `get_db` 상속.
- **이력 스냅샷 자립**: 종료 시점 주문/라인 스냅샷 저장 → 이후 U3/메뉴 변경과 무관하게 US-A7 조회(BR-U4-7).
- **종료 원자성**: 스냅샷 저장·상태 전이·아카이브 마킹 단일 트랜잭션(BR-U4-4).

## 오류 처리 패턴
- **Typed AppError → handler**(U0 상속): `NotFoundError`(활성 세션 없음 등) 등 raise → 표준 `ErrorResponse`.
- **Best-effort 발행**: publish 예외 격리(U0 `publish` 헬퍼)로 주 트랜잭션 보호(BR-U4-9).

## 관측(경량)
- 표준 로깅(구독/해제, publish 실패 warning). 로컬 데모 범위 — 별도 APM 없음.
