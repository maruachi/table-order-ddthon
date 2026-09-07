# U3 Order (+ Cart) — NFR Design Plan

**유닛**: U3 Order+Cart · **담당**: 최지영. NFR Requirements(승인 완료) 기반.

## 전제
- U3는 U0가 확립한 NFR 설계 패턴(격리·인증 프레임·실시간 계약·영속·오류처리)을 **재사용**한다. 신규 인프라 컴포넌트(큐/캐시/서킷브레이커) 없음 — 로컬 데모 범위 N/A.
- 확장(Security/Resiliency/Property-Based Testing) Disabled → 관련 패턴 강제 N/A.
- 열린 사용자 결정 없음(패턴 상속) → 인터랙티브 질문 없음.

## 산출물 계획 (체크박스)
- [x] `nfr-design-patterns.md` — U3에 적용하는 패턴: 스코프 리포지토리(격리), 오케스트레이션(계약 A/B/D), best-effort 발행, 스냅샷, 소프트 삭제/archived, 채번 동시성, N+1 회피
- [x] `logical-components.md` — U3 논리 컴포넌트(router/service/repository/schemas/gateways) 및 NFR 매핑

## 질문 (카테고리별 평가)
- **Resilience**: best-effort publish + 계약 B 실패 시 주문 미저장(요구에서 확정). 추가 결정 불필요.
- **Scalability**: 로컬 단일 SQLite, 워크샵 규모. 스케일 메커니즘 N/A.
- **Performance**: 인덱스 + selectinload + 페이지네이션(요구에서 확정).
- **Security**: U0 격리/역할 가드 재사용, 확장 Disabled → N/A.
- **Logical Components**: 신규 인프라 컴포넌트 없음.
→ 추가 사용자 입력 불필요.
