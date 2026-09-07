# 유닛 오브 워크 (Unit of Work) — 테이블오더 서비스

시스템을 4인 병렬 개발이 가능한 논리적 유닛으로 분해한 정의 문서. 각 유닛은 이후 Construction 단계(Functional Design → NFR → Code Generation)를 유닛별로 반복 실행한다.

**용어**: 배포 모델은 **모놀리식 단일 백엔드**(로컬 실행)이므로 유닛 = 독립 배포 서비스가 아니라 **논리적 개발 모듈(Module)**. 단, 개발/소유 경계로서의 "Unit of Work"로 취급한다.

## 분해 결정 요약 (`unit-of-work-plan.md` 답변)

| # | 결정 | 선택 |
|---|---|---|
| Q1 | 유닛 경계 | **A** — 공통 기반 U0 + 도메인 4분할(U1~U4), Realtime은 Session과 함께 U4 |
| Q2 | 프론트 화면 귀속 | **A** — 도메인 유닛에 수직 귀속, 앱 셸/공통 UI는 U0 |
| Q3 | U0 선행 방식 | **B** — 얇은 계약만 먼저 고정, U0 구현과 U1~U4 병렬(모킹) |
| Q4 | 계약 고정 범위 | **F** — 전부(Menu조회·Session·이력이관·Realtime·StoreContext) |
| Q5 | 코드 구조 | **A** — backend 도메인 패키지 + frontend-customer / frontend-admin 분리 |
| Q6 | 착수 순서 | **B** — 계약 고정 후 U1~U4 완전 동시 착수 |

> **Q3+Q6 조화 해석**: "선행"은 U0 전체 구현이 아니라 **모든 유닛 간 계약(Q4-F) 고정**을 의미. 계약 확정(Sprint 0) 후 U0 구현과 U1~U4를 모킹 기반 완전 병렬로 진행한다.

---

## 유닛 정의

### U0. Platform / Common (공통 기반)
- **책임**: 멀티테넌트 기반 + 공통 인프라 + 프론트 앱 셸.
  - 백엔드: `Store`·`Table` 엔티티, SQLAlchemy DB/세션 엔진, `BaseRepository`, `StoreContext` 인증 의존성(store_id 주입 단일 지점), 공통 응답/예외 스키마, 페이지네이션 유틸, 시드 스크립트.
  - 이벤트 스키마 정의(Realtime `publish` 계약) — 도메인 유닛이 공유.
  - 프론트: 고객/관리자 SPA 각각의 앱 셸(라우팅·레이아웃·공통 API 클라이언트·토큰 저장 유틸).
- **포함 컴포넌트**: Platform/Common.
- **소유(예정)**: 공동/선행(4인 합의로 계약 고정 → 이후 유지 담당 1인 지정 가능).
- **의존**: 없음(최하위 계층).

### U1. Auth (인증)
- **책임**: 관리자 JWT(16h) 로그인·시도 제한, 테이블 초기 설정·테이블 세션 토큰 발급/검증, 토큰→StoreContext 연동.
- **포함 컴포넌트**: Auth 서비스 + 화면(관리자 로그인, 테이블 설정, 태블릿 자동 로그인).
- **스토리**: US-A1, US-A4, US-C1.
- **담당(예정)**: 임동규.
- **의존**: U0.

### U2. Menu (메뉴)
- **책임**: 메뉴/카테고리 CRUD·노출 순서·데이터 검증(관리자), 카테고리별 정렬 조회(고객).
- **포함 컴포넌트**: Menu 서비스 + 화면(관리자 메뉴 관리, 고객 메뉴 탐색/상세).
- **스토리**: US-A8, US-C2.
- **담당(예정)**: 이원종.
- **의존**: U0.

### U3. Order (+ Cart)
- **책임**: 주문 생성(메뉴 검증·금액 계산·첫 주문 시 세션 시작 오케스트레이션·이벤트 발행), 현재 세션 주문 조회, 주문 상세·상태 변경(대기중/준비중/완료), 주문 삭제(총액 재계산). 장바구니는 **클라이언트 측**(로컬 저장).
- **포함 컴포넌트**: Order 서비스 + 화면(고객 장바구니·주문 확정·현재 세션 내역, 관리자 주문 상세/상태/삭제).
- **스토리**: US-C3, US-C4, US-C5, US-A3, US-A5.
- **담당(예정)**: 최지영.
- **의존**: U0, U2(Menu 조회), U4(Session 시작/조회, Realtime publish).

