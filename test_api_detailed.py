#!/usr/bin/env python3
"""
API 응답 상세 확인
"""

import requests
import json

# 서버 URL
BASE_URL = "http://localhost:8000"

def test_detailed_api_response():
    """API 응답을 자세히 확인"""
    
    print("🔐 로그인...")
    
    # 로그인
    login_data = {
        "email": "demo@example.com",
        "password": "demo1234"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
    
    if response.status_code != 200:
        print(f"❌ 로그인 실패: {response.status_code}")
        return
    
    login_result = response.json()
    access_token = login_result["access_token"]
    
    print(f"✅ 로그인 성공!")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # 간단한 쿼리 실행
    print(f"\n📊 쿼리 실행: '고객 수를 알려주세요'")
    
    query_data = {
        "question": "고객 수를 알려주세요",
        "database": "northwind",
        "include_explanation": True,
        "max_rows": 10
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/query/", json=query_data, headers=headers)
    
    print(f"📡 상태 코드: {response.status_code}")
    print(f"📡 응답 헤더: {dict(response.headers)}")
    
    if response.status_code == 200:
        result = response.json()
        
        print(f"\n📋 전체 응답 구조:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # 각 필드 확인
        print(f"\n🔍 필드별 분석:")
        for key, value in result.items():
            if isinstance(value, str) and len(value) > 100:
                print(f"  {key}: {type(value).__name__} (길이: {len(value)}) - {str(value)[:100]}...")
            else:
                print(f"  {key}: {type(value).__name__} = {value}")
                
    else:
        print(f"❌ 요청 실패")
        print(f"응답 내용: {response.text}")

if __name__ == "__main__":
    test_detailed_api_response()
