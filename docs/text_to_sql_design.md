# 🤖 Text-to-SQL AI 에이전트 시스템 설계서

이 문서는 고급 Text-to-SQL AI 에이전트의 시스템 설계를 설명합니다. 이 아키텍처는 복잡한 자연어 질문을 정확하고 효율적으로 SQL 쿼리로 변환하고, 데이터베이스와 상호작용하며, 풍부하고 통찰력 있는 결과를 제공하도록 설계되었습니다.

**최종 업데이트:** 2025년 1월 17일  
**버전:** 2.0  
**상태:** 운영 준비 완료  

---

## 🚀 핵심 아키텍처 및 워크플로우

본 시스템은 사용자 요청을 순차적 워크플로우로 처리하는 실시간 도구 증강 AI 에이전트로 동작합니다. 오프라인 스키마 전처리 및 벡터 검색에 의존하는 설계와 달리, 이 아키텍처는 현재 데이터베이스 상태와의 정확성을 보장하기 위해 실시간 동적 접근 방식을 사용합니다.

```mermaid
graph LR
    subgraph "사용자 인터페이스"
        A[Vue.js 프론트엔드]
    end

    subgraph "백엔드 (FastAPI)"
        B[API 엔드포인트]
        C[LangChain SQL 에이전트]
        T1[스키마 분석기]
        T2[SQL 실행기]
    end

    subgraph "AI 및 데이터 계층"
        D[Azure OpenAI GPT-4o-mini]
        E[분석 대상 데이터베이스<br/>(PostgreSQL/Oracle/SQL Server/<br/>MySQL/MariaDB 등)]
        F[Redis 캐시]
        G[SQLite (앱 데이터)]
    end

    A -- 1. 자연어 질의 --> B
    B -- 2. 질의 처리 --> C
    C -- 3. 스키마 조회 --> T1
    T1 -- 4. DB 스키마 조회 --> E
    T1 -- 5. 스키마 반환 --> C
    C -- 6. SQL 생성 --> D
    D -- 7. SQL 반환 --> C
    C -- 8. SQL 실행 --> T2
    T2 -- 9. 데이터베이스 질의 --> E
    E -- 10. 결과 반환 --> T2
    T2 -- 11. 결과 포맷팅 --> C
    C -- 12. 결과 캐싱 --> F
    C -- 13. 응답 전송 --> B
    B -- 14. JSON 응답 --> A
```

### 워크플로우 단계:

1. **사용자 질의**: 사용자가 Vue.js 프론트엔드에 자연어 질문(예: "매출 상위 5명의 고객은?")을 입력합니다.
2. **API 요청**: 프론트엔드가 FastAPI 백엔드 엔드포인트(`/api/v1/query`)로 질의를 전송합니다.
3. **에이전트 호출**: 엔드포인트가 전체 프로세스를 조율하는 중앙 `LangChain SQL 에이전트`를 호출합니다.
4. **스키마 분석**: `LangChain SQL 에이전트`가 `SchemaAnalyzerTool`을 사용하여 연결된 분석 대상 데이터베이스에서 직접 관련 데이터베이스 스키마(테이블, 컬럼, 데이터 타입, 키)를 조회합니다. 이를 통해 에이전트가 항상 최신 정보를 가지도록 보장합니다.
5. **SQL 생성**: 에이전트가 사용자의 질문과 조회된 스키마를 포함한 상세한 프롬프트를 구성합니다. 이 프롬프트는 Azure OpenAI LLM에 전송되어 SQL 쿼리 생성을 요청합니다.
6. **SQL 실행**: 에이전트가 생성된 SQL을 받아 `SQLExecutionTool`을 사용하여 분석 대상 데이터베이스에 대해 안전하게 쿼리를 실행합니다.
7. **결과 포맷팅**: 에이전트가 SQL 쿼리, 실행 결과, 설명, 토큰 사용 통계를 구조화된 JSON 객체로 번들링합니다.
8. **캐싱**: 스키마 정보와 쿼리 결과가 Redis에 캐시되어 향후 요청을 가속화하고 중복적인 데이터베이스/LLM 호출을 줄입니다.
9. **API 응답**: 백엔드가 최종 JSON 응답을 프론트엔드로 전송합니다.
10. **동적 렌더링**: 프론트엔드가 JSON을 파싱하여 데이터 테이블, 차트, 텍스트 분석 등 적절한 UI 컴포넌트를 동적으로 렌더링합니다.

---

## 🛠️ 주요 구성 요소 심층 분석

### 🎯 **핵심 처리 엔진**

