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
        
        # Simple keyword-to-SQL mapping for demonstration
        self.query_patterns = {
            r'customers?\s+from\s+(\w+)': 'SELECT * FROM customers WHERE country = \'{}\' LIMIT 10',
            r'how\s+many\s+products?': 'SELECT COUNT(*) as product_count FROM products',
            r'how\s+many\s+customers?': 'SELECT COUNT(*) as customer_count FROM customers',
            r'how\s+many\s+orders?': 'SELECT COUNT(*) as order_count FROM orders',
            r'show\s+me\s+products?': 'SELECT product_id, product_name, unit_price FROM products LIMIT 10',
            r'show\s+me\s+customers?': 'SELECT customer_id, company_name, country FROM customers LIMIT 10',
            r'show\s+me\s+orders?': 'SELECT order_id, customer_id, order_date FROM orders LIMIT 10',
            r'products?\s+by\s+category': 'SELECT c.category_name, COUNT(p.product_id) as product_count FROM categories c LEFT JOIN products p ON c.category_id = p.category_id GROUP BY c.category_name',
            r'top\s+(\d+)\s+customers?': 'SELECT c.customer_id, c.company_name, COUNT(o.order_id) as order_count FROM customers c LEFT JOIN orders o ON c.customer_id = o.customer_id GROUP BY c.customer_id, c.company_name ORDER BY order_count DESC LIMIT {}',
            r'sales?\s+by\s+country': 'SELECT ship_country, COUNT(*) as order_count, SUM(freight) as total_freight FROM orders GROUP BY ship_country ORDER BY order_count DESC LIMIT 10'
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
        
        try:
            # Generate SQL from natural language
            sql_query, explanation = self._generate_sql(question)
            
            logger.info(f"🔍 Generated SQL: {sql_query}")
            
            if not sql_query:
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
                        explanation = f"Finding customers from {country} using the customers table."
                    elif 'top' in pattern and match.groups():
                        # Top N customers query
                        limit = match.group(1)
                        sql_query = sql_template.format(limit)
                        explanation = f"Finding top {limit} customers by order count."
                    else:
                        sql_query = sql_template
                        explanation = "Generated SQL query based on pattern matching."
                else:
                    sql_query = sql_template
                    explanation = self._get_explanation_for_query(sql_query)
                
                logger.info(f"✅ Generated SQL: {sql_query}")
                return sql_query, explanation
        
        # If no pattern matches, try to generate a basic query
        logger.warning(f"⚠️ No pattern matched for question: '{question}'")
        
        # Default fallback queries
        if any(word in question_lower for word in ['customer', 'customers']):
            sql_query = "SELECT customer_id, company_name, country FROM customers LIMIT 10"
            explanation = "Showing sample customers from the database."
        elif any(word in question_lower for word in ['product', 'products']):
            sql_query = "SELECT product_id, product_name, unit_price FROM products LIMIT 10"
            explanation = "Showing sample products from the database."
        elif any(word in question_lower for word in ['order', 'orders']):
            sql_query = "SELECT order_id, customer_id, order_date FROM orders LIMIT 10"
            explanation = "Showing sample orders from the database."
        else:
            # Very basic fallback
            sql_query = "SELECT 'I need more specific information to generate a proper query' as message"
            explanation = "Could not understand the question. Please try asking about customers, products, or orders."
        
        logger.info(f"🔄 Using fallback SQL: {sql_query}")
        return sql_query, explanation
    
    def _get_explanation_for_query(self, sql_query: str) -> str:
        """Generate explanation for SQL query."""
        sql_lower = sql_query.lower()
        
        if 'count(*)' in sql_lower:
            if 'customers' in sql_lower:
                return "Counting the total number of customers in the database."
            elif 'products' in sql_lower:
                return "Counting the total number of products in the database."
            elif 'orders' in sql_lower:
                return "Counting the total number of orders in the database."
            else:
                return "Counting records in the database."
        elif 'group by' in sql_lower:
            return "Grouping and aggregating data to show summary statistics."
        elif 'join' in sql_lower:
            return "Combining data from multiple tables to provide comprehensive results."
        elif 'where' in sql_lower:
            return "Filtering data based on specific conditions."
        else:
            return "Retrieving data from the database based on your question."
    
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