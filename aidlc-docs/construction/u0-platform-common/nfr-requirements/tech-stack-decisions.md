# U0 Tech Stack Decisions

대화형 승인으로 확정된 기반 스택. 4인 병렬 개발의 공통 전제.

| 항목 | 결정 | 근거 |
|---|---|---|
| 언어/런타임 | **Python 3.11** | 표준 venv, 보편·안정 |
| 패키지 관리 | **pip + venv + requirements.txt** | 진입장벽 최소, 워크샵 적합 |
| 웹 프레임워크 | **FastAPI** | (기존 확정) 자동 문서·의존성 주입·SSE 지원 |
| ORM/DB 접근 | **SQLAlchemy 동기(sync)** + sqlite3 | 단순·디버깅 용이, 로컬 데모 적합 |
| DB | **SQLite** (`table_order.db`) | (기존 확정) 파일 기반, 영속 |
| PK 전략 | **정수 자동증가**, Store는 `code` 별도 | 가독성·단순성 |
| 스키마 관리 | **`metadata.create_all()` + seeds** | Alembic 미사용(로컬 데모) |
| 인증 | **JWT(관리자)/테이블 토큰**, bcrypt(passlib) | (기존 확정) NFR-2 |
| 실시간 | **SSE** + 매장별 인메모리 pub-sub | (기존 확정) NFR-1 |
| 프론트 | **Vue 3 + Vite + Vue Router + Pinia + Axios**, 앱 2개 | (기존 확정) Q7-A |
| 테스트 | **pytest**(백엔드), Vitest(프론트, 선택) | 표준 |
| CORS | 고객/관리자 SPA origin 허용 | 로컬 개발 |

## 주요 라이브러리(backend/requirements.txt 예정)
- fastapi, uvicorn[standard], sqlalchemy, pydantic, pydantic-settings
- python-jose[cryptography] (JWT), passlib[bcrypt] (해싱)
- pytest, httpx (테스트)
