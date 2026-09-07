# U1 Auth — 비즈니스 규칙 (Business Rules)

인증·토큰·테이블 설정에 대한 결정 규칙·검증·제약. U0 규칙(BR-U0-*)을 상속하며, 아래는 U1 고유 규칙(BR-U1-*).

## 자격증명 · 로그인
- **BR-U1-1**: 관리자 로그인은 `(store_code, username, password)` 3요소를 요구한다. `store_code`로 `Store`를 해석해 `store_id`를 얻는다.
- **BR-U1-2**: 비밀번호 검증은 bcrypt(U0 `verify_password`)로만 수행한다. 평문 비교 금지.
- **BR-U1-8**: 매장/계정 존재 여부를 노출하지 않는다 — 매장 없음·계정 없음·비밀번호 불일치 모두 동일한 `AuthError("invalid credentials")`로 응답한다.

## 로그인 시도 제한 (NFR-2, Q2=A·Q3=A·Q4=A)
- **BR-U1-3**: 실패 시 `(store_id, username)`별 인메모리 카운터를 1 증가시킨다. 임계값 `max_login_attempts`(=5) 이상이면 `locked_until = now + LOCKOUT_MINUTES`(기본 15분 제안)로 잠근다.
- **BR-U1-4**: 잠금 상태(`now < locked_until`)에서의 로그인 시도는 자격증명 검증 없이 `AuthError`(시도 초과 안내)로 거부한다.
- **BR-U1-5**: 로그인 성공 시 해당 키의 카운터·잠금을 즉시 리셋한다.
- **BR-U1-6**: `now >= locked_until`이면 잠금이 자동 해제되어 재시도를 허용한다(시간 기반 자동 해제). 서버 재시작 시 전체 추적 상태 초기화(로컬/워크숍 허용).
- **BR-U1-6a**: 시도 제한은 **관리자 로그인에만** 적용하고 테이블 로그인에는 적용하지 않는다.

## 멀티테넌시 · 격리 (NFR-3)
- **BR-U1-7**: 모든 인증 후 오퍼레이션의 `store_id`는 검증된 토큰(`StoreContext`)에서만 취한다. 클라이언트 요청 본문의 store 식별자는 신뢰하지 않는다(로그인 시 `store_code`는 예외 — 인증 이전 단계). U1 리포지토리는 U0 `BaseRepository`로 store 스코프를 강제한다.
- **BR-U1-8b**: 테이블 설정 오퍼레이션(생성/수정/조회)은 `StoreContext.store_id`가 소유한 테이블에만 작용한다(교차 매장 접근 차단).

## 토큰 (JWT, 계약 E)
- **BR-U1-9**: 관리자 토큰 클레임 = `{sub:username, store_id, role:"admin", iat, exp}`, `exp = iat + admin_token_expire_hours(16h)`.
- **BR-U1-10**: 테이블 토큰 클레임 = `{sub:"table:{table_id}", store_id, role:"table", table_id, iat, exp}`, `exp = iat + table_token_expire_hours(720h)`.
- **BR-U1-10a**: `TokenVerifier.verify`는 서명·만료를 검증하고 실패 시 `AuthError`를 던진다. 만료된 토큰은 재로그인을 강제한다(US-A1 16h 자동 로그아웃).
- **BR-U1-10b**: 로그아웃은 클라이언트 토큰 삭제로만 처리한다(서버 무효화/블랙리스트 없음, Q7=A).

## 테이블 설정 (US-A4, Q5=B)
- **BR-U1-11**: `table_number`는 매장 내 유일해야 한다(`unique(store_id, table_number)`). 생성·번호 변경 시 중복이면 `ValidationError`.
- **BR-U1-12**: 테이블 비밀번호는 저장 전 bcrypt 해싱(`hash_password`)하며 평문을 저장·응답하지 않는다. 조회 응답에 `password_hash`를 포함하지 않는다.
- **BR-U1-13**: 테이블 생성/수정은 `require_admin` 컨텍스트에서만 허용한다(관리자 권한 필수).
- **BR-U1-14**: 잘못된 초기 자격증명(테이블 로그인 실패)은 토큰을 발급하지 않으며 클라이언트는 로그인 정보를 저장하지 않는다(US-C1 "잘못된 초기 자격증명" 시나리오).

## 입력 검증
- **BR-U1-15**: `username`, `table_number`, `password`는 공백만으로 구성될 수 없다(필수·비어있지 않음). 위반 시 `ValidationError`.
- **BR-U1-16**: 관리자 계정은 U1에서 API로 생성하지 않는다(시드 전용, Q1=A). 계정 미존재 시 로그인 실패로만 나타난다.

## 규칙 → 스토리/NFR 추적
| 규칙 | 근거 |
|---|---|
| BR-U1-1,2,8 | US-A1, NFR-2 |
| BR-U1-3~6a | US-A1 시도 제한, NFR-2 |
| BR-U1-7,8b | US-A1/A4/C1, NFR-3 |
| BR-U1-9~10b | US-A1(16h), US-C1(자동 로그인), 계약 E, Q6/Q7 |
| BR-U1-11~14 | US-A4, US-C1 |
| BR-U1-15,16 | US-A4/A1, Q1 |
