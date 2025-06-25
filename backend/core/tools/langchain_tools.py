"""
LangChain Function Tools for Text-to-SQL application.
Based on successful patterns from Jupyter notebook testing.
"""

import logging
import json
from typing import Dict, Any, Optional, TYPE_CHECKING
from langchain.tools import tool

# TYPE_CHECKING을 사용하여 순환 import 방지  
if TYPE_CHECKING:
    from database.connection_manager import DatabaseManager

from .schema_analyzer_tool import SchemaAnalyzerTool
from .sql_execution_tool import SQLExecutionTool

logger = logging.getLogger(__name__)

# Global instances for tools (will be initialized by setup_langchain_tools)
_schema_analyzer = None
_sql_executor = None

def setup_langchain_tools(db_manager: Optional["DatabaseManager"] = None, enable_simulation: bool = True):
    """
    Initialize global tool instances.
    
    Args:
        db_manager: Database manager instance (Optional, 순환 import 방지)
        enable_simulation: Whether to enable simulation mode
    """
    global _schema_analyzer, _sql_executor
    
    _schema_analyzer = SchemaAnalyzerTool(db_manager)
    _sql_executor = SQLExecutionTool(db_manager, enable_simulation=enable_simulation)
    
    logger.info("LangChain Tools 초기화 완료")

@tool
def get_database_schema(database_name: str = "northwind") -> str:
    """
    데이터베이스 스키마 정보를 조회합니다.
    
    Args:
        database_name: 조회할 데이터베이스 이름 (기본값: northwind)
    
    Returns:
        스키마 정보를 포함한 JSON 문자열
    """
    try:
        if _schema_analyzer is None:
            logger.error("Schema Analyzer가 초기화되지 않았습니다. setup_langchain_tools()를 먼저 호출하세요.")
            return json.dumps({
                "error": "Schema Analyzer가 초기화되지 않았습니다.",
                "suggestion": "setup_langchain_tools()를 먼저 호출하세요."
            }, ensure_ascii=False)
        
        # SchemaAnalyzerTool의 get_schema_as_json 메서드 사용
        schema_json = _schema_analyzer.get_schema_as_json(database_name)
        
        logger.info(f"스키마 조회 성공 - Database: {database_name}")
        return schema_json
        
    except Exception as e:
        error_msg = f"스키마 조회 오류: {str(e)}"
        logger.error(error_msg)
        return json.dumps({
            "error": error_msg,
            "database": database_name
        }, ensure_ascii=False)

