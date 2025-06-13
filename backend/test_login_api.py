import asyncio
import aiohttp
import time
import json

async def test_login_performance():
    """수정된 로그인 API 성능을 테스트합니다."""
    print('🚀 === 로그인 API 성능 테스트 ===')
    
    # 로그인 데이터
    login_data = {
        "email": "demo@example.com",
        "password": "demo1234"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            # 1. 헬스 체크
            print('1️⃣ 헬스 체크...')
            start_time = time.time()
            async with session.get('http://localhost:8000/health') as response:
                health_time = time.time() - start_time
                print(f'   ✅ 헬스 체크 완료 ({health_time:.3f}초) - 상태: {response.status}')
            
            # 2. 로그인 API 테스트 (3회 반복)
            print('\n2️⃣ 로그인 API 테스트 (3회 반복)...')
            
            for i in range(3):
                print(f'   🔐 로그인 시도 #{i+1}')
                start_time = time.time()
                
                try:
                    async with session.post(
                        'http://localhost:8000/api/v1/auth/login',
                        json=login_data,
                        headers={'Content-Type': 'application/json'}
                    ) as response:
                        login_time = time.time() - start_time
                        
                        if response.status == 200:
                            result = await response.json()
                            print(f'   ✅ 로그인 성공 ({login_time:.3f}초)')
                            print(f'      👤 사용자: {result.get("user", {}).get("full_name", "Unknown")}')
                            print(f'      🎫 토큰 길이: {len(result.get("access_token", ""))}')
                        else:
                            error_text = await response.text()
                            print(f'   ❌ 로그인 실패 ({login_time:.3f}초) - 상태: {response.status}')
                            print(f'      오류: {error_text}')
                            
                except asyncio.TimeoutError:
                    print(f'   ⏰ 로그인 타임아웃 ({time.time() - start_time:.3f}초)')
                except Exception as e:
                    print(f'   💥 로그인 에러: {str(e)}')
                
                if i < 2:  # 마지막 요청이 아니면 잠시 대기
                    await asyncio.sleep(1)
            
            print('\n🎉 로그인 API 성능 테스트 완료!')
            
    except Exception as e:
        print(f'❌ 테스트 실패: {str(e)}')

if __name__ == "__main__":
    asyncio.run(test_login_performance()) 