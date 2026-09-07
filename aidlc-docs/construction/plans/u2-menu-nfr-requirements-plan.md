# U2 Menu — NFR Requirements Plan

**유닛**: U2 Menu · **담당**: 이원종
**입력**: `aidlc-docs/construction/u2-menu/functional-design/*` (승인 완료), U0 NFR·tech-stack.

> U2는 순수 CRUD·조회 도메인. **기술 스택은 U0에서 전면 고정**(FastAPI · SQLAlchemy 동기 · SQLite · pytest · Vue3)되어 U2 전용 신규 스택 결정은 거의 없다. NFR 대부분은 U0에서 상속된다. 아래는 상속 매핑 + U2 고유로 실제 결정이 필요한 소수 항목이다.

---

## 상속·확정된 NFR (재확인용, 질문 아님)

| NFR | U2에서의 의미 | 처리 |
|---|---|---|
| **NFR-3 멀티테넌시** | Category/Menu 전건 store_id 격리 | U0 `BaseRepository` 상속으로 자동 강제(BR-U2-0) |
| **NFR-4 영속성** | 메뉴/카테고리 SQLite 영속 | U0 엔진·`create_all`에 모델 등록(BR-U2-18) |
| **NFR-6 터치 UI** | 고객 메뉴 화면 카드형·44×44px | U0 셸/스타일 기준 상속, 화면은 U2(frontend-components) |
| **NFR-2 인증(소비)** | 관리자 `require_admin`, 고객 `require_table` | U0 StoreContext 가드 사용(발급은 U1) |
| **NFR-1 실시간** | 해당 없음 — 메뉴 변경은 실시간 push 대상 아님 | N/A (U2는 이벤트 미발행) |
| **확장(Security/Resiliency/PBT)** | Disabled(`aidlc-state.md`) | 강제 규칙 N/A |

## 규모·성능 전제
- 규모: 매장당 카테고리 ~수십, 카테고리당 메뉴 ~수십 → **작은 데이터셋**. 조회는 인덱스 `(store_id, category_id, display_order)`로 충분.
- 성능 목표: 별도 SLA 없음(로컬/데모). 조회 응답은 체감 즉시.

---

## 산출물 계획 (체크박스 — 답변 확정 후 생성)

- [x] `nfr-requirements.md` — U2 NFR 상속 매핑 + 성능/신뢰성/유지보수 요구, 결정 반영
- [x] `tech-stack-decisions.md` — U0 스택 상속 확인 + U2 추가 의존성(있으면) 명시

---

## 질문 (U2 고유 NFR 결정)

`[Answer]:` 뒤에 letter를 채워주세요. 다 채우면 "완료"로 알려주세요.

### Question 1 — 메뉴/카테고리 목록 페이지네이션
조회 시 페이지네이션을 둘까요? (U0에 `Page[T]`/`PageParams` 유틸 존재)

A) **페이지네이션 없음 — 전체 반환**. 매장당 메뉴 수십 개 규모라 불필요. 고객 조회는 카테고리 그룹 전체, 관리자 목록도 전체. *(권장)*

B) **관리자 목록에만 페이지네이션 적용**(고객 조회는 전체). 향후 메뉴가 많아질 것 대비.

C) Other (please describe after [Answer]: tag below)

[Answer]: A

### Question 2 — 고객 메뉴 응답 캐싱
`GET /api/menu`(고객 조회) 응답에 캐싱을 도입할까요?

A) **캐싱 없음 — 매 요청 DB 조회**. 데이터 작고 메뉴 변경이 바로 반영돼야 함. MVP에 단순. *(권장)*

B) **HTTP 캐싱(ETag/Cache-Control) 또는 서버 인메모리 캐시** 도입. 조회 부하 감소.

C) Other (please describe after [Answer]: tag below)

[Answer]: A

### Question 3 — 신규 기술/라이브러리
U2 구현에 U0 스택(FastAPI · SQLAlchemy 동기 · Pydantic · SQLite · pytest · Vue3) 외 추가 의존성이 필요할까요?

A) **U0 스택 그대로, 추가 의존성 없음**. 검증은 Pydantic, 이미지 URL 형식 검증도 Pydantic(HttpUrl 등)으로 충분. *(권장)*

B) **추가 라이브러리 필요** (Other에 명시 — 예: 특정 검증/이미지 처리 라이브러리)

C) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## 답변 후 진행
- 모든 `[Answer]:` 확인 → 모순/모호성 검사 → 산출물 2종 생성 → REVIEW 게이트 → 다음: NFR Design(U2).
