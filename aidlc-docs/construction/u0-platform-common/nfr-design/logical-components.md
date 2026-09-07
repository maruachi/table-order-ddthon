# U0 논리 컴포넌트 (Logical Components)

| 논리 컴포넌트 | 파일(예정) | 역할 | 관련 NFR |
|---|---|---|---|
| Database | `common/database.py` | 엔진·세션·Base·get_db·init_db | NFR-4 |
| Security/Context | `common/security.py` | StoreContext·TokenVerifier 레지스트리·주입 의존성·role guards·bcrypt 헬퍼 | NFR-2, NFR-3 |
| BaseRepository | `common/repository.py` | store_id 강제 스코프 리포지토리 | NFR-3 |
| Events | `common/events.py` | 이벤트 스키마·팩토리(계약 D 스키마 소스) | NFR-1 |
| Realtime | `common/realtime.py` | RealtimePublisher 프로토콜·레지스트리·NoOp 기본 | NFR-1 |
| Schemas | `common/schemas.py` | ErrorResponse·PageParams·Page | - |
| Exceptions | `common/exceptions.py` | AppError 계층·예외 핸들러 | - |
| Config | `common/config.py` | 설정(DB URL, JWT secret, CORS, 토큰 만료) via pydantic-settings | NFR-2 |
| App | `app/main.py` | 앱 조립·CORS·핸들러·라우터 등록·startup 훅 | - |
| Models(공통) | `common/models.py` | Store·Table 엔티티 | NFR-3, NFR-4 |
| Frontend Shell(×2) | `frontend-*/src/{api,router,layouts,stores}` | 토큰·API 클라이언트·라우팅·레이아웃 | NFR-5, NFR-6 |

**인프라 컴포넌트(큐/캐시/서킷브레이커 등)**: 로컬 데모 범위로 불필요 — N/A. 실시간은 인메모리 pub-sub(U4)로 충분.
