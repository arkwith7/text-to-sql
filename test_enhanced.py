import requests
import json

# Enhanced Agent 상세 테스트
print("🚀 === Enhanced Chat 엔드포인트 상세 테스트 ===")
print()

response = requests.get(
    'http://localhost:8000/api/v1/chat/test/agents',
    params={
        'question': '카테고리별 제품 수를 자세히 보여주세요',
        'agent_type': 'enhanced'
    }
)

result = response.json()

print("✅ Enhanced Agent 결과:")
print(f"   성공: {result.get('success')}")
print(f"   실행 시간: {result.get('execution_time'):.4f}초")
print()
print(f"🔍 생성된 SQL 쿼리:")
print(f"   {result['result']['sql_query']}")
print()
print(f"📊 결과 데이터:")
for i, item in enumerate(result['result']['results'], 1):
    print(f"   {i}. {item}")
print()
print(f"📝 설명: {result['result'].get('explanation', 'N/A')}")
print(f"🗂️ 데이터베이스: {result['result'].get('database', 'N/A')}")
print(f"📈 총 행 수: {result['result'].get('row_count', 0)}")

# 추가 테스트: 다양한 질문들
print("\n" + "="*60)
print("🧪 === 다양한 질문 테스트 ===")

test_questions = [
    "직원별 판매 실적을 보여주세요",
    "국가별 고객 수를 알려주세요",
    "가장 비싼 제품 3개는 무엇인가요?",
    "최근 주문 현황을 보여주세요"
]

for i, question in enumerate(test_questions, 1):
    print(f"\n🔹 테스트 {i}: {question}")
    try:
        response = requests.get(
            'http://localhost:8000/api/v1/chat/test/agents',
            params={'question': question, 'agent_type': 'enhanced'},
            timeout=5
        )
        result = response.json()
        success = result.get('success', False)
        exec_time = result.get('execution_time', 0)
        row_count = len(result.get('result', {}).get('results', []))
        
        print(f"   결과: {'✅ 성공' if success else '❌ 실패'}")
        print(f"   시간: {exec_time:.4f}초")
        print(f"   데이터: {row_count}행")
        
        if success and row_count > 0:
            first_result = result['result']['results'][0]
            print(f"   예시: {first_result}")
            
    except Exception as e:
        print(f"   ❌ 오류: {str(e)}")

print("\n🎉 테스트 완료!") 