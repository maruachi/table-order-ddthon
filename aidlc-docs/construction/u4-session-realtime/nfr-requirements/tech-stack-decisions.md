# U4 Tech Stack Decisions — Session + Realtime

U0 확정 스택을 상속하며, U4 고유 실시간 구현 선택을 추가한다.

| 항목 | 결정 | 근거 |
|---|---|---|
| 웹 프레임워크 | **FastAPI**(상속) | SSE `StreamingResponse`·의존성 주입 |
| ORM/DB | **SQLAlchemy 동기 + SQLite**(상속) | 세션/이력 영속(NFR-4) |
| 실시간 전송 | **SSE**(`text/event-stream`, `StreamingResponse`) | (확정) 단방향 서버→클라이언트, EventSource 호환 |
| 브로커 | **매장별 인메모리 pub-sub**, 구독자당 `asyncio.Queue` | NFR-1 저지연 fan-out, 단일 프로세스 로컬 |
| 스레드→루프 핸드오프 | **`loop.call_soon_threadsafe`** | 동기 요청 핸들러(스레드풀)의 `publish()`를 asyncio 큐로 안전 전달 |
| 계약 C 디커플링 | **Provider 프로토콜 + 레지스트리**(U0 `register_publisher` 패턴) | U3 런타임 의존 제거, 병렬 개발/모킹 |
| 인증(SSE) | **query param 토큰 → `verify_token()`** | EventSource 헤더 불가(BR-U4-11) |
| 프론트 | **Vue 3 + Vite + Pinia + Axios**(상속), EventSource(SSE) | Admin 대시보드/이력, Customer 실시간 |
| 테스트 | **pytest + httpx**(상속) | 세션/브로커 유닛·통합 |

## U4 신규 코드 모듈
- `backend/app/session/`(models, repository, service, provider, router, schemas)
- `backend/app/realtime/`(broker, router)
- `backend/app/common/security.py`에 **additive** `verify_token()` 추가(계약 E 확장, 유일한 공유 파일 편집)
- `frontend-admin/src/views/{DashboardView,HistoryView}.vue`, `src/api/session.js`
- `frontend-customer/src/api/sse.js`, 실시간 스토어/컴포저블

## 추가 의존성
- 없음 — U0 `requirements.txt`로 충분(FastAPI `StreamingResponse`·`asyncio` 표준 라이브러리).
