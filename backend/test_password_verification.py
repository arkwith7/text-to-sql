import asyncio
from database.connection_manager import DatabaseManager
from services.auth_service import AuthService

async def test_password_verification():
    print("🔐 비밀번호 검증 테스트...")
    
    db = DatabaseManager()
    await db.initialize()
    auth = AuthService(db)
    
    # 데모 사용자 정보 가져오기
    user = await auth.get_user_by_email('demo@example.com')
    if not user:
        print('❌ Demo 사용자를 찾을 수 없습니다')
        return
    
    print(f'📋 사용자 정보: {user["email"]} ({user["full_name"]})')
    
    # 비밀번호 검증 테스트
    test_passwords = ['demo1234', 'wrong_password', 'Demo1234', '']
    
    for password in test_passwords:
        try:
            result = await auth.verify_password(password, user["password_hash"])
            status = "✅ 성공" if result else "❌ 실패"
            print(f'   비밀번호 "{password}": {status}')
        except Exception as e:
            print(f'   비밀번호 "{password}": ❌ 오류 - {str(e)}')
    
    await db.close_all_connections()

if __name__ == "__main__":
    asyncio.run(test_password_verification()) 