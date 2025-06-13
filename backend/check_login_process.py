import asyncio
import time
from database.connection_manager import DatabaseManager
from services.auth_service import AuthService

async def test_login_process():
    """로그인 과정을 단계별로 테스트합니다."""
    print('🔍 === 로그인 과정 진단 ===')
    
    try:
        # 1. 데이터베이스 매니저 초기화
        print('1️⃣ 데이터베이스 매니저 초기화...')
        start_time = time.time()
        db = DatabaseManager()
        await db.initialize()
        print(f'   ✅ 완료 ({time.time() - start_time:.3f}초)')
        
        # 2. 인증 서비스 초기화
        print('2️⃣ 인증 서비스 초기화...')
        start_time = time.time()
        auth_service = AuthService(db)
        print(f'   ✅ 완료 ({time.time() - start_time:.3f}초)')
        
        # 3. 사용자 존재 확인
        print('3️⃣ 데모 사용자 존재 확인...')
        start_time = time.time()
        user_result = await db.execute_query('app', 
            'SELECT id, email, full_name, password_hash, is_active FROM users WHERE email = "demo@example.com"'
        )
        print(f'   ✅ 완료 ({time.time() - start_time:.3f}초)')
        
        if user_result.get('success') and user_result.get('data'):
            user = user_result['data'][0]
            print(f'   👤 사용자 정보: {user["email"]} ({user["full_name"]})')
            print(f'   🔐 패스워드 해시 존재: {"✅" if user["password_hash"] else "❌"}')
            print(f'   ✅ 활성 상태: {"✅" if user["is_active"] else "❌"}')
        else:
            print('   ❌ 사용자를 찾을 수 없음')
            return
        
        # 4. 패스워드 검증 테스트
        print('4️⃣ 패스워드 검증 테스트...')
        start_time = time.time()
        
        # 직접 패스워드 해시 검증
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        is_valid = pwd_context.verify("demo1234", user["password_hash"])
        print(f'   ✅ 패스워드 검증 완료 ({time.time() - start_time:.3f}초)')
        print(f'   🔐 패스워드 유효: {"✅" if is_valid else "❌"}')
        
        # 5. 인증 서비스를 통한 로그인 테스트
        print('5️⃣ 인증 서비스 로그인 테스트...')
        start_time = time.time()
        
        try:
            login_result = await auth_service.authenticate_user("demo@example.com", "demo1234")
            print(f'   ✅ 인증 서비스 완료 ({time.time() - start_time:.3f}초)')
            print(f'   🎯 로그인 결과: {"✅" if login_result else "❌"}')
        except Exception as auth_error:
            print(f'   ❌ 인증 서비스 에러 ({time.time() - start_time:.3f}초): {str(auth_error)}')
        
        # 6. 토큰 생성 테스트
        if 'login_result' in locals() and login_result:
            print('6️⃣ 토큰 생성 테스트...')
            start_time = time.time()
            try:
                token_data = await auth_service.create_access_token(user["id"])
                print(f'   ✅ 토큰 생성 완료 ({time.time() - start_time:.3f}초)')
                print(f'   🎫 토큰 길이: {len(token_data.get("access_token", "")) if token_data else 0}')
            except Exception as token_error:
                print(f'   ❌ 토큰 생성 에러 ({time.time() - start_time:.3f}초): {str(token_error)}')
        
        await db.close_all_connections()
        print('\n🎉 로그인 과정 진단 완료!')
        
    except Exception as e:
        print(f'❌ 진단 실패: {str(e)}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_login_process()) 