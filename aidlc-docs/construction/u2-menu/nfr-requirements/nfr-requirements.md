# U2 Menu — NFR Requirements

U2(메뉴)는 순수 CRUD·조회 도메인. NFR 대부분을 U0에서 상속하며, U2 고유 결정은 Q1:A(페이지네이션 없음)·Q2:A(캐싱 없음)·Q3:A(추가 의존성 없음)로 확정.

## 상속 NFR 매핑

| NFR | U2에서의 요구 | 처리 방식 |
|---|---|---|
| **NFR-3 멀티테넌시** | Category/Menu 전건 store 격리, 타 매장 접근 불가 | U0 `BaseRepository` store_id 강제 상속(BR-U2-0). store_id는 StoreContext에서만 파생(BR-U0-3) |
| **NFR-4 영속성** | 메뉴/카테고리 데이터 영속 저장 | U0 SQLAlchemy 동기 엔진 + `create_all`에 Menu/Category 모델 등록(BR-U2-18) |
| **NFR-6 터치 UI** | 고객 메뉴 화면 카드형·버튼 44×44px·명확한 계층 | U0 레이아웃 셸/스타일 상속, 화면 구현은 U2 frontend-components |
| **NFR-2 인증(소비자)** | 관리자 API `require_admin`, 고객 조회 `require_table` | U0 StoreContext 가드 사용(토큰 발급/검증은 U1) |
| **NFR-1 실시간** | 해당 없음 | 메뉴 변경은 실시간 push 대상 아님 — U2는 이벤트 미발행(변경은 다음 조회 시 반영) |
| **NFR-5 클라이언트 영속** | 부분 해당 | 토큰 저장은 U0/U1. U2는 메뉴 화면 로컬 상태만(영속 요구 없음) |

## 성능 (Q1:A · Q2:A)
- **데이터 규모**: 매장당 카테고리·메뉴 각 수십 개 → 소량. 조회 인덱스 `(store_id, category_id, display_order)`로 충분.
- **페이지네이션 없음**: 고객 조회(카테고리 그룹 전체)·관리자 목록 모두 전체 반환. U0 `Page[T]` 미사용.
- **캐싱 없음**: `GET /api/menu`는 매 요청 DB 조회. 메뉴 변경이 즉시 반영되도록 함(단순성 우선).
- **응답 목표**: 별도 SLA 없음(로컬/데모). 소량 데이터라 체감 즉시.

## 신뢰성 / 오류 처리
- 입력 검증 실패→422, 미존재→404, 권한→403(U0 표준 매핑 BR-U0-10 준수, BR-U2-* 참조).
- 트랜잭션: 각 쓰기(생성/수정/삭제/품절토글) 단일 트랜잭션. 재정렬은 다건 update를 한 트랜잭션에서 처리.
- 카테고리 삭제 시 활성 메뉴 존재하면 거부(BR-U2-8) — 데이터 정합성 보호.

## 가용성
- 로컬 실행 데모 — 고가용성 목표 없음. SQLite 재시작 시 데이터 유지.

## 유지보수성 / 테스트
- 3계층(Router/Service/Repository) 유지, Repository는 U0 `BaseRepository` 상속.
- pytest로 유닛/통합 테스트: 멀티테넌시 격리, 검증 규칙, 소프트삭제/품절 조회 제외, 계약 A 반환, 재정렬 검증.

## 확장(Extension) 준수
- Security / Resiliency / Property-Based Testing: 모두 **Disabled**(`aidlc-state.md`). 관련 강제 규칙 N/A.
