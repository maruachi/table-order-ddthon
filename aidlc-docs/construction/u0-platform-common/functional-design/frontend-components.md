# U0 프론트엔드 컴포넌트 (앱 셸)

U0는 고객/관리자 **두 Vue SPA의 앱 셸**을 제공한다(Q2-A: 화면은 도메인 유닛 수직 귀속, 셸은 U0). 각 유닛은 이 셸 위에 `views/`를 추가한다.

## 공통 스택
- Vue 3 + Vite + Vue Router 4 + Pinia + Axios.
- 각 앱: `frontend-customer/`, `frontend-admin/` (독립 빌드).

## 앱 셸 구성 요소 (양쪽 공통)
- **API 클라이언트** (`src/api/client.js`): Axios 인스턴스, `baseURL`(예: `http://localhost:8000`), 요청 인터셉터(저장 토큰을 `Authorization: Bearer`로 주입), 응답 인터셉터(401 시 로그인/설정 화면으로).
- **토큰 저장 유틸** (`src/api/token.js`): `localStorage` 기반 저장/조회/삭제(NFR-5, 새로고침 유지). 고객=테이블 세션 토큰, 관리자=JWT.
- **라우터** (`src/router/index.js`): 기본 라우트 + 네비게이션 가드(토큰 없으면 로그인/설정으로). 각 유닛이 라우트를 등록할 수 있도록 라우트 배열을 모듈로 분리.
- **레이아웃** (`src/layouts/`): 고객=풀스크린 태블릿 레이아웃(하단 탭: 메뉴/장바구니/내역), 관리자=사이드바+헤더 콘솔 레이아웃.
- **Pinia 스토어 베이스** (`src/stores/auth.js`): 인증 상태(토큰/컨텍스트) 관리.

## 고객 SPA (`frontend-customer`)
- 진입: 저장 토큰 있으면 자동 로그인→메뉴(기본 화면), 없으면 테이블 설정/로그인 화면(U1).
- 셸이 제공하는 라우트 슬롯: `/setup`(U1), `/menu`(U2), `/cart`+`/order`(U3), `/history`(U3), 상태 실시간(U4, 선택).
- 터치 친화(NFR-6): 최소 44×44px 버튼, 카드형.
- `data-testid` 규약: `{view}-{role}`(예: `menu-category-tab`, `cart-submit-button`).

## 관리자 SPA (`frontend-admin`)
- 진입: JWT 있으면 대시보드, 없으면 로그인(U1).
- 라우트 슬롯: `/login`(U1), `/tables`(U1 설정), `/menu`(U2 관리), `/dashboard`(U4), `/orders/:id`(U3), `/history`(U4).
- SSE 연결 유틸(EventSource, U4가 사용).

## 컴포넌트 계층(셸)
```
App.vue
 └─ <RouterView>  (레이아웃 → 유닛 뷰)
     Layout(Customer|Admin)
      └─ 유닛별 View (auth/menu/order/session)
```

> 각 유닛의 상세 화면 컴포넌트(props/state/상호작용/폼 검증)는 해당 유닛 Functional Design에서 정의. U0는 셸·라우팅·API·토큰·레이아웃 계약만 제공.
