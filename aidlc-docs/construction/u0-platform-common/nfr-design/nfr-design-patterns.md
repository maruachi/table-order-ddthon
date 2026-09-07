# U0 NFR Design Patterns — Platform/Common

## 멀티테넌시 격리 패턴 (NFR-3)
- **Context-injected tenant scoping**: 인증 의존성(`get_current_store_context`)이 토큰에서 `store_id`를 추출→`StoreContext` 주입. 클라이언트 입력 store_id 불신(BR-U0-3).
- **Scoped Repository**: `BaseRepository`가 모든 쿼리에 `store_id` 필터를 강제 적용(단일 강제 지점). 도메인 리포지토리는 이를 상속만 하면 격리 자동 충족.
- **Fail-closed**: 크로스 테넌트 접근은 404로 은닉(BR-U0-4).

## 인증 프레임 패턴 (NFR-2 기반)
- **Pluggable verifier(레지스트리)**: U0가 `TokenVerifier` 프로토콜 + 레지스트리 제공, U1이 구현 등록. U0→U1 역의존 제거(의존 역전).
- **Role guards**: `require_admin`/`require_table` 의존성으로 라우터 레벨 권한 강제.

## 실시간 계약 패턴 (NFR-1 기반)
- **Publisher 인터페이스 + 레지스트리**: `RealtimePublisher` 프로토콜 + `NoOpPublisher` 기본값. U4가 실제 브로커 등록. 발행자(U3/U4)는 인터페이스에만 의존→병렬 개발/모킹 가능.
- **Best-effort 발행**: publish 예외가 주 트랜잭션에 영향 없음(BR-U0-13).

## 영속성 패턴 (NFR-4)
- **Session-per-request**: `get_db` 의존성이 요청당 세션 생성/정리.
- **Declarative create_all**: 시작 시 스키마 보장, 파괴적 변경 없음.

## 오류 처리 패턴
- **Typed AppError → handler**: 도메인 예외 계층 + 중앙 예외 핸들러 → 표준 `ErrorResponse`. 유닛은 예외만 raise.

## 관측(경량)
- 표준 로깅(구성 오류/publish 실패 warning). 로컬 데모 범위 — 별도 APM 없음.
