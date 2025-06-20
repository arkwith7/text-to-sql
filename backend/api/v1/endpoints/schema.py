"""
Schema endpoints for Text-to-SQL application.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from sqlalchemy import MetaData
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from services.auth_dependencies import get_current_user
from services.auth_service import UserResponse
from core.tools.schema_analyzer_tool import SchemaAnalyzerTool
from services.schema_service import SchemaService
from database.connection_manager import db_manager
from models.models import User
from core.config import get_settings
from sqlalchemy.engine.url import make_url
import os

logger = logging.getLogger(__name__)

router = APIRouter()

# Dependency for database session
async def get_db_session():
    """Get database session for dependency injection"""
    async with db_manager.get_session("app") as session:
        yield session

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
    table_filter: Optional[str] = None,
    connection_id: Optional[str] = None
):
    """Get database schema information."""
    try:
        # Get database manager from app state
        db_manager = request.app.state.db_manager
        
        # If connection_id가 제공되면 해당 연결의 실제 스키마를 조회합니다.
        if connection_id:
            user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id

            # 동적 엔진 생성
            analysis_engine = await db_manager.get_analysis_db_engine(
                connection_id=connection_id,
                user_id=user_id
            )

            metadata = MetaData()
            async with analysis_engine.connect() as conn:
                await conn.run_sync(metadata.reflect)

            tables: List[TableInfo] = []
            for tbl_name, tbl in metadata.tables.items():
                # 테이블 필터가 지정된 경우 적용
                if table_filter:
                    filters = table_filter.split(",")
                    if tbl_name not in filters:
                        continue

                cols = [
                    {
                        "column_name": col.name,
                        "data_type": str(col.type),
                        "is_nullable": col.nullable,
                    }
                    for col in tbl.columns
                ]
                tables.append(
                    TableInfo(
                        name=tbl_name,
                        columns=cols,
                        row_count=None,
                        sample_data=None,
                        relationships=None,
                    )
                )

            return SchemaResponse(
                database=f"conn:{connection_id}",
                tables=tables,
                total_tables=len(tables),
                success=True,
            )

        # ---- 기존 northwind (또는 database 파라미터) 로직 유지 ----
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

@router.get("/{connection_id}")
async def get_database_schema(
    connection_id: str,
    force_refresh: bool = Query(False, description="강제로 스키마 새로고침"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    연결된 데이터베이스의 스키마 정보를 조회합니다.
    캐시된 정보가 있으면 사용하고, 없거나 변경되었으면 새로 조회하여 LLM으로 문서화합니다.
    """
    try:
        # current_user가 딕셔너리인지 객체인지 확인
        user_id = current_user.get('id') if isinstance(current_user, dict) else current_user.id
        print(f"🔍 스키마 조회 시작: connection_id={connection_id}, user_id={user_id}")
        
        schema_service = SchemaService(session)
        schema_info = await schema_service.get_schema_info(
            user_id=user_id,
            connection_id=connection_id,
            force_refresh=force_refresh
        )
        
        return {
            "success": True,
            "data": schema_info,
            "message": "스키마 정보 조회 성공"
        }
        
    except ValueError as e:
        print(f"❌ ValueError in get_database_schema: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"❌ Exception in get_database_schema: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"스키마 정보 조회 실패: {str(e)}")

