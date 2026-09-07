# 요구사항 확인 질문 (Requirements Verification Questions)

기능 요구사항은 `requirements/table-order-requirements.md`에 상세히 정의되어 있고, 제외 범위는 `requirements/constraints.md`에 명시되어 있습니다. 아래는 구현 방향을 확정하기 위해 필요한 기술적/비기능적 결정과 확장(extension) 옵션에 대한 질문입니다.

각 질문의 `[Answer]:` 태그 뒤에 해당하는 **알파벳**을 적어주세요. 보기 중 맞는 것이 없으면 마지막 옵션(Other)을 선택하고 설명을 적어주세요. 모두 작성하신 후 알려주시면 다음 단계로 진행하겠습니다.

---

## Question 1
백엔드(서버 시스템)는 어떤 기술 스택으로 구현할까요?

A) Python (FastAPI)

B) Node.js (Express 또는 NestJS)

C) Java (Spring Boot)

D) 추천에 맡김 (AI가 요구사항에 가장 적합한 스택 제안)

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 2
고객용/관리자용 웹 프론트엔드는 어떤 방식으로 구현할까요? (요구사항: 브라우저에서 동작하는 웹 UI)

A) React (SPA)

B) Vue (SPA)

C) 서버 렌더링 + 최소 JavaScript (예: 서버 템플릿 + HTMX/바닐라 JS)

D) 추천에 맡김

X) Other (please describe after [Answer]: tag below)

[Answer]: B

## Question 3
데이터 저장소(매장/메뉴/주문/주문이력)는 무엇을 사용할까요?

A) 관계형 DB (PostgreSQL)

B) 관계형 DB (MySQL)

C) 개발 편의를 위한 경량 DB (SQLite) — 워크숍/프로토타입에 적합

D) NoSQL (DynamoDB / MongoDB)

E) 추천에 맡김

X) Other (please describe after [Answer]: tag below)

[Answer]: C

## Question 4
이 MVP의 배포/실행 대상 환경은 무엇인가요?

A) 로컬 개발 환경에서 실행 (워크숍/데모 목적)

B) 컨테이너 (Docker / docker-compose)

C) 클라우드 (AWS 등)

D) 추천에 맡김

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 5
MVP에서 지원해야 하는 매장(store) 범위는 어떻게 되나요?

A) 단일 매장 (하나의 매장만 운영)

B) 다중 매장 (매장 식별자로 여러 매장을 구분하는 멀티테넌트 구조)

X) Other (please describe after [Answer]: tag below)

[Answer]: B

## Question 6
예상 동시 사용 규모는 어느 정도인가요? (성능/스케일 요구사항 판단용)

A) 소규모 — 단일 매장, 동시 테이블 수 ~20개 수준

B) 중규모 — 여러 매장, 매장당 수십 개 테이블

C) 규모는 중요하지 않음 (기능 구현 우선, 성능 최적화는 범위 외)

X) Other (please describe after [Answer]: tag below)

[Answer]: B

## Question 7
테이블 세션 및 관리자 인증에 필요한 초기 데이터(매장 정보, 관리자 계정, 메뉴 등)는 어떻게 준비할까요?

A) 코드/스크립트로 시드(seed) 데이터를 자동 생성

B) 관리자 UI를 통해 수동 등록 (메뉴 관리 기능 사용)

C) 둘 다 지원 (시드 데이터 + UI 등록)

X) Other (please describe after [Answer]: tag below)

[Answer]: C

## Question 8
메뉴 이미지는 어떻게 처리할까요? (constraints.md에서 이미지 리사이징/최적화는 제외됨)

A) 이미지 URL만 저장 (외부/정적 URL 참조, 업로드 없음)

B) 서버에 파일 업로드 후 저장 (원본 그대로, 최적화 없음)

X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

# 확장(Extensions) 옵트인 질문

아래는 AI-DLC 확장 규칙 적용 여부를 결정하는 질문입니다. 프로젝트 성격(워크숍/프로토타입 vs. 프로덕션)에 맞게 선택해주세요.

## Question 9: Security Extensions
이 프로젝트에 보안(SECURITY) 확장 규칙을 적용할까요?

A) Yes — 모든 SECURITY 규칙을 차단 제약(blocking constraint)으로 적용 (프로덕션급 애플리케이션에 권장)

B) No — 모든 SECURITY 규칙 생략 (PoC, 프로토타입, 실험용 프로젝트에 적합)

X) Other (please describe after [Answer]: tag below)

[Answer]: B

## Question 10: Resiliency Extensions
이 프로젝트에 복원력(RESILIENCY) 베이스라인을 적용할까요?

**설명**: 활성화하면 AWS Well-Architected Framework(신뢰성 기둥) 기반의 설계 단계 모범 사례(내결함성, 고가용성, 관찰 가능성, 복구성 등)를 요구사항/설계/코드에 반영합니다. 단, 이것이 프로덕션 준비 완료를 보장하지는 않으며 시작점(first draft)으로 활용됩니다.

A) Yes — 복원력 베이스라인을 설계 단계 모범 사례로 적용 (비즈니스 크리티컬 워크로드에 권장)

B) No — 복원력 베이스라인 생략 (빠른 반복이 더 중요한 PoC/프로토타입/실험용에 적합)

X) Other (please describe after [Answer]: tag below)

[Answer]: B

## Question 11: Property-Based Testing Extension
이 프로젝트에 속성 기반 테스트(Property-Based Testing, PBT) 규칙을 적용할까요?

A) Yes — 모든 PBT 규칙을 차단 제약으로 적용 (비즈니스 로직, 데이터 변환, 직렬화, 상태 컴포넌트가 있는 프로젝트에 권장)

B) Partial — 순수 함수와 직렬화 왕복(round-trip)에만 PBT 규칙 적용 (알고리즘 복잡도가 제한적인 프로젝트에 적합)

C) No — 모든 PBT 규칙 생략 (단순 CRUD, UI 전용, 얇은 통합 계층에 적합)

X) Other (please describe after [Answer]: tag below)

[Answer]: C