@tool
def generate_sql_from_question(question: str) -> str:
    """
    LLM을 이용하여 자연어 질문을 SQL 쿼리로 변환합니다.
    
    Args:
        question: 자연어 질문
    
    Returns:
        생성된 SQL 쿼리와 설명을 포함한 JSON 문자열
    """
    try:
        from langchain_openai import AzureChatOpenAI
        from core.config import get_settings
        
        settings = get_settings()
        
        # Azure OpenAI LLM 초기화 (백오프 전략 포함)
        llm = AzureChatOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            azure_deployment=settings.azure_openai_deployment_name,
            temperature=0.1,  # 일관된 결과를 위해 낮은 온도
            max_tokens=1000,
            max_retries=3,      # 재시도 횟수 증가
            timeout=60,         # 타임아웃 증가
            request_timeout=60, # 요청 타임아웃 추가
            model_kwargs={
                "seed": 42,
                "frequency_penalty": 0.1,  # 반복 감소
                "presence_penalty": 0.1    # 다양성 증가
            }
        )
        
        # 먼저 스키마 정보를 가져옴
        schema_info = get_database_schema("northwind")
        schema_data = json.loads(schema_info)
        
        if "error" in schema_data:
            return json.dumps({
                "error": "스키마 정보를 가져올 수 없습니다.",
                "question": question
            }, ensure_ascii=False, indent=2)
        
        # LLM에게 전달할 프롬프트 구성
        prompt = f"""
당신은 PostgreSQL 전문가입니다. 주어진 Northwind 데이터베이스 스키마를 바탕으로 자연어 질문을 정확한 SQL 쿼리로 변환해주세요.

=== 데이터베이스 스키마 정보 ===
{json.dumps(schema_data, ensure_ascii=False, indent=2)}

=== 중요한 규칙 ===
1. PostgreSQL 문법을 사용하세요
2. **테이블명과 컬럼명은 스키마에 정의된 정확한 이름을 사용하세요**
   - customers 테이블의 컬럼: customerid, customername, contactname, address, city, postalcode, country
   - orders 테이블의 컬럼: order_id, customer_id, employee_id, order_date, required_date, shipped_date, ship_via, freight
   - order_details 테이블의 컬럼: order_id, product_id, unit_price, quantity, discount
   - 주의: customers.customerid와 orders.customer_id는 다른 이름입니다!
3. JOIN을 사용할 때는 적절한 FK 관계를 활용하세요:
   - customers.customerid = orders.customer_id (고객-주문)
   - orders.order_id = order_details.order_id (주문-주문상세)
   - products.product_id = order_details.product_id (제품-주문상세)
4. 날짜 관련 함수는 PostgreSQL 문법을 사용하세요 (EXTRACT, INTERVAL 등)
5. 결과는 의미있는 순서로 정렬하세요
6. LIMIT을 적절히 사용하여 결과를 제한하세요
7. 집계 함수 사용 시 GROUP BY를 적절히 활용하세요

=== 사용자 질문 ===
{question}

=== 응답 형식 ===
다음 JSON 형식으로만 응답하세요:
{{
    "sql_query": "생성된 SQL 쿼리",
    "explanation": "쿼리에 대한 한국어 설명",
    "confidence": "높음/보통/낮음"
}}

JSON 외의 다른 텍스트는 포함하지 마세요.
"""

        # LLM 호출 (백오프 전략 포함)
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                response = llm.invoke(prompt)
                break  # 성공하면 루프 종료
            except Exception as e:
                if "429" in str(e) or "rate_limit" in str(e).lower():
                    if attempt < max_attempts - 1:
                        wait_time = (2 ** attempt) * 2  # 지수 백오프 (2, 4, 8초)
                        logger.warning(f"API 레이트 제한 감지, {wait_time}초 대기 후 재시도 (시도 {attempt + 1}/{max_attempts})")
                        import time
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"API 레이트 제한으로 최대 재시도 횟수 초과: {e}")
                        raise e
                else:
                    # 다른 오류는 바로 전파
                    raise e
        response_text = response.content.strip()
        
        # JSON 파싱 시도
        try:
            # JSON 코드 블록이 있다면 제거
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].strip()
            
            sql_result = json.loads(response_text)
            
            # 필수 필드 검증
            if "sql_query" not in sql_result:
                raise ValueError("sql_query 필드가 없습니다")
            
            # 기본값 설정
            if "explanation" not in sql_result:
                sql_result["explanation"] = "LLM이 생성한 SQL 쿼리입니다."
            if "confidence" not in sql_result:
                sql_result["confidence"] = "보통"
            
            # 추가 정보
            sql_result["question"] = question
            sql_result["generation_method"] = "LLM"
            
            logger.info(f"LLM SQL 생성 성공 - 신뢰도: {sql_result.get('confidence', '보통')}")
            
            return json.dumps(sql_result, ensure_ascii=False, indent=2)
            
        except json.JSONDecodeError as e:
            logger.error(f"LLM 응답 JSON 파싱 실패: {e}, 응답: {response_text}")
            
            # 간단한 정규식으로 SQL 추출 시도
            import re
            sql_match = re.search(r'SELECT.*?(?=\}|$)', response_text, re.DOTALL | re.IGNORECASE)
            if sql_match:
                sql_query = sql_match.group(0).strip()
                return json.dumps({
                    "sql_query": sql_query,
                    "explanation": "LLM이 생성한 SQL 쿼리입니다 (JSON 파싱 실패로 추출)",
                    "question": question,
                    "generation_method": "LLM_fallback",
                    "confidence": "낮음"
                }, ensure_ascii=False, indent=2)
            
            # LLM 실패 시 패턴 매칭으로 폴백
            return _fallback_pattern_matching(question)
        
    except Exception as e:
        error_msg = f"LLM SQL 생성 실패: {str(e)}"
        logger.error(error_msg)
        
        # LLM 실패 시 패턴 매칭으로 폴백
        logger.info("LLM 실패, 패턴 매칭으로 폴백")
        return _fallback_pattern_matching(question)


