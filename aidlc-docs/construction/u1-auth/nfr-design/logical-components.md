# U1 Auth — 논리 컴포넌트 (Logical Components)

U1의 논리 컴포넌트와 예정 파일. 백엔드는 `backend/app/auth/` 3계층, 프론트는 각 SPA의 auth 화면. 인프라 컴포넌트(큐/캐시/서킷브레이커)는 불필요(N/A).

## 백엔드 (`backend/app/auth/`)
| 논리 컴포넌트 | 파일(예정) | 역할 | 관련 NFR |
|---|---|---|---|
| AuthRouter | `auth/router.py` | 로그인/테이블 설정 엔드포인트, `require_admin` 보호 | NFR-2 |
| AuthService | `auth/service.py` | 자격증명 검증·시도 제한 오케스트레이션·토큰 발급·테이블 생성/수정 | NFR-2, NFR-3 |
| TokenService | `auth/tokens.py` | JWT 인코딩(admin/table)·디코딩, `JwtTokenVerifier`(계약 E 구현) | NFR-2 |
| LoginAttemptTracker | `auth/attempts.py` | 인메모리 시도 카운터/잠금(임계 5, 15분 자동 해제) | NFR-2 |
| AdminUserRepository | `auth/repository.py` | `BaseRepository` 상속, `get_by_username(store_id, ...)` | NFR-3 |
| TableRepository | `auth/repository.py` | `BaseRepository` 상속, 테이블 조회/생성/수정(U0 Table) | NFR-3 |
| AdminUser Model | `auth/models.py` | `AdminUser` 엔티티(U0 Base 상속) | NFR-4 |
| Schemas | `auth/schemas.py` | 로그인 요청/응답·테이블 설정 요청/응답(pydantic) | - |

## U0 통합 지점 (채울 슬롯)
| 지점 | U1 작업 |
|---|---|
| `app/main.py` lifespan | `register_token_verifier(JwtTokenVerifier())` 호출 |
| `app/main.py` create_app | `include_router(auth.router)` |
| `common/database.py` init_db | `AdminUser` 모델 import 등록(create_all 대상) |
| `common/config.py` Settings | `lockout_minutes: int = 15` 신규 필드 추가(`TO_LOCKOUT_MINUTES`) |
| seed(`seeds/seed.py`) | 매장당 관리자 계정 1개 + 테이블 비밀번호 시드(Q1 FD=A) |

## 프론트엔드 논리 컴포넌트
| SPA | 컴포넌트 | 파일(예정) | 관련 NFR |
|---|---|---|---|
| admin | AdminLoginView | `frontend-admin/src/views/auth/AdminLoginView.vue` | NFR-2, NFR-5 |
| admin | TableManageView | `frontend-admin/src/views/auth/TableManageView.vue` | NFR-2, NFR-6 |
| customer | SetupView | `frontend-customer/src/views/auth/SetupView.vue` | NFR-5, NFR-6 |
| both | 라우트/가드 등록 | 각 `router/index.js` 슬롯 | NFR-5 |

- 토큰 저장/주입/401 처리·auth store는 U0 셸(`api/token`,`api/client`,`stores/auth`) 재사용 — 신규 구현 없음.

## 인프라 컴포넌트
- 큐·캐시·서킷브레이커·외부 세션 스토어: **N/A**(로컬 데모, 인증 부하 낮음). 시도 제한은 인메모리로 충분.
