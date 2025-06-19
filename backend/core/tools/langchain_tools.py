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
    자연어 질문을 SQL 쿼리로 변환합니다.
    
    Args:
        question: 자연어 질문
    
    Returns:
        생성된 SQL 쿼리와 설명을 포함한 JSON 문자열
    """
    try:
        # 기본 패턴 매칭 기반 SQL 생성 (올바른 PostgreSQL Northwind 스키마 사용)
        sql_patterns = {
            r'고객\s*수': ('SELECT COUNT(*) as customer_count FROM customers', '데이터베이스의 총 고객 수를 계산합니다.'),
            r'제품\s*수': ('SELECT COUNT(*) as product_count FROM products', '데이터베이스의 총 제품 수를 계산합니다.'),
            r'주문\s*수': ('SELECT COUNT(*) as order_count FROM orders', '데이터베이스의 총 주문 수를 계산합니다.'),
            r'어떤\s*제품이?\s*가장\s*많이\s*주문': (
                '''SELECT p.product_name, SUM(od.quantity) AS total_quantity 
                FROM order_details od 
                JOIN products p ON od.product_id = p.product_id 
                GROUP BY p.product_name 
                ORDER BY total_quantity DESC LIMIT 1''',
                '가장 많이 주문된 제품을 조회합니다.'
            ),
            r'(\d{4})년.*월별.*매출': (
                '''SELECT 
                    EXTRACT(MONTH FROM o.order_date) as month,
                    ROUND(SUM(od.quantity * od.unit_price * (1 - od.discount)), 2) as total_sales
                FROM orders o 
                JOIN order_details od ON o.order_id = od.order_id 
                WHERE EXTRACT(YEAR FROM o.order_date) = {}
                GROUP BY EXTRACT(MONTH FROM o.order_date)
                ORDER BY month''',
                '지정된 연도의 월별 매출을 계산합니다.'
            ),
            r'매출.*현황|매출.*분석': (
                '''SELECT 
                    EXTRACT(YEAR FROM o.order_date) as year,
                    EXTRACT(MONTH FROM o.order_date) as month,
                    ROUND(SUM(od.quantity * od.unit_price * (1 - od.discount)), 2) as total_sales,
                    COUNT(DISTINCT o.order_id) as order_count
                FROM orders o 
                JOIN order_details od ON o.order_id = od.order_id 
                GROUP BY EXTRACT(YEAR FROM o.order_date), EXTRACT(MONTH FROM o.order_date)
                ORDER BY year DESC, month DESC
                LIMIT 12''',
                '최근 12개월의 매출 현황을 분석합니다.'
            ),
            r'카테고리별\s*제품': (
                'SELECT c.category_name, COUNT(p.product_id) as product_count FROM categories c LEFT JOIN products p ON c.category_id = p.category_id GROUP BY c.category_name ORDER BY product_count DESC',
                '카테고리별 제품 수를 계산합니다.'
            ),
            r'가장\s*비싼\s*제품\s*(\d+)개?': (
                'SELECT product_name, unit_price FROM products ORDER BY unit_price DESC LIMIT {}',
                '가격이 높은 순으로 제품을 조회합니다.'
            ),
            r'주문이?\s*가장\s*많은\s*고객': (
                'SELECT c.company_name, COUNT(o.order_id) as order_count FROM customers c LEFT JOIN orders o ON c.customer_id = o.customer_id GROUP BY c.customer_id, c.company_name ORDER BY order_count DESC LIMIT 10',
                '주문 건수가 많은 고객을 조회합니다.'
            ),
            r'국가별\s*고객\s*수': (
                'SELECT country, COUNT(*) as customer_count FROM customers GROUP BY country ORDER BY customer_count DESC',
                '국가별 고객 수를 계산합니다.'
            ),
            r'직원별\s*.*주문': (
                'SELECT e.first_name || \' \' || e.last_name as employee_name, COUNT(o.order_id) as order_count FROM employees e LEFT JOIN orders o ON e.employee_id = o.employee_id GROUP BY e.employee_id, employee_name ORDER BY order_count DESC',
                '직원별 처리한 주문 수를 계산합니다.'
            ),
            r'배송업체별\s*.*주문': (
                'SELECT s.company_name, COUNT(o.order_id) as order_count FROM shippers s LEFT JOIN orders o ON s.shipper_id = o.ship_via GROUP BY s.shipper_id, s.company_name ORDER BY order_count DESC',
                '배송업체별 주문 수를 계산합니다.'
            )
        }
        
        import re
        
        # 패턴 매칭
        for pattern, (sql_template, explanation) in sql_patterns.items():
            match = re.search(pattern, question)
            if match:
                # 숫자가 있는 경우 처리
                if '{}' in sql_template and match.groups():
                    sql_query = sql_template.format(match.group(1))
                else:
                    sql_query = sql_template
                
                logger.info(f"SQL 생성 성공 - 패턴: {pattern}")
                
                return json.dumps({
                    "sql_query": sql_query,
                    "explanation": explanation,
                    "question": question,
                    "pattern_matched": pattern
                }, ensure_ascii=False, indent=2)
        
        # 패턴 매칭 실패
        logger.warning(f"패턴 매칭 실패 - 질문: {question}")
        return json.dumps({
            "error": "질문을 이해할 수 없습니다. 다른 방식으로 질문해 주세요.",
            "question": question,
            "suggestions": [
                "고객 수를 알려주세요",
                "제품 수는 몇 개인가요?",
                "카테고리별 제품 수를 보여주세요",
                "1997년 월별 매출 현황을 보여주세요",
                "매출 분석을 해주세요"
            ]
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        error_msg = f"SQL 생성 실패: {str(e)}"
        logger.error(error_msg)
        return json.dumps({
            "error": error_msg,
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
                # 실제 실행 실패 시 시뮬레이션으로 대체
                results = _sql_executor._execute_simulated_query(sql_query, "northwind")
                simulation_used = True
                logger.warning(f"실제 SQL 실행 실패, 시뮬레이션으로 대체: {execution_result.get('error')}")
        
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