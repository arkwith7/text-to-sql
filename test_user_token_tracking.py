#!/usr/bin/env python3
"""
사용자별 토큰 사용량 기록 테스트
"""

import requests
import json
import time

# 서버 URL
BASE_URL = "http://localhost:8000"

def test_token_usage_recording():
    """사용자별 토큰 사용량 기록 테스트"""
    
    print("🔐 1. 로그인 테스트...")
    
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
    user_info = login_result["user"]
    user_id = user_info["id"]
    
    print(f"✅ 로그인 성공!")
    print(f"   사용자 ID: {user_id}")
    print(f"   이름: {user_info['full_name']}")
    print(f"   기존 토큰 사용량: {user_info.get('token_usage', 0)}")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # 여러 쿼리 실행해서 토큰 사용량 누적 확인
    test_questions = [
        "고객 수를 알려주세요",
        "카테고리별 제품 수를 보여주세요", 
        "가장 비싼 제품 5개는?"
    ]
    
    total_tokens_used = 0
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n📊 {i}. 쿼리 테스트: '{question}'")
        
        query_data = {
            "question": question,
            "database": "northwind",
            "include_explanation": True,
            "max_rows": 10
        }
        
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/api/v1/query/", json=query_data, headers=headers)
        request_time = time.time() - start_time
        
        print(f"   ⏱️  응답 시간: {request_time:.3f}초")
        print(f"   📡 상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            success = result.get('success', False)
            print(f"   ✅ 성공: {success}")
            
            if success:
                print(f"   📋 SQL: {result.get('sql_query', 'N/A')}")
                print(f"   📈 결과 행 수: {result.get('row_count', 0)}")
                print(f"   ⏱️ 실행 시간: {result.get('execution_time', 0):.3f}초")
                
                # 토큰 사용량 확인
                token_usage = result.get('token_usage')
                if token_usage:
                    prompt_tokens = token_usage.get('prompt_tokens', 0)
                    completion_tokens = token_usage.get('completion_tokens', 0)
                    total_tokens = token_usage.get('total_tokens', 0)
                    
                    print(f"   🎯 토큰 사용량:")
                    print(f"      입력: {prompt_tokens}")
                    print(f"      출력: {completion_tokens}")
                    print(f"      총합: {total_tokens}")
                    
                    total_tokens_used += total_tokens
                else:
                    print(f"   ❌ 토큰 사용량 정보 없음")
            else:
                error_msg = result.get('error_message', 'Unknown error')
                print(f"   ❌ 오류: {error_msg}")
        else:
            print(f"   ❌ 요청 실패: {response.status_code}")
            print(f"   {response.text}")
    
    print(f"\n📊 총 토큰 사용량: {total_tokens_used}")
    
    # 최종 사용자 정보 다시 확인 (토큰 사용량 업데이트 확인)
    print(f"\n🔍 최종 사용자 정보 확인...")
    
    # 사용자 정보 재조회 (만약 그런 엔드포인트가 있다면)
    try:
        response = requests.get(f"{BASE_URL}/api/v1/auth/me", headers=headers)
        if response.status_code == 200:
            user_info_updated = response.json()
            print(f"   업데이트된 토큰 사용량: {user_info_updated.get('token_usage', 'N/A')}")
        else:
            print(f"   사용자 정보 재조회 실패: {response.status_code}")
    except Exception as e:
        print(f"   사용자 정보 재조회 중 오류: {e}")

if __name__ == "__main__":
    print("🧪 사용자별 토큰 사용량 기록 테스트 시작\n")
    test_token_usage_recording()
    print("\n🏁 테스트 완료")
