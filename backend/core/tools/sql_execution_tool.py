"""
SQL Execution Tool for Text-to-SQL application.
Provides safe SQL query execution with validation and monitoring.
Enhanced with simulation mode and improved error handling.
"""

import logging
import time
import json
from typing import Dict, Any, Optional, List, TYPE_CHECKING

# TYPE_CHECKING을 사용하여 순환 import 방지
if TYPE_CHECKING:
    from database.connection_manager import DatabaseManager
    
from utils.logging_config import SQLLogger

logger = logging.getLogger(__name__)

class SQLExecutionTool:
    """
    SQL Execution Tool for safe SQL query execution.
    Enhanced with simulation mode based on successful Jupyter notebook patterns.
    """
    
    def __init__(self, db_manager: Optional["DatabaseManager"] = None, enable_simulation: bool = True):
        """
        Initialize the SQL execution tool.
        
        Args:
            db_manager: Database manager instance (Optional, 순환 import 방지)
            enable_simulation: Whether to enable simulation mode for testing
        """
        self.db_manager = db_manager
        self.enable_simulation = enable_simulation
        
        # 시뮬레이션용 데이터 (주피터 노트북에서 성공한 패턴)
        self.simulation_data = {
            "customers": {"count": 91, "sample": [{"customerid": 1, "customername": "Alfreds Futterkiste", "country": "Germany"}]},
            "products": {"count": 77, "sample": [{"productid": 1, "productname": "Chais", "price": 18.00}]},
            "orders": {"count": 196, "sample": [{"orderid": 10248, "customerid": 1, "orderdate": "1996-07-04"}]},
            "categories": {"count": 8, "sample": [{"categoryid": 1, "categoryname": "Beverages"}]},
            "employees": {"count": 10, "sample": [{"employeeid": 1, "firstname": "Nancy", "lastname": "Davolio"}]},
            "suppliers": {"count": 29, "sample": [{"supplierid": 1, "suppliername": "Exotic Liquids"}]},
            "shippers": {"count": 3, "sample": [{"shipperid": 1, "shippername": "Speedy Express"}]},
            "orderdetails": {"count": 518, "sample": [{"orderdetailid": 1, "orderid": 10248, "productid": 11, "quantity": 12}]}
        }
        
        logger.info(f"SQL Execution Tool 초기화 완료 - 시뮬레이션 모드: {enable_simulation}")
    
    async def execute_query(
        self,
        sql_query: str,
        database: str,
        max_rows: Optional[int] = None,
        timeout: Optional[int] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute SQL query with safety checks and monitoring.
        Enhanced with simulation mode and proper logging.
        
        Args:
            sql_query: SQL query to execute
            database: Target database name
            max_rows: Maximum number of rows to return
            timeout: Query timeout in seconds
            user_id: User ID for logging
            
        Returns:
            Dictionary containing query results and metadata
        """
        start_time = time.time()
        
        try:
            logger.info(
                f"🗄️ SQL 실행 시작 - Database: {database}",
                extra={
                    'user_id': user_id,
                    'sql_query': sql_query[:200] + '...' if len(sql_query) > 200 else sql_query,
                    'database': database,
                    'max_rows': max_rows,
                    'timeout': timeout,
                    'simulation_mode': self.enable_simulation
                }
            )
            
            # SQL 쿼리 검증
            validation_result = await self.validate_query(sql_query, database)
            if not validation_result["is_valid"]:
                raise ValueError(f"Invalid SQL query: {validation_result['error_message']}")
            
            # 실제 DB 연결이 가능한 경우 실제 실행
            if self.db_manager and not self.enable_simulation:
                results = await self._execute_real_query(sql_query, database, max_rows, timeout)
            else:
                # 시뮬레이션 모드
                results = self._execute_simulated_query(sql_query, database, max_rows)
            
            execution_time = time.time() - start_time
            
            # 성공 로깅
            SQLLogger.log_query_execution(
                query=sql_query,
                execution_time=execution_time,
                result_count=len(results),
                user_id=user_id,
                success=True
            )
            
            logger.info(
                f"✅ SQL 실행 완료 - 시간: {execution_time:.3f}s, 결과: {len(results)}행",
                extra={
                    'user_id': user_id,
                    'execution_time': execution_time,
                    'result_count': len(results),
                    'database': database
                }
            )
            
            return {
                "success": True,
                "sql_query": sql_query,
                "results": results,
                "row_count": len(results),
                "execution_time": execution_time,
                "database": database,
                "simulation_mode": self.enable_simulation
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            
            # 에러 로깅
            SQLLogger.log_query_execution(
                query=sql_query,
                execution_time=execution_time,
                result_count=0,
                user_id=user_id,
                success=False,
                error=error_msg
            )
            
            logger.error(
                f"❌ SQL 실행 실패 - Database: {database}, Error: {error_msg}",
                extra={
                    'user_id': user_id,
                    'sql_query': sql_query[:200] + '...' if len(sql_query) > 200 else sql_query,
                    'database': database,
                    'execution_time': execution_time,
                    'error': error_msg
                }
            )
            
            return {
                "success": False,
                "error": error_msg,
                "sql_query": sql_query,
                "execution_time": execution_time,
                "database": database,
                "results": [],
                "row_count": 0
            }
    
    def _execute_simulated_query(self, sql_query: str, database: str, max_rows: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Execute query in simulation mode based on successful Jupyter notebook patterns.
        
        Args:
            sql_query: SQL query to simulate
            database: Target database name
            max_rows: Maximum number of rows to return
            
        Returns:
            Simulated query results
        """
        try:
            sql_upper = sql_query.upper().strip()
            
            # COUNT 쿼리 처리
            if "COUNT(*)" in sql_upper:
                for table_name, table_data in self.simulation_data.items():
                    if table_name.upper() in sql_upper:
                        return [{"count": table_data["count"]}]
                
                # 기본 COUNT 결과
                return [{"count": 0}]
            
            # SELECT 쿼리 처리
            elif sql_upper.startswith("SELECT"):
                # 테이블별 샘플 데이터 반환
                for table_name, table_data in self.simulation_data.items():
                    if table_name.upper() in sql_upper:
                        results = table_data["sample"] * (max_rows if max_rows and max_rows > 1 else 1)
                        if max_rows:
                            results = results[:max_rows]
                        return results
                
                # JOIN이나 복잡한 쿼리의 경우
                if "JOIN" in sql_upper or "GROUP BY" in sql_upper:
                    return [
                        {"category": "음료", "count": 12},
                        {"category": "과자류", "count": 8},
                        {"category": "유제품", "count": 10}
                    ]
                
                # 기본 결과
                return [{"message": "쿼리가 성공적으로 시뮬레이션되었습니다."}]
            
            # INSERT, UPDATE, DELETE 쿼리
            elif any(keyword in sql_upper for keyword in ["INSERT", "UPDATE", "DELETE"]):
                return [{"affected_rows": 1, "message": "쿼리가 성공적으로 시뮬레이션되었습니다."}]
            
            # 기타 쿼리
            else:
                return [{"message": "쿼리가 성공적으로 시뮬레이션되었습니다."}]
                
        except Exception as e:
            logger.warning(f"시뮬레이션 실행 중 오류: {str(e)}")
            return [{"error": f"시뮬레이션 오류: {str(e)}"}]
    
    async def _execute_real_query(
        self,
        sql_query: str,
        database: str,
        max_rows: Optional[int] = None,
        timeout: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute query against real database.
        
        Args:
            sql_query: SQL query to execute
            database: Target database name
            max_rows: Maximum number of rows to return
            timeout: Query timeout in seconds
            
        Returns:
            Real query results
        """
        try:
            # TODO: 실제 데이터베이스 연결 및 실행 로직 구현
            # 현재는 시뮬레이션으로 대체
            logger.warning("실제 DB 연결 미구현 - 시뮬레이션 모드로 전환")
            return self._execute_simulated_query(sql_query, database, max_rows)
            
        except Exception as e:
            logger.error(f"실제 쿼리 실행 실패: {str(e)}")
            raise
    
    async def validate_query(
        self,
        sql_query: str,
        database: str
    ) -> Dict[str, Any]:
        """
        Validate SQL query without executing it.
        Enhanced with better validation logic.
        
        Args:
            sql_query: SQL query to validate
            database: Target database name
            
        Returns:
            Dictionary containing validation results
        """
        try:
            sql_query = sql_query.strip()
            
            # 기본 검증
            if not sql_query:
                return {
                    "is_valid": False,
                    "error_message": "빈 쿼리입니다.",
                    "suggestions": ["유효한 SQL 쿼리를 입력하세요."]
                }
            
            # 위험한 키워드 검사
            dangerous_keywords = ["DROP", "TRUNCATE", "DELETE FROM", "ALTER", "CREATE", "GRANT", "REVOKE"]
            sql_upper = sql_query.upper()
            
            for keyword in dangerous_keywords:
                if keyword in sql_upper:
                    return {
                        "is_valid": False,
                        "error_message": f"위험한 키워드가 포함되어 있습니다: {keyword}",
                        "suggestions": ["SELECT, INSERT, UPDATE 쿼리만 허용됩니다."]
                    }
            
            # 허용된 키워드 검사
            allowed_keywords = ["SELECT", "INSERT", "UPDATE", "WITH", "EXPLAIN"]
            if not any(keyword in sql_upper for keyword in allowed_keywords):
                return {
                    "is_valid": False,
                    "error_message": "허용되지 않는 SQL 문입니다.",
                    "suggestions": ["SELECT, INSERT, UPDATE 쿼리만 허용됩니다."]
                }
            
            # 기본 구문 검사
            if sql_upper.startswith("SELECT") and "FROM" not in sql_upper:
                return {
                    "is_valid": False,
                    "error_message": "SELECT 문에 FROM 절이 누락되었습니다.",
                    "suggestions": ["FROM 절을 추가하세요."]
                }
            
            # 검증 통과
            logger.debug(f"SQL 검증 성공: {sql_query[:100]}...")
            return {
                "is_valid": True,
                "error_message": None,
                "suggestions": [],
                "query_type": self._get_query_type(sql_query)
            }
            
        except Exception as e:
            logger.error(f"SQL 검증 중 오류 - Database: {database}, Error: {str(e)}")
            return {
                "is_valid": False,
                "error_message": f"검증 중 오류가 발생했습니다: {str(e)}",
                "suggestions": ["쿼리 구문을 다시 확인하세요."]
            }
    
    def _get_query_type(self, sql_query: str) -> str:
        """
        Determine the type of SQL query.
        
        Args:
            sql_query: SQL query string
            
        Returns:
            Query type (SELECT, INSERT, UPDATE, etc.)
        """
        sql_upper = sql_query.upper().strip()
        
        if sql_upper.startswith("SELECT"):
            return "SELECT"
        elif sql_upper.startswith("INSERT"):
            return "INSERT"
        elif sql_upper.startswith("UPDATE"):
            return "UPDATE"
        elif sql_upper.startswith("DELETE"):
            return "DELETE"
        elif sql_upper.startswith("WITH"):
            return "CTE"
        elif sql_upper.startswith("EXPLAIN"):
            return "EXPLAIN"
        else:
            return "OTHER"
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """
        Get execution statistics for monitoring.
        
        Returns:
            Dictionary containing execution statistics
        """
        try:
            # TODO: 실제 통계 수집 로직 구현
            return {
                "total_queries": 0,
                "successful_queries": 0,
                "failed_queries": 0,
                "avg_execution_time": 0.0,
                "simulation_mode": self.enable_simulation
            }
            
        except Exception as e:
            logger.error(f"통계 조회 실패: {str(e)}")
            return {"error": str(e)} 