# U1 Auth — Code Generation Plan

**유닛**: U1. Auth (인증) · **담당**: 임동규 · **의존**: U0 (Platform/Common)
**스토리**: US-A1(관리자 로그인·JWT 16h·시도 제한), US-A4(테이블 초기 설정 — 생성/수정), US-C1(태블릿 자동 로그인·테이블 세션 토큰)
**제공 계약**: **E** (`JwtTokenVerifier` → U0 `register_token_verifier` 등록)

**워크스페이스 루트**: `/Users/dgyim/works/aidlc-workshop-day1/table-order-ddthon` (Greenfield 멀티유닛 모놀리식).
**단일 진실 소스**: 이 계획서. 코드=워크스페이스 루트, 요약 문서=`aidlc-docs/construction/u1-auth/code/`.

## 유닛 컨텍스트
- **의존**: U0만. `security`(StoreContext·verifier 레지스트리·role guards·bcrypt), `database`(Base·get_db·SessionLocal), `models`(Store·Table), `repository`(BaseRepository), `exceptions`(AppError 계층), `config`(jwt/만료/시도), `schemas`.
- **엔티티 소유**: `AdminUser`(신규). `Table`(U0 소유)에 대해 생성/수정 수행(Q5=B).
- **다른 유닛 직접 호출**: 없음. U2~U4는 U1 발급 토큰을 U0 의존성으로 간접 소비.
- **API 프리픽스**: `/api` (프론트 baseURL=host, 401→admin `/login`·customer `/setup`).
- **커밋 규약**: 리포지토리는 `flush`, 서비스가 쓰기 후 `db.commit()` (U0 seed 패턴 일치).

## 확정 결정(요약)
Q1=A(관리자 시드 전용) · Q2=A(인메모리 트래커) · Q3=A(잠금 15분 자동해제) · Q4=A(관리자만 시도제한) · Q5=B(테이블 생성/수정) · Q6=A(테이블 JWT, store_code+번호+비밀번호) · Q7=A(무상태 로그아웃) · lockout_minutes=15.

---

## 생성 단계

- [x] **Step 1. 프로젝트 구조 셋업** — `backend/app/auth/__init__.py`, `backend/tests/auth/__init__.py`, 프론트 `frontend-admin/src/views/auth/`, `frontend-customer/src/views/auth/` 디렉터리.
- [x] **Step 2. 도메인 모델** — `backend/app/auth/models.py`: `AdminUser`(id, store_id FK, username, password_hash, created_at, `unique(store_id, username)`). U0 `Base` 상속. (NFR-4) 〔US-A1〕
- [x] **Step 3. 스키마** — `backend/app/auth/schemas.py`: `AdminLoginRequest`, `TableLoginRequest`, `TokenResponse`, `TableCreateRequest`, `TableUpdateRequest`, `TableResponse`(password_hash 제외). (BR-U1-12) 〔US-A1/A4/C1〕
- [x] **Step 4. 리포지토리** — `backend/app/auth/repository.py`: `AdminUserRepository`(BaseRepository 상속 + `get_by_username`), `TableRepository`(BaseRepository 상속 + `get_by_number`). store 스코프 자동(NFR-3). 〔US-A1/A4/C1〕
- [x] **Step 5. 토큰 서비스/검증자** — `backend/app/auth/tokens.py`: `issue_admin(store_id, username)`, `issue_table(store_id, table_id)`(python-jose HS256, exp 16h/720h), `JwtTokenVerifier.verify(token)->StoreContext`(서명/만료 검증→AuthError). (계약 E, BR-U1-9/10/10a) 〔US-A1/C1〕
- [x] **Step 6. 시도 트래커** — `backend/app/auth/attempts.py`: 인메모리 `LoginAttemptTracker`(check/record_failure/reset, 임계 `max_login_attempts`, 잠금 `lockout_minutes`, 시간 기반 lazy 자동해제). 관리자만. (BR-U1-3~6a, Q2/Q3/Q4) 〔US-A1〕
- [x] **Step 7. 서비스 계층** — `backend/app/auth/service.py`: `admin_login`(store 해석·잠금검사·bcrypt검증·실패기록/성공리셋·토큰발급), `table_login`(store/table 해석·검증·토큰발급, 시도제한 미적용), `list_tables`/`create_table`/`update_table`(require_admin, 유일성·해싱, commit). 균일 실패 메시지(BR-U1-8). 〔US-A1/A4/C1〕
- [x] **Step 8. API 계층** — `backend/app/auth/router.py`: `POST /api/auth/admin/login`, `POST /api/auth/table/login`, `GET /api/admin/tables`(require_admin), `POST /api/admin/tables`(require_admin), `PUT /api/admin/tables/{table_id}`(require_admin). U0 예외→핸들러 위임. 〔US-A1/A4/C1〕
- [x] **Step 9. 설정 추가** — `backend/app/common/config.py`(U0)에 `lockout_minutes: int = 15` 필드 in-place 추가(`TO_LOCKOUT_MINUTES`). (Q1=A)
- [x] **Step 10. U0 통합(슬롯 채움, in-place 수정)** — `backend/app/main.py`: lifespan에서 `register_token_verifier(JwtTokenVerifier())`, create_app에서 `include_router(auth_router)`. `backend/app/common/database.py`: `init_db`에 `from app.auth import models` import 등록. (계약 E)
- [x] **Step 11. 시드 확장(in-place)** — `backend/seeds/seed.py`: 매장별 관리자 계정 1개 생성(예: username `admin`, pw `admin1234`) idempotent 추가. (Q1=A) 〔US-A1〕
- [x] **Step 12. 백엔드 유닛 테스트** — `backend/tests/auth/test_auth.py`: 관리자 로그인 성공/실패, 시도제한 잠금·자동해제, JWT 발급·검증(만료/서명오류), store 격리(교차매장 차단), 테이블 로그인 성공/실패, 테이블 생성/수정·번호 유일성(ValidationError). (실행은 Build & Test 단계)
- [x] **Step 13. 프론트 관리자** — `frontend-admin/src/api/auth.js`(admin_login/list/create/update 호출), `views/auth/AdminLoginView.vue`, `views/auth/TableManageView.vue`(data-testid 부여), `router/index.js` 라우트 등록(`/login` public, `/tables` requiresAuth). auth store `login()` 연동. 〔US-A1/A4〕
- [x] **Step 14. 프론트 고객** — `frontend-customer/src/api/auth.js`(table_login), `views/auth/SetupView.vue`(data-testid), `router/index.js` `/setup` 라우트 + 자동 로그인 가드 연계(토큰 있으면 `/menu`). 실패 시 토큰 미저장(BR-U1-14). 〔US-C1〕
- [x] **Step 15. 문서/요약** — `aidlc-docs/construction/u1-auth/code/code-summary.md`(생성 파일·계약·통합 지점·검증 방법), 루트 `README.md` U1 실행/시드 노트 반영.

## 스토리 트레이스
- US-A1 → Step 2,3,4,5,6,7,8,11,12,13
- US-A4 → Step 3,4,7,8,12,13
- US-C1 → Step 3,4,5,7,8,12,14
- 계약 E → Step 5,10

## 검증(생성 단계 내 자체 확인)
- pytest(`backend/tests/auth/`) 통과.
- 앱 부팅 시 verifier 등록 → 보호 엔드포인트가 401(미토큰)/정상(토큰) 동작.
- 프론트 빌드(`npm run build`) 성공.
> 통합/전체 테스트 실행은 이후 Build & Test 단계.
