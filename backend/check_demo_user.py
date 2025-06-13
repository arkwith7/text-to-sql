import asyncio
from database.connection_manager import DatabaseManager
from services.auth_service import AuthService

async def check_demo_user():
    print("🔍 데모 사용자 확인 중...")
    
    db = DatabaseManager()
    await db.initialize()
    auth = AuthService(db)
    
    user = await auth.get_user_by_email('demo@example.com')
    if user:
        print(f'✅ Demo 사용자 존재:')
        print(f'   ID: {user["id"]}')
        print(f'   이메일: {user["email"]}')
        print(f'   이름: {user["full_name"]}')
        print(f'   활성화: {user["is_active"]}')
        print(f'   역할: {user["role"]}')
        print(f'   비밀번호 해시: {user["password_hash"][:20]}...')
    else:
        print('❌ Demo 사용자가 존재하지 않습니다')
    
    await db.close_all_connections()

if __name__ == "__main__":
    asyncio.run(check_demo_user()) 