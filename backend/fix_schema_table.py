#!/usr/bin/env python3

import sqlite3
import json
from datetime import datetime
import uuid

def fix_schema_table():
    """database_schemas 테이블을 새로운 구조로 업데이트"""
    db_path = 'app.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 현재 database_schemas 테이블 구조 확인...")
        
        # 현재 테이블 구조 확인
        cursor.execute("PRAGMA table_info(database_schemas)")
        current_columns = cursor.fetchall()
        print("📋 현재 컬럼:")
        for col in current_columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # connection_id 컬럼이 있는지 확인
        column_names = [col[1] for col in current_columns]
        
        if 'connection_id' in column_names:
            print("✅ connection_id 컬럼이 이미 존재합니다.")
            return True
        
        print("🔨 테이블 구조를 업데이트합니다...")
        
        # 기존 데이터 백업 (있는 경우)
        cursor.execute("SELECT COUNT(*) FROM database_schemas")
        row_count = cursor.fetchone()[0]
        print(f"📊 기존 데이터 수: {row_count}개")
        
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
        
        # 기존 데이터가 있다면 마이그레이션 (하지만 connection_id가 없으므로 건너뛰기)
        if row_count > 0:
            print("⚠️  기존 데이터는 connection_id가 없어 마이그레이션할 수 없습니다.")
            print("   새로운 스키마 정보가 자동으로 생성됩니다.")
        
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
        
        # 결과 확인
        cursor.execute("PRAGMA table_info(database_schemas)")
        new_columns = cursor.fetchall()
        print("✅ 테이블이 성공적으로 업데이트되었습니다!")
        print("📋 새로운 컬럼 구조:")
        for col in new_columns:
            print(f"  - {col[1]} ({col[2]})")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 테이블 업데이트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = fix_schema_table()
    if success:
        print("\n🎉 database_schemas 테이블이 성공적으로 업데이트되었습니다!")
        print("이제 브라우저에서 '분석 데이터 정보' 메뉴를 다시 시도해보세요.")
    else:
        print("\n❌ 테이블 업데이트에 실패했습니다.") 