import asyncio
import os
import sys
from uuid import uuid4

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import models and services using current package structure
from models import models  # SQLAlchemy models
from database.connection_manager import DatabaseManager  # Database manager
from services.auth_service import AuthService, UserRole, UserCreate  # Authentication service with user types
from services.analytics_service import AnalyticsService  # Analytics service
from core.config import get_settings  # Configuration settings

# Import types for async operations
from typing import Optional

async def create_users():
    """
    Connects to the database and creates a regular user and an admin user.
    """
    print("Initializing database manager...")
    # Get settings and initialize database manager
    settings = get_settings()
    db_manager = DatabaseManager()
    
    # Set database URL if not already configured
    if not hasattr(settings, 'app_database_url') or not settings.app_database_url:
        settings.app_database_url = os.environ.get("APP_DATABASE_URL", "sqlite:///../app_data.db")
    
    await db_manager.initialize()
    auth_service = AuthService(db_manager)
    analytics_service = AnalyticsService(db_manager)

    # --- Create regular user ---
    user_data = UserCreate(
        email="user99@example.com",
        password="password",
        full_name="User NinetyNine",
        company="Example Inc.",
        role=UserRole.ANALYST
    )
    print(f"Creating user: {user_data.email}...")
    try:
        existing_user = await auth_service.get_user_by_email(user_data.email)
        if existing_user:
            print(f"User {user_data.email} already exists.")
        else:
            new_user = await auth_service.create_user(user_data, analytics_service=analytics_service)
            print(f"Successfully created user with ID: {new_user['id']}")
    except Exception as e:
        print(f"Error creating user {user_data.email}: {e}")
        import traceback
        traceback.print_exc()

    # --- Create regular user ---
    user_data = UserCreate(
        email="demo@example.com",
        password="demo1234",
        full_name="홍길삼",
        company="Example Inc.",
        role=UserRole.ANALYST
    )
    print(f"Creating user: {user_data.email}...")
    try:
        existing_user = await auth_service.get_user_by_email(user_data.email)
        if existing_user:
            print(f"User {user_data.email} already exists.")
        else:
            new_user = await auth_service.create_user(user_data, analytics_service=analytics_service)
            print(f"Successfully created user with ID: {new_user['id']}")
    except Exception as e:
        print(f"Error creating user {user_data.email}: {e}")
        import traceback
        traceback.print_exc()

    # --- Create admin user ---
    admin_data = UserCreate(
        email="admin@example.com",
        password="adminpassword",
        full_name="Admin User",
        company="Admin Corp.",
        role=UserRole.ADMIN
    )
    print(f"Creating admin: {admin_data.email}...")
    try:
        existing_admin = await auth_service.get_user_by_email(admin_data.email)
        if existing_admin:
            print(f"Admin user {admin_data.email} already exists.")
        else:
            new_admin = await auth_service.create_user(admin_data, analytics_service=analytics_service)
            print(f"Successfully created admin user with ID: {new_admin['id']}")
    except Exception as e:
        print(f"Error creating admin {admin_data.email}: {e}")
        import traceback
        traceback.print_exc()

    await db_manager.close_all_connections()
    print("Database connections closed.")


if __name__ == "__main__":
    # The user wanted usernames 'user99' and 'admin', but the system uses email for login.
    # I've used 'user99@example.com' and 'admin@example.com' as their emails.
    # The password requirements (min_length=8) are met.
    
    # We need to set the environment variables that the app would normally get from a .env file
    # For the script, we can set them manually if they aren't already set.
    if 'JWT_SECRET_KEY' not in os.environ:
        print("Setting a temporary JWT_SECRET_KEY for this script.")
        os.environ['JWT_SECRET_KEY'] = 'a-secure-secret-key-for-scripting-only'

    # The user request mentioned usernames, but the model uses email.
    # user: user99, password
    # admin: admin, adminpassword
    # The UserCreate model requires an email address. I will use user99@example.com and admin@example.com
    # The passwords meet the min_length=8 requirement.
    
    # Also, the username in the prompt for admin is 'admin' and password is 'adminpassword'
    # The UserCreate model has a password validator with min_length=8. 'admin' is too short.
    # The prompt says 'admin' and 'adminpassword', so 'adminpassword' is fine.
    
    # I will use 'user99@example.com' and 'admin@example.com' as emails.
    # Passwords 'password' and 'adminpassword' are both >= 8 chars.
    
    asyncio.run(create_users()) 