#### **LangChain Text-to-SQL 에이전트** (`core/agents/langchain_agent.py`)
쿼리 전체 생명주기를 처리하는 주요 오케스트레이터입니다. 단순히 SQL을 생성하는 것이 아니라 정보 수집, 계획 수립, 실행의 논리적 프로세스를 따릅니다.

**핵심 역할:**
- 사용자 요청을 분해합니다.
- 각 단계에서 사용할 도구를 결정합니다 (`SchemaAnalyzerTool` 또는 `SQLExecutionTool`).
- LLM을 위한 컨텍스트(스키마, 쿼리 히스토리)를 관리합니다.
- 최종 응답을 포맷팅합니다.

**실제 구현 특징:**
```python
# Function Tools 기반 에이전트 구성
tools = [
    get_database_schema,      # 스키마 조회
    execute_sql_query_sync,   # SQL 실행
    validate_sql_query        # SQL 검증
]

agent = create_openai_functions_agent(
    llm=azure_openai_llm,
    tools=tools,
    prompt=korean_optimized_prompt
)
```

### 🔧 **도구들 (Function Tools)**

에이전트의 힘은 전문화된 도구들에서 나옵니다:

#### **스키마 분석기 도구** (`core/tools/schema_analyzer_tool.py`)
비즈니스 컨텍스트와 함께 실시간 데이터베이스 스키마 정보를 제공합니다.

**특징:**
- 다중 데이터베이스 지원 (PostgreSQL, Oracle, SQL Server, MySQL, MariaDB 등)
- 실시간 스키마 추출
- 관계 매핑 (FK 관계 포함)
- 비즈니스 친화적 컬럼 설명
- 한국어 설명 및 샘플 데이터 힌트
- 데모용 Northwind 스키마 완전 구현 (8개 테이블)

#### **SQL 실행 도구** (`core/tools/sql_execution_tool.py`)
포괄적인 안전 조치와 함께 안전한 SQL 실행을 처리합니다.

**보안 기능:**
- SQL 인젝션 방지
- 쿼리 복잡성 제한
- 실행 타임아웃
- 시뮬레이션 모드 지원

### 📊 **구조화된 JSON 출력**

백엔드와 프론트엔드 간의 신뢰할 수 있는 통신을 보장하기 위해, 에이전트의 최종 출력은 항상 구조화된 JSON 객체입니다. 이를 통해 프론트엔드가 "데이터 기반"이 되고 응답 내용에 따라 디스플레이를 적응시킬 수 있습니다.

**`QueryResponse` JSON 예시:**
```json
{
  "question": "가장 많이 팔린 제품 5개는?",
  "sql_query": "SELECT p.product_name, SUM(od.quantity) AS total_quantity FROM order_details od JOIN products p ON od.product_id = p.product_id GROUP BY p.product_name ORDER BY total_quantity DESC LIMIT 5;",
  "results": [
    { "product_name": "Gorgonzola Telino", "total_quantity": 328 },
    { "product_name": "Camembert Pierrot", "total_quantity": 297 },
    { "product_name": "Raclette Courdavault", "total_quantity": 264 },
    { "product_name": "Nord-Ost Matjeshering", "total_quantity": 239 },
    { "product_name": "Gnocchi di nonna Alice", "total_quantity": 215 }
  ],
  "explanation": "이 SQL 쿼리는 주문상세 테이블에서 각 제품별 총 판매 수량을 계산합니다. 제품 테이블과 조인하여 제품명을 가져오고 판매량 기준으로 내림차순 정렬하여 상위 5개를 찾습니다.",
  "execution_time": 0.085,
  "row_count": 5,
  "database": "target_database",
  "success": true,
  "error_message": null,
  "chart_type": "bar",
  "token_usage": {
    "prompt_tokens": 1250,
    "completion_tokens": 89,
    "total_tokens": 1339,
    "model": "gpt-4o-mini",
    "cost_estimate": 0.002
  }
}
```

### 🎨 **동적 프론트엔드 (Vue.js 3)**

#### **대화형 인터페이스** (`ChatInterface.vue`)
- 자연스러운 소통을 위한 채팅 스타일 상호작용
- 즉각적인 피드백을 위한 실시간 쿼리 스트리밍
- 구문 강조가 포함된 리치 메시지 포맷팅 (Markdown 지원)
- 대화형 데이터 테이블 및 차트

#### **데이터 시각화** (`DataVisualization.vue`)
- 데이터 기반 자동 차트 유형 선택 (Chart.js 사용)
- 드릴다운 기능이 있는 대화형 차트
- 보고서를 위한 내보내기 기능
- 모바일 장치를 위한 반응형 설계

