# U4 프론트엔드 컴포넌트 (Frontend Components)

U4 화면은 도메인 수직 귀속(Q2-A). U0 앱 셸(라우팅·레이아웃·API 클라이언트·토큰·SSE 헬퍼) 위에 얹는다.

## Admin SPA (`frontend-admin`)

### DashboardView.vue — US-A2 (실시간 대시보드)
- **경로**: `/dashboard` (라우터 슬롯 활성화). 기본 진입 화면 후보.
- **State**: `tables`(테이블 카드 배열), `filterTableId`(필터), `es`(EventSource 핸들), `connected`.
- **초기 로드**: `GET /sessions/dashboard?preview_n=3` → 카드 렌더(테이블별 총액 + 최신 주문 3개 미리보기).
- **라이브 갱신**: `openSse('/realtime/admin/stream', onEvent)`(U0 `api/sse.js` 재사용).
  - `order.created/updated/status_changed/deleted` → 해당 테이블 카드 총액·미리보기 갱신 + 시각적 강조(신규 하이라이트, 2초 이내 반영).
  - `session.closed` → 해당 테이블 카드 리셋(총액 0, 미리보기 비움).
- **상호작용**: 테이블별 필터(칩/드롭다운), 카드 클릭 시 주문 상세(U3 `OrderDetailView`로 이동 — 통합 지점), 세션 종료 버튼(아래 US-A6).
- **재연결(Q7=C)**: EventSource 자동재연결 + `onopen` 시 대시보드 스냅샷 재조회로 재동기화.
- **NFR-6**: 카드 그리드, 터치 타깃 ≥44px, 명확한 시각적 계층.

### 세션 종료 액션 — US-A6
- DashboardView(또는 카드) 내 "이용 완료" 버튼 → 확인 후 `POST /sessions/close`(body: `{table_id}`).
- 성공 시 카드 리셋(서버 `session.closed` SSE로도 반영). `ClosedSessionSummary` 토스트(총액·주문 수).
- 실패 시 오류 피드백, 상태 유지.

### HistoryView.vue — US-A7 (과거 이력)
- **경로**: `/history`.
- **State**: `items`(이력 주문), `filters{tableId, dateFrom, dateTo}`, `page{offset, limit, total}`.
- **로드**: `GET /sessions/history?table_id=&date_from=&date_to=&offset=&limit=` → `closed_at` 역순 표시.
- **표시**: 주문번호, 시각, 메뉴·수량·단가, 총액, 이용완료 시각(스냅샷).
- **상호작용**: 테이블 필터, 날짜 범위 필터(기준 closed_at), 페이지네이션/무한 스크롤.

### api/session.js (신규)
- `getDashboard(previewN)`, `closeSession(tableId)`, `getHistory(params)` — U0 `client.js`(토큰 주입·401 처리) 사용.

## Customer SPA (`frontend-customer`) — US-C6 (고객 상태 실시간)

### api/sse.js (신규 — admin 미러링)
- `openSse(path, onEvent)`를 고객 앱에도 추가(현재 없음). 토큰 query param 전달, JSON 파싱 위임.

### 실시간 반영 컴포저블/스토어 (`stores/realtime.js` 또는 `composables/useOrderRealtime.js`)
- `openSse('/realtime/table/stream', onEvent)` 구독(서버가 table_id로 필터).
- `order.status_changed` 수신 → 주문 상태 맵 갱신(주문번호→상태). 새로고침 없이 반영.
- **통합 지점**: 주문 내역 화면(US-C5, **U3 소유**)이 이 스토어의 상태를 구독해 상태 배지를 라이브 갱신. U4는 스트림·헬퍼·상태 스토어를 제공하고, U3 화면 연동부는 주석/문서로 명시(통합 시 연결).
- **재연결(Q7=C)**: 재연결 시 U3의 현재 세션 주문 조회(US-C5)로 상태 재동기화(U3 API 사용).

## 컴포넌트 계층 (요약)
```text
AdminLayout(U0)
 ├─ DashboardView (US-A2, SSE admin stream)   ── TableCard × N ── (세션 종료 버튼, US-A6)
 └─ HistoryView   (US-A7, REST + 필터/페이지)

CustomerLayout(U0)
 └─ (U3 OrderHistoryView) ← useOrderRealtime(U4, SSE table stream, US-C6)
```

## API 연동 지점 (백엔드 라우트)
| 화면/기능 | 메서드·경로 | 인증 |
|---|---|---|
| 대시보드 스냅샷 | `GET /sessions/dashboard` | require_admin |
| 세션 종료 | `POST /sessions/close` | require_admin |
| 과거 이력 | `GET /sessions/history` | require_admin |
| 관리자 실시간 | `GET /realtime/admin/stream?token=` | query 토큰(admin) |
| 고객 실시간 | `GET /realtime/table/stream?token=` | query 토큰(table) |
