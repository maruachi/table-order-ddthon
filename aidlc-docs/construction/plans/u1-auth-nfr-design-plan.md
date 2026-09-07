# U1 Auth — NFR Design Plan

**유닛**: U1. Auth · **담당**: 임동규 · **의존**: U0
NFR Requirements(`aidlc-docs/construction/u1-auth/nfr-requirements/`)를 패턴·논리 컴포넌트로 구체화.

## 카테고리 평가 (열린 질문 없음 — 근거 명시)
| 카테고리 | 판정 | 근거 |
|---|---|---|
| Resilience 패턴 | 경량 적용 | 로컬 데모. fail-closed 검증(미등록 verifier=U0 처리), 인메모리 트래커 재시작 소실 허용(BR-U1-6). Resiliency 확장 Disabled → N/A |
| Scalability 패턴 | N/A | 인증 부하 낮음(로그인 드묾, 토큰 재사용), SQLite 단일 파일. 스케일 트리거 없음 |
| Performance 패턴 | 경량 | SLA 없음(Q3=A), bcrypt 기본 cost, JWT HS256 경량 디코드 |
| Security 패턴 | **핵심 적용** | 의존성 역전 verifier, 무상태 JWT+role 클레임, bcrypt, 인메모리 throttling(잠금 15분), 균일 실패 응답 |
| Logical Components | 확정 | 3계층 + 인메모리 트래커 + verifier 등록. 큐/캐시/서킷브레이커 불필요(N/A) |

→ 모든 결정이 앞선 단계(FD/NFR Req)에서 확정. 추가 사용자 질문 불필요.

## 산출물 계획
- [x] `nfr-design-patterns.md` — 보안·격리·경량 복원력/성능 패턴을 U1에 매핑.
- [x] `logical-components.md` — U1 논리 컴포넌트/파일·NFR 매핑·U0 통합 지점.