def _attempt_column_correction(sql_query: str, error_msg: str) -> str:
    """
    컬럼명 오류를 감지하고 자동으로 수정을 시도합니다.
    
    Args:
        sql_query: 원본 SQL 쿼리
        error_msg: 오류 메시지
        
    Returns:
        수정된 SQL 쿼리 (수정할 수 없으면 원본 반환)
    """
    try:
        # 일반적인 컬럼명 매핑 (실제 스키마 기준)
        column_corrections = {
            # customers 테이블 (camelCase와 snake_case 모두 처리)
            'customer_name': 'customername',
            'customerName': 'customername',
            'contact_name': 'contactname', 
            'contactName': 'contactname',
            'postal_code': 'postalcode',
            'postalCode': 'postalcode',
            'customerId': 'customerid',  # customers 테이블에서는 customerid
            
            # orders 테이블
            'orderid': 'order_id',
            'orderId': 'order_id',
            'customerid': 'customer_id',  # orders 테이블에서는 customer_id
            'customerId': 'customer_id',
            'employeeid': 'employee_id',
            'employeeId': 'employee_id',
            'employee_id': 'employee_id',  # 이미 올바른 경우
            'orderdate': 'order_date',
            'orderDate': 'order_date',
            'requireddate': 'required_date',
            'requiredDate': 'required_date',
            'shippeddate': 'shipped_date',
            'shippedDate': 'shipped_date',
            'shipvia': 'ship_via',
            'shipVia': 'ship_via',
            
            # order_details 테이블
            'productid': 'product_id',
            'productId': 'product_id',
            'unitprice': 'unit_price',
            'unitPrice': 'unit_price',
            
            # products 테이블
            'product_name': 'productname',
            'productName': 'productname',
            'categoryid': 'category_id',
            'categoryId': 'category_id',
            'unitsinstock': 'units_in_stock',
            'unitsInStock': 'units_in_stock',
            'unitsonorder': 'units_on_order',
            'unitsOnOrder': 'units_on_order',
            'reorderlevel': 'reorder_level',
            'reorderLevel': 'reorder_level',
            
            # categories 테이블
            'category_name': 'categoryname',
            'categoryName': 'categoryname',
            
            # employees 테이블 (실제 컬럼명이 employeeid)
            'employee_id': 'employeeid',  # employees 테이블에서만
            'employeeId': 'employee_id',  # orders 테이블 기준으로 우선 처리
            'first_name': 'firstname',
            'firstName': 'firstname',
            'last_name': 'lastname',
            'lastName': 'lastname',
            'birth_date': 'birthdate',
            'birthDate': 'birthdate',
            'hire_date': 'hiredate',
            'hireDate': 'hiredate',
            
            # suppliers 테이블
            'supplier_id': 'supplierid',
            'supplierId': 'supplierid',
            'supplier_name': 'suppliername',
            'supplierName': 'suppliername',
            'contact_name': 'contactname',
            'contactName': 'contactname'
        }
        
        corrected_sql = sql_query
        
        # 대소문자 무관하게 컬럼명 교체
        for wrong_name, correct_name in column_corrections.items():
            # 단어 경계를 고려한 교체 (부분 문자열 교체 방지)
            import re
            pattern = r'\b' + re.escape(wrong_name) + r'\b'
            corrected_sql = re.sub(pattern, correct_name, corrected_sql, flags=re.IGNORECASE)
        
        # 변경사항이 있으면 로그 출력
        if corrected_sql != sql_query:
            logger.info(f"컬럼명 자동 수정 적용:\n원본: {sql_query}\n수정: {corrected_sql}")
        
        return corrected_sql
        
    except Exception as e:
        logger.error(f"컬럼명 자동 수정 중 오류: {e}")
        return sql_query


