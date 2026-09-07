# U0 Platform/Common — Code Generation Plan

**유닛**: U0 Platform/Common. 스토리: 없음(기반). 의존: 없음(최하위). 제공 계약: E(StoreContext), D(이벤트 스키마/Publisher), 공통 DB·리포지토리·예외·프론트 셸.

**워크스페이스 루트**: `/Users/dgyim/works/aidlc-workshop-day1/table-order-ddthon` (Greenfield 멀티유닛 모놀리식 → `backend/app/{도메인}/`, `frontend-customer/`, `frontend-admin/`).

**단일 진실 소스**: 이 계획서. 코드는 워크스페이스 루트, 요약 문서는 `aidlc-docs/construction/u0-platform-common/code/`.

## 생성 단계

- [x] Step 1. 프로젝트 구조 셋업 — `backend/`(app 패키지, requirements.txt, pytest.ini, .gitignore), 디렉터리 스캐폴드
- [x] Step 2. 설정 — `common/config.py` (pydantic-settings: DB URL, JWT secret, 토큰 만료, CORS)
- [x] Step 3. DB 계층 — `common/database.py` (engine, SessionLocal, Base, get_db, init_db)
- [x] Step 4. 공통 모델 — `common/models.py` (Store, Table)
- [x] Step 5. 공통 스키마/예외 — `common/schemas.py`, `common/exceptions.py`
- [x] Step 6. 보안/컨텍스트 — `common/security.py` (StoreContext, TokenVerifier 레지스트리, get_current_store_context, role guards, bcrypt 헬퍼)
- [x] Step 7. 이벤트/실시간 계약 — `common/events.py`, `common/realtime.py`
- [x] Step 8. BaseRepository — `common/repository.py` (store 스코프 강제)
- [x] Step 9. 앱 조립 — `app/main.py` (FastAPI, CORS, 예외 핸들러, startup init_db, 헬스체크, 도메인 라우터 자리)
- [x] Step 10. 시드 스크립트 — `backend/seeds/seed.py` (샘플 매장/테이블)
- [x] Step 11. 공통 유닛 테스트 — `backend/tests/test_common.py` (BaseRepository 격리, StoreContext, 예외)
- [x] Step 12. 프론트 고객 셸 — `frontend-customer/` (Vite+Vue3, api/client·token, router, layout, stores/auth, 진입 App)
- [x] Step 13. 프론트 관리자 셸 — `frontend-admin/` (동일 셸 구조 + SSE 유틸)
- [x] Step 14. 문서/README — 루트 `README.md`, `aidlc-docs/construction/u0-platform-common/code/` 요약
- [x] Step 15. 실행/배포 아티팩트 — backend 실행 방법(uvicorn), 프론트 실행(npm) README 반영

## 계약 트레이스
- 계약 E → Step 6 (security.py)
- 계약 D → Step 7 (events.py, realtime.py)
- NFR-3 → Step 4/6/8, NFR-4 → Step 3, NFR-5/6 → Step 12/13
