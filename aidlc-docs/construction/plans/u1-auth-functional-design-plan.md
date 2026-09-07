# U1 Auth — Functional Design Plan

**유닛**: U1. Auth (인증) · **담당**: 임동규 · **의존**: U0
**스토리**: US-A1(매장 관리자 로그인·JWT 16h·시도 제한), US-A4(테이블 태블릿 초기 설정), US-C1(태블릿 자동 로그인·테이블 세션 토큰)

## 책임 요약
- 관리자 JWT(16h) 로그인 + 로그인 시도 제한.
- 테이블 초기 설정(번호/비밀번호) 및 테이블 세션 토큰 발급/검증(장기, config 기본 30일).
- **계약 E** 구현: `TokenVerifier`를 U0 `common/security` 레지스트리에 등록 → 토큰을 `StoreContext{store_id, role, subject, table_id?}`로 변환. (U0가 구조/의존성/레지스트리 소유, U1이 검증 로직 소유.)

## 확정된(계약/설정) 사실 — 재질문 불필요
- `StoreContext(store_id:int, role:"admin"|"table", subject:str, table_id:int|None)` — U0 `security.py` 확정.
- `register_token_verifier(verifier)` / `get_current_store_context` / `require_admin` / `require_table` — U0 제공, U1은 `main.py` lifespan에서 verifier 등록.
- 비밀번호 해시: U0 `security.hash_password` / `verify_password`(bcrypt) 재사용.
- config(`common/config.py`): `jwt_secret`, `jwt_algorithm=HS256`, `admin_token_expire_hours=16`, `table_token_expire_hours=720`, `max_login_attempts=5`.
- 엔티티 소유: `Store`(code/name)·`Table`(store_id/table_number/password_hash)는 **U0 소유**. `AdminUser`는 **U1 신규 소유**(Base 상속, store_id 격리).
- Security Baseline 확장 **미적용**(요구사항 기본 보안만 기능 요구로 구현).

---

## 산출물 계획 (승인 후 생성)
- [x] `domain-entities.md` — `AdminUser` 엔티티(store_id, username, password_hash) + 시도추적=인메모리(Q2=A, 엔티티 아님) + `Table`(U0 소유, Q5=B 생성/수정) 참조.
- [x] `business-logic-model.md` — 관리자 로그인/JWT 발급·검증, 시도 제한(인메모리·시간해제), 테이블 설정(생성/수정), 테이블 로그인/토큰 발급, `JwtTokenVerifier` 구현 및 등록 흐름, 에러 정책.
- [x] `business-rules.md` — BR-U1-1~16 (자격증명 검증, 시도 제한, store 격리, 토큰 클레임/만료, 테이블 번호 유일성).
- [x] `frontend-components.md` — 관리자 로그인·테이블 관리(frontend-admin), 태블릿 설정/자동 로그인(frontend-customer): 컴포넌트/상태/폼 검증/API 연동점.

## 답변 요약 (확정)
Q1=A(관리자 시드 전용) · Q2=A(인메모리 카운터) · Q3=A(시간 기반 자동 해제, 기본 15분 제안) · Q4=A(관리자 로그인만) · Q5=B(테이블 생성/수정=U1 관리) · Q6=A(테이블 JWT, store_code+번호+비밀번호) · Q7=A(클라이언트 토큰 삭제, 서버 무상태). 모순 없음.

---

## 질문 (Functional Design 확정을 위한 열린 결정)

아래 각 질문의 `[Answer]:` 뒤에 선택 문자(A/B/...)를 적어 주세요. 해당 없으면 마지막 옵션(Other)에 설명을 적어주세요.

## Question 1
관리자 계정(AdminUser)은 어떻게 생성/관리되나요? (스토리 US-A1~A8에 관리자 계정 CRUD 화면은 없음)

A) 시드 스크립트로만 생성(매장당 1개 관리자 계정을 seed에 추가). MVP에 로그인 화면만 구현, 계정 관리 UI 없음.

B) 시드 + 최소 관리자 등록 API/화면도 U1에서 함께 구현.

C) Other (please describe after [Answer]: tag below)

[Answer]:A

## Question 2
로그인 시도 제한(NFR-2, `max_login_attempts=5`)의 구현 방식은? (워크숍/로컬 성격 고려)

A) 인메모리 카운터(프로세스 메모리, 매장+username 키). 서버 재시작 시 초기화. 가장 단순.

B) DB 영속(AdminUser에 `failed_attempts`, `locked_until` 컬럼 추가). 재시작에도 유지.

C) Other (please describe after [Answer]: tag below)

[Answer]:A

## Question 3
시도 제한 초과 시 잠금 해제(리셋) 방식은?

A) 시간 기반 자동 해제(예: 마지막 실패 후 N분 경과 시 자동 리셋). N분은 설계에서 기본값 제안.

B) 성공 로그인 전까지 잠금 유지 + 관리자/재시작 개입 필요(자동 해제 없음).

C) Other (please describe after [Answer]: tag below)

[Answer]:A

## Question 4
로그인 시도 제한 적용 범위는?

A) 관리자 로그인(US-A1)에만 적용. 테이블 로그인(US-C1)은 태블릿 자동 로그인 특성상 미적용.

B) 관리자 + 테이블 로그인 양쪽 모두 적용.

C) Other (please describe after [Answer]: tag below)

[Answer]:A

## Question 5
US-A4(테이블 태블릿 초기 설정)의 데이터 의미론은? (Table 엔티티는 U0 소유, seed가 테이블 10개 사전 생성)

A) 사전 시드된 기존 테이블의 비밀번호(및 표시 번호)를 **설정/변경**만. 테이블 생성은 seed 담당.

B) 관리자가 신규 테이블을 **생성**하고 번호/비밀번호를 지정(없으면 생성, 있으면 수정 = upsert). 테이블 관리까지 U1 포함.

C) Other (please describe after [Answer]: tag below)

[Answer]:B

## Question 6
테이블 로그인/세션 토큰(US-C1)의 형식과 로그인 입력 자격증명은?

A) 관리자와 동일한 **JWT**(role="table", store_id·table_id 클레임, 만료 720h). 로그인 입력 = 매장 식별자(Store.code) + 테이블 번호 + 테이블 비밀번호. 클라이언트는 토큰을 localStorage에 저장해 자동 로그인.

B) JWT 대신 불투명(opaque) 랜덤 토큰을 DB에 저장/조회하여 검증.

C) Other (please describe after [Answer]: tag below)

[Answer]:A

## Question 7
로그아웃/토큰 무효화 처리는? (JWT는 기본적으로 무상태)

A) 클라이언트 측 토큰 삭제만(서버 블랙리스트 없음). 만료는 JWT `exp`로만 관리. 16h 경과 시 검증 실패 → 자동 로그아웃(US-A1 시나리오와 일치). 가장 단순.

B) 서버 측 토큰 무효화(블랙리스트/버전) 도입.

C) Other (please describe after [Answer]: tag below)

[Answer]:A
