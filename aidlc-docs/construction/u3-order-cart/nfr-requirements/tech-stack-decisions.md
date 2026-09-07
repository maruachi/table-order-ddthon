# U3 Tech Stack Decisions — Order (+ Cart)

U3는 U0에서 고정한 기반 스택을 **그대로 상속**한다. 신규 프레임워크/라이브러리 도입 없음.

## 상속 (U0 고정)
| 항목 | 결정 |
|---|---|
| 언어/런타임 | Python 3.11 |
| 웹 프레임워크 | FastAPI (라우터·의존성 주입·pydantic) |
| ORM/DB | SQLAlchemy 동기 + SQLite (`table_order.db`) |
| PK 전략 | 정수 자동증가 |
| 스키마 | `metadata.create_all()` (U3 모델을 `database.init_db` import에 등록) |
| 인증/격리 | U0 `StoreContext` + `require_table`/`require_admin` 의존성 |
| 실시간 | U0 `events.py` 팩토리 + `realtime.publish` (계약 D) |
| 프론트 | Vue 3 + Vite + Pinia + Vue Router + Axios (U0 앱 셸) |
| 테스트 | pytest + httpx(TestClient) |

## U3 특화 구현 선택 (신규 기술 아님, 구현 방침)
| 항목 | 선택 | 근거 |
|---|---|---|
| 단가/메뉴명 저장 | **스냅샷 복사**(OrderItem에 unit_price·menu_name) | 메뉴 변경/삭제에도 주문·이력 정합 보존 |
| 주문 삭제 | **소프트 삭제**(is_deleted/deleted_at) | 감사 추적, 총액 재계산 안전 |
| 이력 이관 | **archived 플래그**(계약 C) | 레코드 잔존 + 현재 목록 제외, U3↔U4 결합 최소화 |
| order_no | **매장별 일련번호** + `unique(store_id, order_no)` + 충돌 시 재시도 | 가독성, 정합성 |
| 인덱스 | `(store_id, session_id)`, `(store_id, table_id)`, `(store_id, order_no)` unique | 현재 세션 조회·대시보드·채번 성능 |
| 계약 A/B 주입 | `Protocol` 인터페이스 + 통합 시 실제 구현 주입, 단위 테스트는 모킹 | 병렬 개발(Q6-B) |
| 로딩 전략 | `selectinload(Order.items)` | N+1 회피 |

## 라이브러리 추가
- **없음** — U0 `requirements.txt`(fastapi, sqlalchemy, pydantic, pytest, httpx 등)로 충분. U3는 신규 의존성 도입하지 않음.

## 확장
- Security / Resiliency / Property-Based Testing: 모두 Disabled → 추가 도구/라이브러리 도입 없음.
