#!/usr/bin/env python3
"""
API 테스트 스크립트 - 토큰 사용량 추적 확인
"""

import requests
import json
import time

# 서버 URL
BASE_URL = "http://localhost:8000"

def test_api():
    """API 테스트"""
    
    # 1. 로그인
    print("🔐 로그인 중...")
    login_data = {
        "email": "demo@example.com",
        "password": "demo1234"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
    
    if response.status_code != 200:
        print(f"❌ 로그인 실패: {response.status_code}")
        print(response.text)
        return
    
    login_result = response.json()
    access_token = login_result["access_token"]
    print(f"✅ 로그인 성공! 토큰: {access_token[:50]}...")
    
    # 2. 쿼리 테스트
    print("\n📊 쿼리 테스트 중...")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    query_data = {
        "question": "고객 수를 알려주세요",
        "database": "northwind",
        "include_explanation": True,
        "max_rows": 100
    }
    
    start_time = time.time()
    response = requests.post(f"{BASE_URL}/api/v1/query/", json=query_data, headers=headers)
    request_time = time.time() - start_time
    
    print(f"⏱️  응답 시간: {request_time:.3f}초")
    print(f"📡 상태 코드: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("\n✅ 쿼리 성공!")
        print(f"  - 질문: {result.get('question')}")
        print(f"  - SQL: {result.get('sql_query', 'N/A')}")
        print(f"  - 결과 행 수: {result.get('row_count', 0)}")
        print(f"  - 실행 시간: {result.get('execution_time', 0):.3f}초")
        print(f"  - 성공 여부: {result.get('success', False)}")
        
        # 토큰 사용량 확인
        token_usage = result.get('token_usage')
        if token_usage:
            print(f"\n🎯 토큰 사용량:")
            print(f"  - 입력 토큰: {token_usage.get('prompt_tokens', 0)}")
            print(f"  - 출력 토큰: {token_usage.get('completion_tokens', 0)}")
            print(f"  - 총 토큰: {token_usage.get('total_tokens', 0)}")
        else:
            print(f"\n❌ 토큰 사용량 정보 없음")
        
        # 결과 일부 출력
        results = result.get('results', [])
        if results:
            print(f"\n📋 결과 미리보기:")
            for i, row in enumerate(results[:3]):
                print(f"  {i+1}: {row}")
            if len(results) > 3:
                print(f"  ... ({len(results)-3}개 더)")
        
        # 오류 메시지 확인
        if not result.get('success', True):
            error_msg = result.get('error_message', 'Unknown error')
            print(f"\n❌ 오류: {error_msg}")
            
    else:
        print(f"❌ 쿼리 실패: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_api()
