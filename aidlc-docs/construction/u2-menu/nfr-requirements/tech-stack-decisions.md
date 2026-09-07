# U2 Menu — Tech Stack Decisions

**결정(Q3:A)**: U0에서 고정한 공통 스택을 그대로 사용하며 **U2 전용 추가 의존성은 없다.**

## 상속 스택 (U0 확정 — 변경 없음)

| 항목 | 사용 | U2 적용 |
|---|---|---|
| 언어/런타임 | Python 3.11 | 그대로 |
| 웹 프레임워크 | FastAPI | Menu 라우터(고객/관리자) |
| ORM/DB | SQLAlchemy 동기 + SQLite | Category/Menu 모델, `BaseRepository` 상속 |
| 스키마 | `create_all` + seeds | `init_db`에 Menu/Category 모델 import 등록 |
| 검증 | **Pydantic / pydantic-settings** | MenuInput 스키마 검증(필수 필드·가격·이미지 URL) |
| 인증 | JWT/테이블 토큰(U1 발급) | `require_admin` / `require_table` 가드 소비 |
| 테스트 | pytest, httpx | U2 유닛/통합 테스트 |
| 프론트 | Vue 3 + Vite + Vue Router + Pinia + Axios | 고객 MenuView, 관리자 MenuManageView |

## U2 구현 세부 (신규 라이브러리 아님, 기존 도구 활용)
- **이미지 URL 형식 검증**(BR-U2-5, Q7:B): Pydantic의 `HttpUrl`(또는 `AnyHttpUrl`) 타입으로 http(s) 형식 검증. 별도 라이브러리 불필요.
- **가격 검증**(BR-U2-2, Q6:B): Pydantic `int` + `ge=0` 제약.
- **필수/선택 필드**(Q7:B): Pydantic 필드 Optional 여부로 표현.
- **재정렬**(BR-U2-7): 표준 SQLAlchemy update, 추가 도구 없음.

## backend/requirements.txt 변경
- **추가 없음.** U0가 이미 포함한 fastapi/sqlalchemy/pydantic/pydantic-settings/pytest/httpx로 충분.

## frontend 변경
- **추가 없음.** U0 셸의 Vue Router/Pinia/Axios로 화면·상태·API 처리.
