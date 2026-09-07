# U1 Auth — Tech Stack Decisions

U1은 U0 기반 스택을 상속하며 **신규 백엔드 의존성이 없다**. 아래는 상속 항목 확정과 U1 고유 파라미터 결정.

## 상속 스택 (U0에서 확정 — 재결정 없음)
| 영역 | 선택 | 출처 |
|---|---|---|
| 웹 프레임워크 | FastAPI 0.111 | U0 `requirements.txt` |
| JWT | `python-jose[cryptography]==3.3.0`, HS256 | U0 deps + `config.jwt_algorithm` |
| 비밀번호 해시 | `passlib[bcrypt]==1.7.4` + `bcrypt==4.0.1`(핀) | U0 `security.py` 유틸 |
| ORM/DB | SQLAlchemy 2.0 sync + SQLite | U0 `database.py` |
| 설정 | pydantic-settings(`TO_` prefix) | U0 `config.py` |
| 예외 | `AppError` 계층(`AuthError`/`ForbiddenError`/`ValidationError`/`NotFoundError`) | U0 `exceptions.py` |
| 프론트 | Vue3 + Vite + Pinia, 토큰 localStorage | U0 셸 |

## U1 고유 결정
| 항목 | 결정 | 근거 |
|---|---|---|
| AdminUser 저장 | 신규 SQLAlchemy 모델(U0 `Base` 상속), `unique(store_id, username)` | 관리자 계정 영속(NFR-4) |
| 관리자 계정 프로비저닝 | 시드 전용(seed에 매장당 1개 추가), CRUD API 없음 | Q1(FD)=A |
| 로그인 시도 추적 | **인메모리** dict, 키 `(store_id, username)` | Q2=A, 비영속 허용 |
| 잠금 임계/지속 | `max_login_attempts=5`(기존 config) + **`LOCKOUT_MINUTES=15`(신규 config 추가)** | Q1=A |
| 시도 제한 적용 | 관리자 로그인만 | Q4(FD)=A |
| 토큰 형식 | 관리자·테이블 모두 JWT(role 클레임 구분) | Q6(FD)=A |
| 토큰 무효화 | 서버 무상태(클라이언트 삭제만) | Q7(FD)=A |
| 성능 목표 | 명시적 SLA 없음, bcrypt 기본 cost | Q3=A |

## config 추가 항목 (U0 `config.py` Settings 확장)
```text
lockout_minutes: int = 15   # TO_LOCKOUT_MINUTES — 시도 초과 잠금 지속(분), Q1=A
```
> 기존 `max_login_attempts=5`, `jwt_*`, `*_token_expire_hours`는 이미 존재. `lockout_minutes`만 신규 추가(U0 config에 U1이 1줄 추가 — 공통 설정 관례).

## 신규 의존성
- **없음** — U0 `requirements.txt`로 충분(python-jose·passlib·bcrypt 포함).