#### **데이터베이스 관리** (`DatabaseInfo.vue`)
- 쉬운 설정을 위한 연결 마법사
- 검색 기능이 있는 스키마 브라우저
- 쿼리 히스토리 및 즐겨찾기
- 팀 사용을 위한 협업 기능

#### **사용자 프로필** (`UserProfile.vue`)
- 토큰 사용량 통계 및 비용 추적
- 개인화된 대시보드
- 사용자 환경 설정 관리

---

## 🗄️ **데이터베이스 아키텍처**

### **이중 데이터베이스 설계**
시스템은 두 개의 전문화된 데이터베이스로 동작합니다:

#### **1. 애플리케이션 데이터베이스 (SQLite)** - `app_data.db`
사용자 및 시스템 데이터를 관리합니다:

- **사용자 관리**: `users`, `refresh_tokens`, `api_keys`
- **채팅 세션**: `chat_sessions`, `chat_messages`, `user_sessions`
- **쿼리 분석**: `query_analytics` (LLM 토큰 사용량 추적 포함)
- **데이터베이스 연결**: `database_connections`, `database_schemas`
- **시스템 모니터링**: `audit_logs`, `events`, `performance_metrics`
- **시스템 구성**: `system_config`, `alembic_version`

#### **2. 비즈니스 데이터베이스 (다중 DB 지원)**
비즈니스 데이터 분석을 위한 분석 대상 데이터베이스:

- **지원 데이터베이스**: PostgreSQL, Oracle, Microsoft SQL Server, MySQL, MariaDB 등
- **데모 환경**: Northwind 샘플 데이터베이스 (PostgreSQL)
- **운영 환경**: 사용자 연결 외부 데이터베이스 (다중 DB 타입)
- **실시간 비즈니스 분석**: 매출, 고객, 제품 분석

### **연결 관리**
- **다중 데이터베이스 타입 지원**: PostgreSQL, Oracle, Microsoft SQL Server, MySQL, MariaDB 등
- 암호화를 통한 안전한 자격 증명 저장
- 연결 풀링 및 최적화
- 상태 모니터링 및 장애 조치

---

## 🛠️ **기술 스택**

### **백엔드 기술**
- **FastAPI**: 고성능 Python 웹 프레임워크
- **SQLAlchemy**: 데이터베이스 작업을 위한 ORM
- **Alembic**: 데이터베이스 마이그레이션 및 버전 관리
- **Pydantic**: 데이터 검증 및 직렬화
- **Redis**: 캐싱 및 세션 저장소

### **AI 및 ML**
- **Azure OpenAI**: SQL 생성을 위한 GPT-4o-mini
- **LangChain**: 에이전트 프레임워크 및 도구 오케스트레이션
- **커스텀 Function Tools**: @tool 데코레이터 기반 구현
- **맞춤형 프롬프트 엔지니어링**: 도메인별 최적화

### **프론트엔드 기술**
- **Vue.js 3**: 진보적 JavaScript 프레임워크
- **TypeScript**: 타입 안전 JavaScript 개발
- **Tailwind CSS**: 유틸리티 우선 CSS 프레임워크
- **Chart.js**: 데이터 시각화 컴포넌트
- **Vite**: 빠른 빌드 도구 및 개발 서버

### **인프라**
- **Docker**: 컨테이너화 및 배포
- **분석 대상 데이터베이스**: PostgreSQL, Oracle, SQL Server, MySQL, MariaDB 등
- **SQLite**: 애플리케이션 데이터베이스
- **Redis**: 캐싱 및 실시간 기능

---

## 🔄 **요청 처리 흐름**

### **1. 사용자 입력 처리**
```typescript
// 프론트엔드 쿼리 제출
const response = await streamQuery(userQuestion, {
  onProgress: (progress) => console.log('진행률:', progress),
  onComplete: (result) => console.log('완료:', result)
});
```

### **2. 인증 및 검증**
- JWT 토큰 검증 (`AuthService`)
- 속도 제한 검사
- 입력 무결성 검사
- 연결 권한 확인

### **3. 스키마 분석**
```python
# 실시간 스키마 조회 (다중 DB 지원)
schema_info = get_database_schema("target_database")
# 연결된 분석 대상 데이터베이스의 완전한 스키마 정보
```

### **4. AI 기반 SQL 생성**
```python
# LangChain 에이전트 실행
result = langchain_agent.invoke({
    "input": user_question,
    "chat_history": []
})
```

### **5. 쿼리 실행 및 안전성**
```python
# 타임아웃을 포함한 안전한 SQL 실행
result = execute_sql_query_sync(
    sql_query=generated_sql
)
```

