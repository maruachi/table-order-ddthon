# U4 Session + Realtime — NFR Design Plan

**유닛**: U4 Session + Realtime (담당: 이재환). NFR Requirements 기반.

## 산출물 계획
- [x] `nfr-design-patterns.md` — 실시간(pub-sub/SSE/스레드-루프 핸드오프)·멀티테넌시·영속·best-effort·오류 처리 패턴
- [x] `logical-components.md` — session/realtime 논리 컴포넌트 + 공유 파일 편집 지점 + NFR 매핑

## 질문 (Step 3)
- **Resilience**: best-effort 발행(BR-U4-9) + 재연결 시 REST 재동기화(Q7-C) — Functional Design에서 확정.
- **Scalability**: 로컬 단일 프로세스, 인메모리 fan-out. 별도 확장 메커니즘 불필요(로컬 데모).
- **Performance**: 인메모리 큐 전달로 NFR-1(<2s) 충족. 별도 캐시 불필요.
- **Security**: SSE query 토큰 검증(BR-U4-11), store/table 격리(BR-U4-10).
- **Logical Components**: 큐/캐시/서킷브레이커 등 외부 인프라 불필요 — 인메모리 브로커로 충분.
→ **추가 열린 질문 없음**. NFR Requirements 및 Functional Design과 일관.
