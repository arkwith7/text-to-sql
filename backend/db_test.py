import asyncio
import sys
import os

from database.connection_manager import DatabaseManager
from core.config import get_settings

async def test_database_connection():
    """현재 데이터베이스 연결을 테스트합니다."""
    print("🔍 === 데이터베이스 연결 테스트 ===")
    
    try:
        settings = get_settings()
        print(f"📁 설정된 DB URL: {settings.app_database_url}")
        print(f"💻 현재 작업 디렉토리: {os.getcwd()}")
        
        # 데이터베이스 파일 확인
        db_file = "./app_data.db"
        if os.path.exists(db_file):
            file_size = os.path.getsize(db_file)
            print(f"✅ DB 파일 존재: {db_file} ({file_size} bytes)")
        else:
            print(f"❌ DB 파일 없음: {db_file}")
        
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
            
            # 사용자 테이블 확인
            if 'users' in tables:
                user_result = await db.execute_query('app', 'SELECT COUNT(*) as count FROM users')
                if user_result.get('success'):
                    user_count = user_result['data'][0]['count']
                    print(f"👥 등록된 사용자 수: {user_count}")
                    
            # 채팅 세션 테이블 확인
            if 'chat_sessions' in tables:
                session_result = await db.execute_query('app', 'SELECT COUNT(*) as count FROM chat_sessions')
                if session_result.get('success'):
                    session_count = session_result['data'][0]['count']
                    print(f"💬 채팅 세션 수: {session_count}")
        else:
            print(f"❌ 앱 데이터베이스 쿼리 실패: {result.get('error')}")
            
        # 연결 테스트 완료
        await db.close_all_connections()
        print("🎉 데이터베이스 연결 테스트 완료!")
        
    except Exception as e:
        print(f"❌ 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_database_connection()) 