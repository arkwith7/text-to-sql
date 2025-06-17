"""
Enhanced SQL Agent for Text-to-SQL application.
Handles natural language to SQL conversion and execution with PostgreSQL Northwind optimization.
"""

import logging
import time
import re
from typing import Dict, Any, Optional, List, Tuple

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class SQLAgent(BaseAgent):
    """Enhanced SQL Agent with PostgreSQL Northwind optimization and advanced features."""
    
    def __init__(self, db_manager=None):
        """Initialize Enhanced SQL Agent with database manager."""
        super().__init__(db_manager)
        self.logger = logging.getLogger(__name__)
        
        # 노트북의 AdvancedSQLGenerator 기능 추가
        self.generation_stats = {
            'total_requests': 0,
            'pattern_matches': 0,
            'llm_generations': 0,
            'successful_generations': 0,
            'failed_generations': 0
        }
        
        # PostgreSQL Northwind 최적화된 쿼리 패턴
        self.query_patterns = {
            # 기본 COUNT 쿼리들
            r'고객\s*수': 'SELECT COUNT(*) as customer_count FROM customers',
            r'제품\s*수': 'SELECT COUNT(*) as product_count FROM products',
            r'주문\s*수': 'SELECT COUNT(*) as order_count FROM orders',
            r'카테고리\s*수': 'SELECT COUNT(*) as category_count FROM categories',
            r'직원\s*수': 'SELECT COUNT(*) as employee_count FROM employees',
            
            # 영어 COUNT 쿼리들
            r'how\s+many\s+customers': 'SELECT COUNT(*) as customer_count FROM customers',
            r'how\s+many\s+products': 'SELECT COUNT(*) as product_count FROM products',
            r'customer\s+count': 'SELECT COUNT(*) as customer_count FROM customers',
            
            # 기본 조회 쿼리들
            r'고객\s*목록': 'SELECT customerid, customername, country FROM customers LIMIT 20',
            r'제품\s*목록': 'SELECT productid, productname, price FROM products LIMIT 20',
            r'주문\s*목록': 'SELECT orderid, customerid, orderdate FROM orders ORDER BY orderdate DESC LIMIT 20',
            r'카테고리\s*목록': 'SELECT categoryid, categoryname, description FROM categories',
            
            # 노트북의 복잡한 비즈니스 쿼리 패턴 추가
            r'카테고리별\s*제품\s*수': '''SELECT c.categoryname, COUNT(p.productid) as product_count 
                FROM categories c 
                LEFT JOIN products p ON c.categoryid = p.categoryid 
                GROUP BY c.categoryname, c.categoryid 
                ORDER BY product_count DESC''',
                
            r'카테고리별\s*매출': '''SELECT c.categoryname, 
                ROUND(SUM(od.unitprice * od.quantity * (1 - od.discount)), 2) as total_sales
                FROM categories c
                JOIN products p ON c.categoryid = p.categoryid
                JOIN orderdetails od ON p.productid = od.productid
                GROUP BY c.categoryname, c.categoryid
                ORDER BY total_sales DESC''',
                
            r'인기\s*제품': '''SELECT p.productname, SUM(od.quantity) as total_quantity
                FROM products p
                JOIN orderdetails od ON p.productid = od.productid
                GROUP BY p.productname, p.productid
                ORDER BY total_quantity DESC
                LIMIT 10''',
            
            # 영어 패턴
            r'show\s+customers': 'SELECT customerid, customername, country FROM customers LIMIT 20',
            r'show\s+products': 'SELECT productid, productname, price FROM products LIMIT 20',
            r'list\s+customers': 'SELECT customerid, customername, country FROM customers LIMIT 20'
        }
        
        self.logger.info(f"Enhanced SQL Agent 초기화 완료 - {len(self.query_patterns)}개 패턴 로드됨")
    
    def _generate_sql(self, question: str) -> Tuple[str, str]:
        """자연어 질문을 SQL로 변환합니다."""
        question_lower = question.lower().strip()
        self.logger.debug(f"SQL 생성 시작: '{question}'")
        
        # 패턴 매칭
        for pattern, sql_template in self.query_patterns.items():
            if re.search(pattern, question_lower, re.IGNORECASE):
                self.logger.debug(f"패턴 매치: {pattern}")
                sql_query = sql_template.strip()
                explanation = self._get_explanation_for_pattern(pattern, question)
                return sql_query, explanation
        
        # 패턴 매칭 실패 시 fallback
        return self._get_fallback_query(question_lower)
    
    def _get_explanation_for_pattern(self, pattern: str, question: str) -> str:
        """패턴에 대한 한국어 설명 생성"""
        if '고객' in pattern or 'customer' in pattern:
            return '고객 관련 정보를 조회합니다.'
        elif '제품' in pattern or 'product' in pattern:
            return '제품 관련 정보를 조회합니다.'
        elif '주문' in pattern or 'order' in pattern:
            return '주문 관련 정보를 조회합니다.'
        elif '카테고리' in pattern:
            return '카테고리 정보를 조회합니다.'
        else:
            return f"'{question}'에 대한 데이터를 조회합니다."
    
    def _get_fallback_query(self, question_lower: str) -> Tuple[str, str]:
        """패턴 매칭 실패 시 fallback 쿼리 생성"""
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
        else:
            return (
                "SELECT 'PostgreSQL Northwind 데이터베이스에 대해 질문해 주세요. 예: 고객 수, 제품 수' as message",
                '질문을 이해하지 못했습니다. 더 구체적으로 질문해 주세요.'
            )

    # === 노트북의 AdvancedSQLGenerator 통계 관리 기능 ===
    
    def get_generation_stats(self) -> Dict[str, Any]:
        """SQL 생성 통계 반환 (노트북 AdvancedSQLGenerator 기능)"""
        stats = self.generation_stats.copy()
        if stats['total_requests'] > 0:
            stats['pattern_match_rate'] = round(stats['pattern_matches'] / stats['total_requests'] * 100, 1)
            stats['llm_success_rate'] = round(stats['successful_generations'] / max(stats['llm_generations'], 1) * 100, 1) if stats['llm_generations'] > 0 else 0
        else:
            stats['pattern_match_rate'] = 0
            stats['llm_success_rate'] = 0
        
        return stats
    
    def reset_generation_stats(self):
        """SQL 생성 통계 초기화"""
        self.generation_stats = {
            'total_requests': 0,
            'pattern_matches': 0,
            'llm_generations': 0,
            'successful_generations': 0,
            'failed_generations': 0
        }
        self.logger.info("🔄 SQL 생성 통계 초기화 완료")
    
    def get_supported_patterns(self) -> List[str]:
        """지원되는 쿼리 패턴 목록 반환"""
        patterns = []
        for pattern in self.query_patterns.keys():
            # 정규표현식을 사람이 읽기 쉬운 형태로 변환
            readable_pattern = pattern.replace(r'\s*', ' ').replace(r'\s+', ' ')
            patterns.append(readable_pattern)
        return patterns
    
    def _execute_simulated_query(self, sql_query: str, max_rows: Optional[int] = None) -> List[Dict[str, Any]]:
        """시뮬레이션된 쿼리 실행 (노트북의 실제 Northwind 데이터 수치 반영)"""
        sql_upper = sql_query.upper().strip()
        
        # COUNT 쿼리 처리 (노트북에서 확인된 실제 데이터 수치)
        if "COUNT(*)" in sql_upper:
            if "CUSTOMERS" in sql_upper:
                return [{"customer_count": 91}]  # 실제 Northwind DB 수치
            elif "PRODUCTS" in sql_upper:
                return [{"product_count": 77}]   # 실제 Northwind DB 수치
            elif "ORDERS" in sql_upper:
                return [{"order_count": 830}]    # 실제 Northwind DB 수치 (노트북에서 확인)
            elif "CATEGORIES" in sql_upper:
                return [{"category_count": 8}]
            elif "EMPLOYEES" in sql_upper:
                return [{"employee_count": 9}]   # 실제 Northwind DB 수치
            else:
                return [{"count": 0}]
        
        # 복잡한 비즈니스 쿼리 처리 (노트북 패턴)
        elif "GROUP BY" in sql_upper:
            if "CATEGORYNAME" in sql_upper and "PRODUCT_COUNT" in sql_upper:
                # 카테고리별 제품 수
                return [
                    {"categoryname": "Beverages", "product_count": 12},
                    {"categoryname": "Condiments", "product_count": 12},
                    {"categoryname": "Dairy Products", "product_count": 10},
                    {"categoryname": "Grains/Cereals", "product_count": 7},
                    {"categoryname": "Meat/Poultry", "product_count": 6},
                    {"categoryname": "Produce", "product_count": 5},
                    {"categoryname": "Seafood", "product_count": 12},
                    {"categoryname": "Confections", "product_count": 13}
                ]
            elif "TOTAL_SALES" in sql_upper:
                # 카테고리별 매출
                return [
                    {"categoryname": "Beverages", "total_sales": 267868.20},
                    {"categoryname": "Dairy Products", "total_sales": 234507.30},
                    {"categoryname": "Confections", "total_sales": 167357.26},
                    {"categoryname": "Meat/Poultry", "total_sales": 163022.37},
                    {"categoryname": "Seafood", "total_sales": 131261.75}
                ]
            elif "TOTAL_QUANTITY" in sql_upper:
                # 인기 제품
                return [
                    {"productname": "Camembert Pierrot", "total_quantity": 1577},
                    {"productname": "Raclette Courdavault", "total_quantity": 1496},
                    {"productname": "Gorgonzola Telino", "total_quantity": 1397},
                    {"productname": "Chartreuse verte", "total_quantity": 1158},
                    {"productname": "Côte de Blaye", "total_quantity": 623}
                ]
        
        # 기본 테이블 조회
        elif "SELECT" in sql_upper:
            if "CUSTOMERS" in sql_upper:
                return [
                    {"customerid": "ALFKI", "customername": "Alfreds Futterkiste", "country": "Germany"},
                    {"customerid": "ANATR", "customername": "Ana Trujillo Emparedados y helados", "country": "Mexico"},
                    {"customerid": "ANTON", "customername": "Antonio Moreno Taquería", "country": "Mexico"}
                ]
            elif "PRODUCTS" in sql_upper:
                return [
                    {"productid": 1, "productname": "Chai", "price": 18.00},
                    {"productid": 2, "productname": "Chang", "price": 19.00},
                    {"productid": 3, "productname": "Aniseed Syrup", "price": 10.00}
                ]
            elif "CATEGORIES" in sql_upper:
                return [
                    {"categoryid": 1, "categoryname": "Beverages", "description": "Soft drinks, coffees, teas, beers, and ales"},
                    {"categoryid": 2, "categoryname": "Condiments", "description": "Sweet and savory sauces, relishes, spreads, and seasonings"},
                    {"categoryid": 3, "categoryname": "Dairy Products", "description": "Cheeses"}
                ]
        
        # 메시지 쿼리
        return [{"message": "PostgreSQL Northwind 데이터베이스에 대해 질문해 주세요."}]
    
    def execute_query_sync(
        self,
        question: str,
        database: str = "northwind",
        include_explanation: bool = True,
        max_rows: Optional[int] = None,
        include_metadata: bool = False
    ) -> Dict[str, Any]:
        """동기 방식으로 쿼리를 실행합니다 (노트북 AdvancedSQLGenerator 기능 포함)."""
        start_time = time.time()
        
        try:
            # 메타데이터 포함 SQL 생성
            if include_metadata:
                sql_query, explanation, metadata = self._generate_sql_with_metadata(question)
            else:
                sql_query, explanation = self._generate_sql(question)
                metadata = {}
            
            # 시뮬레이션된 결과 실행
            results = self._execute_simulated_query(sql_query, max_rows)
            
            execution_time = time.time() - start_time
            
            self.logger.info(
                f"동기 쿼리 실행 완료 - 시간: {execution_time:.3f}s, 결과: {len(results)}행"
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
                
            if include_metadata and metadata:
                response["metadata"] = metadata
                response["generation_method"] = metadata.get('method', 'unknown')
                response["sql_complexity"] = metadata.get('complexity', 'simple')
                
            return response
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            
            self.logger.error(f"동기 쿼리 실행 실패: {error_msg}")
            
            return {
                "success": False,
                "error": error_msg,
                "execution_time": execution_time,
                "question": question,
                "database": database,
                "results": [],
                "row_count": 0
            }
    
    async def execute_query(
        self,
        question: str,
        database: str = "northwind",
        context: Optional[str] = None,
        user_id: Optional[int] = None,
        include_explanation: bool = True,
        max_rows: Optional[int] = None
    ) -> Dict[str, Any]:
        """비동기 방식으로 쿼리를 실행합니다."""
        return self.execute_query_sync(
            question=question,
            database=database,
            include_explanation=include_explanation,
            max_rows=max_rows
        )
    
    async def validate_query(
        self,
        sql_query: str,
        database: str = "northwind"
    ) -> Dict[str, Any]:
        """SQL 쿼리 유효성을 검증합니다."""
        try:
            sql_upper = sql_query.upper().strip()
            
            # 위험한 키워드 검사
            dangerous_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE', 'UPDATE', 'INSERT']
            for keyword in dangerous_keywords:
                if keyword in sql_upper:
                    return {
                        "is_valid": False,
                        "error_message": f"'{keyword}' 키워드는 허용되지 않습니다.",
                        "suggestions": ["SELECT 쿼리만 사용해 주세요."]
                    }
            
            # SELECT 쿼리인지 확인
            if not sql_upper.startswith('SELECT'):
                return {
                    "is_valid": False,
                    "error_message": "SELECT 쿼리만 허용됩니다.",
                    "suggestions": ["SELECT 문으로 시작하는 쿼리를 작성해 주세요."]
                }
            
            return {
                "is_valid": True,
                "suggestions": ["쿼리가 유효합니다."]
            }
            
        except Exception as e:
            return {
                "is_valid": False,
                "error_message": f"쿼리 검증 중 오류 발생: {str(e)}",
                "suggestions": ["쿼리 문법을 확인해 주세요."]
            }
    
    def _generate_sql_with_metadata(self, question: str) -> Tuple[str, str, Dict[str, Any]]:
        """SQL 생성 with 메타데이터 (노트북의 AdvancedSQLGenerator 기능)"""
        start_time = time.time()
        self.generation_stats['total_requests'] += 1
        
        question_lower = question.lower().strip()
        self.logger.debug(f"SQL 생성 시작: '{question}'")
        
        # 패턴 매칭 시도
        for pattern, sql_template in self.query_patterns.items():
            if re.search(pattern, question_lower, re.IGNORECASE):
                self.logger.debug(f"패턴 매치: {pattern}")
                self.generation_stats['pattern_matches'] += 1
                
                sql_query = sql_template.strip()
                explanation = self._get_explanation_for_pattern(pattern, question)
                generation_time = time.time() - start_time
                
                # 복잡도 판단
                complexity = 'complex' if 'JOIN' in sql_query.upper() or 'GROUP BY' in sql_query.upper() else 'simple'
                
                metadata = {
                    'method': 'pattern_matching',
                    'complexity': complexity,
                    'generation_time': round(generation_time, 3),
                    'confidence': 0.9,
                    'pattern_used': pattern
                }
                
                return sql_query, explanation, metadata
        
        # 패턴 매칭 실패 시 fallback
        sql_query, explanation = self._get_fallback_query(question_lower)
        generation_time = time.time() - start_time
        
        metadata = {
            'method': 'fallback',
            'complexity': 'simple',
            'generation_time': round(generation_time, 3),
            'confidence': 0.5
        }
        
        return sql_query, explanation, metadata
