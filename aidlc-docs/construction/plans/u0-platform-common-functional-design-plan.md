# U0 Platform/Common — Functional Design Plan

**유닛**: U0 Platform/Common (공통 기반). 스토리 없음 — 전 유닛이 의존하는 기반 계층. NFR-3(멀티테넌시)·NFR-4(영속성) 및 계약 A~E(`unit-of-work-dependency.md`)의 소유/정의 지점.

## 확정된 기반 기술 결정 (대화형 승인)
- SQLAlchemy **동기(sync)** + sqlite3
- 엔티티 PK: **정수 자동증가**(Store는 로그인용 `code` 별도 보유)
- 스키마 초기화: **`metadata.create_all()` + 시드 스크립트**(Alembic 미사용)
- Python **3.11 + pip/venv**, `requirements.txt`

## 산출물 계획
- [x] `domain-entities.md` — Store, Table 엔티티 + 공통 Base + StoreContext 구조
- [x] `business-logic-model.md` — DB 세션, BaseRepository(스토어 스코프), StoreContext 주입, 이벤트 스키마, Realtime publisher 계약, 공통 응답/페이지네이션
- [x] `business-rules.md` — 멀티테넌시 강제 규칙, 검증, 예외 정책
- [x] `frontend-components.md` — 고객/관리자 SPA 앱 셸(라우팅·레이아웃·API 클라이언트·토큰 유틸)

## 질문
기반 기술 결정은 대화형 질문으로 확정 완료(위 4개). 추가 열린 질문 없음 — Application Design/Units Generation 결정과 일관.
