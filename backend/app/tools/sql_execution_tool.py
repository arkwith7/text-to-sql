"""
SQL Execution Tool for AI Agent
Provides safe SQL execution with validation and security checks
"""
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import re
import structlog
from app.database.connection_manager import db_manager

logger = structlog.get_logger(__name__)


class SQLExecutionInput(BaseModel):
    """Input schema for SQL execution tool"""
    query: str = Field(description="SQL query to execute")
    target_db: str = Field(
        default="northwind", 
        description="Target database name (northwind, app)"
    )
    limit: Optional[int] = Field(
        default=100, 
        description="Maximum number of rows to return"
    )


class SQLExecutionTool(BaseTool):
    """
    Tool for executing SQL queries safely with validation and security
    Implements multiple security layers and result formatting
    """
    
    name: str = "sql_execution"
    description: str = """Execute SQL queries on specified database with safety checks.
    Use this tool to run SELECT queries on business data.
    The tool automatically validates queries and applies security constraints."""
    args_schema: type = SQLExecutionInput
    max_result_size: int = 1000  # Maximum rows to return
    
    def __init__(self):
        super().__init__()
    
    def _run(self, query: str, target_db: str = "northwind", limit: Optional[int] = 100) -> str:
        """Execute SQL query with comprehensive validation"""
        try:
            # Step 1: Basic validation
            if not self._is_safe_query(query):
                return "Query validation failed: Only SELECT queries are allowed"
            
            # Step 2: Apply security constraints
            safe_query = self._apply_security_constraints(query, limit)
            
            # Step 3: Execute query
            result = db_manager.execute_query(target_db, safe_query)
            
            if not result['success']:
                logger.error("SQL execution failed", query=safe_query, error=result['error'])
                return f"Query execution failed: {result['error']}"
            
            # Step 4: Format results
            formatted_result = self._format_results(result)
            
            logger.info(
                "SQL query executed successfully", 
                query=safe_query, 
                row_count=result.get('row_count', 0)
            )
            
            return formatted_result
            
        except Exception as e:
            logger.error("SQL execution tool error", query=query, error=str(e))
            return f"Execution error: {str(e)}"
    
    def _is_safe_query(self, query: str) -> bool:
        """Basic safety check for SQL queries"""
        query_upper = query.upper().strip()
        
        # Only allow SELECT queries
        if not query_upper.startswith('SELECT'):
            return False
        
        # Block dangerous keywords
        dangerous_keywords = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE', 'TRUNCATE']
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                return False
        
        return True
    
    def _apply_security_constraints(self, query: str, limit: Optional[int]) -> str:
        """Apply security constraints to SQL query"""
        # Remove any existing LIMIT clause
        query_no_limit = re.sub(r'\s+LIMIT\s+\d+\s*$', '', query, flags=re.IGNORECASE)
        
        # Apply result limit
        effective_limit = min(limit or 100, self.max_result_size)
        safe_query = f"{query_no_limit.rstrip(';')} LIMIT {effective_limit}"
        
        return safe_query
    
    def _format_results(self, result: Dict[str, Any]) -> str:
        """Format query results for AI consumption"""
        if not result.get('data'):
            return "Query executed successfully but returned no data."
        
        data = result['data']
        columns = result['columns']
        row_count = result['row_count']
        
        # Create formatted output
        output_parts = [
            f"Query executed successfully. Retrieved {row_count} rows.",
            f"Columns: {', '.join(columns)}",
            ""
        ]
        
        # Add sample data (first 5 rows)
        sample_size = min(5, len(data))
        if sample_size > 0:
            output_parts.append("Sample data:")
            for i, row in enumerate(data[:sample_size]):
                row_str = ", ".join([f"{k}: {v}" for k, v in row.items()])
                output_parts.append(f"Row {i+1}: {row_str}")
        
        # Add summary if there are more rows
        if row_count > sample_size:
            output_parts.append(f"... and {row_count - sample_size} more rows")
        
        return "\n".join(output_parts)
