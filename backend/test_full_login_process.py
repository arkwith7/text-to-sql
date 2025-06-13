import asyncio
import time
from database.connection_manager import DatabaseManager
from services.auth_service import AuthService, UserLogin
from services.analytics_service import AnalyticsService

async def test_full_login_process():
    print("🔍 전체 로그인 프로세스 테스트...")
    
    # 서비스 초기화
    db = DatabaseManager()
    await db.initialize()
    auth = AuthService(db)
    analytics = AnalyticsService(db)
    
    print("✅ 서비스 초기화 완료")
    
    # 1단계: 사용자 조회
    print("\n1️⃣ 사용자 조회 테스트...")
    start_time = time.time()
    user = await auth.get_user_by_email('demo@example.com')
    user_lookup_time = time.time() - start_time
    
    if user:
        print(f"   ✅ 사용자 찾음 ({user_lookup_time:.3f}초)")
        print(f"   📋 사용자: {user['email']} - {user['full_name']}")
    else:
        print("   ❌ 사용자를 찾을 수 없음")
        return
    
    # 2단계: 비밀번호 검증
    print("\n2️⃣ 비밀번호 검증 테스트...")
    start_time = time.time()
    password_valid = await auth.verify_password('demo1234', user['password_hash'])
    password_time = time.time() - start_time
    
    if password_valid:
        print(f"   ✅ 비밀번호 검증 성공 ({password_time:.3f}초)")
    else:
        print("   ❌ 비밀번호 검증 실패")
        return
    
    # 3단계: 전체 authenticate_user 테스트
    print("\n3️⃣ 전체 authenticate_user 테스트...")
    login_data = UserLogin(email='demo@example.com', password='demo1234')
    
    start_time = time.time()
    try:
        authenticated_user = await auth.authenticate_user(login_data, analytics)
        auth_time = time.time() - start_time
        print(f"   ✅ 사용자 인증 성공 ({auth_time:.3f}초)")
        print(f"   👤 인증된 사용자: {authenticated_user['email']}")
    except Exception as e:
        auth_time = time.time() - start_time
        print(f"   ❌ 사용자 인증 실패 ({auth_time:.3f}초): {str(e)}")
        return
    
    # 4단계: 토큰 생성 테스트
    print("\n4️⃣ 토큰 생성 테스트...")
    start_time = time.time()
    try:
        token_response = await auth.create_token(authenticated_user['id'])
        token_time = time.time() - start_time
        print(f"   ✅ 토큰 생성 성공 ({token_time:.3f}초)")
        print(f"   🎫 액세스 토큰 길이: {len(token_response.access_token)}")
        print(f"   🔄 리프레시 토큰 길이: {len(token_response.refresh_token)}")
    except Exception as e:
        token_time = time.time() - start_time
        print(f"   ❌ 토큰 생성 실패 ({token_time:.3f}초): {str(e)}")
        return
    
    total_time = user_lookup_time + password_time + auth_time + token_time
    print(f"\n⏱️ 총 소요 시간: {total_time:.3f}초")
    print("   - 사용자 조회: {:.3f}초".format(user_lookup_time))
    print("   - 비밀번호 검증: {:.3f}초".format(password_time))
    print("   - 사용자 인증: {:.3f}초".format(auth_time))
    print("   - 토큰 생성: {:.3f}초".format(token_time))
    
    await db.close_all_connections()
    print("\n🎉 전체 로그인 프로세스 테스트 완료!")

if __name__ == "__main__":
    asyncio.run(test_full_login_process()) 