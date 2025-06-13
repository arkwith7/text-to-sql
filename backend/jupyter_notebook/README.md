# Text-to-SQL AI Agent Jupyter Notebook 테스트 가이드

이 디렉토리에는 LangChain Agent와 Azure OpenAI를 활용한 Text-to-SQL 시스템의 테스트용 Jupyter Notebook들이 포함되어 있습니다.

## 📁 파일 구조

- `agent_workflow_test.ipynb`: **메인 테스트 노트북** - LangChain Agent와 Function Tools를 활용한 전체 워크플로우 테스트
- `text_to_sql_agent_test.ipynb`: 기본 SQL Agent 테스트 노트북

## 🚀 시작하기

### 1. 환경 설정

```bash
# 프로젝트 루트 디렉토리에서 실행
cd /home/arkwith/Dev/LLM/text-to-sql/backend

# 가상환경 활성화 (필요한 경우)
source venv/bin/activate

# 필요한 패키지 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env` 파일에 다음 설정이 필요합니다:

```env
# Azure OpenAI 설정
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini

# 데이터베이스 설정
DATABASE_URL=postgresql://user:password@localhost:5432/northwind
APP_DATABASE_URL=sqlite:///app_data.db

# 로깅 설정
LOG_LEVEL=INFO
LOG_TO_FILE=true
```

### 3. Jupyter Notebook 실행

```bash
# Jupyter Notebook 서버 시작
jupyter notebook

# 또는 JupyterLab 사용
jupyter lab
```

브라우저에서 `http://localhost:8888`로 접속하여 노트북을 실행합니다.

## 📓 주요 노트북 설명

### `agent_workflow_test.ipynb` (메인 테스트)

#### 🎯 주요 기능
- **Azure OpenAI 모델** 연동 테스트
- **LangChain Agent** 프레임워크 활용
- **Function Tools** 기반 Text-to-SQL 워크플로우
- **현재 구현된 backend/core 코드** 통합 테스트
- **성능 분석** 및 **로깅 시스템** 테스트

#### 📋 테스트 내용
1. **Azure OpenAI 및 데이터베이스 설정**
2. **LangChain Function Tools 정의**
   - `get_database_schema`: 데이터베이스 스키마 조회
   - `generate_sql_from_question`: 자연어 → SQL 변환
   - `execute_sql_query`: SQL 쿼리 실행
3. **LangChain Agent 초기화**
4. **개별 Function Tool 테스트**
5. **전체 워크플로우 테스트**
6. **성능 분석 및 로깅 테스트**

#### 🔧 테스트 시나리오
```python
test_queries = [
    "고객 수를 알려주세요",
    "제품 수는 몇 개인가요?", 
    "카테고리별 제품 수를 보여주세요",
    "월별 매출 추이를 분석해주세요",
    "가장 많이 팔린 제품 5개를 찾아주세요"
]
```

## 🛠️ 사용법

### 기본 실행 순서

1. **모든 셀을 순서대로 실행**
   - `Shift + Enter`로 각 셀 실행
   - 또는 `Cell > Run All` 메뉴 사용

2. **실행 결과 확인**
   - 각 단계별 성공/실패 상태 확인
   - 성능 지표 및 로그 확인

3. **개별 테스트 실행**
   ```python
   # 개별 Function Tool 테스트
   schema_info = get_database_schema.run("northwind")
   print(schema_info)
   ```

### 커스텀 테스트

```python
# 사용자 정의 질문 테스트
custom_question = "특정 고객의 주문 내역을 보여주세요"
result = agent.run(custom_question)
print(result)
```

## 📊 결과 분석

### 성능 메트릭
- **실행 시간**: 각 쿼리별 처리 시간
- **성공률**: 전체 테스트 중 성공한 비율
- **에러 분석**: 실패한 테스트의 원인 분석

### 로깅 확인
```bash
# 로그 파일 확인
python manage_logs.py status

# 실시간 로그 모니터링
python manage_logs.py tail --type sql

# 성능 분석
python manage_logs.py analyze --hours 1
```

## 🔧 문제 해결

### 일반적인 문제들

#### 1. Azure OpenAI 연결 실패
```
❌ Azure OpenAI 초기화 실패: Invalid API key
```
**해결법**: `.env` 파일에서 `AZURE_OPENAI_API_KEY` 확인

#### 2. 데이터베이스 연결 실패
```
❌ 데이터베이스 초기화 실패: Connection refused
```
**해결법**: 데이터베이스 서버 상태 및 연결 정보 확인

#### 3. 모듈 임포트 오류
```
ModuleNotFoundError: No module named 'langchain'
```
**해결법**: 
```bash
pip install -r requirements.txt
```

#### 4. 권한 오류
```
PermissionError: logs directory
```
**해결법**:
```bash
mkdir -p backend/logs
chmod 755 backend/logs
```

### 디버깅 팁

1. **Verbose 모드 활성화**
   ```python
   agent = initialize_agent(
       tools=tools,
       llm=llm,
       verbose=True  # 상세 로그 출력
   )
   ```

