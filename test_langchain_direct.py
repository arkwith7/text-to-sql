#!/usr/bin/env python3
import sys
sys.path.append('/home/wjadmin/Dev/text-to-sql/backend')

from core.agents.langchain_agent import LangChainTextToSQLAgent
from database.connection_manager import DatabaseManager
import asyncio

async def test_langchain_agent():
    """LangChain Agent 직접 테스트"""
    print("🤖 LangChain Agent 직접 테스트 시작...")
    
    try:
        # Database Manager 초기화
        db_manager = DatabaseManager()
        await db_manager.initialize()
        
        # LangChain Agent 초기화
        agent = LangChainTextToSQLAgent(
            db_manager=db_manager,
            enable_simulation=False,
            verbose=True
        )
        
        print("✅ Agent 초기화 완료")
        print(f"🔧 Agent 정보: {agent.get_agent_info()}")
        
        # 테스트 질문
        question = "고객 수를 알려주세요"
        print(f"\n📝 질문: {question}")
        
        # Agent 실행
        result = await agent.execute_query(
            question=question,
            user_id="test_user",
            include_debug_info=True
        )
        
        print(f"\n📊 결과:")
        print(f"  - 성공: {result.get('success')}")
        print(f"  - 답변: {result.get('answer', 'N/A')}")
        print(f"  - 실행시간: {result.get('execution_time', 0):.3f}초")
        
        # 토큰 사용량 확인
        token_usage = result.get('token_usage')
        if token_usage:
            print(f"\n🎯 토큰 사용량:")
            print(f"  - 입력 토큰: {token_usage.get('prompt_tokens', 0)}")
            print(f"  - 출력 토큰: {token_usage.get('completion_tokens', 0)}")
            print(f"  - 총 토큰: {token_usage.get('total_tokens', 0)}")
        else:
            print(f"\n❌ 토큰 사용량 정보 없음")
            
        if not result.get('success'):
            print(f"\n❌ 오류: {result.get('error')}")
            
        return result
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = asyncio.run(test_langchain_agent())
    print(f"\n🏁 테스트 완료")
