# U1 Auth — NFR Design Patterns

NFR 요구를 U1 설계 패턴으로 구체화. U0 기반 패턴(격리/인증 프레임/오류 처리)을 상속·구현한다.

## 인증 패턴 (NFR-2) — 핵심
- **의존성 역전 verifier 등록**: U1 `JwtTokenVerifier`가 U0 `TokenVerifier` 프로토콜을 구현하고 `register_token_verifier(...)`로 등록(앱 lifespan). U0→U1 역의존 제거, 병렬 개발 시 U0는 verifier 미등록 상태로 fail-closed.
- **무상태 JWT 토큰**: 세션 저장 없이 서명 토큰. `role` 클레임(`admin`/`table`)으로 권한 구분, `store_id`/`table_id` 클레임으로 컨텍스트 운반. 만료는 `exp`로만(관리자 16h → 자동 로그아웃, 테이블 720h).
- **Role guards 재사용**: 라우터는 U0 `require_admin`으로 테이블 설정 API 보호. 테이블 로그인/관리자 로그인은 공개(인증 발급 지점).
- **Password hashing 위임**: bcrypt(passlib, U0 유틸)로만 검증. 평문 미저장·미응답.

## Throttling / 로그인 시도 제한 패턴 (NFR-2)
- **In-memory rate limiter**: 프로세스 로컬 딕셔너리 `(store_id, username) -> {failed_count, locked_until}`.
  - 실패 시 카운트 증가 → 임계(5) 도달 시 `locked_until = now + 15분` 설정.
  - 잠금 중 시도는 자격증명 검증 없이 즉시 거부(자원 절약 + 무차별 대입 완화).
  - **시간 기반 자동 해제**: `now >= locked_until`이면 상태 리셋(별도 스케줄러 없이 조회 시 lazy 평가).
  - 성공 시 즉시 리셋.
- **적용 경계**: 관리자 로그인만. 테이블 로그인은 태블릿 자동화 특성상 제외(Q4=A).
- **degradation 허용**: 재시작 시 트래커 소실 → 잠금 해제. 로컬/워크숍 수용(고정 저장소 불필요).

## 멀티테넌시 격리 패턴 (NFR-3)
- **Context-injected scoping 상속**: 인증 후 오퍼레이션의 `store_id`는 `StoreContext`에서만. 로그인 단계의 `store_code`만 클라이언트 입력(인증 전, `Store` 해석용).
- **Scoped Repository**: `AdminUserRepository`·테이블 접근은 U0 `BaseRepository` 상속 → `store_id` 필터 자동 강제. 교차 매장 접근 fail-closed.

## 오류 처리 / 정보 노출 패턴
- **Typed AppError 재사용**: `AuthError`/`ForbiddenError`/`ValidationError`/`NotFoundError`만 raise → U0 중앙 핸들러가 표준 `ErrorResponse` 변환.
- **Uniform failure(열거 방지)**: 매장 없음/계정 없음/비밀번호 불일치를 동일 `AuthError("invalid credentials")`로 응답(BR-U1-8).

## 복원력 / 성능 (경량)
- **Fail-closed 인증**: verifier 미등록·토큰 오류 시 접근 거부(U0 정책 준수).
- **성능**: SLA 없음. bcrypt는 로그인 시에만, 토큰 검증은 경량 HS256 디코드. 캐시/큐/서킷브레이커 불필요.

## 확장 준수
- Security/Resiliency/Property-Based Testing 확장 모두 Disabled → 강제 규칙 N/A. 위 보안 패턴은 요구사항 NFR-2의 기능적 구현.