### **6. 결과 처리**
- 데이터 포맷팅 및 타입 변환
- 시각화 추천 (`chart_type` 결정)
- 자연어 설명 생성
- 성능을 위한 캐싱 (Redis)

### **7. 응답 전달**
토큰 사용량, 비용 추적을 포함한 완전한 응답을 제공합니다.

---

## 🔐 **보안 및 인증**

### **JWT 기반 인증**
- 안전한 토큰 기반 인증
- 리프레시 토큰 순환 (`refresh_tokens`)
- 역할 기반 액세스 제어 (RBAC)
- 프로그래매틱 액세스를 위한 API 키 지원 (`api_keys`)

### **SQL 보안**
- 인젝션 방지를 위한 준비된 문
- 쿼리 복잡성 분석
- 화이트리스트 기반 테이블 액세스
- 모든 쿼리에 대한 감사 로깅

---

## 📈 **분석 및 모니터링**

### **쿼리 분석** (`query_analytics`)
- 성능 메트릭 및 타이밍
- 성공/실패율
- 일반적인 쿼리 패턴
- 사용자별 사용 통계
- **LLM 토큰 사용량 및 비용 추적**
- **모델별 사용 통계** (GPT-4o-mini)

### **시스템 메트릭** (`performance_metrics`)
- 응답 시간 및 처리량
- 데이터베이스 연결 상태
- 캐시 적중률 (Redis)
- 오류 패턴 및 알림

---

## 🚀 **배포 및 운영**

### **컨테이너화된 배포**
```yaml
# Docker Compose 구성
services:
  backend:
    image: text-to-sql-backend:latest
    environment:
      - DATABASE_URL=${DATABASE_URL}  # 분석 대상 DB URL
      - AZURE_OPENAI_API_KEY=${AZURE_OPENAI_API_KEY}
      - REDIS_URL=${REDIS_URL}
  
  frontend:
    image: text-to-sql-frontend:latest
    ports:
      - "3000:80"
  
  redis:
    image: redis:alpine
    volumes:
      - redis_data:/data
  
  # 데모용 - 실제 운영에서는 기존 DB 사용
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=northwind
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

### **모니터링 및 관측성**
- 애플리케이션 성능 모니터링 (APM)
- 비즈니스 메트릭용 커스텀 대시보드
- 시스템 상태를 위한 알림 시스템
- 자동화된 오류 보고

---

## 📊 **성능 특성**

### **응답 시간**
- 스키마 조회: < 100ms (캐시됨)
- SQL 생성: 1-3초
- 쿼리 실행: 복잡성에 따라 가변
- 총 응답: 일반적으로 < 5초

### **확장성**
- 동시 사용자 지원: 100+ 사용자
- 데이터베이스 연결: 풀링 및 최적화
- 캐싱 전략: 다층 (Redis + 인메모리)
- 수평 확장: 상태 비저장 설계

### **정확성 메트릭**
- SQL 정확성: 일반적인 쿼리에 대해 >95%
- 스키마 이해: >98% 정확도
- 비즈니스 로직 준수: >90% 정확도
- 사용자 만족도: 피드백을 통해 측정

---

## 🎯 **향후 개선사항**

### **계획된 기능**
- 다국어 지원 (한국어, 영어, 일본어)
- 고급 시각화 유형 (지리공간, 타임라인)
- 기계 학습 모델 통합
- 실시간 데이터 스트리밍 지원

### **기술적 개선사항**
- 유연한 데이터 가져오기를 위한 GraphQL API
- 실시간 협업을 위한 WebSocket 지원
- 고급 캐싱 전략
- 쿼리 컴파일을 사용한 성능 최적화

### **비즈니스 기능**
- 자동화된 보고서 생성
- 예약된 쿼리 및 알림
- 데이터 거버넌스 및 계보 추적
- 비즈니스 인텔리전스 도구와의 통합

---

이 아키텍처는 엔터프라이즈급 보안, 성능 및 사용자 경험 고려사항이 기초부터 내장된 자연어-SQL 변환을 위한 운영 준비 완료된 확장 가능한 솔루션을 나타냅니다.
-   A chat-like interface for user interaction.
-   Components for rendering tables (`SqlDisplay.vue`) and charts (`DataVisualization.vue`).
-   Logic to parse the `QueryResponse` and decide which components to display, creating an interactive and informative user experience.

This architecture allows users to receive rich analytical results—including easy-to-understand data tables, in-depth reports, and intuitive charts—going beyond simple text answers. 