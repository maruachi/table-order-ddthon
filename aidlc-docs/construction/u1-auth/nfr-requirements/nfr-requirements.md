# U1 Auth — NFR Requirements

Auth 유닛의 비기능 요구/목표. 요구사항 NFR-1~6 중 U1 관련 항목과 확장 준수. 기술 스택은 U0에서 상속(신규 의존성 없음).

## NFR 매핑 (U1 책임)
| NFR | 요구 | U1 목표/책임 |
|---|---|---|
| **NFR-2 인증/세션 보안** | JWT 16h·bcrypt·시도 제한 | 관리자 JWT(16h)·테이블 JWT(720h) 발급/검증(HS256, `jwt_secret`); bcrypt 검증(U0 유틸); 로그인 시도 제한(임계 5, 잠금 15분 자동 해제, 관리자 로그인만) |
| **NFR-3 멀티테넌시** | 매장 간 완전 격리 | 모든 인증 후 오퍼레이션의 `store_id`는 토큰(StoreContext)에서만; `AdminUser`/`Table` 조회는 U0 `BaseRepository` store 스코프; 자격증명/존재 여부 비노출(BR-U1-8) |
| **NFR-4 영속성** | SQLite 영속 | `AdminUser`(U0 Base 상속) + `Table.password_hash`(bcrypt) SQLite 저장. 시도 추적은 **비영속**(인메모리, 재시작 초기화 — 허용) |
| **NFR-5 클라이언트 영속** | 로컬 저장·새로고침 유지 | 토큰 localStorage(U0 `api/token` 재사용); 관리자/태블릿 자동 로그인 |
| **NFR-6 터치 UI** | 44×44px·카드형 | 태블릿 설정/로그인 화면 버튼 ≥44×44px(U0 레이아웃/스타일 기준) |
| **NFR-1 실시간** | 2초 SSE | **N/A** — Auth는 실시간 이벤트 미발행 |

## 성능 (Q3=A)
- 명시적 SLA 없음 — 로컬/워크숍 수준의 합리적 응답. 규모: 매장당 소수 관리자 로그인 + 태블릿 최초 1회 로그인(이후 토큰 재사용) → 인증 부하 낮음.
- bcrypt: passlib **기본 cost** 사용(별도 튜닝 없음). 로그인 시에만 해시 검증 발생.
- 토큰 검증(`JwtTokenVerifier.verify`)은 요청마다 수행되나 HS256 디코드로 경량.

## 보안 (NFR-2 상세, Security Baseline 확장은 Disabled → 기능 요구로만 구현)
- 비밀번호 평문 미저장/미응답(bcrypt only). `password_hash` 응답 제외(BR-U1-12).
- 자격증명 실패는 단일 메시지("invalid credentials")로 매장/계정 열거 방지(BR-U1-8).
- 시도 제한: `(store_id, username)` 키(Q2=A), 임계 `max_login_attempts=5`, `LOCKOUT_MINUTES=15`(Q1=A) 자동 해제. 관리자만(Q4=A/FD).
- JWT 만료 강제: 관리자 16h(자동 로그아웃), 테이블 720h. 서버 무효화 없음(무상태, Q7=A).
- `jwt_secret`은 config(환경변수 `TO_JWT_SECRET`)로 주입; 로컬 기본값은 개발 전용.

## 가용성/신뢰성
- 로컬 실행 데모 — 고가용성 목표 없음.
- 시도 추적 인메모리 → 서버 재시작 시 잠금 상태 소실(재시도 허용). 워크숍/로컬 수용 가능(BR-U1-6).
- AdminUser 미존재(시드 누락) 시 로그인 실패로만 표면화; `TokenVerifier` 미등록은 U0가 fail-closed 처리.

## 유지보수/테스트
- 3계층(router→service→repository) 일관 구조, U0 계약/유틸 재사용으로 결합 최소화.
- 단위 테스트 대상: 로그인 성공/실패, 시도 제한 잠금/자동 해제, JWT 발급·검증(만료/서명 오류), store 격리(교차 매장 차단), 테이블 생성/수정 유일성.
- `JwtTokenVerifier`는 U0 `register_token_verifier`로 주입 → 통합 시 실제 검증 활성화.

## 확장(Extension) 준수
| 확장 | 상태 | U1 판정 |
|---|---|---|
| Security Baseline | Disabled | N/A (기본 보안은 NFR-2 기능 요구로 구현) |
| Resiliency Baseline | Disabled | N/A |
| Property-Based Testing | Disabled | N/A |
