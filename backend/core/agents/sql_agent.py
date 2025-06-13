"""
SQL Agent for Text-to-SQL application.
Handles natural language to SQL conversion and execution.
"""

import logging
import time
import re
from typing import Dict, Any, Optional, List
from datetime import datetime

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

class SQLAgent(BaseAgent):
    """
    SQL Agent wrapper that extends the core SQL agent functionality.
    This class provides additional features specific to the API layer.
    """
    
    def __init__(self, db_manager=None):
        """Initialize SQL Agent with database manager."""
        super().__init__(db_manager)
        
        # Simple keyword-to-SQL mapping for demonstration (English and Korean)
        self.query_patterns = {
            # English patterns
            r'customers?\s+from\s+(\w+)': 'SELECT * FROM customers WHERE country = \'{}\' LIMIT 10',
            r'how\s+many\s+products?': 'SELECT COUNT(*) as product_count FROM products',
            r'how\s+many\s+customers?': 'SELECT COUNT(*) as customer_count FROM customers',
            r'how\s+many\s+orders?': 'SELECT COUNT(*) as order_count FROM orders',
            r'show\s+me\s+products?': 'SELECT product_id, product_name, unit_price FROM products LIMIT 10',
            r'show\s+me\s+customers?': 'SELECT customer_id, company_name, country FROM customers LIMIT 10',
            r'show\s+me\s+orders?': 'SELECT order_id, customer_id, order_date FROM orders LIMIT 10',
            r'products?\s+by\s+category': 'SELECT c.category_name, COUNT(p.product_id) as product_count FROM categories c LEFT JOIN products p ON c.category_id = p.category_id GROUP BY c.category_name',
            r'top\s+(\d+)\s+customers?': 'SELECT c.customer_id, c.company_name, COUNT(o.order_id) as order_count FROM customers c LEFT JOIN orders o ON c.customer_id = o.customer_id GROUP BY c.customer_id, c.company_name ORDER BY order_count DESC LIMIT {}',
            r'sales?\s+by\s+country': 'SELECT ship_country, COUNT(*) as order_count, SUM(freight) as total_freight FROM orders GROUP BY ship_country ORDER BY order_count DESC LIMIT 10',
            
            # Korean patterns
            r'월별\s*매출\s*추이': '''
                SELECT 
                    strftime('%Y-%m', o.order_date) as month,
                    COUNT(o.order_id) as order_count,
                    ROUND(SUM(od.unit_price * od.quantity * (1 - od.discount)), 2) as total_sales
                FROM orders o
                JOIN order_details od ON o.order_id = od.order_id
                WHERE o.order_date IS NOT NULL
                GROUP BY strftime('%Y-%m', o.order_date)
                ORDER BY month
            ''',
            r'고객\s*수': 'SELECT COUNT(*) as customer_count FROM customers',
            r'제품\s*수': 'SELECT COUNT(*) as product_count FROM products',
            r'주문\s*수': 'SELECT COUNT(*) as order_count FROM orders',
            r'카테고리별\s*제품': 'SELECT c.category_name, COUNT(p.product_id) as product_count FROM categories c LEFT JOIN products p ON c.category_id = p.category_id GROUP BY c.category_name',
            r'카테고리별\s*평균\s*주문\s*금액': '''
                SELECT 
                    c.category_name,
                    ROUND(AVG(od.unit_price * od.quantity * (1 - od.discount)), 2) as avg_order_amount
                FROM categories c
                JOIN products p ON c.category_id = p.category_id
                JOIN order_details od ON p.product_id = od.product_id
                GROUP BY c.category_name
                ORDER BY avg_order_amount DESC
            ''',
            r'고객별\s*주문\s*횟수': '''
                SELECT 
                    c.customer_id,
                    c.company_name,
                    COUNT(o.order_id) as order_count
                FROM customers c
                LEFT JOIN orders o ON c.customer_id = o.customer_id
                GROUP BY c.customer_id, c.company_name
                ORDER BY order_count DESC
                LIMIT 20
            ''',
            r'가장\s*많이\s*팔린\s*제품\s*(\d+)개?': '''
                SELECT 
                    p.product_name,
                    SUM(od.quantity) as total_quantity,
                    ROUND(SUM(od.unit_price * od.quantity * (1 - od.discount)), 2) as total_sales
                FROM products p
                JOIN order_details od ON p.product_id = od.product_id
                GROUP BY p.product_id, p.product_name
                ORDER BY total_quantity DESC
                LIMIT {}
            ''',
            r'국가별\s*고객\s*수': '''
                SELECT 
                    country,
                    COUNT(*) as customer_count
                FROM customers
                WHERE country IS NOT NULL
                GROUP BY country
                ORDER BY customer_count DESC
            ''',
            r'직원별\s*매출': '''
                SELECT 
                    e.first_name || ' ' || e.last_name as employee_name,
                    COUNT(o.order_id) as order_count,
                    ROUND(SUM(od.unit_price * od.quantity * (1 - od.discount)), 2) as total_sales
                FROM employees e
                LEFT JOIN orders o ON e.employee_id = o.employee_id
                LEFT JOIN order_details od ON o.order_id = od.order_id
                GROUP BY e.employee_id, employee_name
                ORDER BY total_sales DESC
            '''
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
        
        logger.info(f"🤖 Processing question: '{question}' for user {user_id}")
        logger.info(f"🔧 SQL Agent execute_query called with: question='{question}', database='{database}'")
        
        try:
            # Generate SQL from natural language
            logger.info(f"🔍 Calling _generate_sql with question: '{question}'")
            sql_query, explanation = self._generate_sql(question)
            
            logger.info(f"🔍 Generated SQL: '{sql_query}'")
            logger.info(f"📝 Generated explanation: '{explanation}'")
            
            if not sql_query:
                logger.error("❌ No SQL query generated!")
                raise ValueError("Could not generate SQL query from the question")
            
            # Execute the SQL query
            results = await self._execute_sql(sql_query, database, max_rows)
            
            execution_time = time.time() - start_time
            
            logger.info(f"⏱️ Query executed in {execution_time:.3f}s, returned {len(results)} rows")
            
            # Add execution metadata
            result = {
                "sql_query": sql_query,
                "results": results,
                "explanation": explanation if include_explanation else None,
                "execution_time": execution_time,
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": user_id,
                "database": database,
                "success": True
            }
            
            logger.info(f"✅ Query executed successfully for user {user_id}")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_message = str(e)
            
            logger.error(f"❌ Query execution failed after {execution_time:.3f}s: {error_message}")
            
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
            logger.warning("⚠️ No database manager available, returning mock data")
            return [{"message": "Database connection not available"}]
        
        try:
            # Apply row limit if specified
            if max_rows and 'LIMIT' not in sql_query.upper():
                sql_query += f" LIMIT {max_rows}"
            
            logger.info(f"🗄️ Executing SQL: {sql_query}")
            
            # Execute query using database manager
            result = await self.db_manager.execute_query(database, sql_query)
            
            if result.get("success"):
                data = result.get("data", [])
                logger.info(f"📊 Query returned {len(data)} rows")
                return data
            else:
                error_msg = result.get("error", "Unknown database error")
                logger.error(f"❌ Database query failed: {error_msg}")
                raise Exception(f"Database query failed: {error_msg}")
                
        except Exception as e:
            logger.error(f"❌ SQL execution error: {str(e)}")
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