def _fallback_pattern_matching(question: str) -> str:
    """
    LLM 실패 시 사용할 패턴 매칭 폴백 함수
    """
    try:
        # 간단한 패턴 매칭 (우선순위 순으로 더 구체적인 패턴을 먼저 배치)
        simple_patterns = {
            # 카테고리별 제품 수 (더 유연한 패턴)
            r'카테고리.*제품|제품.*카테고리': (
                'SELECT c.categoryname, COUNT(p.product_id) as product_count FROM categories c LEFT JOIN products p ON c.categoryid = p.category_id GROUP BY c.categoryname ORDER BY product_count DESC',
                '카테고리별 제품 수를 계산합니다.'
            ),
            # 기본 개수 조회 (더 구체적인 패턴은 위에, 일반적인 패턴은 아래에)
            r'^고객\s*수\s*$|^고객\s*수\s*를|^고객\s*수\s*는|고객.*몇|전체\s*고객\s*수|전체\s*고객.*몇': ('SELECT COUNT(*) as customer_count FROM customers', '총 고객 수를 계산합니다.'),
            r'^제품\s*수\s*$|^제품\s*수\s*를|^제품\s*수\s*는|제품.*몇|전체\s*제품\s*수|전체\s*제품.*몇': ('SELECT COUNT(*) as product_count FROM products', '총 제품 수를 계산합니다.'),
            r'^주문\s*수\s*$|^주문\s*수\s*를|^주문\s*수\s*는|주문.*몇|전체\s*주문\s*수|전체\s*주문.*몇': ('SELECT COUNT(*) as order_count FROM orders', '총 주문 수를 계산합니다.'),
            r'고객별.*구매량.*(\d+)|구매량.*많은.*고객.*(\d+)': (
                '''SELECT 
                    c.customername,
                    c.contactname,
                    SUM(od.quantity) as total_quantity
                FROM customers c
                JOIN orders o ON c.customerid = o.customer_id
                JOIN order_details od ON o.order_id = od.order_id
                GROUP BY c.customerid, c.customername, c.contactname
                ORDER BY total_quantity DESC
                LIMIT {}''',
                '고객별 총 구매량을 계산합니다.'
            ),
            r'직원별.*판매|판매.*실적.*직원': (
                '''SELECT 
                    e.firstname, e.lastname,
                    COUNT(o.order_id) as total_orders,
                    SUM(od.quantity) as total_quantity
                FROM employees e
                LEFT JOIN orders o ON e.employeeid = o.employee_id
                LEFT JOIN order_details od ON o.order_id = od.order_id
                GROUP BY e.employeeid, e.firstname, e.lastname
                ORDER BY total_quantity DESC''',
                '직원별 판매 실적을 계산합니다.'
            ),
            r'월별.*매출|매출.*월별': (
                '''SELECT 
                    EXTRACT(YEAR FROM o.order_date) as year,
                    EXTRACT(MONTH FROM o.order_date) as month,
                    SUM(od.unit_price * od.quantity * (1 - od.discount)) as monthly_sales
                FROM orders o
                JOIN order_details od ON o.order_id = od.order_id
                GROUP BY EXTRACT(YEAR FROM o.order_date), EXTRACT(MONTH FROM o.order_date)
                ORDER BY year DESC, month DESC''',
                '월별 매출을 계산합니다.'
            )
        }
        
        import re
        
        for pattern, (sql_template, explanation) in simple_patterns.items():
            match = re.search(pattern, question, re.IGNORECASE)
            if match:
                if '{}' in sql_template and match.groups():
                    number = None
                    for group in match.groups():
                        if group and group.isdigit():
                            number = group
                            break
                    sql_query = sql_template.format(number or '5')
                else:
                    sql_query = sql_template
                
                return json.dumps({
                    "sql_query": sql_query,
                    "explanation": explanation,
                    "question": question,
                    "generation_method": "pattern_matching",
                    "confidence": "보통"
                }, ensure_ascii=False, indent=2)
        
        # 모든 패턴 매칭 실패
        return json.dumps({
            "error": "질문을 이해할 수 없습니다. 다른 방식으로 질문해 주세요.",
            "question": question,
            "suggestions": [
                "고객 수를 알려주세요",
                "제품 수는 몇 개인가요?",
                "카테고리별 제품 수를 보여주세요",
                "고객별 구매량 상위 5명을 보여주세요"
            ],
            "generation_method": "pattern_matching_failed"
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": f"패턴 매칭 폴백도 실패: {str(e)}",
            "question": question
        }, ensure_ascii=False, indent=2)

