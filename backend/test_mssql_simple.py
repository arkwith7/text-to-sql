#!/usr/bin/env python3
"""
MS SQL Server 간단한 연결 테스트 - ConnectionService 없이
"""

import asyncio
import sys
import os

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_mssql_simple():
    """MS SQL Server 직접 연결 테스트"""
    
    print("🔧 MS SQL Server 간단 연결 테스트 시작...")
    print("=" * 50)
    
    try:
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text
        
        # 연결 정보
        host = "localhost"
        port = 1433
        database = "AdventureWorks"
        username = "sa"
        password = "Adventure123!"
        
        # MS SQL Server 연결 URL 생성 
        db_url = f"mssql+aioodbc://{username}:{password}@{host}:{port}/{database}?driver=ODBC+Driver+17+for+SQL+Server&Encrypt=yes&TrustServerCertificate=yes"
        
        print("1️⃣ SQLAlchemy 엔진 생성...")
        engine = create_async_engine(db_url, pool_pre_ping=True)
        print(f"✅ 엔진 생성 성공")
        
        print("\n2️⃣ 데이터베이스 연결 및 기본 정보 조회...")
        async with engine.connect() as conn:
            # 서버 버전 확인
            result = await conn.execute(text("SELECT @@VERSION"))
            version = result.fetchone()[0]
            print(f"✅ 서버 버전: {version[:80]}...")
            
            # 현재 데이터베이스 확인
            result = await conn.execute(text("SELECT DB_NAME()"))
            current_db = result.fetchone()[0]
            print(f"✅ 현재 데이터베이스: {current_db}")
            
            # 테이블 수 확인
            result = await conn.execute(text("""
                SELECT COUNT(*) as table_count
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_TYPE = 'BASE TABLE'
            """))
            table_count = result.fetchone()[0]
            print(f"✅ 테이블 수: {table_count}개")
        
        print("\n3️⃣ 스키마 정보 조회...")
        async with engine.connect() as conn:
            # 스키마별 테이블 수
            result = await conn.execute(text("""
                SELECT 
                    TABLE_SCHEMA,
                    COUNT(*) as table_count
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_TYPE = 'BASE TABLE'
                GROUP BY TABLE_SCHEMA
                ORDER BY table_count DESC
            """))
            
            schemas = result.fetchall()
            print("📊 스키마별 테이블 수:")
            for schema, count in schemas:
                print(f"   - {schema}: {count}개")
        
        print("\n4️⃣ 샘플 데이터 조회...")
        async with engine.connect() as conn:
            # Person.Person 테이블 샘플
            result = await conn.execute(text("""
                SELECT TOP 3
                    BusinessEntityID,
                    FirstName, 
                    LastName,
                    PersonType
                FROM Person.Person 
                ORDER BY BusinessEntityID
            """))
            
            persons = result.fetchall()
            print("👥 Person.Person 샘플:")
            for entity_id, first, last, person_type in persons:
                print(f"   - ID: {entity_id}, 이름: {first} {last}, 타입: {person_type}")
            
            # Sales.SalesOrderHeader 샘플
            result = await conn.execute(text("""
                SELECT TOP 3
                    SalesOrderID,
                    CAST(OrderDate as DATE) as OrderDate,
                    CustomerID,
                    CAST(TotalDue as DECIMAL(10,2)) as TotalDue
                FROM Sales.SalesOrderHeader
                ORDER BY SalesOrderID
            """))
            
            orders = result.fetchall()
            print("\n💰 Sales.SalesOrderHeader 샘플:")
            for order_id, order_date, customer_id, total in orders:
                print(f"   - 주문ID: {order_id}, 날짜: {order_date}, 고객ID: {customer_id}, 금액: ${total}")
            
            # Production.Product 샘플  
            result = await conn.execute(text("""
                SELECT TOP 3
                    ProductID,
                    Name,
                    ProductNumber,
                    CAST(ListPrice as DECIMAL(10,2)) as ListPrice
                FROM Production.Product
                WHERE ListPrice > 0
                ORDER BY ListPrice DESC
            """))
            
            products = result.fetchall()
            print("\n🛠️ Production.Product 샘플:")
            for product_id, name, product_number, price in products:
                print(f"   - ID: {product_id}, 제품: {name}, 번호: {product_number}, 가격: ${price}")
        
        print("\n5️⃣ Text-to-SQL 에서 자주 사용할 쿼리 패턴 테스트...")
        async with engine.connect() as conn:
            # 조인 쿼리 예시
            result = await conn.execute(text("""
                SELECT TOP 5
                    p.FirstName + ' ' + p.LastName AS CustomerName,
                    COUNT(soh.SalesOrderID) AS OrderCount,
                    CAST(SUM(soh.TotalDue) as DECIMAL(12,2)) AS TotalAmount
                FROM Sales.SalesOrderHeader soh
                INNER JOIN Sales.Customer c ON soh.CustomerID = c.CustomerID
                INNER JOIN Person.Person p ON c.PersonID = p.BusinessEntityID
                GROUP BY p.FirstName, p.LastName
                ORDER BY TotalAmount DESC
            """))
            
            customer_orders = result.fetchall()
            print("📈 고객별 주문 집계 (TOP 5):")
            for customer_name, order_count, total_amount in customer_orders:
                print(f"   - {customer_name}: {order_count}건, ${total_amount}")
        
        await engine.dispose()
        
        print("\n" + "=" * 50)
        print("🎉 MS SQL Server 연결 테스트 완료!")
        print("✅ Text-to-SQL 백엔드에서 MS SQL Server 사용 가능")
        print("\n💡 주요 확인 사항:")
        print("   ✅ SQLAlchemy + aioodbc 연결 성공")
        print("   ✅ 비동기 쿼리 실행 가능")
        print("   ✅ AdventureWorks 스키마 접근 가능")
        print("   ✅ 복잡한 조인 쿼리 실행 가능")
        print("   ✅ Text-to-SQL AI 연동 준비 완료")
        
    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mssql_simple())