@router.post("/{connection_id}/refresh")
async def refresh_database_schema(
    connection_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    데이터베이스 스키마 정보를 강제로 새로고침합니다.
    """
    try:
        # current_user가 딕셔너리인지 객체인지 확인
        user_id = current_user.get('id') if isinstance(current_user, dict) else current_user.id
        
        schema_service = SchemaService(session)
        schema_info = await schema_service.refresh_schema(
            user_id=user_id,
            connection_id=connection_id
        )
        
        return {
            "success": True,
            "data": schema_info,
            "message": "스키마 새로고침 완료"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"스키마 새로고침 실패: {str(e)}")

@router.get("/list")
async def get_user_schemas(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    사용자의 모든 데이터베이스 연결에 대한 스키마 목록을 조회합니다.
    """
    try:
        # current_user가 딕셔너리인지 객체인지 확인
        user_id = current_user.get('id') if isinstance(current_user, dict) else current_user.id
        
        schema_service = SchemaService(session)
        schemas = await schema_service.get_schema_list(user_id=user_id)
        
        return {
            "success": True,
            "data": schemas,
            "count": len(schemas),
            "message": "스키마 목록 조회 성공"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"스키마 목록 조회 실패: {str(e)}")

# 기존 northwind 스키마 조회 (호환성 유지)
@router.get("/northwind/info")
async def get_northwind_schema():
    """
    Northwind 데이터베이스 스키마 정보 조회 (기존 호환성 유지)
    """
    # 기존 하드코딩된 northwind 스키마 정보
    northwind_schema = {
        "database_name": "northwind",
        "table_count": 14,
        "tables": [
            {
                "table_name": "customers",
                "description": "고객 정보",
                "columns": [
                    {"name": "customer_id", "type": "varchar", "description": "고객 ID"},
                    {"name": "company_name", "type": "varchar", "description": "회사명"},
                    {"name": "contact_name", "type": "varchar", "description": "담당자명"},
                    {"name": "country", "type": "varchar", "description": "국가"},
                    {"name": "city", "type": "varchar", "description": "도시"}
                ]
            },
            {
                "table_name": "products",
                "description": "제품 정보",
                "columns": [
                    {"name": "product_id", "type": "integer", "description": "제품 ID"},
                    {"name": "product_name", "type": "varchar", "description": "제품명"},
                    {"name": "unit_price", "type": "decimal", "description": "단가"},
                    {"name": "units_in_stock", "type": "integer", "description": "재고량"},
                    {"name": "category_id", "type": "integer", "description": "카테고리 ID"}
                ]
            },
            {
                "table_name": "orders",
                "description": "주문 정보",
                "columns": [
                    {"name": "order_id", "type": "integer", "description": "주문 ID"},
                    {"name": "customer_id", "type": "varchar", "description": "고객 ID"},
                    {"name": "order_date", "type": "date", "description": "주문일자"},
                    {"name": "required_date", "type": "date", "description": "요청일자"},
                    {"name": "shipped_date", "type": "date", "description": "배송일자"}
                ]
            },
            {
                "table_name": "order_details",
                "description": "주문 상세 정보",
                "columns": [
                    {"name": "order_id", "type": "integer", "description": "주문 ID"},
                    {"name": "product_id", "type": "integer", "description": "제품 ID"},
                    {"name": "unit_price", "type": "decimal", "description": "단가"},
                    {"name": "quantity", "type": "integer", "description": "수량"},
                    {"name": "discount", "type": "decimal", "description": "할인율"}
                ]
            }
        ],
        "relationships": [
            "customers.customer_id → orders.customer_id",
            "orders.order_id → order_details.order_id",
            "products.product_id → order_details.product_id"
        ]
    }
    
    return {
        "success": True,
        "data": northwind_schema,
        "message": "Northwind 스키마 정보 조회 성공"
    }



@router.post("/fix-table", tags=["Schema"], summary="Fix database_schemas table structure")
async def fix_database_schemas_table(
    session: AsyncSession = Depends(get_db_session)
):
    """임시: database_schemas 테이블 구조를 수정합니다."""
    try:
        import sqlite3
        
        settings_cfg = get_settings()
        db_url = settings_cfg.app_database_url
        db_path = os.path.abspath(make_url(db_url).database or 'app_data.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        logger.info(f"🔗 SQLite file in use → {db_path}")
        
        logger.info("🔍 현재 database_schemas 테이블 구조 확인...")
        
        # 현재 테이블 구조 확인
        cursor.execute("PRAGMA table_info(database_schemas)")
        current_columns = cursor.fetchall()
        column_names = [col[1] for col in current_columns]
        
        if 'connection_id' in column_names:
            conn.close()
            return {"success": True, "message": "connection_id 컬럼이 이미 존재합니다."}
        
        logger.info("🔨 테이블 구조를 업데이트합니다...")
        
        # 기존 데이터 수 확인
        cursor.execute("SELECT COUNT(*) FROM database_schemas")
        row_count = cursor.fetchone()[0]
        
        # 기존 테이블 이름 변경
        cursor.execute("ALTER TABLE database_schemas RENAME TO database_schemas_backup")
        
        # 새로운 테이블 생성
        create_table_sql = """
        CREATE TABLE database_schemas (
            id VARCHAR(36) NOT NULL PRIMARY KEY,
            connection_id VARCHAR(36) NOT NULL,
            schema_hash VARCHAR(64) NOT NULL,
            raw_schema TEXT NOT NULL,
            generated_documentation TEXT,
            table_count INTEGER,
            total_columns INTEGER,
            last_updated DATETIME NOT NULL,
            created_at DATETIME NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT 1,
            database_name VARCHAR(100),
            table_name VARCHAR(100),
            schema_info TEXT,
            row_count INTEGER,
            table_size VARCHAR(50),
            FOREIGN KEY(connection_id) REFERENCES database_connections (id) ON DELETE CASCADE
        );
        """
        
        cursor.execute(create_table_sql)
        
        # 인덱스 생성
        cursor.execute("CREATE INDEX ix_database_schemas_connection_id ON database_schemas (connection_id);")
        cursor.execute("CREATE INDEX ix_database_schemas_schema_hash ON database_schemas (schema_hash);")
        
        # 백업 테이블 삭제
        cursor.execute("DROP TABLE database_schemas_backup")
        
        # alembic_version 업데이트
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='alembic_version'")
        alembic_exists = cursor.fetchone()[0] > 0
        
        if alembic_exists:
            cursor.execute("UPDATE alembic_version SET version_num = '9f3e5a1b7c4d'")
        else:
            cursor.execute("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL PRIMARY KEY)")
            cursor.execute("INSERT INTO alembic_version (version_num) VALUES ('9f3e5a1b7c4d')")
        
        conn.commit()
        conn.close()
        
        logger.info("✅ database_schemas 테이블이 성공적으로 업데이트되었습니다!")
        
        return {
            "success": True, 
            "message": "database_schemas 테이블이 성공적으로 업데이트되었습니다.",
            "old_row_count": row_count
        }
        
    except Exception as e:
        logger.error(f"❌ 테이블 업데이트 중 오류 발생: {e}")
        return {"success": False, "error": str(e)} 