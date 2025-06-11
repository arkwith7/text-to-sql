"""
Schema Analyzer Tool for database schema inspection and documentation.

This tool provides comprehensive database schema analysis including tables,
columns, relationships, and statistics to help the SQL Agent generate better queries.
"""

import logging
from typing import Dict, List, Any, Optional
from langchain.tools import BaseTool
from pydantic import Field
import json

from ..database.connection_manager import DatabaseManager

logger = logging.getLogger(__name__)

class SchemaAnalyzerTool(BaseTool):
    """
    Tool for analyzing database schema and providing structured information
    about tables, columns, relationships, and data statistics.
    """
    
    name: str = "schema_analyzer"
    description: str = """
    Analyze database schema to get information about tables, columns, data types,
    relationships, and basic statistics. This information helps in generating
    accurate SQL queries.
    
    Input: Optional table name to get specific table info, or empty string for full schema.
    Output: JSON formatted schema information.
    """
    
    db_manager: DatabaseManager = Field(exclude=True)
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager=db_manager)
    
    def _run(self, table_name: str = "") -> str:
        """
        Analyze database schema and return structured information.
        
        Args:
            table_name: Optional specific table name to analyze
            
        Returns:
            JSON string with schema information
        """
        try:
            if table_name.strip():
                return self._analyze_specific_table(table_name.strip())
            else:
                return self._analyze_full_schema()
                
        except Exception as e:
            logger.error(f"Error analyzing schema: {str(e)}")
            return json.dumps({
                "error": f"Failed to analyze schema: {str(e)}",
                "tables": []
            })
    
    async def _arun(self, table_name: str = "") -> str:
        """Async version of schema analysis."""
        return self._run(table_name)
    
    def _analyze_full_schema(self) -> str:
        """Analyze the complete database schema."""
        try:
            schema_info = self.db_manager.get_schema_info()
            
            # Enhance schema info with additional details
            enhanced_schema = {
                "database_type": "postgresql",
                "total_tables": len(schema_info),
                "tables": []
            }
            
            for table_info in schema_info:
                table_name = table_info["table_name"]
                
                # Get column details
                columns = self._get_table_columns(table_name)
                
                # Get table statistics
                stats = self._get_table_statistics(table_name)
                
                # Get foreign key relationships
                relationships = self._get_table_relationships(table_name)
                
                enhanced_table = {
                    "name": table_name,
                    "columns": columns,
                    "row_count": stats.get("row_count", 0),
                    "relationships": relationships,
                    "primary_keys": self._get_primary_keys(table_name),
                    "indexes": self._get_table_indexes(table_name)
                }
                
                enhanced_schema["tables"].append(enhanced_table)
            
            return json.dumps(enhanced_schema, indent=2, default=str)
            
        except Exception as e:
            logger.error(f"Error in full schema analysis: {str(e)}")
            raise
    
    def _analyze_specific_table(self, table_name: str) -> str:
        """Analyze a specific table in detail."""
        try:
            # Verify table exists
            schema_info = self.db_manager.get_schema_info()
            table_exists = any(
                table["table_name"].lower() == table_name.lower() 
                for table in schema_info
            )
            
            if not table_exists:
                return json.dumps({
                    "error": f"Table '{table_name}' not found",
                    "available_tables": [t["table_name"] for t in schema_info]
                })
            
            # Get detailed table information
            columns = self._get_table_columns(table_name)
            stats = self._get_table_statistics(table_name)
            relationships = self._get_table_relationships(table_name)
            sample_data = self._get_sample_data(table_name)
            
            table_info = {
                "name": table_name,
                "columns": columns,
                "row_count": stats.get("row_count", 0),
                "relationships": relationships,
                "primary_keys": self._get_primary_keys(table_name),
                "indexes": self._get_table_indexes(table_name),
                "sample_data": sample_data,
                "column_stats": self._get_column_statistics(table_name)
            }
            
            return json.dumps(table_info, indent=2, default=str)
            
        except Exception as e:
            logger.error(f"Error analyzing table {table_name}: {str(e)}")
            raise
    
    def _get_table_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """Get detailed column information for a table."""
        try:
            query = """
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default,
                character_maximum_length,
                numeric_precision,
                numeric_scale,
                ordinal_position
            FROM information_schema.columns 
            WHERE table_name = %s 
            ORDER BY ordinal_position
            """
            
            result = self.db_manager.execute_query_safe(
                query, 
                params=(table_name,),
                database_type="app"
            )
            
            columns = []
            for row in result["data"]:
                column_info = {
                    "name": row["column_name"],
                    "type": row["data_type"],
                    "nullable": row["is_nullable"] == "YES",
                    "default": row["column_default"],
                    "max_length": row["character_maximum_length"],
                    "precision": row["numeric_precision"],
                    "scale": row["numeric_scale"],
                    "position": row["ordinal_position"]
                }
                columns.append(column_info)
            
            return columns
            
        except Exception as e:
            logger.error(f"Error getting columns for {table_name}: {str(e)}")
            return []
    
    def _get_table_statistics(self, table_name: str) -> Dict[str, Any]:
        """Get basic statistics for a table."""
        try:
            # Get row count
            count_query = f"SELECT COUNT(*) as row_count FROM {table_name}"
            result = self.db_manager.execute_query_safe(
                count_query,
                database_type="business"
            )
            
            row_count = result["data"][0]["row_count"] if result["data"] else 0
            
            return {
                "row_count": row_count,
                "has_data": row_count > 0
            }
            
        except Exception as e:
            logger.error(f"Error getting statistics for {table_name}: {str(e)}")
            return {"row_count": 0, "has_data": False}
    
    def _get_table_relationships(self, table_name: str) -> List[Dict[str, Any]]:
        """Get foreign key relationships for a table."""
        try:
            query = """
            SELECT
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name,
                tc.constraint_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_name = %s
            """
            
            result = self.db_manager.execute_query_safe(
                query,
                params=(table_name,),
                database_type="app"
            )
            
            relationships = []
            for row in result["data"]:
                rel_info = {
                    "column": row["column_name"],
                    "references_table": row["foreign_table_name"],
                    "references_column": row["foreign_column_name"],
                    "constraint_name": row["constraint_name"]
                }
                relationships.append(rel_info)
            
            return relationships
            
        except Exception as e:
            logger.error(f"Error getting relationships for {table_name}: {str(e)}")
            return []
    
    def _get_primary_keys(self, table_name: str) -> List[str]:
        """Get primary key columns for a table."""
        try:
            query = """
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
            WHERE tc.constraint_type = 'PRIMARY KEY'
                AND tc.table_name = %s
            ORDER BY kcu.ordinal_position
            """
            
            result = self.db_manager.execute_query_safe(
                query,
                params=(table_name,),
                database_type="app"
            )
            
            return [row["column_name"] for row in result["data"]]
            
        except Exception as e:
            logger.error(f"Error getting primary keys for {table_name}: {str(e)}")
            return []
    
    def _get_table_indexes(self, table_name: str) -> List[Dict[str, Any]]:
        """Get index information for a table."""
        try:
            query = """
            SELECT
                indexname,
                indexdef
            FROM pg_indexes
            WHERE tablename = %s
            """
            
            result = self.db_manager.execute_query_safe(
                query,
                params=(table_name,),
                database_type="business"
            )
            
            indexes = []
            for row in result["data"]:
                index_info = {
                    "name": row["indexname"],
                    "definition": row["indexdef"]
                }
                indexes.append(index_info)
            
            return indexes
            
        except Exception as e:
            logger.error(f"Error getting indexes for {table_name}: {str(e)}")
            return []
    
    def _get_sample_data(self, table_name: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Get sample data from a table."""
        try:
            query = f"SELECT * FROM {table_name} LIMIT {limit}"
            result = self.db_manager.execute_query_safe(
                query,
                database_type="business"
            )
            
            return result["data"]
            
        except Exception as e:
            logger.error(f"Error getting sample data for {table_name}: {str(e)}")
            return []
    
    def _get_column_statistics(self, table_name: str) -> Dict[str, Any]:
        """Get statistical information about columns."""
        try:
            columns = self._get_table_columns(table_name)
            numeric_columns = [
                col["name"] for col in columns 
                if col["type"] in ["integer", "bigint", "decimal", "numeric", "real", "double precision"]
            ]
            
            stats = {}
            
            for col in numeric_columns[:5]:  # Limit to 5 columns to avoid performance issues
                try:
                    stat_query = f"""
                    SELECT 
                        MIN({col}) as min_val,
                        MAX({col}) as max_val,
                        AVG({col}) as avg_val,
                        COUNT(DISTINCT {col}) as distinct_count
                    FROM {table_name}
                    WHERE {col} IS NOT NULL
                    """
                    
                    result = self.db_manager.execute_query_safe(
                        stat_query,
                        database_type="business"
                    )
                    
                    if result["data"]:
                        stats[col] = result["data"][0]
                        
                except Exception as e:
                    logger.warning(f"Could not get stats for column {col}: {str(e)}")
                    continue
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting column statistics for {table_name}: {str(e)}")
            return {}
    
    def get_business_context(self) -> str:
        """Get business context information about the Northwind database."""
        return """
        NORTHWIND DATABASE CONTEXT:
        
        This is a sample business database representing a fictional company called Northwind Traders.
        
        KEY BUSINESS ENTITIES:
        - Customers: Companies that purchase products
        - Orders: Purchase orders placed by customers
        - Products: Items sold by the company
        - Categories: Product categories for organization
        - Suppliers: Companies that supply products
        - Employees: Staff members who handle orders and sales
        - Shippers: Companies that handle order delivery
        
        COMMON BUSINESS QUESTIONS:
        - Sales performance analysis
        - Customer behavior insights
        - Product popularity and inventory
        - Employee performance metrics
        - Geographic sales distribution
        - Seasonal trends and patterns
        
        DATA RELATIONSHIPS:
        - Customers place Orders
        - Orders contain multiple Order Details (line items)
        - Order Details reference Products
        - Products belong to Categories and are supplied by Suppliers
        - Orders are handled by Employees and shipped by Shippers
        """
