import asyncio
import os
import sys
from passlib.context import CryptContext

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models import models
from database.connection_manager import DatabaseManager
from services.auth_service import AuthService
from core.config import get_settings

async def update_demo_password():
    """
    demo@example.com 사용자의 비밀번호를 demo1234로 업데이트합니다.
    """
    print("데이터베이스 연결 중...")
    
    # 설정 및 데이터베이스 매니저 초기화
    settings = get_settings()
    db_manager = DatabaseManager()
    
    if not hasattr(settings, 'app_database_url') or not settings.app_database_url:
        settings.app_database_url = os.environ.get("APP_DATABASE_URL", "sqlite:///../app_data.db")
    
    await db_manager.initialize()
    auth_service = AuthService(db_manager)
    
    try:
        # demo@example.com 사용자 찾기
        user_email = "demo@example.com"
        new_password = "demo1234"
        
        print(f"사용자 {user_email} 검색 중...")
        existing_user = await auth_service.get_user_by_email(user_email)
        
        if existing_user:
            print(f"사용자를 찾았습니다. ID: {existing_user['id']}")
            
            # 비밀번호 해시 생성
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            hashed_password = pwd_context.hash(new_password)
            
            # 데이터베이스에서 직접 비밀번호 업데이트
            async with db_manager.get_session("app") as session:
                # 사용자 찾기
                user_query = await session.execute(
                    models.User.__table__.select().where(
                        models.User.email == user_email
                    )
                )
                user_row = user_query.first()
                
                if user_row:
                    # 비밀번호 업데이트
                    await session.execute(
                        models.User.__table__.update().where(
                            models.User.id == user_row.id
                        ).values(
                            password_hash=hashed_password
                        )
                    )
                    await session.commit()
                    print(f"✅ 사용자 {user_email}의 비밀번호가 성공적으로 업데이트되었습니다.")
                else:
                    print(f"❌ 사용자 {user_email}를 데이터베이스에서 찾을 수 없습니다.")
        else:
            print(f"❌ 사용자 {user_email}가 존재하지 않습니다.")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db_manager.close_all_connections()
        print("데이터베이스 연결 종료.")

if __name__ == "__main__":
    asyncio.run(update_demo_password())