### U4. Session + Realtime
- **책임**: 테이블 세션 라이프사이클(시작/현재 조회/종료·이력 이관), 과거 이력 조회, 매장별 인메모리 pub-sub 브로커 + SSE 스트림(관리자 대시보드·고객 실시간 반영), 이벤트 2초 이내 전파(NFR-1).
- **포함 컴포넌트**: TableSession 서비스 + Realtime 컴포넌트 + 화면(관리자 실시간 대시보드·과거 이력, 고객 상태 실시간 반영).
- **스토리**: US-A2, US-A6, US-A7, US-C6.
- **담당(예정)**: 이재환.
- **의존**: U0, U3(세션 종료 시 주문 이력 수집 — U3와 상호 협력).

---

## Greenfield 코드 조직 전략 (Q5-A)

```text
table-order-ddthon/                 # 워크스페이스 루트 (앱 코드)
├── backend/
│   ├── app/
│   │   ├── common/                 # U0: models(Store,Table,Base), db, deps(StoreContext),
│   │   │                           #     base_repository, schemas, events(스키마), pagination
│   │   ├── auth/                   # U1: router, service, repository, models, schemas
│   │   ├── menu/                   # U2: router, service, repository, models, schemas
│   │   ├── order/                  # U3: router, service, repository, models, schemas
│   │   ├── session/                # U4: router, service, repository, models, schemas
│   │   ├── realtime/               # U4: broker(pub-sub), sse router, events
│   │   └── main.py                 # FastAPI 앱 조립(라우터 등록)
│   ├── seeds/                      # U0: 시드 스크립트(매장/테이블/메뉴 초기 데이터)
│   ├── tests/                      # 유닛/통합 테스트(유닛별 하위 디렉터리)
│   └── pyproject.toml / requirements.txt
├── frontend-customer/              # 고객용 Vue SPA (U0 셸 + U1/U2/U3/U4 화면 수직 귀속)
│   └── src/{router, layouts, api, views/{auth,menu,order,session}}
└── frontend-admin/                 # 관리자용 Vue SPA (U0 셸 + U1/U2/U3/U4 화면 수직 귀속)
    └── src/{router, layouts, api, views/{auth,menu,order,dashboard,history}}
```

- 백엔드 각 도메인 패키지 내부는 **3계층**(router → service → repository) 구성(Q3-A).
- 프론트 화면은 **도메인 유닛에 수직 귀속**(Q2-A). 앱 셸(라우팅·레이아웃·API 클라이언트·토큰 유틸)은 **U0**가 제공.

---

## 개발 순서 및 병렬 전략 (Q3-B · Q6-B)

1. **Sprint 0 — 계약 고정(선행, 공동)**: `unit-of-work-dependency.md`의 계약 지점(A~E)을 인터페이스·스키마·스텁으로 확정. DB 엔티티/공통 스키마/이벤트 스키마/StoreContext 시그니처 동결.
2. **병렬 개발(완전 동시)**: 계약 고정 후 U0 구현 + U1·U2·U3·U4를 4인이 동시 착수. 유닛 간 의존은 고정 계약에 대한 **모킹/스텁**으로 대체해 독립 진행.
3. **통합**: 각 유닛 완료 후 실제 구현으로 모킹 교체, 통합 지점(주문 생성→세션→실시간, 세션 종료→이력 이관) 검증.

---

## 검증
- ✅ 모든 스토리가 유닛에 배정됨(`unit-of-work-story-map.md` 참조).
- ✅ 유닛 경계가 4인 병렬 편성과 1:1 정렬(U1~U4) + 공통 선행(U0).
- ✅ 순환 의존(U3↔U4) 식별 → 계약(B: Order→Session, C: Session→Order)을 인터페이스로 고정해 방향 분리, 상세는 Functional Design.
- ✅ 프론트 화면 귀속·코드 구조·개발 순서 결정이 일관 반영됨.
