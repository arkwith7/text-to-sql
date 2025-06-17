#!/usr/bin/env python3
"""
노트북 개선사항이 백엔드에 반영되었는지 테스트하는 스크립트
"""

import sys
import asyncio
import time
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from database.connection_manager import DatabaseManager
from core.agents.sql_agent import SQLAgent

async def test_enhanced_features():
    """노트북의 개선사항들이 백엔드에 잘 반영되었는지 테스트"""
    print("🧪 === 노트북 개선사항 반영 테스트 ===")
    print()
    
    # 1. Enhanced DatabaseManager 테스트
    print("1️⃣ Enhanced DatabaseManager 성능 모니터링 테스트")
    db_manager = DatabaseManager()
    await db_manager.initialize()
    
    # 초기 성능 통계 확인
    initial_stats = db_manager.get_performance_stats()
    print(f"   📊 초기 성능 통계: {initial_stats}")
    
    # 몇 개의 테스트 쿼리 실행
    test_queries = [
        "SELECT 'test1' as message",
        "SELECT 'test2' as message",
        "SELECT 'test3' as message"
    ]
    
    for i, query in enumerate(test_queries, 1):
        try:
            result = await db_manager.execute_query('app', query)
            print(f"   ✅ 테스트 쿼리 {i}: 성공 (실행시간: {result.get('execution_time', 0):.3f}초)")
        except Exception as e:
            print(f"   ❌ 테스트 쿼리 {i}: 실패 - {str(e)}")
    
    # 최종 성능 통계 확인
    final_stats = db_manager.get_performance_stats()
    print(f"   📊 최종 성능 통계: {final_stats}")
    
    # 쿼리 로그 확인
    query_log = db_manager.get_query_log(3)
    print(f"   📋 최근 쿼리 로그: {len(query_log)}개 항목")
    
    print()
    
    # 2. Enhanced SQL Agent 테스트
    print("2️⃣ Enhanced SQL Agent 기능 테스트")
    sql_agent = SQLAgent(db_manager)
    
    # 초기 생성 통계 확인
    initial_gen_stats = sql_agent.get_generation_stats()
    print(f"   📊 초기 SQL 생성 통계: {initial_gen_stats}")
    
    # 노트북에서 테스트된 질문들
    test_questions = [
        "고객 수를 알려주세요",
        "제품 수는 몇 개인가요?",
        "카테고리별 제품 수",
        "인기 제품이 뭐야?",
        "카테고리별 매출을 보여주세요"
    ]
    
    print("   🎯 테스트 질문들:")
    for i, question in enumerate(test_questions, 1):
        try:
            result = sql_agent.execute_query_sync(
                question, 
                include_metadata=True,
                include_explanation=True
            )
            
            if result['success']:
                metadata = result.get('metadata', {})
                print(f"      {i}. '{question}'")
                print(f"         ✅ 성공 (방법: {metadata.get('method', 'unknown')}, "
                      f"복잡도: {metadata.get('complexity', 'unknown')}, "
                      f"실행시간: {result.get('execution_time', 0):.3f}초)")
                print(f"         📊 결과: {result.get('row_count', 0)}개 행")
            else:
                print(f"      {i}. '{question}' ❌ 실패: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"      {i}. '{question}' 💥 에러: {str(e)}")
    
    # 최종 생성 통계 확인
    final_gen_stats = sql_agent.get_generation_stats()
    print(f"   📊 최종 SQL 생성 통계: {final_gen_stats}")
    
    # 지원되는 패턴 확인
    supported_patterns = sql_agent.get_supported_patterns()
    print(f"   🎯 지원되는 패턴 수: {len(supported_patterns)}개")
    
    print()
    
    # 3. 종합 평가
    print("3️⃣ 종합 평가")
    
    # 성능 개선 확인
    if final_stats['total_queries'] > initial_stats['total_queries']:
        print("   ✅ 데이터베이스 성능 모니터링: 작동")
        print(f"      💾 실행된 쿼리: {final_stats['total_queries'] - initial_stats['total_queries']}개")
        print(f"      ⚡ 평균 실행시간: {final_stats.get('avg_query_time', 0):.3f}초")
    else:
        print("   ❌ 데이터베이스 성능 모니터링: 미작동")
    
    # SQL 생성 개선 확인
    if final_gen_stats['total_requests'] > 0:
        print("   ✅ SQL 생성 통계 추적: 작동")
        print(f"      🎯 패턴 매칭 성공률: {final_gen_stats.get('pattern_match_rate', 0):.1f}%")
        print(f"      📝 총 요청 처리: {final_gen_stats['total_requests']}개")
    else:
        print("   ❌ SQL 생성 통계 추적: 미작동")
    
    # 노트북 핵심 기능 체크
    notebook_features = [
        ("성능 통계 수집", hasattr(db_manager, 'get_performance_stats')),
        ("쿼리 로그 관리", hasattr(db_manager, 'get_query_log')),
        ("SQL 생성 통계", hasattr(sql_agent, 'get_generation_stats')),
        ("메타데이터 지원", 'metadata' in str(result.keys()) if 'result' in locals() else False),
        ("복잡한 쿼리 패턴", len([p for p in sql_agent.query_patterns.keys() if 'JOIN' in sql_agent.query_patterns[p] or 'GROUP BY' in sql_agent.query_patterns[p]]) > 0),
        ("실제 데이터 수치", any('91' in str(result.get('results', [])) for result in [sql_agent.execute_query_sync("고객 수")] if result['success']))
    ]
    
    print("   📋 노트북 핵심 기능 체크:")
    for feature_name, is_implemented in notebook_features:
        status = "✅" if is_implemented else "❌"
        print(f"      {status} {feature_name}")
    
    # 성공률 계산
    success_count = sum(1 for _, implemented in notebook_features if implemented)
    success_rate = (success_count / len(notebook_features)) * 100
    
    print(f"\n🎉 === 최종 결과 ===")
    print(f"   📊 구현 성공률: {success_rate:.1f}% ({success_count}/{len(notebook_features)})")
    
    if success_rate >= 80:
        print("   🎯 노트북 개선사항이 백엔드에 잘 반영되었습니다!")
    elif success_rate >= 60:
        print("   ⚠️ 대부분의 개선사항이 반영되었지만 일부 보완이 필요합니다.")
    else:
        print("   ❌ 추가 작업이 필요합니다.")
    
    await db_manager.close_all_connections()

if __name__ == "__main__":
    asyncio.run(test_enhanced_features())
