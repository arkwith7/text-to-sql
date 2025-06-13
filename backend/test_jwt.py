#!/usr/bin/env python3
"""
JWT Authentication Test Script
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
import json
from services.auth_service import AuthService, UserCreate, UserLogin
from database.connection_manager import DatabaseManager
from services.analytics_service import AnalyticsService

async def test_jwt_auth():
    """Test JWT authentication system."""
    print("🔐 JWT Authentication Test Starting...")
    
    # Initialize services
    db_manager = DatabaseManager()
    await db_manager.initialize()
    
    auth_service = AuthService(db_manager)
    analytics_service = AnalyticsService(db_manager)
    
    try:
        # Test 1: User Registration
        print("\n📝 Test 1: User Registration")
        user_data = UserCreate(
            email="testuser@example.com",
            password="password123",
            full_name="Test User",
            company="Test Company"
        )
        
        user = await auth_service.create_user(user_data, analytics_service)
        print(f"✅ User created successfully: {user['email']}")
        
        # Test 2: Token Creation
        print("\n🔑 Test 2: Token Creation")
        token_response = await auth_service.create_token(user["id"])
        print(f"✅ Access token created: {token_response.access_token[:50]}...")
        print(f"✅ Refresh token created: {token_response.refresh_token[:50]}...")
        
        # Test 3: Token Verification
        print("\n🔍 Test 3: Token Verification")
        payload = auth_service.verify_token(token_response.access_token)
        print(f"✅ Token verified - User ID: {payload.get('sub')}")
        
        # Test 4: User Login
        print("\n🔐 Test 4: User Login")
        login_data = UserLogin(
            email="testuser@example.com",
            password="password123"
        )
        
        auth_user = await auth_service.authenticate_user(login_data, analytics_service)
        print(f"✅ User authenticated: {auth_user['email']}")
        
        # Test 5: Refresh Token
        print("\n🔄 Test 5: Refresh Token")
        new_token_response = await auth_service.refresh_access_token(token_response.refresh_token)
        print(f"✅ Token refreshed successfully")
        
        print("\n🎉 All JWT Authentication tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        await db_manager.close_all_connections()

if __name__ == "__main__":
    asyncio.run(test_jwt_auth())
