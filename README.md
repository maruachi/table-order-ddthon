# 테이블오더 서비스 (Table Order Service)

멀티테넌트 테이블오더 서비스. 고객 태블릿에서 메뉴 조회·주문, 관리자 콘솔에서 실시간 모니터링·메뉴/테이블/세션 관리.

- **백엔드**: FastAPI (Python 3.11) · SQLAlchemy(동기) · SQLite
- **프론트엔드**: Vue 3 + Vite SPA 2개 (고객 / 관리자)
- **실시간**: SSE + 매장별 인메모리 pub-sub
- **격리**: 멀티테넌트(store_id) — 인증 컨텍스트 + 리포지토리 강제

> 개발 방법론: AI-DLC. 설계/계획 문서는 `aidlc-docs/` 참조.

## 프로젝트 구조

```
backend/                 FastAPI 백엔드 (도메인 패키지)
  app/common/            U0 공통 기반: DB, 모델(Store/Table), StoreContext, BaseRepository, 이벤트/실시간 계약
  app/{auth,menu,order,session,realtime}/   도메인 유닛(U1~U4, 병렬 개발)
  seeds/seed.py          샘플 매장/테이블 시드
  tests/                 pytest
frontend-customer/       고객용 Vue SPA (앱 셸 U0 + 유닛 화면)
frontend-admin/          관리자용 Vue SPA (앱 셸 U0 + 유닛 화면)
```

## 유닛 편성 (4인 병렬)
| 유닛 | 범위 | 담당 |
|---|---|---|
| U0 Platform/Common | 공통 기반(선행 계약 고정) | 공동 |
| U1 Auth | 관리자/테이블 인증 | 임동규 |
| U2 Menu | 메뉴 CRUD·조회 | 이원종 |
| U3 Order (+Cart) | 주문·장바구니 | 최지영 |
| U4 Session + Realtime | 세션·이력·SSE | 이재환 |

## 실행 방법

### 백엔드
```bash
cd backend
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m seeds.seed          # 샘플 데이터(매장 demo-cafe/demo-bistro, 관리자 admin/admin1234, 테이블 비번 1234)
uvicorn app.main:app --reload # http://localhost:8000 (문서: /docs)
```

### 프론트엔드
```bash
cd frontend-customer && npm install && npm run dev   # http://localhost:5173
cd frontend-admin    && npm install && npm run dev   # http://localhost:5174
```

### 테스트
```bash
cd backend && source .venv/bin/activate && pytest
```

## 현재 상태
- ✅ **U0 Platform/Common** 완료 — 공통 기반·계약(A~E)·앱 셸·시드·테스트. 병렬 개발(U1~U4) 착수 준비 완료.
- ✅ **U1 Auth**(임동규) 완료 — 관리자 로그인(JWT 16h·시도제한 5회/15분 자동해제), 테이블 로그인(JWT 720h·자동 로그인), 테이블 설정 CRUD(관리자), 계약 E `JwtTokenVerifier` 등록. 화면: 관리자 `/login`·`/tables`, 고객 `/setup`.
- ⏳ U2~U4: Sprint 0 계약 고정 후 병렬 개발 예정.

### U1 인증 사용 (시드 계정)
- 관리자 로그인: 매장코드 `demo-cafe`, 아이디 `admin`, 비밀번호 `admin1234`.
- 테이블 로그인: 매장코드 `demo-cafe`, 테이블 번호 `1`, 비밀번호 `1234`.
