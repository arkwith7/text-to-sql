"""
Schema Analyzer Tool for Text-to-SQL application.
Provides database schema analysis and information retrieval.
"""

import logging
import json
from typing import Dict, Any, Optional, List, TYPE_CHECKING

# TYPE_CHECKING을 사용하여 순환 import 방지
if TYPE_CHECKING:
    from database.connection_manager import DatabaseManager

logger = logging.getLogger(__name__)

class SchemaAnalyzerTool:
    """
    Schema Analyzer Tool for database schema analysis.
    Enhanced with actual PostgreSQL Northwind schema information.
    """
    
    def __init__(self, db_manager: Optional["DatabaseManager"] = None):
        """
        Initialize the schema analyzer tool.
        
        Args:
            db_manager: Database manager instance (Optional, 순환 import 방지)
        """
        self.db_manager = db_manager
        
        # PostgreSQL Northwind 실제 스키마 정보 (주피터 노트북에서 성공한 구조)
        self.northwind_schema = {
            "database": "northwind",
            "description": "Microsoft Northwind 샘플 데이터베이스 - 가상 무역회사의 판매 데이터",
            "tables": {
                "categories": {
                    "columns": [
                        {"name": "categoryid", "type": "INTEGER PRIMARY KEY", "description": "카테고리 ID (자동 증가)"},
                        {"name": "categoryname", "type": "VARCHAR(25)", "description": "카테고리 이름"},
                        {"name": "description", "type": "VARCHAR(255)", "description": "카테고리 설명"}
                    ],
                    "description": "제품 카테고리 정보 테이블",
                    "sample_data": "음료, 조미료, 과자류, 유제품, 곡물/시리얼, 육류/가금류, 농산물, 해산물",
                    "row_count": 8
                },
                "customers": {
                    "columns": [
                        {"name": "customerid", "type": "INTEGER PRIMARY KEY", "description": "고객 ID (자동 증가)"},
                        {"name": "customername", "type": "VARCHAR(50)", "description": "고객회사명"},
                        {"name": "contactname", "type": "VARCHAR(50)", "description": "담당자명"},
                        {"name": "address", "type": "VARCHAR(50)", "description": "주소"},
                        {"name": "city", "type": "VARCHAR(20)", "description": "도시"},
                        {"name": "postalcode", "type": "VARCHAR(10)", "description": "우편번호"},
                        {"name": "country", "type": "VARCHAR(15)", "description": "국가"}
                    ],
                    "description": "고객 정보 테이블",
                    "row_count": 91
                },
                "employees": {
                    "columns": [
                        {"name": "employeeid", "type": "INTEGER PRIMARY KEY", "description": "직원 ID (자동 증가)"},
                        {"name": "lastname", "type": "VARCHAR(15)", "description": "성"},
                        {"name": "firstname", "type": "VARCHAR(15)", "description": "이름"},
                        {"name": "birthdate", "type": "TIMESTAMP", "description": "생년월일"},
                        {"name": "photo", "type": "VARCHAR(25)", "description": "사진 파일명"},
                        {"name": "notes", "type": "VARCHAR(1024)", "description": "직원 설명"}
                    ],
                    "description": "직원 정보 테이블",
                    "row_count": 10
                },
                "shippers": {
                    "columns": [
                        {"name": "shipperid", "type": "INTEGER PRIMARY KEY", "description": "배송업체 ID (자동 증가)"},
                        {"name": "shippername", "type": "VARCHAR(25)", "description": "배송업체명"},
                        {"name": "phone", "type": "VARCHAR(15)", "description": "전화번호"}
                    ],
                    "description": "배송업체 정보 테이블",
                    "row_count": 3
                },
                "suppliers": {
                    "columns": [
                        {"name": "supplierid", "type": "INTEGER PRIMARY KEY", "description": "공급업체 ID (자동 증가)"},
                        {"name": "suppliername", "type": "VARCHAR(50)", "description": "공급업체명"},
                        {"name": "contactname", "type": "VARCHAR(50)", "description": "담당자명"},
                        {"name": "address", "type": "VARCHAR(50)", "description": "주소"},
                        {"name": "city", "type": "VARCHAR(20)", "description": "도시"},
                        {"name": "postalcode", "type": "VARCHAR(10)", "description": "우편번호"},
                        {"name": "country", "type": "VARCHAR(15)", "description": "국가"},
                        {"name": "phone", "type": "VARCHAR(15)", "description": "전화번호"}
                    ],
                    "description": "공급업체 정보 테이블",
                    "row_count": 29
                },
                "products": {
                    "columns": [
                        {"name": "productid", "type": "INTEGER PRIMARY KEY", "description": "제품 ID (자동 증가)"},
                        {"name": "productname", "type": "VARCHAR(50)", "description": "제품명"},
                        {"name": "supplierid", "type": "INTEGER", "description": "공급업체 ID (FK)"},
                        {"name": "categoryid", "type": "INTEGER", "description": "카테고리 ID (FK)"},
                        {"name": "unit", "type": "VARCHAR(25)", "description": "단위"},
                        {"name": "price", "type": "NUMERIC(10,2)", "description": "단가"}
                    ],
                    "description": "제품 정보 테이블",
                    "row_count": 77
                },
                "orders": {
                    "columns": [
                        {"name": "orderid", "type": "INTEGER PRIMARY KEY", "description": "주문 ID (자동 증가)"},
                        {"name": "customerid", "type": "INTEGER", "description": "고객 ID (FK)"},
                        {"name": "employeeid", "type": "INTEGER", "description": "직원 ID (FK)"},
                        {"name": "orderdate", "type": "TIMESTAMP", "description": "주문 날짜"},
                        {"name": "shipperid", "type": "INTEGER", "description": "배송업체 ID (FK)"}
                    ],
                    "description": "주문 정보 테이블",
                    "row_count": 196
                },
                "orderdetails": {
                    "columns": [
                        {"name": "orderdetailid", "type": "INTEGER PRIMARY KEY", "description": "주문상세 ID (자동 증가)"},
                        {"name": "orderid", "type": "INTEGER", "description": "주문 ID (FK)"},
                        {"name": "productid", "type": "INTEGER", "description": "제품 ID (FK)"},
                        {"name": "quantity", "type": "INTEGER", "description": "주문 수량"}
                    ],
                    "description": "주문 상세 정보 테이블",
                    "row_count": 518
                }
            },
            "relationships": [
                {"from_table": "products", "from_column": "categoryid", "to_table": "categories", "to_column": "categoryid"},
                {"from_table": "products", "from_column": "supplierid", "to_table": "suppliers", "to_column": "supplierid"},
                {"from_table": "orders", "from_column": "customerid", "to_table": "customers", "to_column": "customerid"},
                {"from_table": "orders", "from_column": "employeeid", "to_table": "employees", "to_column": "employeeid"},
                {"from_table": "orders", "from_column": "shipperid", "to_table": "shippers", "to_column": "shipperid"},
                {"from_table": "orderdetails", "from_column": "orderid", "to_table": "orders", "to_column": "orderid"},
                {"from_table": "orderdetails", "from_column": "productid", "to_table": "products", "to_column": "productid"}
            ],
            "common_queries": [
                "SELECT COUNT(*) FROM customers; -- 고객 수 조회",
                "SELECT COUNT(*) FROM products; -- 제품 수 조회",
                "SELECT COUNT(*) FROM orders; -- 주문 수 조회",
                "SELECT categoryname, COUNT(*) FROM categories c JOIN products p ON c.categoryid = p.categoryid GROUP BY categoryname; -- 카테고리별 제품 수",
                "SELECT productname, price FROM products ORDER BY price DESC LIMIT 5; -- 가장 비싼 제품 5개",
                "SELECT c.customername, COUNT(o.orderid) as order_count FROM customers c LEFT JOIN orders o ON c.customerid = o.customerid GROUP BY c.customerid, c.customername ORDER BY order_count DESC LIMIT 10; -- 주문이 많은 고객",
                "SELECT country, COUNT(*) as customer_count FROM customers GROUP BY country ORDER BY customer_count DESC; -- 국가별 고객 수"
            ]
        }
        
        logger.info("Schema Analyzer Tool 초기화 완료 - PostgreSQL Northwind 스키마 로드됨")
    
    async def get_table_list(self, database: str) -> List[str]:
        """
        Get list of tables in the database.
        
        Args:
            database: Target database name
            
        Returns:
            List of table names
        """
        try:
            if database.lower() == "northwind":
                return list(self.northwind_schema["tables"].keys())
            
            # 실제 데이터베이스 연결이 있다면 여기서 조회
            if self.db_manager:
                # TODO: 실제 DB 연결 구현
                pass
                
            # 기본 반환값
            return ["customers", "orders", "products", "categories", "employees", "suppliers", "shippers", "orderdetails"]
            
        except Exception as e:
            logger.error(f"테이블 목록 조회 실패 - Database: {database}, Error: {str(e)}")
            raise
    
    async def get_table_info(
        self,
        database: str,
        table_name: str,
        include_sample_data: bool = False
    ) -> Dict[str, Any]:
        """
        Get detailed information about a specific table.
        
        Args:
            database: Target database name
            table_name: Name of the table
            include_sample_data: Whether to include sample data
            
        Returns:
            Dictionary containing table information
        """
        try:
            if database.lower() == "northwind" and table_name in self.northwind_schema["tables"]:
                table_info = self.northwind_schema["tables"][table_name].copy()
                
                if include_sample_data and "sample_data" in table_info:
                    # 샘플 데이터가 있으면 포함
                    pass
                elif "sample_data" in table_info:
                    # 샘플 데이터 제거
                    del table_info["sample_data"]
                
                return table_info
            
            # 기본 placeholder (실제 DB 연결 시 실제 스키마 조회)
            return {
                "table_name": table_name,
                "columns": [
                    {"name": "id", "type": "INTEGER PRIMARY KEY", "description": "기본 키"},
                    {"name": "name", "type": "VARCHAR(50)", "description": "이름"}
                ],
                "description": f"{table_name} 테이블",
                "row_count": 0
            }
            
        except Exception as e:
            logger.error(f"테이블 정보 조회 실패 - Table: {table_name}, Database: {database}, Error: {str(e)}")
            raise
    
    async def get_table_relationships(self, database: str) -> List[Dict[str, Any]]:
        """
        Get table relationships and foreign key constraints.
        
        Args:
            database: Target database name
            
        Returns:
            List of relationship information
        """
        try:
            if database.lower() == "northwind":
                return self.northwind_schema["relationships"]
            
            # 기본 반환값
            return [
                {"from_table": "orders", "from_column": "customerid", "to_table": "customers", "to_column": "customerid"},
                {"from_table": "orderdetails", "from_column": "orderid", "to_table": "orders", "to_column": "orderid"}
            ]
            
        except Exception as e:
            logger.error(f"테이블 관계 조회 실패 - Database: {database}, Error: {str(e)}")
            raise
    
    def get_schema_as_json(self, database: str = "northwind") -> str:
        """
        Get complete schema information as JSON string.
        This method is compatible with LangChain Tools.
        
        Args:
            database: Target database name
            
        Returns:
            JSON string containing schema information
        """
        try:
            if database.lower() == "northwind":
                return json.dumps(self.northwind_schema, ensure_ascii=False, indent=2)
            
            # 기본 스키마 정보
            basic_schema = {
                "database": database,
                "description": f"{database} 데이터베이스",
                "tables": {},
                "relationships": []
            }
            
            return json.dumps(basic_schema, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"스키마 JSON 변환 실패 - Database: {database}, Error: {str(e)}")
            return f"스키마 조회 오류: {str(e)}"
    
    async def get_common_queries(self, database: str = "northwind") -> List[str]:
        """
        Get list of common SQL queries for the database.
        
        Args:
            database: Target database name
            
        Returns:
            List of common SQL queries with Korean comments
        """
        try:
            if database.lower() == "northwind":
                return self.northwind_schema["common_queries"]
            
            return [
                "SELECT COUNT(*) FROM customers; -- 고객 수 조회",
                "SELECT COUNT(*) FROM products; -- 제품 수 조회"
            ]
            
        except Exception as e:
            logger.error(f"공통 쿼리 조회 실패 - Database: {database}, Error: {str(e)}")
            return []

    async def _run(
        self,
        database: str,
        include_sample_data: bool = False,
        table_filter: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Run schema analysis for the specified database.
        
        Args:
            database: Target database name
            include_sample_data: Whether to include sample data
            table_filter: List of tables to include (None for all)
            
        Returns:
            Dictionary containing schema information
        """
        try:
            if database.lower() == "northwind":
                schema_info = self.northwind_schema.copy()
                
                if table_filter:
                    # 필터링된 테이블만 포함
                    filtered_tables = {}
                    for table_name in table_filter:
                        if table_name in schema_info["tables"]:
                            filtered_tables[table_name] = schema_info["tables"][table_name]
                    schema_info["tables"] = filtered_tables
                
                if not include_sample_data:
                    # 샘플 데이터 제거
                    for table_info in schema_info["tables"].values():
                        if "sample_data" in table_info:
                            del table_info["sample_data"]
                
                logger.info(f"스키마 분석 완료 - Database: {database}, Tables: {len(schema_info['tables'])}개")
                return schema_info
            
            # 다른 데이터베이스의 경우 기본 로직
            tables = await self.get_table_list(database)
            
            if table_filter:
                tables = [t for t in tables if t in table_filter]
            
            schema_info = {"database": database, "tables": {}, "relationships": []}
            
            for table_name in tables:
                table_info = await self.get_table_info(
                    database=database,
                    table_name=table_name,
                    include_sample_data=include_sample_data
                )
                schema_info["tables"][table_name] = table_info
            
            # 관계 정보 추가
            schema_info["relationships"] = await self.get_table_relationships(database)
            
            logger.info(f"스키마 분석 완료 - Database: {database}, Tables: {len(schema_info['tables'])}개")
            return schema_info
            
        except Exception as e:
            logger.error(f"스키마 분석 실패 - Database: {database}, Error: {str(e)}")
            raise 