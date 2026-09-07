# U0 Platform/Common — Code Generation Summary

**Greenfield · 생성 완료 · 검증됨.** 애플리케이션 코드는 워크스페이스 루트, 문서는 여기.

## 생성된 백엔드 파일 (`backend/`)
| 파일 | 역할 | 계약/NFR |
|---|---|---|
| `requirements.txt` | 의존성(FastAPI, SQLAlchemy, passlib+bcrypt==4.0.1 핀, jose, pytest) | - |
| `pytest.ini`, `.gitignore` | 테스트/무시 설정 | - |
| `app/main.py` | FastAPI 조립: CORS, 예외 핸들러, lifespan `init_db`, `/health`, 라우터/통합 등록 자리 | - |
| `app/common/config.py` | pydantic-settings(DB URL, JWT, CORS, 토큰 만료) | NFR-2 |
| `app/common/database.py` | 동기 엔진·SessionLocal·Base·get_db·init_db(create_all) | NFR-4 |
| `app/common/models.py` | `Store`, `Table` 엔티티(정수 PK, store 격리) | NFR-3/4 |
| `app/common/schemas.py` | ErrorResponse·PageParams·Page[T] | - |
| `app/common/exceptions.py` | AppError 계층 + 핸들러 → 표준 ErrorResponse | BR-U0-10 |
| `app/common/security.py` | StoreContext·TokenVerifier 레지스트리·get_current_store_context·require_admin/table·bcrypt 헬퍼 | **계약 E**, NFR-2/3 |
| `app/common/events.py` | 이벤트 스키마·타입 상수·팩토리 | **계약 D** |
| `app/common/realtime.py` | RealtimePublisher 프로토콜·레지스트리·NoOp·best-effort publish | **계약 D**, BR-U0-13 |
| `app/common/repository.py` | BaseRepository(store_id 강제 스코프) | **NFR-3**, BR-U0-2 |
| `seeds/seed.py` | 샘플 매장/테이블 시드(idempotent) | - |
| `tests/test_common.py` | 격리·컨텍스트·예외·해시 테스트 (5 passed) | - |

## 생성된 프론트엔드 셸
- `frontend-customer/` — Vue3+Vite, api/client(토큰 주입·401 처리)·token(localStorage)·router(가드)·CustomerLayout(하단 탭)·auth 스토어. **빌드 성공**.
- `frontend-admin/` — 동일 셸 + `api/sse.js`(EventSource)·AdminLayout(사이드바). **빌드 성공**.

## 검증 결과
- `pytest`: **5 passed** (tenant isolation, cross-tenant fail-closed, password roundtrip, admin guard, missing-verifier).
- `python -m seeds.seed`: 매장 2개(demo-cafe/demo-bistro) + 테이블 10개 생성.
- 앱 부팅: `/health` 200, `/openapi.json` 200.
- 프론트: `npm run build` 양쪽 성공(각 32 모듈).

## 병렬 개발을 위한 통합 지점(도메인 유닛이 채울 자리)
- `app/main.py` lifespan: U1 `register_token_verifier(...)`, U4 `register_publisher(...)`.
- `app/main.py` create_app: 각 유닛 `include_router(...)`.
- `database.py init_db`: 각 유닛 모델 import 등록.
- 프론트 `router/index.js`: 각 유닛 라우트 주석 슬롯.

## 계약 상태 (Sprint 0)
- **E StoreContext**: 구조·의존성·레지스트리 확정(U1이 verifier 구현).
- **D 이벤트/publish**: 스키마·프로토콜 확정(U4가 브로커 구현).
- **A/B/C**(Menu조회·Session·이력): 인터페이스는 소비/제공 유닛(U2/U4/U3)의 Functional Design에서 시그니처 확정 예정 — 본 문서 `unit-of-work-dependency.md`에 개략 정의됨.
