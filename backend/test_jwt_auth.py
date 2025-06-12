#!/usr/bin/env python3
"""
JWT Authentication Test Script
"""
import asyncio
import aiohttp
import json
import sys
from typing import Dict, Any

BASE_URL = "http://localhost:8000/api/v1"

class APIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.access_token = None
        self.refresh_token = None
    
    async def register_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new user."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/auth/register", 
                json=user_data
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.access_token = data["access_token"]
                    self.refresh_token = data["refresh_token"]
                    return data
                else:
                    text = await response.text()
                    raise Exception(f"Registration failed: {response.status} - {text}")
    
    async def login_user(self, login_data: Dict[str, str]) -> Dict[str, Any]:
        """Login user."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/auth/login", 
                json=login_data
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.access_token = data["access_token"]
                    self.refresh_token = data["refresh_token"]
                    return data
                else:
                    text = await response.text()
                    raise Exception(f"Login failed: {response.status} - {text}")
    
    async def get_current_user(self) -> Dict[str, Any]:
        """Get current user info."""
        headers = {"Authorization": f"Bearer {self.access_token}"}
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/auth/me", 
                headers=headers
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    text = await response.text()
                    raise Exception(f"Get user failed: {response.status} - {text}")
    
    async def test_protected_endpoint(self) -> Dict[str, Any]:
        """Test a protected endpoint."""
        headers = {"Authorization": f"Bearer {self.access_token}"}
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/schema", 
                headers=headers
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    text = await response.text()
                    raise Exception(f"Protected endpoint failed: {response.status} - {text}")
    
    async def test_without_token(self) -> bool:
        """Test accessing protected endpoint without token."""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/schema") as response:
                return response.status == 401


async def main():
    """Main test function."""
    client = APIClient(BASE_URL)
    
    print("🔐 JWT Authentication Test")
    print("=" * 50)
    
    # Test user data
    test_user = {
        "email": "test2@example.com",
        "password": "testpassword123",
        "full_name": "Test User 2",
        "company": "Test Company 2",
        "role": "analyst"
    }
    
    try:
        print("1. Testing user registration...")
        registration_result = await client.register_user(test_user)
        print(f"✅ Registration successful! User ID: {registration_result['user']['id']}")
        print(f"   Access Token: {client.access_token[:20]}...")
        
        print("\n2. Testing get current user...")
        user_info = await client.get_current_user()
        print(f"✅ Current user: {user_info['email']} ({user_info['role']})")
        
        print("\n3. Testing protected endpoint access...")
        schema_data = await client.test_protected_endpoint()
        print(f"✅ Protected endpoint accessible! Found {len(schema_data.get('tables', []))} tables")
        
        print("\n4. Testing access without token...")
        unauthorized = await client.test_without_token()
        if unauthorized:
            print("✅ Unauthorized access properly blocked!")
        else:
            print("❌ Unauthorized access not blocked!")
        
        print("\n5. Testing login with same user...")
        login_data = {
            "email": test_user["email"],
            "password": test_user["password"]
        }
        login_result = await client.login_user(login_data)
        print(f"✅ Login successful! New token: {client.access_token[:20]}...")
        
        print("\n🎉 All JWT authentication tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