@tool
def execute_sql_query_sync(sql_query: str) -> str:
    """
    SQL 쿼리를 실행하고 결과를 반환합니다 (동기 버전).
    
    Args:
        sql_query: 실행할 SQL 쿼리
    
    Returns:
        쿼리 실행 결과를 포함한 JSON 문자열
    """
    try:
        if _sql_executor is None:
            logger.error("SQL Executor가 초기화되지 않았습니다. setup_langchain_tools()를 먼저 호출하세요.")
            return json.dumps({
                "success": False,
                "error": "SQL Executor가 초기화되지 않았습니다.",
                "suggestion": "setup_langchain_tools()를 먼저 호출하세요."
            }, ensure_ascii=False)
        
        # 실제 SQL 실행 (시뮬레이션 모드가 활성화된 경우만 시뮬레이션 사용)
        if _sql_executor.enable_simulation:
            results = _sql_executor._execute_simulated_query(sql_query, "northwind")
            simulation_used = True
        else:
            # 실제 데이터베이스에서 실행
            import asyncio
            
            # 비동기 메서드를 동기적으로 실행
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            if loop.is_running():
                # 이미 실행 중인 루프가 있는 경우 태스크 생성
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        lambda: asyncio.run(_sql_executor.execute_query(sql_query, "northwind"))
                    )
                    execution_result = future.result()
            else:
                execution_result = loop.run_until_complete(
                    _sql_executor.execute_query(sql_query, "northwind")
                )
            
            if execution_result.get('success'):
                results = execution_result.get('results', [])
                simulation_used = False
            else:
                error_msg = execution_result.get('error', '')
                
                # 컬럼명 오류인 경우 자동 수정 시도
                if 'column' in error_msg.lower() or 'does not exist' in error_msg.lower():
                    logger.info(f"컬럼명 오류 감지, 자동 수정 시도: {error_msg}")
                    corrected_sql = _attempt_column_correction(sql_query, error_msg)
                    
                    if corrected_sql != sql_query:
                        logger.info(f"수정된 SQL로 재시도: {corrected_sql}")
                        corrected_result = loop.run_until_complete(
                            _sql_executor.execute_query(corrected_sql, "northwind")
                        )
                        
                        if corrected_result.get('success'):
                            results = corrected_result.get('results', [])
                            simulation_used = False
                            logger.info("컬럼명 수정 후 실행 성공")
                        else:
                            # 수정 후에도 실패하면 시뮬레이션
                            results = _sql_executor._execute_simulated_query(sql_query, "northwind")
                            simulation_used = True
                            logger.warning(f"수정 후에도 실패, 시뮬레이션으로 대체: {corrected_result.get('error')}")
                    else:
                        # 수정할 수 없으면 시뮬레이션
                        results = _sql_executor._execute_simulated_query(sql_query, "northwind")
                        simulation_used = True
                        logger.warning(f"컬럼명 자동 수정 불가, 시뮬레이션으로 대체: {error_msg}")
                else:
                    # 다른 오류는 바로 시뮬레이션
                    results = _sql_executor._execute_simulated_query(sql_query, "northwind")
                    simulation_used = True
                    logger.warning(f"실제 SQL 실행 실패, 시뮬레이션으로 대체: {error_msg}")
        
        logger.info(f"SQL 실행 성공 - 결과: {len(results)}행 (시뮬레이션: {simulation_used})")
        
        return json.dumps({
            "success": True,
            "sql_query": sql_query,
            "results": results,
            "row_count": len(results),
            "simulation_mode": simulation_used
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        error_msg = f"SQL 실행 실패: {str(e)}"
        logger.error(error_msg)
        return json.dumps({
            "success": False,
            "error": error_msg,
            "sql_query": sql_query
        }, ensure_ascii=False, indent=2)

@tool
def validate_sql_query(sql_query: str, database: str = "northwind") -> str:
    """
    SQL 쿼리를 검증합니다.
    
    Args:
        sql_query: 검증할 SQL 쿼리
        database: 대상 데이터베이스 이름
    
    Returns:
        검증 결과를 포함한 JSON 문자열
    """
    try:
        if _sql_executor is None:
            return json.dumps({
                "is_valid": False,
                "error": "SQL Executor가 초기화되지 않았습니다."
            }, ensure_ascii=False)
        
        # 동기적으로 검증 (비동기 함수를 동기로 변환)
        import asyncio
        
        try:
            # 새 이벤트 루프가 필요한 경우
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        validation_result = loop.run_until_complete(
            _sql_executor.validate_query(sql_query, database)
        )
        
        logger.info(f"SQL 검증 완료 - 유효성: {validation_result['is_valid']}")
        return json.dumps(validation_result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        error_msg = f"SQL 검증 실패: {str(e)}"
        logger.error(error_msg)
        return json.dumps({
            "is_valid": False,
            "error": error_msg,
            "sql_query": sql_query
        }, ensure_ascii=False, indent=2)

# LangChain Agent에서 사용할 도구 목록
def get_langchain_tools():
    """
    LangChain Agent에서 사용할 도구 목록을 반환합니다.
    
    Returns:
        LangChain Tool 객체 리스트
    """
    return [
        get_database_schema,
        generate_sql_from_question,
        execute_sql_query_sync,
        validate_sql_query
    ]

# Agent 호환성을 위한 추가 유틸리티 함수들
def create_agent_compatible_tools(db_manager: Optional["DatabaseManager"], enable_simulation: bool = True):
    """
    Agent와 호환되는 도구 세트를 생성합니다.
    
    Args:
        db_manager: 데이터베이스 매니저
        enable_simulation: 시뮬레이션 모드 활성화
        
    Returns:
        초기화된 도구 목록
    """
    setup_langchain_tools(db_manager, enable_simulation)
    return get_langchain_tools()

def get_tool_descriptions():
    """
    도구 설명 정보를 반환합니다.
    
    Returns:
        도구별 설명 딕셔너리
    """
    return {
        "get_database_schema": "데이터베이스 스키마 정보 조회",
        "generate_sql_from_question": "자연어 질문을 SQL로 변환",
        "execute_sql_query_sync": "SQL 쿼리 실행 (동기 버전)",
        "validate_sql_query": "SQL 쿼리 검증"
    }