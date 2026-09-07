# U4 Session + Realtime — NFR Requirements Plan

**유닛**: U4 Session + Realtime (담당: 이재환). Functional Design 승인 완료 기반.

## 산출물 계획
- [x] `nfr-requirements.md` — NFR-1(실시간 <2s)·NFR-3(멀티테넌시)·NFR-4(영속)·NFR-6(터치 UI) 중 U4 책임 매핑, 규모/성능/가용성
- [x] `tech-stack-decisions.md` — U0 확정 스택 상속 + U4 고유 선택(SSE StreamingResponse, asyncio.Queue 브로커)

## 질문 (Step 3)
Functional Design에서 NFR 영향 결정이 이미 확정됨:
- SSE 재연결/keepalive 정책 = Q7-C(keepalive + REST 스냅샷 재동기화)
- 고객 스트림 격리 = Q8-A(서버 table_id 필터)
- 활성 세션 유일성 = Q1-C
기술 스택은 U0에서 전 유닛 공통으로 확정(FastAPI 동기 + SSE + SQLite). 확장(Security/Resiliency/Property-Based Testing) 전부 Disabled(`aidlc-state.md`).
→ **추가 열린 질문 없음**. U0 결정 및 Functional Design과 일관.
