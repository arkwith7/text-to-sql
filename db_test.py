import asyncio
import sys
sys.path.append('.')

from database.connection_manager import DatabaseManager

async def test_database_connection():
    """현재 데이터베이스 연결을 테스트합니다."""
    print("🔍 === 데이터베이스 연결 테스트 ===")
    
    try:
        db = DatabaseManager()
        await db.initialize()
        print("✅ 데이터베이스 매니저 초기화 완료")
        
        # 앱 데이터베이스 테스트
        result = await db.execute_query('app', 'SELECT name FROM sqlite_master WHERE type="table"')
        
        if result.get('success'):
            tables = [row['name'] for row in result.get('data', [])]
            print(f"✅ 앱 데이터베이스 연결 성공")
            print(f"📋 테이블 목록: {tables}")
            print(f"📊 총 테이블 수: {len(tables)}")
        else:
            print(f"❌ 앱 데이터베이스 쿼리 실패: {result.get('error')}")
            
        # 연결된 데이터베이스 파일 확인
        from core.config import get_settings
        settings = get_settings()
        db_path = settings.app_database_url.replace('sqlite:///', '')
        
        import os
        if os.path.exists(db_path):
            file_size = os.path.getsize(db_path)
            print(f"📁 사용 중인 DB 파일: {db_path}")
            print(f"💾 파일 크기: {file_size} bytes")
        else:
            print(f"❌ DB 파일이 존재하지 않음: {db_path}")
            
        # 연결 테스트 완료
        await db.close_all_connections()
        print("🎉 테스트 완료!")
        
    except Exception as e:
        print(f"❌ 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_database_connection()) 