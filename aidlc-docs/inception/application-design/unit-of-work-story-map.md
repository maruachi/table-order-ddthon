# 스토리 ↔ 유닛 매핑 (Unit of Work Story Map)

모든 사용자 스토리를 유닛에 배정하고 커버리지를 검증한다. 출처: `aidlc-docs/inception/user-stories/stories.md`.

## 유닛별 스토리 배정

| 유닛 | 담당(예정) | 스토리 | 우선순위 | 화면(수직 귀속, Q2-A) |
|---|---|---|---|---|
| **U0 Platform/Common** | 공동/선행 | (기반, 스토리 없음) — NFR-3 멀티테넌시, NFR-4 영속성, 앱 셸/공통 UI | - | 고객·관리자 SPA 앱 셸(라우팅·레이아웃·API 클라이언트·토큰 유틸) |
| **U1 Auth** | 임동규 | US-A1(관리자 로그인·JWT), US-A4(테이블 초기 설정), US-C1(태블릿 자동 로그인·세션 유지) | Must×3 | 관리자 로그인, 테이블 설정, 태블릿 자동 로그인 |
| **U2 Menu** | 이원종 | US-A8(메뉴 CRUD·노출 순서), US-C2(메뉴 조회·카테고리 탐색) | Must×2 | 관리자 메뉴 관리, 고객 메뉴 탐색/상세 |
| **U3 Order (+Cart)** | 최지영 | US-C3(장바구니), US-C4(주문 생성), US-C5(현재 세션 내역), US-A3(주문 상세·상태 변경), US-A5(주문 삭제) | Must×4, +US-C3 Must | 고객 장바구니·주문 확정·현재 세션 내역, 관리자 주문 상세/상태/삭제 |
| **U4 Session + Realtime** | 이재환 | US-A2(실시간 대시보드), US-A6(세션 종료·이력 이관), US-A7(과거 이력), US-C6(고객 상태 실시간) | Must×2, Should×1, Could×1 | 관리자 실시간 대시보드·과거 이력, 고객 상태 실시간 반영 |

## 스토리 → 유닛 역매핑 (전수 커버리지 검증)

| 스토리 | 우선순위 | 배정 유닛 |
|---|---|---|
| US-C1 자동 로그인·세션 | Must | U1 Auth |
| US-C2 메뉴 조회·탐색 | Must | U2 Menu |
| US-C3 장바구니 관리 | Must | U3 Order |
| US-C4 주문 생성 | Must | U3 Order |
| US-C5 현재 세션 내역 | Must | U3 Order |
| US-C6 주문 상태 실시간(고객) | Could | U4 Session+Realtime |
| US-A1 관리자 로그인·JWT | Must | U1 Auth |
| US-A2 실시간 대시보드(SSE) | Must | U4 Session+Realtime |
| US-A3 주문 상세·상태 변경 | Must | U3 Order |
| US-A4 테이블 초기 설정 | Must | U1 Auth |
| US-A5 주문 삭제(직권) | Must | U3 Order |
| US-A6 세션 종료(이용 완료) | Must | U4 Session+Realtime |
| US-A7 과거 주문 내역 | Should | U4 Session+Realtime |
| US-A8 메뉴 관리(CRUD) | Must | U2 Menu |

## 커버리지 요약
- **총 14개 스토리** (US-C1~C6, US-A1~A8) → **모두 배정 완료**. 미배정 없음.
- Must 11 / Should 1(US-A7) / Could 1(US-C6) — Could/Should는 U4에 포함되며 우선순위에 따라 후순위 구현 가능.
- **크로스 유닛 스토리**: US-A3/A5(주문 상태·삭제, U3)는 U4 Realtime(계약 D)으로 대시보드 전파. US-A6(세션 종료, U4)는 U3 주문 데이터(계약 C) 사용. → 계약으로 고정됨(`unit-of-work-dependency.md`).
- **NFR 반영**: NFR-1(실시간)→U4, NFR-2(인증 보안)→U1, NFR-3(멀티테넌시)→U0 전역 강제, NFR-4(SQLite 영속)→U0+각 유닛, NFR-5(클라이언트 영속)→U1/U3 프론트, NFR-6(터치 UI)→각 프론트 화면.