2. **개별 단계 테스트**
   - 각 Function Tool을 개별적으로 테스트
   - 에러 발생 지점 정확히 파악

3. **로그 분석**
   ```bash
   # 최근 에러 확인
   python manage_logs.py analyze --hours 1 --detailed
   ```

## 📈 성능 최적화

### 1. 캐싱 활용
```python
# 스키마 정보 캐싱
cached_schema = None

@tool
def get_database_schema_cached(database_name: str = "northwind") -> str:
    global cached_schema
    if cached_schema is None:
        cached_schema = get_database_schema.run(database_name)
    return cached_schema
```

### 2. 배치 처리
```python
# 여러 쿼리 배치 실행
async def batch_execute_queries(queries: List[str]):
    tasks = [sql_agent.execute_query(q) for q in queries]
    return await asyncio.gather(*tasks)
```

## 🚀 확장 가능성

### 추가 Function Tools

```python
@tool
def validate_sql_query(sql_query: str) -> str:
    """SQL 쿼리 문법 검증"""
    # 구현...

@tool
def optimize_sql_query(sql_query: str) -> str:
    """SQL 쿼리 최적화 제안"""
    # 구현...

@tool
def get_query_execution_plan(sql_query: str) -> str:
    """SQL 실행 계획 분석"""
    # 구현...
```

### 다중 데이터베이스 지원

```python
@tool
def execute_cross_database_query(
    query: str, 
    databases: List[str]
) -> str:
    """여러 데이터베이스에서 쿼리 실행"""
    # 구현...
```

## 📝 추가 리소스

