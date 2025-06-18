#!/usr/bin/env python3
"""
Test script for token usage API
"""

import requests
import json

def test_token_api():
    base_url = "http://localhost:8000"
    
    # Login first
    login_data = {
        "email": "demo@example.com",
        "password": "demo1234"
    }
    
    try:
        print("🔑 Logging in...")
        login_response = requests.post(
            f"{base_url}/api/v1/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        if login_response.status_code == 200:
            token_data = login_response.json()
            access_token = token_data["access_token"]
            print("✅ Login successful!")
            print(f"🔑 Token: {access_token[:50]}...")
            
            # Test token usage API
            print("\n📊 Testing token usage API...")
            headers = {
                "Authorization": f"Bearer {access_token}",
                "accept": "application/json"
            }
            
            usage_response = requests.get(
                f"{base_url}/api/v1/tokens/usage?include_details=true",
                headers=headers
            )
            
            print(f"📊 Token usage API status: {usage_response.status_code}")
            print(f"📊 Response: {usage_response.text}")
            
            if usage_response.status_code == 200:
                usage_data = usage_response.json()
                print("✅ Token usage API successful!")
                print(json.dumps(usage_data, indent=2))
            else:
                print("❌ Token usage API failed!")
                
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            print(f"❌ Response: {login_response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_token_api()
