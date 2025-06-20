# Advanced Text-to-SQL Agent: System Design

이 문서는 복잡한 자연어 질문을 이해하여 데이터베이스와 상호작용하고, 다양한 형태의 분석 결과를 제공하는 고성능 Text-to-SQL AI 에이전트의 시스템 설계를 제안합니다. 이 아키텍처는 정확성, 효율성, 확장성 및 사용자 경험을 극대화하는 것을 목표로 합니다.

---

## 🚀 전체 시스템 워크플로우

시스템은 크게 4개의 단계로 구성됩니다. 1단계는 사전 준비 과정(Offline)이며, 2~4단계는 사용자 요청에 실시간으로 반응하는 과정(Online)입니다.

![System Workflow](https://i.imgur.com/example.png)  <!-- 이 부분은 나중에 실제 다이어그램 이미지 링크로 교체할 수 있습니다. -->

---

### 1단계: 스키마 사전 처리 및 인덱싱 (Schema Pre-processing & Indexing)

> **핵심 아이디어:** "DB 스키마 정보를 가져와 LLM으로 문서화하고, 별도 매체에 저장/관리한다."

이 단계는 AI가 데이터베이스 구조를 빠르고 정확하게 이해할 수 있도록 '사전 학습' 또는 '치트 시트(Cheat Sheet)'를 만드는 과정입니다.

#### 구현 방법

1.  **스키마 추출 (Schema Extraction):** 대상 데이터베이스에서 테이블, 컬럼, 데이터 타입, 제약 조건(PK, FK) 등 모든 메타데이터를 프로그래밍 방식으로 추출합니다.
2.  **LLM을 통한 지능적 문서화 (Intelligent Documentation):** 추출된 딱딱한 스키마 정보를 LLM에 입력하여, 인간이 이해하기 쉬운 자연어 설명과 컨텍스트를 추가합니다.

    *   **예시 (LLM이 생성할 문서):**
        > **테이블: `order_details`**
        > **설명:** 이 테이블은 각 주문에 어떤 상품이 몇 개나 포함되었는지 기록하는 주문의 '상세 항목'에 해당합니다. `orders` 테이블과 `products` 테이블을 연결하는 핵심적인 다대다 관계 테이블입니다.
        > **주요 컬럼:**
        > - `order_id`: 어떤 주문에 속하는지 나타냅니다. `orders` 테이블의 `order_id`를 참조합니다.
        > - `product_id`: 어떤 상품이 주문되었는지 나타냅니다. `products` 테이블의 `product_id`를 참조합니다.
        > - `quantity`: 해당 상품이 몇 개나 팔렸는지를 나타내는 '판매 수량'입니다.
3.  **벡터 임베딩 및 저장 (Vector Embedding & Storage):** 문서화된 텍스트(테이블 설명, 컬럼 설명 등)를 의미론적 정보를 담은 벡터로 변환(Embedding)한 후, `ChromaDB`, `FAISS` 같은 **벡터 저장소(Vector Database)**에 저장하고 인덱싱합니다.

---

### 2단계: 의미 기반 컨텍스트 검색 (Semantic Context Retrieval)

> **핵심 아이디어:** "사용자 질의가 오면, 질의와 유사한 스키마 정보를 검색하여 컨텍스트로 사용한다."

이 단계는 전체 스키마 정보를 무작정 제공하는 대신, 사용자 질문과 가장 관련 있는 '핵심 스키마 정보'만을 동적으로 찾아내 AI 에이전트에게 제공하는 과정입니다.

#### 구현 방법

1.  **질문 벡터화 (Query Embedding):** 사용자 질문 (예: "지난 3개월간 가장 많이 팔린 제품 5개는?")을 1단계에서 사용한 것과 동일한 임베딩 모델을 사용해 벡터로 변환합니다.
2.  **유사도 검색 (Similarity Search):** 변환된 질문 벡터를 사용해 벡터 저장소에서 의미적으로 가장 유사한 스키마 문서 조각들을 검색합니다. 예를 들어, 위의 질문에 대해서는 `products`, `orders`, `order_details` 테이블의 설명 문서가 높은 관련성 점수로 반환될 것입니다.
3.  **컨텍스트 조합 (Context Assembly):** 검색된 스키마 정보들을 조합하여 AI 에이전트에게 전달할 최종 프롬프트 컨텍스트를 구성합니다.

---

### 3단계: 강화된 AI 에이전트 실행 (Enhanced Agent Execution)

> **핵심 아이디어:** "에이전트는 컨텍스트를 받아 SQL 생성, 실행 후 다양한 유형(데이터, 보고서, 차트)으로 결과를 가공하여 제공한다."

이 단계에서 AI 에이전트는 단순한 SQL 생성기를 넘어, 데이터를 분석하고 사용자에게 최적의 형태로 결과를 가공하는 '데이터 분석가'의 역할을 수행합니다.

#### 구현 방법

1.  **지능적 프롬프트 엔지니어링 (Sophisticated Prompting):** 에이전트의 역할, 작업 흐름, 출력 형식을 매우 구체적으로 정의하는 시스템 프롬프트를 사용합니다.
2.  **구조화된 출력 강제 (Structured Output):** 에이전트가 항상 일관된 JSON 형식으로 결과를 반환하도록 설정합니다. 이를 통해 프론트엔드에서 결과를 안정적으로 처리할 수 있습니다.

    *   **출력 JSON 예시:**
        ```json
        {
          "output_type": "chart",
          "data": [ { "product_name": "Chai", "total_quantity": 120 }, ... ],
          "columns": [ "Product Name", "Total Quantity" ],
          "analysis": "지난 3개월간 'Chai' 제품이 가장 많이 팔렸으며, 상위 5개 제품이 전체 판매량의 45%를 차지하는 것으로 나타났습니다. 이는 특정 제품에 대한 고객 선호도가 높음을 시사합니다.",
          "chart_suggestion": {
            "type": "bar",
            "x_axis": "product_name",
            "y_axis": "total_quantity",
            "title": "지난 3개월간 Top 5 판매 제품"
          },
          "generated_sql": "SELECT p.product_name, SUM(od.quantity) as total_quantity FROM ..."
        }
        ```

---

### 4단계: 동적 프론트엔드 렌더링 (Dynamic Frontend Rendering)

> **핵심 아이디어:** "프론트엔드는 채팅 형식으로 질문하고, 정형/비정형 데이터를 답변으로 받는다."

이 단계는 시스템의 분석 결과를 사용자에게 가장 효과적으로 시각화하여 전달하는 사용자 경험(UX)의 최종 과정입니다.

#### 구현 방법

1.  **응답 파싱:** 프론트엔드는 백엔드로부터 받은 구조화된 JSON 응답을 파싱합니다.
2.  **조건부 렌더링 (Conditional Rendering):** 응답의 `output_type` 필드 값에 따라 각기 다른 컴포넌트를 동적으로 렌더링합니다.

    *   `"table"`: 데이터를 표(Table)로 렌더링합니다.
    *   `"report"`: `analysis` 텍스트와 함께 데이터를 서술형으로 표시합니다.
    *   `"chart"`: `chart_suggestion` 정보를 바탕으로 `Chart.js`, `ECharts` 같은 라이브러리를 사용해 동적으로 차트를 렌더링합니다.

이 아키텍처를 통해 사용자는 단순한 텍스트 답변을 넘어, 한눈에 이해하기 쉬운 데이터 테이블, 심도 있는 분석 보고서, 직관적인 차트 등 풍부한 형태의 분석 결과를 얻을 수 있습니다. 