"""
Schema endpoints for Text-to-SQL application.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging

from services.auth_dependencies import get_current_user
from services.auth_service import UserResponse
from core.tools.schema_analyzer_tool import SchemaAnalyzerTool

logger = logging.getLogger(__name__)

router = APIRouter()

class SchemaRequest(BaseModel):
    database: str = Field(default="northwind", description="Target database")
    include_sample_data: bool = Field(default=False, description="Include sample data")
    table_filter: Optional[List[str]] = Field(None, description="Filter specific tables")

class TableInfo(BaseModel):
    name: str
    columns: List[Dict[str, Any]]
    row_count: Optional[int] = None
    sample_data: Optional[List[Dict[str, Any]]] = None
    relationships: Optional[List[Dict[str, Any]]] = None

class SchemaResponse(BaseModel):
    database: str
    tables: List[TableInfo]
    total_tables: int
    success: bool
    error_message: Optional[str] = None

@router.get("/", response_model=SchemaResponse)
async def get_schema(
    request: Request,
    current_user: UserResponse = Depends(get_current_user),
    database: str = "northwind",
    include_sample_data: bool = False,
    table_filter: Optional[str] = None
):
    """Get database schema information."""
    try:
        # Get database manager from app state
        db_manager = request.app.state.db_manager
        
        # Create schema analyzer tool
        schema_analyzer = SchemaAnalyzerTool(db_manager)
        
        # Parse table filter if provided
        tables_to_include = table_filter.split(",") if table_filter else None
        
        # Get schema information
        schema_info = await schema_analyzer._run(
            database=database,
            include_sample_data=include_sample_data,
            table_filter=tables_to_include
        )
        
        # Parse the schema information
        tables = []
        if isinstance(schema_info, dict) and "tables" in schema_info:
            for table_name, table_data in schema_info["tables"].items():
                table_info = TableInfo(
                    name=table_name,
                    columns=table_data.get("columns", []),
                    row_count=table_data.get("row_count"),
                    sample_data=table_data.get("sample_data") if include_sample_data else None,
                    relationships=table_data.get("relationships", [])
                )
                tables.append(table_info)
        
        return SchemaResponse(
            database=database,
            tables=tables,
            total_tables=len(tables),
            success=True
        )
        
    except Exception as e:
        logger.error(f"Schema retrieval failed: {str(e)}")
        return SchemaResponse(
            database=database,
            tables=[],
            total_tables=0,
            success=False,
            error_message=str(e)
        )

@router.get("/tables")
async def get_table_list(
    request: Request,
    current_user: UserResponse = Depends(get_current_user),
    database: str = "northwind"
):
    """Get list of tables in the database."""
    try:
        db_manager = request.app.state.db_manager
        schema_analyzer = SchemaAnalyzerTool(db_manager)
        
        # Get table list
        tables = await schema_analyzer.get_table_list(database)
        
        return {
            "database": database,
            "tables": tables,
            "total": len(tables)
        }
        
    except Exception as e:
        logger.error(f"Failed to get table list: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve table list"
        )

@router.get("/tables/{table_name}")
async def get_table_info(
    table_name: str,
    request: Request,
    current_user: UserResponse = Depends(get_current_user),
    database: str = "northwind",
    include_sample_data: bool = False
):
    """Get detailed information about a specific table."""
    try:
        db_manager = request.app.state.db_manager
        schema_analyzer = SchemaAnalyzerTool(db_manager)
        
        # Get table information
        table_info = await schema_analyzer.get_table_info(
            database=database,
            table_name=table_name,
            include_sample_data=include_sample_data
        )
        
        return {
            "database": database,
            "table": table_info,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Failed to get table info for {table_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve information for table {table_name}"
        )

@router.get("/relationships")
async def get_table_relationships(
    request: Request,
    current_user: UserResponse = Depends(get_current_user),
    database: str = "northwind"
):
    """Get table relationships and foreign key constraints."""
    try:
        db_manager = request.app.state.db_manager
        schema_analyzer = SchemaAnalyzerTool(db_manager)
        
        # Get relationships
        relationships = await schema_analyzer.get_table_relationships(database)
        
        return {
            "database": database,
            "relationships": relationships,
            "total": len(relationships)
        }
        
    except Exception as e:
        logger.error(f"Failed to get table relationships: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve table relationships"
        ) 