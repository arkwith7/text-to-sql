import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
import asyncpg
import asyncio

from models.models import DatabaseConnection, User
from services.encryption_service import encryption_service

class ConnectionService:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_connection(self, user_id: str, connection_id: str) -> Optional[Dict[str, Any]]:
        stmt = select(DatabaseConnection).where(
            DatabaseConnection.id == connection_id,
            DatabaseConnection.user_id == user_id
        )
        result = await self.db_session.execute(stmt)
        connection = result.scalars().first()
        if connection:
            return self._connection_to_dict(connection, decrypt=True)
        return None

    async def get_all_connections(self, user_id: str) -> List[Dict[str, Any]]:
        stmt = select(DatabaseConnection).where(DatabaseConnection.user_id == user_id)
        result = await self.db_session.execute(stmt)
        connections = result.scalars().all()
        return [self._connection_to_dict(c) for c in connections]

    async def create_connection(self, user_id: str, conn_data: Dict[str, Any]) -> Dict[str, Any]:
        encrypted_password = encryption_service.encrypt(conn_data.pop("db_password", ""))
        
        new_connection = DatabaseConnection(
            user_id=user_id,
            encrypted_db_password=encrypted_password,
            **conn_data
        )
        self.db_session.add(new_connection)
        await self.db_session.commit()
        await self.db_session.refresh(new_connection)
        return self._connection_to_dict(new_connection)

    async def update_connection(self, user_id: str, connection_id: str, conn_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        stmt = select(DatabaseConnection).where(
            DatabaseConnection.id == connection_id,
            DatabaseConnection.user_id == user_id
        )
        result = await self.db_session.execute(stmt)
        connection = result.scalars().first()

        if not connection:
            return None

        if "db_password" in conn_data:
            connection.encrypted_db_password = encryption_service.encrypt(conn_data.pop("db_password"))

        for key, value in conn_data.items():
            setattr(connection, key, value)

        await self.db_session.commit()
        await self.db_session.refresh(connection)
        return self._connection_to_dict(connection)

    async def delete_connection(self, user_id: str, connection_id: str) -> bool:
        stmt = select(DatabaseConnection).where(
            DatabaseConnection.id == connection_id,
            DatabaseConnection.user_id == user_id
        )
        result = await self.db_session.execute(stmt)
        connection = result.scalars().first()

        if not connection:
            return False

        await self.db_session.delete(connection)
        await self.db_session.commit()
        return True

    async def test_connection(self, user_id: str, connection_id: str) -> Dict[str, Any]:
        """Test database connection by attempting to connect."""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"🔍 연결 조회 시작: user_id={user_id}, connection_id={connection_id}")
        
        conn_data = await self.get_connection(user_id, connection_id)
        if not conn_data:
            logger.error(f"❌ 연결을 찾을 수 없음: connection_id={connection_id}")
            return {"success": False, "error": "Connection not found"}
        
        # 연결 정보 로깅 (비밀번호 제외)
        connection_info = f"{conn_data['connection_name']} ({conn_data['db_type']}://{conn_data['db_user']}@{conn_data['db_host']}:{conn_data['db_port']}/{conn_data['db_name']})"
        logger.info(f"🔍 연결 정보: {connection_info}")
        
        try:
            # Extract connection parameters
            db_password = conn_data.get("db_password", "")
            db_type = conn_data["db_type"].lower()
            
            logger.info(f"🔍 데이터베이스 타입: {db_type}")
            logger.info(f"🔍 비밀번호 존재 여부: {'있음' if db_password else '없음'}")
            
            if db_type == "postgresql":
                # PostgreSQL 연결 테스트
                dsn = f"postgresql://{conn_data['db_user']}:{db_password}@{conn_data['db_host']}:{conn_data['db_port']}/{conn_data['db_name']}"
                dsn_safe = f"postgresql://{conn_data['db_user']}:***@{conn_data['db_host']}:{conn_data['db_port']}/{conn_data['db_name']}"
                
                logger.info(f"🔗 PostgreSQL 연결 시도: {dsn_safe}")
                
                # 연결 테스트 (타임아웃 5초)
                logger.info("⏱️ 연결 대기 중... (최대 5초)")
                conn = await asyncio.wait_for(
                    asyncpg.connect(dsn), 
                    timeout=5.0
                )
                
                logger.info("✅ 연결 성공, 테스트 쿼리 실행 중...")
                # 간단한 쿼리 실행으로 연결 확인
                await conn.fetch("SELECT 1")
                await conn.close()
                
                print(f"✅ 분석 대상 데이터베이스 연결 성공: {connection_info}")
                return {"success": True, "message": "Connection successful"}
                
            elif db_type in ["mysql", "mariadb"]:
                # MySQL/MariaDB 연결 테스트 (향후 구현)
                print(f"⚠️ MySQL/MariaDB 연결 테스트는 향후 구현 예정: {connection_info}")
                return {"success": False, "error": "MySQL/MariaDB support is not yet implemented"}
                
            elif db_type in ["oracle", "oracledb"]:
                # Oracle 연결 테스트 (향후 구현)
                print(f"⚠️ Oracle 연결 테스트는 향후 구현 예정: {connection_info}")
                return {"success": False, "error": "Oracle support is not yet implemented"}
                
            elif db_type in ["sqlserver", "mssql"]:
                # MS SQL Server 연결 테스트
                try:
                    import pyodbc
                    
                    # MS SQL Server 연결 문자열 구성
                    connection_string = (
                        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                        f"SERVER={conn_data['db_host']},{conn_data['db_port']};"
                        f"DATABASE={conn_data['db_name']};"
                        f"UID={conn_data['db_user']};"
                        f"PWD={db_password};"
                        f"Encrypt=yes;"
                        f"TrustServerCertificate=yes;"
                        f"Connection Timeout=5"
                    )
                    
                    connection_string_safe = (
                        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                        f"SERVER={conn_data['db_host']},{conn_data['db_port']};"
                        f"DATABASE={conn_data['db_name']};"
                        f"UID={conn_data['db_user']};"
                        f"PWD=***;"
                        f"Encrypt=yes;TrustServerCertificate=yes"
                    )
                    
                    logger.info(f"🔗 MS SQL Server 연결 시도: {connection_string_safe}")
                    
                    # 동기 연결 테스트 (pyodbc는 비동기를 지원하지 않음)
                    conn = pyodbc.connect(connection_string)
                    cursor = conn.cursor()
                    cursor.execute("SELECT @@VERSION")
                    version_info = cursor.fetchone()[0]
                    cursor.close()
                    conn.close()
                    
                    print(f"✅ MS SQL Server 연결 성공: {connection_info}")
                    logger.info(f"✅ MS SQL Server 연결 성공: {connection_info}")
                    logger.info(f"📋 서버 버전: {version_info[:100]}...")
                    
                    return {"success": True, "message": "MS SQL Server connection successful", "version": version_info}
                    
                except ImportError:
                    error_msg = "pyodbc package is not installed. Please install it to use MS SQL Server connections."
                    print(f"❌ MS SQL Server 연결 실패: {error_msg}")
                    return {"success": False, "error": error_msg}
                except pyodbc.Error as e:
                    error_msg = f"MS SQL Server connection error: {str(e)}"
                    print(f"❌ MS SQL Server 연결 실패: {connection_info} - {error_msg}")
                    logger.error(f"MS SQL Server 연결 실패: {connection_info} - {error_msg}")
                    return {"success": False, "error": error_msg}
                except Exception as e:
                    error_msg = f"Unexpected error connecting to MS SQL Server: {str(e)}"
                    print(f"❌ MS SQL Server 연결 중 예상치 못한 오류: {connection_info} - {error_msg}")
                    logger.error(f"MS SQL Server 연결 오류: {connection_info} - {error_msg}")
                    return {"success": False, "error": error_msg}
                
            else:
                print(f"❌ 지원하지 않는 데이터베이스 타입: {connection_info}")
                return {"success": False, "error": f"Unsupported database type: {conn_data['db_type']}"}
                
        except asyncio.TimeoutError:
            print(f"⏰ 분석 대상 데이터베이스 연결 시간 초과: {connection_info}")
            return {"success": False, "error": "Connection timeout (5 seconds)"}
        except asyncpg.InvalidPasswordError:
            print(f"🔐 분석 대상 데이터베이스 비밀번호 오류: {connection_info}")
            return {"success": False, "error": "Invalid password"}
        except asyncpg.InvalidCatalogNameError:
            print(f"📂 분석 대상 데이터베이스 존재하지 않음: {connection_info}")
            return {"success": False, "error": "Database does not exist"}
        except asyncpg.CannotConnectNowError:
            print(f"🚫 분석 대상 데이터베이스 서버 연결 불가: {connection_info}")
            return {"success": False, "error": "Cannot connect to database server"}
        except Exception as e:
            print(f"💥 분석 대상 데이터베이스 연결 실패: {connection_info} - {str(e)}")
            return {"success": False, "error": f"Connection failed: {str(e)}"}

    def _connection_to_dict(self, connection: DatabaseConnection, decrypt: bool = False) -> Dict[str, Any]:
        data = {
            "id": connection.id,
            "user_id": connection.user_id,
            "connection_name": connection.connection_name,
            "db_type": connection.db_type,
            "db_host": connection.db_host,
            "db_port": connection.db_port,
            "db_user": connection.db_user,
            "db_name": connection.db_name,
            "created_at": connection.created_at.isoformat(),
            "updated_at": connection.updated_at.isoformat()
        }
        if decrypt and connection.encrypted_db_password:
            try:
                data['db_password'] = encryption_service.decrypt(connection.encrypted_db_password)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"❌ 비밀번호 복호화 실패: connection_id={connection.id}, error={str(e)}")
                # 복호화 실패 시 빈 비밀번호로 설정하여 연결 테스트에서 명확한 에러 발생
                data['db_password'] = ""
        return data 