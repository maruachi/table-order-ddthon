# U1 Auth — Code Generation Summary

**유닛**: U1 Auth (인증) · **담당**: 임동규 · **의존**: U0 (Platform/Common)
**스토리**: US-A1(관리자 로그인·JWT 16h·시도 제한), US-A4(테이블 초기 설정), US-C1(태블릿 자동 로그인)
**제공 계약**: **E** — `JwtTokenVerifier`를 U0 `register_token_verifier`에 등록.

## 생성/수정 파일

### 백엔드 (`backend/app/auth/`) — 신규
| 파일 | 역할 |
|---|---|
| `models.py` | `AdminUser`(id, store_id FK, username, password_hash, created_at, `unique(store_id, username)`). U0 `Base` 상속. |
| `schemas.py` | `AdminLoginRequest`, `TableLoginRequest`, `TokenResponse`(+`StoreInfo`), `TableCreateRequest`, `TableUpdateRequest`, `TableResponse`(password_hash 미노출). 공백 검증(BR-U1-15). |
| `repository.py` | `AdminUserRepository`(+`get_by_username`), `TableRepository`(+`get_by_number`) — U0 `BaseRepository` 상속(store 스코프). `StoreResolver`(로그인 시 store_code→Store, pre-auth). |
| `tokens.py` | `issue_admin`(16h)/`issue_table`(720h) JWT HS256, `JwtTokenVerifier.verify`→`StoreContext`(서명/만료 실패 시 `AuthError`). 계약 E. |
| `attempts.py` | 인메모리 `LoginAttemptTracker`(임계 `max_login_attempts`, 잠금 `lockout_minutes`, 시간 기반 lazy 자동해제) + 프로세스 공유 `tracker` 싱글턴. 관리자만. |
| `service.py` | `AuthService`: `admin_login`(잠금검사·bcrypt·실패기록/성공리셋·토큰), `table_login`(시도제한 미적용), `list_tables`/`create_table`/`update_table`(commit, 유일성·해싱). 균일 실패 메시지(BR-U1-8). |
| `router.py` | `POST /api/auth/admin/login`, `POST /api/auth/table/login`, `GET/POST /api/admin/tables`, `PUT /api/admin/tables/{id}`(`require_admin`). |

### 백엔드 U0 통합(in-place 수정)
| 파일 | 변경 |
|---|---|
| `app/main.py` | lifespan에서 `register_token_verifier(JwtTokenVerifier())`; create_app에서 `include_router(auth_router)`. |
| `app/common/database.py` | `init_db`에 `from app.auth import models` import(create_all 등록). |
| `app/common/config.py` | `lockout_minutes: int = 15`(`TO_LOCKOUT_MINUTES`) 신규 필드. |
| `seeds/seed.py` | 매장별 관리자 계정 1개(`admin`/`admin1234`) idempotent 시드. |

### 백엔드 테스트 (`backend/tests/auth/test_auth.py`) — 신규
관리자 로그인 성공/실패·균일 오류, 잠금·자동해제·성공 리셋, JWT 발급/검증(서명·만료), 테이블 토큰 클레임, 교차 매장 차단, 테이블 로그인 성공/실패, 테이블 생성/조회·중복(ValidationError)·수정(번호/비번)·미존재(NotFoundError)·중복 수정. **16 테스트**.

### 프론트엔드 — 신규/수정
| 파일 | 역할 |
|---|---|
| `frontend-admin/src/api/auth.js` | adminLogin/listTables/createTable/updateTable. |
| `frontend-admin/src/views/auth/AdminLoginView.vue` | 관리자 로그인 화면(data-testid). 잠금/실패 메시지 구분. |
| `frontend-admin/src/views/auth/TableManageView.vue` | 테이블 생성/수정·목록(비번 미노출, 실패 시 목록 미변경). |
| `frontend-admin/src/router/index.js` | `/login`(public)·`/tables`(requiresAuth) 등록. |
| `frontend-customer/src/api/auth.js` | tableLogin. |
| `frontend-customer/src/views/auth/SetupView.vue` | 태블릿 최초 설정(터치 친화 NFR-6). 실패 시 토큰 미저장(BR-U1-14). |
| `frontend-customer/src/router/index.js` | `/setup`(public) 등록 + 토큰 보유 시 `/menu` 자동 로그인 가드. |

> 토큰 저장/주입/401 처리·auth store는 U0 셸 재사용 — 신규 구현 없음.

## 통합 지점(계약 E)
- 앱 부팅 시 `JwtTokenVerifier` 등록 → U0 `get_current_store_context`가 전 유닛 라우터에서 `StoreContext` 주입 활성화.
- U2~U4는 U1 발급 토큰을 U0 의존성(`require_admin`/`require_table`)으로 간접 소비.

## 토큰 규약
- 관리자: `{sub:username, store_id, role:"admin", iat, exp(+16h)}`.
- 테이블: `{sub:"table:{id}", store_id, role:"table", table_id, iat, exp(+720h)}`.

## 확정 결정
Q1=A(관리자 시드 전용) · Q2=A(인메모리 트래커) · Q3=A(잠금 15분 자동해제) · Q4=A(관리자만 시도제한) · Q5=B(테이블 생성/수정) · Q6=A(테이블 JWT) · Q7=A(무상태 로그아웃) · lockout_minutes=15.

## 검증 결과
- **pytest** `backend/tests/` → **21 passed**(U0 5 + U1 16).
- **앱 부팅**: verifier 등록 확인 — 미토큰 `GET /api/admin/tables` → 401, 시드 후 관리자 로그인 200 → 토큰으로 200(6 tables), 테이블 로그인 200.
- **프론트 빌드**: `frontend-admin` / `frontend-customer` `npm run build` 성공.
> 통합/전체 테스트는 이후 Build & Test 단계.
