# U3 Order (+ Cart) — NFR Requirements Plan

**유닛**: U3 Order+Cart · **담당**: 최지영. Functional Design(승인 완료) 기반.

## 전제
- 기술 스택은 **U0에서 고정**(Python 3.11 · FastAPI · SQLAlchemy sync · SQLite · Pinia/Vue3 · pytest). U3는 **신규 기술 결정 없음** — 기반 스택 상속.
- 확장(Security Baseline / Resiliency Baseline / Property-Based Testing)은 모두 **Disabled**(`aidlc-state.md`) → 강제 규칙 **N/A**.
- 따라서 열린 사용자 결정 질문 없음(U0와 동일). NFR은 요구사항 NFR-1~6을 U3 관점으로 구체화하는 작업.

## 산출물 계획 (체크박스)
- [x] `nfr-requirements.md` — U3에 적용되는 NFR-1(실시간)·NFR-3(격리)·NFR-4(영속)·NFR-5(장바구니 로컬)·NFR-6(터치 UI) 구체화 + 성능/동시성/신뢰성 목표
- [x] `tech-stack-decisions.md` — U0 스택 상속 확인 + U3 특화 선택(스냅샷 저장, 소프트 삭제 인덱스, order_no 채번 전략)

## 질문
신규 기술 결정 없음(U0 상속). 확장 비활성 → N/A. 추가 사용자 입력 불필요.
