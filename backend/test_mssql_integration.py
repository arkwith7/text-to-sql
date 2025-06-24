#!/usr/bin/env python3
"""
MS SQL Server AdventureWorks 연결 테스트 스크립트
Text-to-SQL 백엔드에서 MS SQL Server 지원 확인
"""

import asyncio
import sys
import os

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.connection_manager import DatabaseManager
from services.connection_service import ConnectionService

async def test_mssql_backend_integration():
    """백엔드 코드를 통한 MS SQL Server 연결 테스트"""
    
    print("🔧 MS SQL Server 백엔드 통합 테스트 시작...")
    print("=" * 50)
    
    # 연결 정보
    connection_config = {
        "host": "localhost",
        "port": 1433,
        "database": "AdventureWorks", 
        "username": "sa",
        "password": "Adventure123!",
        "db_type": "mssql"
    }
    
    try:
        # 1. ConnectionService를 통한 연결 테스트
        print("\n1️⃣ ConnectionService 연결 테스트...")
        
        # DatabaseManager 인스턴스 생성
        db_manager = DatabaseManager()
        
        # 앱 데이터베이스 세션을 통한 ConnectionService 테스트
        async with db_manager.get_session('app') as session:
            connection_service = ConnectionService(session)
            
            # 연결 테스트 실행
            test_result = await connection_service.test_database_connection(connection_config)
            
            if test_result["success"]:
                print("✅ ConnectionService 연결 테스트 성공!")
                print(f"📋 메시지: {test_result['message']}")
                
                # 추가 정보 출력
                if "details" in test_result:
                    details = test_result["details"]
                    if "version" in details:
                        print(f"📋 서버 버전: {details['version'][:80]}...")
                    if "database_count" in details:
                        print(f"📂 데이터베이스 수: {details['database_count']}")
            else:
                print(f"❌ ConnectionService 연결 테스트 실패: {test_result['message']}")
                return
        
        # 2. 직접 SQLAlchemy 엔진으로 연결 테스트
        print("\n2️⃣ 직접 SQLAlchemy 엔진 연결 테스트...")
        
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text
        
        # MS SQL Server 연결 URL 생성 
        db_url = f"mssql+aioodbc://{connection_config['username']}:{connection_config['password']}@{connection_config['host']}:{connection_config['port']}/{connection_config['database']}?driver=ODBC+Driver+17+for+SQL+Server&Encrypt=yes&TrustServerCertificate=yes"
        
        engine = create_async_engine(db_url, pool_pre_ping=True)
        print(f"✅ 엔진 생성 성공: mssql+aioodbc://{connection_config['username']}@{connection_config['host']}:{connection_config['port']}/{connection_config['database']}")
        
        # 3. 스키마 정보 조회 테스트
        print("\n3️⃣ 스키마 정보 조회 테스트...")
        
        async with engine.connect() as conn:
            # 테이블 목록 조회
            result = await conn.execute(text("""
                SELECT 
                    TABLE_SCHEMA, 
                    TABLE_NAME,
                    TABLE_TYPE
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_TYPE = 'BASE TABLE'
                ORDER BY TABLE_SCHEMA, TABLE_NAME
            """))
            
            tables = result.fetchall()
            print(f"🗄️ 총 테이블 수: {len(tables)}")
            
            # 스키마별 테이블 수 집계
            schema_counts = {}
            for schema, table, table_type in tables:
                schema_counts[schema] = schema_counts.get(schema, 0) + 1
            
            print("📊 스키마별 테이블 수:")
            for schema, count in sorted(schema_counts.items()):
                print(f"   - {schema}: {count}개")
            
            # 주요 테이블 샘플 표시
            print("\n📋 주요 테이블 목록:")
            for schema, table, table_type in tables[:15]:
                print(f"   - {schema}.{table}")
            
            # 샘플 데이터 조회
            print("\n4️⃣ 샘플 데이터 조회 테스트...")
            
            # Person.Person 테이블에서 샘플 데이터
            result = await conn.execute(text("""
                SELECT TOP 5 
                    BusinessEntityID,
                    FirstName, 
                    LastName,
                    PersonType
                FROM Person.Person 
                ORDER BY BusinessEntityID
            """))
            
            persons = result.fetchall()
            print("👥 Person.Person 샘플 데이터:")
            for entity_id, first, last, person_type in persons:
                print(f"   - ID: {entity_id}, 이름: {first} {last}, 타입: {person_type}")
            
            # Sales.SalesOrderHeader 테이블에서 주문 정보
            result = await conn.execute(text("""
                SELECT TOP 5
                    SalesOrderID,
                    OrderDate,
                    CustomerID,
                    TotalDue
                FROM Sales.SalesOrderHeader
                ORDER BY SalesOrderID
            """))
            
            orders = result.fetchall()
            print("\n💰 Sales.SalesOrderHeader 샘플 데이터:")
            for order_id, order_date, customer_id, total in orders:
                print(f"   - 주문ID: {order_id}, 날짜: {order_date}, 고객ID: {customer_id}, 금액: ${total:.2f}")
            
            # Production.Product 테이블에서 제품 정보
            result = await conn.execute(text("""
                SELECT TOP 5
                    ProductID,
                    Name,
                    ProductNumber,
                    ListPrice
                FROM Production.Product
                WHERE ListPrice > 0
                ORDER BY ListPrice DESC
            """))
            
            products = result.fetchall()
            print("\n🛠️ Production.Product 샘플 데이터:")
            for product_id, name, product_number, price in products:
                print(f"   - ID: {product_id}, 제품: {name}, 번호: {product_number}, 가격: ${price:.2f}")
        
        await engine.dispose()
        
        print("\n" + "=" * 50)
        print("🎉 MS SQL Server 백엔드 통합 테스트 완료!")
        print("✅ Text-to-SQL 백엔드에서 MS SQL Server 사용 준비 완료")
        print("\n💡 다음 단계:")
        print("   1. 웹 앱에서 MS SQL Server 연결 추가")
        print("   2. Text-to-SQL 쿼리 생성 테스트")
        print("   3. AdventureWorks 샘플 데이터로 AI 응답 확인")
        
    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mssql_backend_integration())
