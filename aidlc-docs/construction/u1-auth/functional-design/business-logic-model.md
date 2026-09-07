# U1 Auth — 비즈니스 로직 모델 (Business Logic Model)

인증 유닛의 핵심 로직: 관리자 로그인·JWT 발급/검증, 로그인 시도 제한(인메모리), 테이블 설정(생성/수정), 테이블 로그인·토큰 발급, 그리고 **계약 E** `TokenVerifier` 구현·등록. 기술 스택은 확정(FastAPI + SQLAlchemy sync + python-jose HS256), 상세 코드는 Code Generation에서.

## 논리 컴포넌트 (3계층)
- **AuthRouter** — 로그인/테이블 설정 엔드포인트. `require_admin` 의존성으로 관리자 전용 보호.
- **AuthService** — 자격증명 검증, 시도 제한, 토큰 발급, 테이블 upsert 오케스트레이션.
- **TokenService** — JWT 인코딩/디코딩(클레임·만료), `JwtTokenVerifier`(계약 E) 구현.
- **AdminUserRepository / TableRepository** — U0 `BaseRepository`(store 스코프) 상속.
- **LoginAttemptTracker** — 인메모리 시도 카운터/잠금(Q2=A, Q3=A).

## 토큰 클레임 규약 (JWT, HS256, `jwt_secret`)
| 클레임 | 값 | 비고 |
|---|---|---|
| `sub` | admin=username, table=`"table:{table_id}"` | StoreContext.subject |
| `store_id` | int | 격리 키 |
| `role` | `"admin"` \| `"table"` | 권한 |
| `table_id` | int (table만) | admin은 생략 |
| `iat` / `exp` | 발급/만료(초) | admin=16h, table=720h (config) |

## 로직 흐름

### 1. 관리자 로그인 (US-A1) — `admin_login(store_code, username, password)`
```text
1. store = StoreRepo.get_by_code(store_code)
   - 없으면 → AuthError("invalid credentials")  # 매장 존재 여부 노출 안 함(BR-U1-8)
2. attempt = Tracker.check(store.id, username)
   - locked_until > now 이면 → AuthError("too many attempts", 잠금 안내)  # BR-U1-4
3. user = AdminUserRepo.get_by_username(store.id, username)
4. if user is None or not verify_password(password, user.password_hash):
       Tracker.record_failure(store.id, username)   # count+1, 임계 초과 시 locked_until 설정
       → AuthError("invalid credentials")           # BR-U1-8 동일 메시지
5. Tracker.reset(store.id, username)                 # 성공 시 카운터 리셋(BR-U1-5)
6. token = TokenService.issue_admin(store.id, username)   # exp=16h
7. return { access_token, token_type="bearer", expires_in=57600, store:{code,name}, subject:username }
```

### 2. 테이블 설정 (US-A4, Q5=B) — 관리자 전용(`require_admin`)
- `list_tables()` → 현재 매장 테이블 목록(번호, id; 비밀번호 해시 미노출).
- `create_table(table_number, password)`:
  ```text
  1. 중복 검사: TableRepo.get_by_number(store_id, table_number) 존재 시 → ValidationError(BR-U1-11)  # U0 예외셋에 ConflictError 없음 → ValidationError 사용
  2. Table(store_id, table_number, password_hash=hash_password(password)) 저장
  3. return { id, table_number }
  ```
- `update_table(table_id, table_number?, password?)`:
  ```text
  1. table = TableRepo.get(store_id, table_id) → 없으면 NotFoundError
  2. table_number 변경 시 유일성 재검사(BR-U1-11)
  3. password 제공 시 password_hash = hash_password(password)
  4. 저장 → return { id, table_number }
  ```
- `store_id`는 항상 `StoreContext`에서(클라이언트 입력 금지, BR-U0-3 / BR-U1-7).

### 3. 테이블 로그인 (US-C1, Q6=A) — `table_login(store_code, table_number, password)`
```text
1. store = StoreRepo.get_by_code(store_code) → 없으면 AuthError("invalid credentials")
2. table = TableRepo.get_by_number(store.id, table_number) → 없으면 AuthError
3. if not verify_password(password, table.password_hash): → AuthError  # 시도 제한 미적용(Q4=A)
4. token = TokenService.issue_table(store.id, table.id)   # exp=720h
5. return { access_token, token_type="bearer", expires_in=2592000, table_id, store:{code,name} }
```
> 클라이언트(태블릿)는 최초 1회 성공 시 토큰을 localStorage에 저장(U0 token 유틸), 이후 자동 로그인(프론트 로직, `frontend-components.md`).

### 4. 토큰 검증 (계약 E) — `JwtTokenVerifier.verify(token) -> StoreContext`
```text
1. payload = jwt.decode(token, jwt_secret, algorithms=[HS256])
   - 만료/서명 오류 → AuthError("invalid or expired token")  # exp 초과 시 자동 로그아웃(US-A1)
2. return StoreContext(
       store_id=payload["store_id"], role=payload["role"],
       subject=payload["sub"], table_id=payload.get("table_id"))
```
- U1은 앱 시작(`main.py` lifespan)에서 `register_token_verifier(JwtTokenVerifier())` 호출 → U0 `get_current_store_context`가 이를 사용.

### 5. 로그아웃 (Q7=A)
- 서버 상태 없음. 클라이언트가 저장 토큰 삭제. 만료는 JWT `exp`로만 관리(무상태).

## 시도 제한 (LoginAttemptTracker, Q2=A·Q3=A·Q4=A)
- 저장: 인메모리 `dict[(store_id, username)] -> AttemptState`.
- `record_failure`: `failed_count += 1`; `failed_count >= max_login_attempts`(=5)이면 `locked_until = now + LOCKOUT_MINUTES`.
- `check`: `locked_until`가 설정되어 있고 `now < locked_until`이면 잠금.
- **자동 해제(Q3=A)**: `now >= locked_until`이면 상태 리셋(재시도 허용).
- **제안 기본값**: `LOCKOUT_MINUTES = 15` (config에 추가 예정, NFR 단계에서 확정).
- 적용 범위: 관리자 로그인만(테이블 로그인 제외, Q4=A).

## 논리 API 오퍼레이션 (라우팅은 Code Generation에서 확정)
| 오퍼레이션 | 입력 | 보호 | 스토리 |
|---|---|---|---|
| admin_login | store_code, username, password | 공개 | US-A1 |
| table_login | store_code, table_number, password | 공개 | US-C1 |
| list_tables | - | require_admin | US-A4 |
| create_table | table_number, password | require_admin | US-A4 |
| update_table | table_id, table_number?, password? | require_admin | US-A4 |

## 계약/통합 지점
- **계약 E(제공)**: `JwtTokenVerifier` 등록 → 전 유닛 라우터의 `StoreContext` 주입 활성화.
- **U0 재사용**: `hash_password`/`verify_password`, `BaseRepository`, `AuthError`/`ForbiddenError`/`ValidationError`/`NotFoundError`(U0 예외셋 전체), `config`(jwt/만료/시도), `Store`/`Table` 모델.
- **다른 유닛**: 직접 호출 없음. U2~U4는 U1이 발급한 토큰을 U0 의존성으로 소비(간접).
