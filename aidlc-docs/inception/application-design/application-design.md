# 애플리케이션 설계 (Application Design) — 통합본

테이블오더 서비스의 고수준 애플리케이션 설계 통합 문서. 세부 문서는 다음을 참조:
- `components.md` — 컴포넌트 정의·책임·인터페이스
- `component-methods.md` — 서비스 메서드 시그니처
- `services.md` — 서비스 정의·오케스트레이션 시나리오
- `component-dependency.md` — 의존 관계·통신 패턴·데이터 흐름

> 상세 비즈니스 규칙/데이터 스키마는 이후 **Functional Design(유닛별, Construction)** 에서 확정한다.

---

## 1. 설계 결정 요약 (application-design-plan.md 답변)

| # | 결정 사항 | 선택 |
|---|---|---|
| Q1 | 컴포넌트 경계 | **B** — 도메인 4분할(Auth/Menu/Order+Cart/Realtime+Session) + Store·Table 공통 모듈 |
| Q2 | Realtime(SSE) 배치 | **A** — 독립 컴포넌트, 매장별 인메모리 pub-sub 브로커 |
| Q3 | 백엔드 계층 | **A** — 3계층(Router → Service → Repository) |
| Q4 | 데이터 접근 | **A** — SQLAlchemy ORM (+선택 Alembic) |
| Q5 | 멀티테넌시 강제 | **A** — 인증 컨텍스트 store_id 주입, 모든 서비스 메서드 필수 |
| Q6 | 테이블 인증 | **A** — 테이블 세션 토큰 |
| Q7 | 프론트엔드 구성 | **A** — 고객/관리자 SPA 2개 분리 |
| Q8 | 서비스 오케스트레이션 | **A** — 서비스 간 직접 호출(동기) |

**기술 스택**: FastAPI(Python) · Vue SPA × 2 · SQLite · 로컬 실행 · 멀티테넌트.

---

## 2. 컴포넌트 구성 (요약)

**백엔드 도메인 컴포넌트(각 Router/Service/Repository 3계층)**
1. **Platform/Common** — Store·Table 엔티티, DB, BaseRepository, StoreContext 인증 의존성(멀티테넌시 강제 단일 지점).
2. **Auth** — 관리자 JWT(16h) 로그인, 테이블 설정/토큰 발급·검증.
3. **Menu** — 메뉴/카테고리 CRUD·노출 순서, 고객 조회.
4. **Order** — 주문 생성/조회/상태/삭제, 세션 시작 트리거, 이벤트 발행. (장바구니는 클라이언트 측.)
5. **TableSession** — 세션 라이프사이클·이력 이관(핵심 도메인), 과거 이력.
6. **Realtime** — 매장별 pub-sub 브로커 + SSE 스트림(독립).

**프론트엔드**
7. **Customer SPA** — 자동 로그인·메뉴·장바구니(로컬)·주문·현재 세션 내역.
8. **Admin SPA** — 로그인·실시간 대시보드·테이블/세션·메뉴 관리.

상세: `components.md`.

---

## 3. 아키텍처 및 오케스트레이션 (요약)

- **3계층**: 라우터(컨텍스트 주입) → 서비스(도메인 조율) → 리포지토리(SQLAlchemy) → SQLite.
- **동기 직접 호출**(Q8-A): 예) 주문 생성 시 OrderService가 MenuService(가격 검증)·TableSessionService(세션 시작)를 직접 호출.
- **실시간만 pub-sub 분리**(Q2-A): 도메인 서비스는 `RealtimeService.publish(store_id, event)`만 호출, SSE 전송은 Realtime 전담. 신규 주문 2초 이내 전파(NFR-1).
- **멀티테넌시**(Q5-A): 모든 서비스 메서드가 `StoreContext.store_id`를 요구, 리포지토리가 쿼리에 강제.

핵심 시나리오(주문 생성·상태 변경·삭제·세션 종료·대시보드 구독): `services.md` 및 `component-dependency.md`의 시퀀스 다이어그램 참조.

---

## 4. 요구사항/스토리 커버리지

| 스토리 | 주요 컴포넌트 |
|---|---|
| US-C1 자동 로그인 | Auth, Customer SPA |
| US-C2 메뉴 조회 | Menu, Customer SPA |
| US-C3 장바구니 | Customer SPA(클라이언트) |
| US-C4 주문 생성 | Order(+Menu, TableSession, Realtime) |
| US-C5 현재 세션 내역 | Order, TableSession |
| US-C6 상태 실시간(고객) | Realtime, Order |
| US-A1 관리자 로그인 | Auth |
| US-A2 실시간 대시보드 | Realtime, Order |
| US-A3 주문 상세·상태 | Order, Realtime |
| US-A4 테이블 설정 | Auth |
| US-A5 주문 삭제 | Order, Realtime |
| US-A6 세션 종료 | TableSession, Order, Realtime |
| US-A7 과거 이력 | TableSession |
| US-A8 메뉴 관리 | Menu |

모든 Must 스토리가 컴포넌트에 매핑됨. NFR-1(실시간)·NFR-3(멀티테넌시)·NFR-4(영속성)·NFR-5(클라이언트 영속)는 아키텍처 결정으로 반영.

---

## 5. 병렬 개발(4인) 예비 유닛 매핑

| 유닛 | 컴포넌트 | 담당(예정) |
|---|---|---|
| 공통 기반 | Platform/Common(계약 우선) | 공동/선행 |
| 유닛 1 | Auth (+ 관련 화면) | 임동규 |
| 유닛 2 | Menu (+ 관련 화면) | 이원종 |
| 유닛 3 | Order (+ Customer 장바구니/주문 화면) | 최지영 |
| 유닛 4 | TableSession + Realtime (+ 대시보드) | 이재환 |

> 유닛 경계·인터페이스 계약·담당자 확정은 다음 **Units Generation** 단계에서 진행. 위 매핑은 예비안이다.

---

## 6. 설계 완전성/일관성 검증

- ✅ 모든 Must/Should 스토리가 컴포넌트/메서드에 매핑됨(4절).
- ✅ 8개 설계 결정이 컴포넌트·서비스·의존성 문서 전반에 일관 반영됨.
- ✅ 멀티테넌시(store_id) 강제 지점이 단일화(Platform 인증 컨텍스트 + 리포지토리).
- ✅ 실시간 요구(NFR-1)를 독립 Realtime 컴포넌트 + SSE로 충족.
- ✅ 순환 의존 위험(Order↔TableSession)을 식별하고 Functional Design에서 인터페이스 정리로 이관.
- ✅ 병렬 개발을 위한 컴포넌트 경계와 계약 우선 지점 명시.
- ⏭️ 데이터 모델 필드/트랜잭션 경계/예외 처리 등 상세는 Functional Design 범위(의도적 이연).
