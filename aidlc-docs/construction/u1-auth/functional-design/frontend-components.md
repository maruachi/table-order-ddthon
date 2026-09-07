# U1 Auth — 프론트엔드 컴포넌트 (Frontend Components)

U1 화면은 U0 앱 셸에 **수직 귀속**된다. 관리자 로그인·테이블 설정은 `frontend-admin`, 태블릿 자동 로그인은 `frontend-customer`. 모두 U0가 제공한 `api/client`(토큰 주입·401 처리), `api/token`(localStorage), `stores/auth`(pinia), `router`(가드)를 재사용한다.

## 재사용하는 U0 셸 요소
- `api/token.js`: `getToken/setToken/clearToken` (admin=`to_admin_token`, customer=`to_customer_token` 키).
- `stores/auth.js`: `login(token)` / `logout()` / `isAuthenticated`.
- `api/client.js`: Authorization 헤더 자동 주입, 401 시 토큰 클리어 처리.
- `router/index.js`: `beforeEach` 가드 — 미인증 시 admin→`/login`, customer→`/setup` 리다이렉트(슬롯 존재).

---

## frontend-admin

### AdminLoginView (`views/auth/AdminLoginView.vue`) — US-A1
매장 관리자 로그인 화면.

- **State/Form**: `storeCode`, `username`, `password`, `loading`, `errorMessage`.
- **폼 검증(BR-U1-15)**: 세 필드 모두 비어있지 않음. 미충족 시 제출 비활성화.
- **동작**:
  1. 제출 → `POST /api/auth/admin/login {store_code, username, password}`.
  2. 성공: `authStore.login(access_token)` → `router.push('/')`(대시보드).
  3. 실패(AuthError): `errorMessage`에 "아이디 또는 비밀번호가 올바르지 않습니다" 표시(존재 여부 비노출, BR-U1-8).
  4. 시도 초과(잠금) 응답: "로그인 시도가 제한되었습니다. 잠시 후 다시 시도하세요" 표시.
- **API 연동점**: admin_login.
- **가드 연계**: 로그인 성공 전까지 보호 라우트 접근 시 이 화면으로 리다이렉트.

### TableManageView (`views/auth/TableManageView.vue`) — US-A4 (Q5=B)
관리자가 테이블(태블릿) 번호·비밀번호를 생성/수정하는 화면(`require_admin`).

- **State**: `tables[]`(id, table_number), `editing`(선택 테이블), `form{tableNumber, password}`, `loading`, `feedback`.
- **로드**: 진입 시 `GET /api/admin/tables` → 목록 표시(비밀번호 미표시, BR-U1-12).
- **생성**: `POST /api/admin/tables {table_number, password}`.
- **수정**: `PUT /api/admin/tables/{id} {table_number?, password?}` (비밀번호 재설정 포함).
- **폼 검증**: `tableNumber` 필수·매장 내 유일(서버 ValidationError 표시, BR-U1-11); 생성 시 `password` 필수.
- **피드백**: 성공/실패 토스트. 실패 시 목록 미변경.
- **API 연동점**: list_tables, create_table, update_table.

---

## frontend-customer

### TableSetupView (`views/auth/SetupView.vue`) — US-C1 (최초 1회 설정)
태블릿 최초 설정 화면(관리자가 태블릿에서 1회 입력). `router` 미인증 리다이렉트 대상(`/setup`).

- **State/Form**: `storeCode`, `tableNumber`, `password`, `loading`, `errorMessage`.
- **폼 검증**: 세 필드 필수·비어있지 않음.
- **동작**:
  1. 제출 → `POST /api/auth/table/login {store_code, table_number, password}`.
  2. 성공: `authStore.login(access_token)`(localStorage 저장, NFR-5) → `router.push('/menu')`.
  3. 실패: `errorMessage` 표시, **토큰 저장하지 않음**(US-C1 "잘못된 초기 자격증명", BR-U1-14).
- **터치 친화(NFR-6)**: 버튼 ≥44x44px, 큰 입력 필드.

### 자동 로그인 로직 (앱 부팅 시)
- 별도 화면 아님 — 셸 부팅/가드에서 처리:
  1. 앱 실행 → `getToken()` 존재 시 보호 라우트(`/menu`) 진입 허용(자동 로그인, NFR-5).
  2. 토큰 없음/만료(401) → `api/client`가 토큰 클리어 → 가드가 `/setup`으로 이동.
- 장기 테이블 토큰(720h)이라 통상 재입력 불필요. 만료·오류 시에만 재설정.

---

## 라우트 등록 (U0 슬롯 채움)
| SPA | 경로 | 컴포넌트 | requiresAuth |
|---|---|---|---|
| admin | `/login` | AdminLoginView | false |
| admin | `/tables` | TableManageView | true (admin) |
| customer | `/setup` | SetupView | false |

> customer `/menu` 등 보호 라우트는 U2/U3가 등록. U1은 인증/설정 진입점과 가드 연계만 제공.

## 화면 상호작용 흐름 (요약)
```text
[관리자] /login → admin_login → 토큰저장 → 대시보드(U4) / 테이블설정(/tables)
[관리자] /tables → 테이블 생성·수정(번호/비밀번호) → 태블릿 자동로그인 전제 마련(US-A4)
[태블릿] 앱실행 → 토큰있음? → 예:/menu(자동로그인) / 아니오:/setup → table_login → 토큰저장 → /menu
```
