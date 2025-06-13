"""
SQL Agent for Text-to-SQL application.
Handles natural language to SQL conversion and execution.
Enhanced with successful patterns from Jupyter notebook testing.
"""

import logging
import time
import re
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

from .base_agent import BaseAgent
from utils.logging_config import SQLLogger

logger = logging.getLogger(__name__)

class SQLAgent(BaseAgent):
    """
    SQL Agent wrapper that extends the core SQL agent functionality.
    Enhanced with successful patterns from Jupyter notebook testing.
    """
    
    def __init__(self, db_manager=None):
        """Initialize SQL Agent with database manager."""
        super().__init__(db_manager)

        # 로거 설정
        self.logger = logging.getLogger(__name__)
        self.sql_logger = logging.getLogger("sql_queries")
        
        # PostgreSQL Northwind에 최적화된 쿼리 패턴 (주피터 노트북에서 성공한 패턴)
        self.query_patterns = {
            # 기본 COUNT 쿼리들
            r'고객\s*수': 'SELECT COUNT(*) as customer_count FROM customers',
            r'제품\s*수': 'SELECT COUNT(*) as product_count FROM products',
            r'주문\s*수': 'SELECT COUNT(*) as order_count FROM orders',
            r'카테고리\s*수': 'SELECT COUNT(*) as category_count FROM categories',
            r'직원\s*수': 'SELECT COUNT(*) as employee_count FROM employees',
            r'공급업체\s*수': 'SELECT COUNT(*) as supplier_count FROM suppliers',
            r'배송업체\s*수': 'SELECT COUNT(*) as shipper_count FROM shippers',
            
            # English COUNT queries
            r'how\s+many\s+customers?': 'SELECT COUNT(*) as customer_count FROM customers',
            r'how\s+many\s+products?': 'SELECT COUNT(*) as product_count FROM products',
            r'how\s+many\s+orders?': 'SELECT COUNT(*) as order_count FROM orders',
            r'customer\s+count': 'SELECT COUNT(*) as customer_count FROM customers',
            r'product\s+count': 'SELECT COUNT(*) as product_count FROM products',
            
            # 카테고리별 분석
            r'카테고리별\s*제품\s*수': '''
                SELECT c.categoryname, COUNT(p.productid) as product_count 
                FROM categories c 
                LEFT JOIN products p ON c.categoryid = p.categoryid 
                GROUP BY c.categoryname, c.categoryid 
                ORDER BY product_count DESC
            ''',
            r'제품\s*카테고리\s*별': '''
                SELECT c.categoryname, COUNT(p.productid) as product_count 
                FROM categories c 
                LEFT JOIN products p ON c.categoryid = p.categoryid 
                GROUP BY c.categoryname, c.categoryid 
                ORDER BY product_count DESC
            ''',
            
            # 가격 기반 쿼리
            r'가장\s*비싼\s*제품\s*(\d+)개?': '''
                SELECT productname, price, c.categoryname
                FROM products p
                LEFT JOIN categories c ON p.categoryid = c.categoryid
                ORDER BY price DESC NULLS LAST
                LIMIT {}
            ''',
            r'비싼\s*제품\s*(\d+)개?': '''
                SELECT productname, price, c.categoryname
                FROM products p
                LEFT JOIN categories c ON p.categoryid = c.categoryid
                ORDER BY price DESC NULLS LAST
                LIMIT {}
            ''',
            r'가격\s*높은\s*제품': '''
                SELECT productname, price, c.categoryname
                FROM products p
                LEFT JOIN categories c ON p.categoryid = c.categoryid
                ORDER BY price DESC NULLS LAST
                LIMIT 10
            ''',
            
            # 고객 분석
            r'주문이?\s*가장\s*많은\s*고객\s*(\d+)명?': '''
                SELECT c.customername, COUNT(o.orderid) as order_count
                FROM customers c
                LEFT JOIN orders o ON c.customerid = o.customerid
                GROUP BY c.customerid, c.customername
                ORDER BY order_count DESC
                LIMIT {}
            ''',
            r'주문\s*많은\s*고객': '''
                SELECT c.customername, COUNT(o.orderid) as order_count
                FROM customers c
                LEFT JOIN orders o ON c.customerid = o.customerid
                GROUP BY c.customerid, c.customername
                ORDER BY order_count DESC
                LIMIT 10
            ''',
            r'고객별\s*주문\s*수': '''
                SELECT c.customername, COUNT(o.orderid) as order_count
                FROM customers c
                LEFT JOIN orders o ON c.customerid = o.customerid
                GROUP BY c.customerid, c.customername
                ORDER BY order_count DESC
                LIMIT 20
            ''',
            
            # 국가별 분석
            r'국가별\s*고객\s*수': '''
                SELECT country, COUNT(*) as customer_count
                FROM customers
                WHERE country IS NOT NULL
                GROUP BY country
                ORDER BY customer_count DESC
            ''',
            r'나라별\s*고객': '''
                SELECT country, COUNT(*) as customer_count
                FROM customers
                WHERE country IS NOT NULL
                GROUP BY country
                ORDER BY customer_count DESC
            ''',
            
            # 직원 분석
            r'직원별\s*.*주문\s*수': '''
                SELECT e.firstname || ' ' || e.lastname as employee_name, 
                       COUNT(o.orderid) as order_count
                FROM employees e
                LEFT JOIN orders o ON e.employeeid = o.employeeid
                GROUP BY e.employeeid, employee_name
                ORDER BY order_count DESC
            ''',
            r'직원\s*성과': '''
                SELECT e.firstname || ' ' || e.lastname as employee_name, 
                       COUNT(o.orderid) as order_count
                FROM employees e
                LEFT JOIN orders o ON e.employeeid = o.employeeid
                GROUP BY e.employeeid, employee_name
                ORDER BY order_count DESC
            ''',
            
            # 배송업체 분석
            r'배송업체별\s*.*주문\s*수': '''
                SELECT s.shippername, COUNT(o.orderid) as order_count
                FROM shippers s
                LEFT JOIN orders o ON s.shipperid = o.shipperid
                GROUP BY s.shipperid, s.shippername
                ORDER BY order_count DESC
            ''',
            r'배송\s*회사\s*별': '''
                SELECT s.shippername, COUNT(o.orderid) as order_count
                FROM shippers s
                LEFT JOIN orders o ON s.shipperid = o.shipperid
                GROUP BY s.shipperid, s.shippername
                ORDER BY order_count DESC
            ''',
            
            # 인기 제품
            r'가장\s*인기\s*있는\s*제품\s*(\d+)개?': '''
                SELECT p.productname, SUM(od.quantity) as total_quantity
                FROM products p
                JOIN orderdetails od ON p.productid = od.productid
                GROUP BY p.productid, p.productname
                ORDER BY total_quantity DESC
                LIMIT {}
            ''',
            r'인기\s*제품': '''
                SELECT p.productname, SUM(od.quantity) as total_quantity
                FROM products p
                JOIN orderdetails od ON p.productid = od.productid
                GROUP BY p.productid, p.productname
                ORDER BY total_quantity DESC
                LIMIT 10
            ''',
            
            # 월별 분석 (PostgreSQL 문법)
            r'월별\s*주문\s*수': '''
                SELECT DATE_TRUNC('month', orderdate) as month,
                       COUNT(*) as order_count
                FROM orders
                WHERE orderdate IS NOT NULL
                GROUP BY DATE_TRUNC('month', orderdate)
                ORDER BY month DESC
                LIMIT 12
            ''',
            
            # 기본 조회 쿼리들
            r'고객\s*목록': 'SELECT customerid, customername, country FROM customers LIMIT 20',
            r'제품\s*목록': 'SELECT productid, productname, price FROM products LIMIT 20',
            r'주문\s*목록': 'SELECT orderid, customerid, orderdate FROM orders ORDER BY orderdate DESC LIMIT 20',
            r'카테고리\s*목록': 'SELECT categoryid, categoryname, description FROM categories',
            
            # English patterns
            r'show\s+me\s+customers?': 'SELECT customerid, customername, country FROM customers LIMIT 20',
            r'show\s+me\s+products?': 'SELECT productid, productname, price FROM products LIMIT 20',
            r'list\s+customers?': 'SELECT customerid, customername, country FROM customers LIMIT 20',
            r'list\s+products?': 'SELECT productid, productname, price FROM products LIMIT 20',
            
            # 복합 분석 쿼리
            r'카테고리별\s*평균\s*가격': '''
                SELECT c.categoryname, 
                       ROUND(AVG(p.price), 2) as avg_price,
                       COUNT(p.productid) as product_count
                FROM categories c
                LEFT JOIN products p ON c.categoryid = p.categoryid
                WHERE p.price IS NOT NULL
                GROUP BY c.categoryid, c.categoryname
                ORDER BY avg_price DESC
            '''
        }
        
        # 패턴 매핑 로깅
        self.logger.info(f"SQL Agent 초기화 완료 - {len(self.query_patterns)}개 패턴 로드됨 (PostgreSQL Northwind 최적화)")
    
    def generate_sql_sync(self, question: str) -> Tuple[str, str]:
        """
        동기 버전의 SQL 생성 메서드 (주피터 노트북에서 성공한 패턴).
        
        Args:
            question: 자연어 질문
            
        Returns:
            Tuple of (sql_query, explanation)
        """
        question_lower = question.lower().strip()
        
        self.logger.info(f"🔍 Analyzing question: '{question}'")
        
        # 패턴 매칭
        for pattern, sql_template in self.query_patterns.items():
            match = re.search(pattern, question_lower)
            if match:
                self.logger.info(f"📝 Matched pattern: {pattern}")
                
                # 숫자 매개변수가 있는 패턴 처리
                if '{}' in sql_template and match.groups():
                    try:
                        number = match.group(1)
                        sql_query = sql_template.format(number)
                        explanation = f"상위 {number}개의 결과를 조회합니다."
                    except (IndexError, ValueError):
                        sql_query = sql_template.replace('{}', '10')
                        explanation = "상위 10개의 결과를 조회합니다."
                else:
                    sql_query = sql_template.strip()
                    explanation = self._get_korean_explanation_for_pattern(pattern)
                
                self.logger.info(f"✅ Generated SQL: {sql_query[:100]}...")
                return sql_query, explanation
        
        # 패턴 매칭 실패 시 fallback
        self.logger.warning(f"⚠️ No pattern matched for question: '{question}'")
        return self._get_fallback_query(question_lower)
    
    def _get_fallback_query(self, question_lower: str) -> Tuple[str, str]:
        """
        패턴 매칭 실패 시 fallback 쿼리 생성.
        
        Args:
            question_lower: 소문자로 변환된 질문
            
        Returns:
            Tuple of (sql_query, explanation)
        """
        # 키워드 기반 fallback
        if any(word in question_lower for word in ['customer', 'customers', '고객']):
            return (
                'SELECT customerid, customername, country FROM customers LIMIT 10',
                '고객 정보를 조회합니다.'
            )
        elif any(word in question_lower for word in ['product', 'products', '제품', '상품']):
            return (
                'SELECT productid, productname, price FROM products LIMIT 10',
                '제품 정보를 조회합니다.'
            )
        elif any(word in question_lower for word in ['order', 'orders', '주문']):
            return (
                'SELECT orderid, customerid, orderdate FROM orders ORDER BY orderdate DESC LIMIT 10',
                '최근 주문 정보를 조회합니다.'
            )
        elif any(word in question_lower for word in ['category', 'categories', '카테고리']):
            return (
                'SELECT categoryid, categoryname, description FROM categories',
                '카테고리 정보를 조회합니다.'
            )
        else:
            return (
                "SELECT 'PostgreSQL Northwind 데이터베이스에 대해 질문해 주세요. 예: 고객 수, 제품 수, 카테고리별 제품 수' as message",
                '질문을 이해하지 못했습니다. 더 구체적으로 질문해 주세요.'
            )
    
    def execute_query_sync(
        self,
        question: str,
        database: str = "northwind",
        include_explanation: bool = True,
        max_rows: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        동기 버전의 쿼리 실행 메서드 (시뮬레이션 모드).
        주피터 노트북에서 성공한 패턴을 기반으로 함.
        
        Args:
            question: 자연어 질문
            database: 대상 데이터베이스
            include_explanation: 설명 포함 여부
            max_rows: 최대 행 수
            
        Returns:
            실행 결과 딕셔너리
        """
        start_time = time.time()
        
        try:
            # SQL 생성
            sql_query, explanation = self.generate_sql_sync(question)
            
            # 시뮬레이션된 결과 생성
            results = self._execute_simulated_query(sql_query, max_rows)
            
            execution_time = time.time() - start_time
            
            self.logger.info(
                f"✅ 동기 쿼리 실행 완료 - 시간: {execution_time:.3f}s, 결과: {len(results)}행"
            )
            
            response = {
                "success": True,
                "sql_query": sql_query,
                "results": results,
                "row_count": len(results),
                "execution_time": execution_time,
                "database": database,
                "question": question
            }
            
            if include_explanation:
                response["explanation"] = explanation
                
            return response
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            
            self.logger.error(f"❌ 동기 쿼리 실행 실패: {error_msg}")
            
            return {
                "success": False,
                "error": error_msg,
                "execution_time": execution_time,
                "question": question,
                "database": database,
                "results": [],
                "row_count": 0
            }
    
    def _execute_simulated_query(self, sql_query: str, max_rows: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        시뮬레이션된 쿼리 실행 (주피터 노트북에서 성공한 패턴).
        
        Args:
            sql_query: 실행할 SQL 쿼리
            max_rows: 최대 행 수
            
        Returns:
            시뮬레이션된 결과 목록
        """
        sql_upper = sql_query.upper().strip()
        
        # COUNT 쿼리 처리
        if "COUNT(*)" in sql_upper:
            if "CUSTOMERS" in sql_upper:
                return [{"customer_count": 91}]
            elif "PRODUCTS" in sql_upper:
                return [{"product_count": 77}]
            elif "ORDERS" in sql_upper:
                return [{"order_count": 196}]
            elif "CATEGORIES" in sql_upper:
                return [{"category_count": 8}]
            elif "EMPLOYEES" in sql_upper:
                return [{"employee_count": 10}]
            elif "SUPPLIERS" in sql_upper:
                return [{"supplier_count": 29}]
            elif "SHIPPERS" in sql_upper:
                return [{"shipper_count": 3}]
            else:
                return [{"count": 0}]
        
        # GROUP BY 쿼리 처리
        elif "GROUP BY" in sql_upper:
            if "CATEGORYNAME" in sql_upper:
                return [
                    {"categoryname": "음료", "product_count": 12},
                    {"categoryname": "과자류", "product_count": 13},
                    {"categoryname": "유제품", "product_count": 10},
                    {"categoryname": "해산물", "product_count": 12},
                    {"categoryname": "조미료", "product_count": 12},
                    {"categoryname": "육류/가금류", "product_count": 6},
                    {"categoryname": "농산물", "product_count": 5},
                    {"categoryname": "곡물/시리얼", "product_count": 7}
                ]
            elif "COUNTRY" in sql_upper:
                return [
                    {"country": "Germany", "customer_count": 11},
                    {"country": "Mexico", "customer_count": 5},
                    {"country": "UK", "customer_count": 7},
                    {"country": "Brazil", "customer_count": 9},
                    {"country": "France", "customer_count": 11},
                    {"country": "Spain", "customer_count": 5},
                    {"country": "Canada", "customer_count": 3}
                ]
            elif "EMPLOYEE_NAME" in sql_upper:
                return [
                    {"employee_name": "Margaret Peacock", "order_count": 40},
                    {"employee_name": "Janet Leverling", "order_count": 31},
                    {"employee_name": "Nancy Davolio", "order_count": 29},
                    {"employee_name": "Andrew Fuller", "order_count": 25},
                    {"employee_name": "Robert King", "order_count": 18}
                ]
            elif "SHIPPERNAME" in sql_upper:
                return [
                    {"shippername": "United Package", "order_count": 74},
                    {"shippername": "Speedy Express", "order_count": 54},
                    {"shippername": "Federal Shipping", "order_count": 68}
                ]
        
        # 가격 순 정렬 쿼리
        elif "ORDER BY PRICE DESC" in sql_upper:
            limit = max_rows if max_rows else 5
            products = [
                {"productname": "Côte de Blaye", "price": 263.50, "categoryname": "음료"},
                {"productname": "Thüringer Rostbratwurst", "price": 123.79, "categoryname": "육류/가금류"},
                {"productname": "Mishi Kobe Niku", "price": 97.00, "categoryname": "육류/가금류"},
                {"productname": "Sir Rodney's Marmalade", "price": 81.00, "categoryname": "과자류"},
                {"productname": "Carnarvon Tigers", "price": 62.50, "categoryname": "해산물"},
                {"productname": "Raclette Courdavault", "price": 55.00, "categoryname": "유제품"},
                {"productname": "Manjimup Dried Apples", "price": 53.00, "categoryname": "농산물"}
            ]
            return products[:limit]
        
        # 기본 테이블 조회
        elif "SELECT" in sql_upper:
            if "CUSTOMERS" in sql_upper:
                return [
                    {"customerid": 1, "customername": "Alfreds Futterkiste", "country": "Germany"},
                    {"customerid": 2, "customername": "Ana Trujillo", "country": "Mexico"},
                    {"customerid": 3, "customername": "Antonio Moreno", "country": "Mexico"}
                ]
            elif "PRODUCTS" in sql_upper:
                return [
                    {"productid": 1, "productname": "Chais", "price": 18.00},
                    {"productid": 2, "productname": "Chang", "price": 19.00},
                    {"productid": 3, "productname": "Aniseed Syrup", "price": 10.00}
                ]
            elif "ORDERS" in sql_upper:
                return [
                    {"orderid": 10248, "customerid": 1, "orderdate": "1996-07-04"},
                    {"orderid": 10249, "customerid": 2, "orderdate": "1996-07-05"},
                    {"orderid": 10250, "customerid": 3, "orderdate": "1996-07-08"}
                ]
            elif "CATEGORIES" in sql_upper:
                return [
                    {"categoryid": 1, "categoryname": "음료", "description": "음료, 커피, 차, 맥주, 와인"},
                    {"categoryid": 2, "categoryname": "조미료", "description": "달콤하고 짭짤한 소스, 양념, 스프레드"},
                    {"categoryid": 3, "categoryname": "과자류", "description": "디저트, 캔디, 달콤한 빵"}
                ]
        
        # 메시지 쿼리
        else:
            return [{"message": "PostgreSQL Northwind 데이터베이스에 대해 질문해 주세요."}]

    async def execute_query(
        self,
        question: str,
        database: str = "northwind",
        context: Optional[str] = None,
        user_id: Optional[int] = None,
        include_explanation: bool = True,
        max_rows: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute a natural language query and return results.
        
        Args:
            question: Natural language question
            database: Target database name
            context: Additional context for the query
            user_id: User ID for logging and analytics
            include_explanation: Whether to include SQL explanation
            max_rows: Maximum number of rows to return
            
        Returns:
            Dictionary containing query results and metadata
        """
        start_time = time.time()
        
        # 쿼리 실행 시작 로깅
        self.logger.info(
            f"🤖 SQL Agent 쿼리 실행 시작",
            extra={
                'user_id': user_id,
                'question': question[:100] + '...' if len(question) > 100 else question,
                'database': database,
                'include_explanation': include_explanation,
                'max_rows': max_rows,
                'context_provided': context is not None
            }
        )
        
        try:
            # SQL 생성 단계
            self.logger.debug(f"🔍 자연어 -> SQL 변환 시작")
            sql_query, explanation = self._generate_sql(question)
            
            generation_time = time.time() - start_time
            
            self.logger.info(
                f"📝 SQL 생성 완료 - 시간: {generation_time:.3f}s",
                extra={
                    'user_id': user_id,
                    'sql_query': sql_query[:200] + '...' if len(sql_query) > 200 else sql_query,
                    'explanation': explanation[:100] + '...' if len(explanation) > 100 else explanation,
                    'generation_time': generation_time,
                    'has_explanation': bool(explanation)
                }
            )
            
            if not sql_query:
                error_msg = "SQL 쿼리 생성 실패 - 질문을 이해할 수 없습니다"
                self.logger.error(error_msg, extra={'user_id': user_id, 'question': question})
                raise ValueError("Could not generate SQL query from the question")
            
            # SQL 실행 단계
            self.logger.debug(f"🗄️ SQL 실행 시작 - Database: {database}")
            execution_start = time.time()
            
            results = await self._execute_sql(sql_query, database, max_rows)
            
            sql_execution_time = time.time() - execution_start
            total_execution_time = time.time() - start_time
            
            # SQL 실행 로깅
            SQLLogger.log_query_execution(
                query=sql_query,
                execution_time=sql_execution_time,
                result_count=len(results),
                user_id=str(user_id) if user_id else None,
                success=True
            )
            
            self.logger.info(
                f"⏱️ SQL 실행 완료 - 시간: {sql_execution_time:.3f}s, 결과: {len(results)}행",
                extra={
                    'user_id': user_id,
                    'sql_execution_time': sql_execution_time,
                    'total_execution_time': total_execution_time,
                    'result_count': len(results),
                    'database': database
                }
            )
            
            # 성공 결과 반환
            result = {
                "sql_query": sql_query,
                "results": results,
                "explanation": explanation if include_explanation else None,
                "execution_time": total_execution_time,
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": user_id,
                "database": database,
                "success": True,
                "performance_metrics": {
                    "generation_time": generation_time,
                    "sql_execution_time": sql_execution_time,
                    "total_time": total_execution_time
                }
            }
            
            self.logger.info(
                f"✅ SQL Agent 쿼리 실행 성공 - 총 시간: {total_execution_time:.3f}s",
                extra={'user_id': user_id, 'success': True, 'total_time': total_execution_time}
            )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_message = str(e)
            
            # 오류 로깅
            self.logger.error(
                f"❌ SQL Agent 쿼리 실행 실패 - 시간: {execution_time:.3f}s, 오류: {error_message}",
                extra={
                    'user_id': user_id,
                    'question': question,
                    'execution_time': execution_time,
                    'error_details': error_message,
                    'database': database
                },
                exc_info=True
            )
            
            # SQL 실행 실패 로깅
            SQLLogger.log_query_execution(
                query=sql_query if 'sql_query' in locals() else "",
                execution_time=execution_time,
                result_count=0,
                user_id=str(user_id) if user_id else None,
                success=False,
                error_message=error_message
            )
            
            return {
                "sql_query": "",
                "results": [],
                "explanation": None,
                "execution_time": execution_time,
                "error": error_message,
                "success": False
            }

    def _generate_sql(self, question: str) -> tuple[str, str]:
        """
        Generate SQL query from natural language question.
        
        Args:
            question: Natural language question
            
        Returns:
            Tuple of (sql_query, explanation)
        """
        question_lower = question.lower().strip()
        
        logger.info(f"🔍 Analyzing question: '{question_lower}'")
        
        # Try to match patterns
        for pattern, sql_template in self.query_patterns.items():
            match = re.search(pattern, question_lower)
            if match:
                logger.info(f"📝 Matched pattern: {pattern}")
                
                # Handle different types of matches
                if '{}' in sql_template:
                    if 'from' in pattern and match.groups():
                        # Country-based customer query
                        country = match.group(1).title()
                        sql_query = sql_template.format(country)
                        explanation = f"{country} 국가의 고객을 조회합니다."
                    elif 'top' in pattern and match.groups():
                        # Top N customers query
                        limit = match.group(1)
                        sql_query = sql_template.format(limit)
                        explanation = f"주문 횟수가 많은 상위 {limit}명의 고객을 조회합니다."
                    elif '가장\s*많이\s*팔린\s*제품' in pattern and match.groups():
                        # Top selling products
                        limit = match.group(1)
                        sql_query = sql_template.format(limit)
                        explanation = f"가장 많이 팔린 상위 {limit}개 제품을 조회합니다."
                    else:
                        sql_query = sql_template
                        explanation = self._get_korean_explanation_for_pattern(pattern)
                else:
                    sql_query = sql_template
                    explanation = self._get_explanation_for_query(sql_query)
                
                logger.info(f"✅ Generated SQL: {sql_query}")
                return sql_query, explanation
        
        # If no pattern matches, try to generate a basic query
        logger.warning(f"⚠️ No pattern matched for question: '{question}'")
        logger.info(f"🔍 Checking fallback keywords in: '{question_lower}'")
        
        # Default fallback queries (English and Korean)
        if any(word in question_lower for word in ['customer', 'customers', '고객']):
            logger.info("📝 Fallback: Customer query detected")
            sql_query = "SELECT customer_id, company_name, country FROM customers LIMIT 10"
            explanation = "고객 정보를 조회합니다."
        elif any(word in question_lower for word in ['product', 'products', '제품', '상품']):
            logger.info("📝 Fallback: Product query detected")
            sql_query = "SELECT product_id, product_name, unit_price FROM products LIMIT 10"
            explanation = "제품 정보를 조회합니다."
        elif any(word in question_lower for word in ['order', 'orders', '주문', '주문서']):
            logger.info("📝 Fallback: Order query detected")
            sql_query = "SELECT order_id, customer_id, order_date FROM orders LIMIT 10"
            explanation = "주문 정보를 조회합니다."
        elif any(word in question_lower for word in ['매출', '판매', 'sales', 'revenue']):
            logger.info("📝 Fallback: Sales/Revenue query detected")
            sql_query = '''
                SELECT 
                    strftime('%Y-%m', o.order_date) as month,
                    ROUND(SUM(od.unit_price * od.quantity * (1 - od.discount)), 2) as total_sales
                FROM orders o
                JOIN order_details od ON o.order_id = od.order_id
                WHERE o.order_date IS NOT NULL
                GROUP BY strftime('%Y-%m', o.order_date)
                ORDER BY month DESC
                LIMIT 12
            '''
            explanation = "최근 12개월간의 월별 매출 데이터를 조회합니다."
        else:
            # Very basic fallback
            logger.warning("📝 No fallback keyword matched, using generic message")
            sql_query = "SELECT 'I need more specific information to generate a proper query' as message"
            explanation = "질문을 이해하지 못했습니다. 고객, 제품, 주문, 매출에 대해 질문해보세요."
        
        logger.info(f"🔄 Using fallback SQL: {sql_query}")
        return sql_query, explanation
    
    def _get_korean_explanation_for_pattern(self, pattern: str) -> str:
        """Generate Korean explanation for pattern."""
        if '월별\s*매출\s*추이' in pattern:
            return "월별 매출 추이를 분석하여 시간에 따른 매출 변화를 보여줍니다."
        elif '고객\s*수' in pattern:
            return "데이터베이스에 등록된 총 고객 수를 조회합니다."
        elif '제품\s*수' in pattern:
            return "데이터베이스에 등록된 총 제품 수를 조회합니다."
        elif '주문\s*수' in pattern:
            return "데이터베이스에 등록된 총 주문 수를 조회합니다."
        elif '카테고리별\s*제품' in pattern:
            return "각 카테고리별로 제품 수를 집계하여 보여줍니다."
        elif '카테고리별\s*평균\s*주문\s*금액' in pattern:
            return "각 카테고리별 평균 주문 금액을 계산하여 보여줍니다."
        elif '고객별\s*주문\s*횟수' in pattern:
            return "각 고객별 주문 횟수를 집계하여 상위 고객을 보여줍니다."
        elif '국가별\s*고객\s*수' in pattern:
            return "국가별로 고객 수를 집계하여 보여줍니다."
        elif '직원별\s*매출' in pattern:
            return "각 직원별 매출 실적을 집계하여 보여줍니다."
        else:
            return "질문에 기반하여 데이터베이스에서 정보를 조회합니다."

    def _get_explanation_for_query(self, sql_query: str) -> str:
        """Generate explanation for SQL query."""
        sql_lower = sql_query.lower()
        
        if 'count(*)' in sql_lower:
            if 'customers' in sql_lower:
                return "데이터베이스의 총 고객 수를 계산합니다."
            elif 'products' in sql_lower:
                return "데이터베이스의 총 제품 수를 계산합니다."
            elif 'orders' in sql_lower:
                return "데이터베이스의 총 주문 수를 계산합니다."
            else:
                return "데이터베이스의 레코드 수를 계산합니다."
        elif 'group by' in sql_lower:
            return "데이터를 그룹화하여 요약 통계를 보여줍니다."
        elif 'join' in sql_lower:
            return "여러 테이블의 데이터를 결합하여 종합적인 결과를 제공합니다."
        elif 'where' in sql_lower:
            return "특정 조건에 따라 데이터를 필터링합니다."
        else:
            return "질문에 기반하여 데이터베이스에서 정보를 조회합니다."
    
    async def _execute_sql(self, sql_query: str, database: str, max_rows: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Execute SQL query against the database.
        
        Args:
            sql_query: SQL query to execute
            database: Target database name
            max_rows: Maximum number of rows to return
            
        Returns:
            List of result dictionaries
        """
        if not self.db_manager:
            self.logger.warning("⚠️ 데이터베이스 매니저 없음 - 목업 데이터 반환")
            return [{"message": "Database connection not available"}]
        
        try:
            # 행 제한 적용
            if max_rows and 'LIMIT' not in sql_query.upper():
                sql_query += f" LIMIT {max_rows}"
            
            self.logger.debug(
                f"🗄️ SQL 실행 중",
                extra={'database': database, 'has_limit': 'LIMIT' in sql_query.upper()}
            )
            
            # 쿼리 실행
            result = await self.db_manager.execute_query(database, sql_query)
            
            if result.get("success"):
                data = result.get("data", [])
                
                self.logger.info(
                    f"📊 SQL 실행 성공 - {len(data)}행 반환",
                    extra={
                        'database': database,
                        'result_count': len(data),
                        'has_columns': bool(result.get("columns"))
                    }
                )
                
                return data
            else:
                error_msg = result.get("error", "Unknown database error")
                self.logger.error(
                    f"❌ 데이터베이스 쿼리 실패",
                    extra={'database': database, 'error_details': error_msg}
                )
                raise Exception(f"Database query failed: {error_msg}")
                
        except Exception as e:
            self.logger.error(
                f"❌ SQL 실행 오류",
                extra={'database': database, 'error_details': str(e)},
                exc_info=True
            )
            raise
    
    async def validate_query(
        self,
        sql_query: str,
        database: str = "northwind"
    ) -> Dict[str, Any]:
        """
        Validate SQL query syntax and structure.
        
        Args:
            sql_query: SQL query to validate
            database: Target database name
            
        Returns:
            Dictionary containing validation results
        """
        try:
            logger.info(f"🔍 Validating SQL: {sql_query}")
            
            # Basic SQL validation
            sql_upper = sql_query.upper().strip()
            
            # Check for dangerous operations
            dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'TRUNCATE']
            for keyword in dangerous_keywords:
                if keyword in sql_upper:
                    return {
                        "is_valid": False,
                        "error_message": f"Query contains potentially dangerous operation: {keyword}",
                        "suggestions": ["Only SELECT queries are allowed for safety"]
                    }
            
            # Check if it starts with SELECT
            if not sql_upper.startswith('SELECT'):
                return {
                    "is_valid": False,
                    "error_message": "Query must start with SELECT",
                    "suggestions": ["Try starting your query with SELECT"]
                }
            
            # Basic syntax checks
            if sql_query.count('(') != sql_query.count(')'):
                return {
                    "is_valid": False,
                    "error_message": "Mismatched parentheses in query",
                    "suggestions": ["Check that all parentheses are properly closed"]
                }
            
            logger.info("✅ SQL validation passed")
            
            return {
                "is_valid": True,
                "error_message": None,
                "suggestions": []
            }
            
        except Exception as e:
            logger.error(f"❌ Query validation failed: {str(e)}")
            
            return {
                "is_valid": False,
                "error_message": str(e),
                "suggestions": ["Please check your SQL syntax"]
            } 