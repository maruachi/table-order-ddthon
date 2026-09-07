# U1 Auth — NFR Requirements Plan

**유닛**: U1. Auth · **담당**: 임동규 · **의존**: U0
Functional Design(`aidlc-docs/construction/u1-auth/functional-design/`) 기반 비기능 요구/기술 결정 평가.

## 확정된(상속) 기술 — 재질문 불필요
- **JWT**: `python-jose[cryptography]==3.3.0` (U0 `requirements.txt`에 이미 포함) · HS256 · `jwt_secret`(config).
- **비밀번호 해시**: `passlib[bcrypt]` + `bcrypt==4.0.1` 핀(U0) — U0 `security.hash_password/verify_password` 재사용. **신규 백엔드 의존성 없음**.
- **영속성**: 동기 SQLAlchemy + SQLite(U0), `AdminUser`는 U0 `Base` 상속.
- **격리**: U0 `StoreContext` + `BaseRepository`(store_id 강제).
- **확장**: Security/Resiliency/Property-Based Testing 모두 Disabled(`aidlc-state.md`) → 해당 강제 규칙 N/A.

## NFR 평가 범위 (요구사항 NFR-1~6 중 U1 관련)
| NFR | U1 관련성 |
|---|---|
| NFR-2 인증/세션 보안 | **핵심** — JWT 발급/검증, bcrypt, 로그인 시도 제한 |
| NFR-3 멀티테넌시 | 토큰 store_id 격리, 테이블/계정 store 스코프 |
| NFR-4 영속성 | AdminUser·Table(비밀번호 해시) SQLite 저장 |
| NFR-5 클라이언트 영속 | 토큰 localStorage(프론트, U0 유틸 재사용) |
| NFR-6 터치 UI | 태블릿 설정/로그인 화면 44×44px(프론트) |
| NFR-1 실시간 | U1 무관(N/A) |

## 산출물 계획 (승인 후 생성)
- [x] `nfr-requirements.md` — U1 NFR 요구/목표(보안·격리·영속·성능·유지보수·테스트) + 확장 준수(N/A 명시).
- [x] `tech-stack-decisions.md` — 상속 스택 확정 + U1 고유 결정(시도 제한 파라미터, config 추가 항목).

## 답변 요약 (확정)
Q1=A(잠금 15분) · Q2=A(키 `(store_id, username)`) · Q3=A(명시적 SLA 없음, bcrypt 기본 cost). 모순 없음. → config에 `lockout_minutes=15` 신규 추가.

---

## 질문 (NFR 확정을 위한 열린 결정)

## Question 1
로그인 시도 제한 잠금 지속시간(`LOCKOUT_MINUTES`) 기본값은? (임계값=5회, config로 관리)

A) 15분 (권장 — 워크숍/데모에 무난한 균형)

B) 5분 (짧게 — 데모 중 재시도 편의 우선)

C) 30분 (길게 — 보안 우선)

D) Other (please describe after [Answer]: tag below)

[Answer]:A

## Question 2
시도 제한 카운터의 키 단위는?

A) `(store_id, username)` — 매장별 계정 단위(권장, 멀티테넌트 자연스러움)

B) `username`만 — 전역(매장 무관) 단위

C) Other (please describe after [Answer]: tag below)

[Answer]:A

## Question 3
인증 엔드포인트(로그인/토큰 검증) 성능 목표는?

A) 명시적 SLA 없음 — 로컬/워크숍 수준의 합리적 응답이면 충분(권장). bcrypt 검증은 passlib 기본 cost 사용.

B) 구체적 목표 지정(예: p95 < Nms) — 아래에 값 기재.

C) Other (please describe after [Answer]: tag below)

[Answer]:A
