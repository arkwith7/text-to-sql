import os
import asyncio
from services.auth_service import AuthService, UserRole, UserCreate
from services.analytics_service import AnalyticsService
from database import connection_manager as _conn_mod
from fastapi import HTTPException

# 현재 파일이 위치한 디렉토리(즉, DB가 있는 backend)에서만 실행되도록 강제
if os.getcwd() != os.path.dirname(os.path.abspath(__file__)):
    print("[오류] create_admin.py는 backend 디렉토리에서 실행해야 합니다.\n예시: cd backend && python3 create_admin.py")
    exit(1)

async def main():
    db_manager = _conn_mod.db_manager
    await db_manager.initialize()
    auth_service = AuthService(db_manager)
    analytics_service = AnalyticsService(db_manager)
    user_data = UserCreate(
        email='admin@example.com',
        password='admin1234!',
        full_name='관리자',
        company=None,
        role=UserRole.ADMIN
    )
    try:
        result = await auth_service.create_user(user_data, analytics_service)
        print('✅ 관리자 계정 생성 완료:', result.get('email', 'admin@example.com'))
    except HTTPException as e:
        if "already exists" in str(e.detail):
            print('✅ 관리자 계정이 이미 존재합니다: admin@example.com')
            print('   비밀번호: admin1234!')
        else:
            print('❌ 관리자 계정 생성 실패:', e.detail)
    except Exception as e:
        print('❌ 관리자 계정 생성 중 오류 발생:', str(e))

if __name__ == '__main__':
    asyncio.run(main())