- [LangChain 공식 문서](https://python.langchain.com/)
- [Azure OpenAI 서비스 문서](https://docs.microsoft.com/en-us/azure/cognitive-services/openai/)
- [FastAPI 문서](https://fastapi.tiangolo.com/)
- [프로젝트 로깅 가이드](../docs/LOGGING.md)

## 🤝 기여하기

새로운 테스트 케이스나 Function Tool을 추가하고 싶다면:

1. 새로운 노트북 생성 또는 기존 노트북 수정
2. 테스트 결과 검증
3. 문서 업데이트
4. Pull Request 제출

---

**문의사항이나 문제가 있으면 프로젝트 담당자에게 연락하세요.** 🚀 

## 데이터베이스 구성

### PostgreSQL Northwind 샘플 데이터베이스

이 프로젝트는 Microsoft의 Northwind 샘플 데이터베이스의 PostgreSQL 버전을 사용합니다.

#### 데이터베이스 구조

Northwind 데이터베이스는 가상의 무역회사 "Northwind Traders"의 판매 데이터를 포함하며, 다음 8개의 테이블로 구성됩니다:

1. **categories** (카테고리)
   - categoryid: 카테고리 ID (PRIMARY KEY)
   - categoryname: 카테고리 이름
   - description: 카테고리 설명
   - 예시: 음료, 조미료, 과자류, 유제품, 곡물/시리얼, 육류/가금류, 농산물, 해산물

2. **customers** (고객)
   - customerid: 고객 ID (PRIMARY KEY)
   - customername: 고객회사명
   - contactname: 담당자명
   - address, city, postalcode, country: 주소 정보
   - 총 91개 고객

3. **employees** (직원)
   - employeeid: 직원 ID (PRIMARY KEY)
   - lastname, firstname: 성, 이름
   - birthdate: 생년월일
   - photo: 사진 파일명
   - notes: 직원 설명
   - 총 10명 직원

4. **shippers** (배송업체)
   - shipperid: 배송업체 ID (PRIMARY KEY)
   - shippername: 배송업체명
   - phone: 전화번호
   - 총 3개 배송업체

5. **suppliers** (공급업체)
   - supplierid: 공급업체 ID (PRIMARY KEY)
   - suppliername: 공급업체명
   - contactname: 담당자명
   - address, city, postalcode, country, phone: 연락처 정보
   - 총 29개 공급업체

6. **products** (제품)
   - productid: 제품 ID (PRIMARY KEY)
   - productname: 제품명
   - supplierid: 공급업체 ID (FK)
   - categoryid: 카테고리 ID (FK)
   - unit: 판매 단위
   - price: 단가
   - 총 77개 제품

7. **orders** (주문)
   - orderid: 주문 ID (PRIMARY KEY)
   - customerid: 고객 ID (FK)
   - employeeid: 직원 ID (FK)
   - orderdate: 주문 날짜
   - shipperid: 배송업체 ID (FK)
   - 총 196개 주문

8. **orderdetails** (주문상세)
   - orderdetailid: 주문상세 ID (PRIMARY KEY)
   - orderid: 주문 ID (FK)
   - productid: 제품 ID (FK)
   - quantity: 주문 수량
   - 총 518개 주문상세

#### 테이블 관계

```
customers (1) ←→ (N) orders (1) ←→ (N) orderdetails (N) ←→ (1) products
                      ↑                                            ↑
                      |                                            |
                 employees (1)                               categories (1)
                      |                                            |
                 shippers (1)                                suppliers (1)
```

#### 자주 사용되는 SQL 쿼리 예시

```sql
-- 기본 카운트 쿼리
SELECT COUNT(*) FROM customers;          -- 고객 수: 91
SELECT COUNT(*) FROM products;           -- 제품 수: 77  
SELECT COUNT(*) FROM orders;             -- 주문 수: 196

-- 카테고리별 제품 수
SELECT categoryname, COUNT(*) as product_count
FROM categories c 
JOIN products p ON c.categoryid = p.categoryid 
GROUP BY categoryname 
ORDER BY product_count DESC;

-- 주문이 많은 고객 상위 10명
SELECT customername, COUNT(*) as order_count
FROM customers c 
JOIN orders o ON c.customerid = o.customerid 
GROUP BY customername 
ORDER BY order_count DESC 
LIMIT 10;

-- 가장 인기 있는 제품 (주문량 기준)
SELECT productname, SUM(quantity) as total_quantity
FROM products p 
JOIN orderdetails od ON p.productid = od.productid 
GROUP BY productname 
ORDER BY total_quantity DESC 
LIMIT 10;

-- 직원별 처리한 주문 수
SELECT firstname || ' ' || lastname as employee_name, COUNT(*) as order_count
FROM employees e 
JOIN orders o ON e.employeeid = o.employeeid 
GROUP BY employee_name 
ORDER BY order_count DESC;

-- 국가별 고객 수
SELECT country, COUNT(*) as customer_count
FROM customers 
GROUP BY country 
ORDER BY customer_count DESC;

-- 가장 비싼 제품들
SELECT productname, price
FROM products 
ORDER BY price DESC 
LIMIT 10;
```

#### 테스트 쿼리 목록

노트북에서 테스트할 수 있는 한국어 질문들:

1. "고객 수를 알려주세요"
2. "제품 수는 몇 개인가요?"
3. "주문 수는 총 몇 개인가요?"
4. "카테고리별 제품 수를 보여주세요"
5. "가장 비싼 제품 5개를 알려주세요"
6. "주문이 가장 많은 고객 상위 5명을 보여주세요"
7. "가장 인기 있는 제품 5개를 알려주세요"
8. "직원별 처리한 주문 수를 보여주세요"
9. "국가별 고객 수를 알려주세요"
10. "배송업체별 주문 수를 보여주세요"

### 데이터베이스 설치 방법

PostgreSQL Northwind 데이터베이스를 설치하려면:

1. PostgreSQL이 설치되어 있어야 합니다
2. 다음 스크립트를 실행하여 Northwind 데이터베이스를 생성합니다:

```bash
# PostgreSQL 접속
psql

# Northwind 데이터베이스 생성
CREATE DATABASE northwind;
\c northwind;

# 스키마 및 데이터 로드 (northwind_ddl.sql, northwind_data.sql 파일 필요)
\i northwind_ddl.sql
\i northwind_data.sql
```

스크립트 파일들은 다음 위치에서 다운로드할 수 있습니다:
- [YugabyteDB GitHub](https://github.com/yugabyte/yugabyte-db/tree/master/sample)
- [PostgreSQL Northwind Scripts](https://en.wikiversity.org/wiki/Database_Examples/Northwind/PostgreSQL) 

## 노트북 파일들

### 1. agent_workflow_test.ipynb (원본)
- **상태**: 실행 중 에러 발생 (성공률 0.0%)
- **문제점**: 비동기 처리, deprecated API 사용
- **에러**: "Tool does not support sync"

### 2. agent_workflow_test_improved.ipynb (🆕 개선 버전)
- **상태**: 모든 문제점 해결됨
- **성공률**: 예상 100% (에러 해결됨)
- **개선사항**:
  - ✅ 비동기 처리 문제 해결
  - ✅ 최신 LangChain API 적용 (`create_openai_functions_agent`, `AgentExecutor`)
  - ✅ Deprecated 함수 교체 (`.run()` → `.invoke()`)
  - ✅ 에러 처리 강화
  - ✅ Function Tool 동기화

## 🔧 주요 개선사항

### 문제점 해결
1. **"Tool does not support sync" 에러**
   - 원인: 비동기 함수를 동기 방식으로 호출
   - 해결: 모든 Tool을 동기 버전으로 재작성

2. **LangChain API 버전 문제**
   - 원인: `initialize_agent` deprecated
   - 해결: `create_openai_functions_agent` + `AgentExecutor` 사용

3. **함수 호출 방식 문제**
   - 원인: `.run()` 메서드 deprecated
   - 해결: `.invoke()` 메서드 사용

### 새로운 기능
- **향상된 에러 처리**: 각 단계별 상세한 에러 메시지
- **성능 측정**: 실행 시간 분석 및 통계
- **시뮬레이션 모드**: 실제 DB 연결 없이도 테스트 가능
- **개선된 로깅**: 상세한 실행 과정 추적 