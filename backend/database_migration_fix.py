"""
Database migration fix for database_schemas table
"""

import sqlite3
import logging
from core.config import get_settings
from sqlalchemy.engine.url import make_url
import os

logger = logging.getLogger(__name__)

def fix_database_schemas_table():
    """database_schemas 테이블에 connection_id 컬럼이 없으면 테이블을 재생성"""
    try:
        settings = get_settings()
        db_url = settings.app_database_url
        db_path = make_url(db_url).database or 'app_data.db'
        db_path = os.path.abspath(db_path)
        logger.info(f"🔗 SQLite file in use → {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 테이블 존재 확인
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='database_schemas'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            logger.info("database_schemas 테이블이 존재하지 않습니다. 새로 생성합니다.")
            create_new_table(cursor)
            conn.commit()
            conn.close()
            return
        
        # 컬럼 구조 확인
        cursor.execute("PRAGMA table_info(database_schemas)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'connection_id' not in column_names:
            logger.info("database_schemas 테이블에 connection_id 컬럼이 없습니다. 테이블을 재생성합니다.")
            
            # 기존 데이터 수 확인
            cursor.execute("SELECT COUNT(*) FROM database_schemas")
            row_count = cursor.fetchone()[0]
            
            if row_count > 0:
                logger.warning(f"기존 데이터 {row_count}개가 있지만 connection_id가 없어 삭제됩니다.")
            
            # 기존 테이블 삭제
            cursor.execute("DROP TABLE database_schemas")
            
            # 새 테이블 생성
            create_new_table(cursor)
            
            # alembic_version 업데이트
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='alembic_version'")
            alembic_exists = cursor.fetchone()[0] > 0
            
            if alembic_exists:
                cursor.execute("UPDATE alembic_version SET version_num = '9f3e5a1b7c4d'")
            else:
                cursor.execute("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL PRIMARY KEY)")
                cursor.execute("INSERT INTO alembic_version (version_num) VALUES ('9f3e5a1b7c4d')")
            
            conn.commit()
            logger.info("database_schemas 테이블이 성공적으로 재생성되었습니다.")
        else:
            logger.info("database_schemas 테이블이 올바른 구조를 가지고 있습니다.")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"database_schemas 테이블 수정 중 오류 발생: {e}")

def create_new_table(cursor):
    """새로운 database_schemas 테이블 생성"""
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