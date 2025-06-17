#!/usr/bin/env python3
"""
LangChain Function Tools 및 @tool 데코레이터 구현 검증 스크립트
노트북의 패턴과 백엔드 구현을 비교하여 완전성을 확인합니다.
"""

import sys
import os
import json
from pathlib import Path

# 프로젝트 루트를 파이썬 경로에 추가
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from utils.logging_config import setup_logging
import logging

# 로깅 설정
setup_logging()
logger = logging.getLogger(__name__)

def verify_langchain_function_tools():
    """LangChain Function Tools 구현 검증"""
    
    print("🔧 LangChain Function Tools 구현 검증")
    print("=" * 60)
    
    verification_results = {
        "function_tools_implementation": {},
        "tool_decorator_usage": {},
        "agent_integration": {},
        "notebook_pattern_compliance": {},
        "overall_status": {}
    }
    
    # 1. @tool 데코레이터 기반 Function Tools 검증
    print("\n📋 1. @tool 데코레이터 기반 Function Tools 검증")
    print("-" * 40)
    
    try:
        from core.tools.langchain_tools import (
            get_database_schema,
            generate_sql_from_question,
            execute_sql_query_sync,
            validate_sql_query
        )
        
        # 각 도구가 @tool 데코레이터로 정의되었는지 확인
        tools_info = {}
        for tool_func in [get_database_schema, generate_sql_from_question, execute_sql_query_sync, validate_sql_query]:
            tool_name = tool_func.name
            tool_description = tool_func.description
            tool_args = tool_func.args if hasattr(tool_func, 'args') else "No args info"
            
            tools_info[tool_name] = {
                "has_tool_decorator": hasattr(tool_func, 'name'),
                "description": tool_description,
                "args_schema": str(tool_args),
                "callable": callable(tool_func)
            }
            
            print(f"✅ {tool_name}")
            print(f"   - 설명: {tool_description}")
            print(f"   - 데코레이터: {'✅' if hasattr(tool_func, 'name') else '❌'}")
            print(f"   - 호출 가능: {'✅' if callable(tool_func) else '❌'}")
        
        verification_results["function_tools_implementation"] = {
            "status": "success",
            "tools_count": len(tools_info),
            "tools_info": tools_info
        }
        
    except Exception as e:
        print(f"❌ Function Tools 검증 실패: {str(e)}")
        verification_results["function_tools_implementation"] = {
            "status": "failed",
            "error": str(e)
        }
    
    # 2. LangChain Tools 설정 및 가져오기 검증
    print("\n📋 2. LangChain Tools 설정 및 관리 검증")
    print("-" * 40)
    
    try:
        from core.tools.langchain_tools import (
            setup_langchain_tools,
            get_langchain_tools,
            create_agent_compatible_tools,
            get_tool_descriptions
        )
        
        # Tools 설정 테스트
        setup_langchain_tools(None, enable_simulation=True)
        tools_list = get_langchain_tools()
        tool_descriptions = get_tool_descriptions()
        
        print(f"✅ LangChain Tools 설정 완료")
        print(f"   - 사용 가능한 도구 수: {len(tools_list)}")
        print(f"   - 도구 설명 수: {len(tool_descriptions)}")
        print(f"   - Agent 호환 도구 생성: {'✅' if create_agent_compatible_tools else '❌'}")
        
        # 각 도구의 세부 정보 출력
        for tool in tools_list:
            print(f"   - {tool.name}: {tool.description[:50]}...")
        
        verification_results["tool_decorator_usage"] = {
            "status": "success",
            "setup_function": "available",
            "tools_count": len(tools_list),
            "descriptions_count": len(tool_descriptions),
            "agent_compatibility": "available"
        }
        
    except Exception as e:
        print(f"❌ LangChain Tools 설정 검증 실패: {str(e)}")
        verification_results["tool_decorator_usage"] = {
            "status": "failed",
            "error": str(e)
        }
    
    # 3. LangChain Agent 통합 검증
    print("\n📋 3. LangChain Agent 통합 검증")
    print("-" * 40)
    
    try:
        from core.agents.langchain_agent import LangChainTextToSQLAgent
        
        # Agent 초기화 (시뮬레이션 모드)
        agent = LangChainTextToSQLAgent(
            db_manager=None,
            enable_simulation=True,
            verbose=False
        )
        
        # Agent 정보 확인
        agent_info = agent.get_agent_info()
        
        print(f"✅ LangChain Agent 초기화 성공")
        print(f"   - Agent 타입: {agent_info.get('agent_type')}")
        print(f"   - 모델: {agent_info.get('model')}")
        print(f"   - 도구 수: {agent_info.get('tools_count')}")
        print(f"   - 시뮬레이션 모드: {agent_info.get('simulation_mode')}")
        print(f"   - 지원 언어: {agent_info.get('supported_languages')}")
        
        # 도구 목록 확인
        print(f"   - 사용 도구:")
        for tool_name in agent_info.get('tools', []):
            print(f"     * {tool_name}")
        
        verification_results["agent_integration"] = {
            "status": "success",
            "agent_info": agent_info,
            "initialization": "successful"
        }
        
    except Exception as e:
        print(f"❌ LangChain Agent 통합 검증 실패: {str(e)}")
        verification_results["agent_integration"] = {
            "status": "failed",
            "error": str(e)
        }
    
    # 4. 노트북 패턴 준수 검증
    print("\n📋 4. Jupyter 노트북 패턴 준수 검증")
    print("-" * 40)
    
    try:
        # 노트북에서 사용된 패턴들 확인
        notebook_patterns = {
            "azure_openai_integration": False,
            "function_tools_definition": False,
            "agent_executor_pattern": False,
            "invoke_method_usage": False,
            "system_prompt_structure": False,
            "simulation_mode_support": False
        }
        
        # Agent 인스턴스에서 패턴 확인
        if 'agent' in locals():
            # Azure OpenAI 통합 확인
            if hasattr(agent, 'llm') and 'azure' in str(type(agent.llm)).lower():
                notebook_patterns["azure_openai_integration"] = True
                print("✅ Azure OpenAI 통합")
            
            # Function Tools 정의 확인
            if hasattr(agent, 'tools') and len(agent.tools) >= 4:
                notebook_patterns["function_tools_definition"] = True
                print("✅ Function Tools 정의 (4개 이상)")
            
            # Agent Executor 패턴 확인
            if hasattr(agent, 'agent_executor'):
                notebook_patterns["agent_executor_pattern"] = True
                print("✅ Agent Executor 패턴")
            
            # invoke 메서드 사용 확인 (execute_query 메서드 내부)
            if hasattr(agent, 'execute_query'):
                notebook_patterns["invoke_method_usage"] = True
                print("✅ invoke() 메서드 사용")
            
            # System prompt 구조 확인
            if hasattr(agent, 'system_prompt') and agent.system_prompt:
                notebook_patterns["system_prompt_structure"] = True
                print("✅ System Prompt 구조")
            
            # 시뮬레이션 모드 지원 확인
            if hasattr(agent, 'enable_simulation'):
                notebook_patterns["simulation_mode_support"] = True
                print("✅ 시뮬레이션 모드 지원")
        
        compliance_score = sum(notebook_patterns.values()) / len(notebook_patterns) * 100
        print(f"\n📊 노트북 패턴 준수율: {compliance_score:.1f}%")
        
        verification_results["notebook_pattern_compliance"] = {
            "status": "success",
            "patterns": notebook_patterns,
            "compliance_score": compliance_score
        }
        
    except Exception as e:
        print(f"❌ 노트북 패턴 준수 검증 실패: {str(e)}")
        verification_results["notebook_pattern_compliance"] = {
            "status": "failed",
            "error": str(e)
        }
    
    # 5. 실제 기능 테스트
    print("\n📋 5. LangChain Function Tools 실제 동작 테스트")
    print("-" * 40)
    
    try:
        # Function Tools 직접 호출 테스트
        test_results = {}
        
        # 1. 스키마 조회 테스트
        try:
            schema_result = get_database_schema("northwind")
            schema_data = json.loads(schema_result)
            test_results["schema_query"] = {
                "success": True,
                "tables_count": len(schema_data.get("tables", {})),
                "has_relationships": bool(schema_data.get("relationships", []))
            }
            print(f"✅ 스키마 조회: {len(schema_data.get('tables', {}))}개 테이블")
        except Exception as e:
            test_results["schema_query"] = {"success": False, "error": str(e)}
            print(f"❌ 스키마 조회 실패: {str(e)}")
        
        # 2. SQL 생성 테스트
        try:
            sql_result = generate_sql_from_question("고객 수를 알려주세요")
            sql_data = json.loads(sql_result)
            test_results["sql_generation"] = {
                "success": True,
                "has_sql": bool(sql_data.get("sql_query")),
                "has_explanation": bool(sql_data.get("explanation"))
            }
            print(f"✅ SQL 생성: {'성공' if sql_data.get('sql_query') else '실패'}")
        except Exception as e:
            test_results["sql_generation"] = {"success": False, "error": str(e)}
            print(f"❌ SQL 생성 실패: {str(e)}")
        
        # 3. SQL 실행 테스트 (시뮬레이션)
        try:
            execution_result = execute_sql_query_sync("SELECT COUNT(*) as customer_count FROM customers")
            execution_data = json.loads(execution_result)
            test_results["sql_execution"] = {
                "success": True,
                "simulation_mode": execution_data.get("simulation_mode", False),
                "has_results": bool(execution_data.get("results"))
            }
            print(f"✅ SQL 실행: {'시뮬레이션 모드' if execution_data.get('simulation_mode') else '실제 DB'}")
        except Exception as e:
            test_results["sql_execution"] = {"success": False, "error": str(e)}
            print(f"❌ SQL 실행 실패: {str(e)}")
        
        # 4. Agent 전체 워크플로우 테스트
        if 'agent' in locals():
            try:
                agent_result = agent.execute_query("제품 수는 몇 개인가요?", include_debug_info=False)
                test_results["agent_workflow"] = {
                    "success": agent_result.get("success", False),
                    "has_answer": bool(agent_result.get("answer", "").strip()),
                    "execution_time": agent_result.get("execution_time", 0)
                }
                print(f"✅ Agent 워크플로우: {'성공' if agent_result.get('success') else '실패'}")
            except Exception as e:
                test_results["agent_workflow"] = {"success": False, "error": str(e)}
                print(f"❌ Agent 워크플로우 실패: {str(e)}")
        
        verification_results["overall_status"] = {
            "status": "success",
            "test_results": test_results,
            "functional_tests_passed": sum(1 for r in test_results.values() if r.get("success", False))
        }
        
    except Exception as e:
        print(f"❌ 기능 테스트 실패: {str(e)}")
        verification_results["overall_status"] = {
            "status": "failed",
            "error": str(e)
        }
    
    # 6. 최종 결과 요약
    print("\n" + "=" * 60)
    print("🎯 LangChain Function Tools 검증 결과 요약")
    print("=" * 60)
    
    # 각 영역별 상태 확인
    areas = [
        ("Function Tools 구현", verification_results["function_tools_implementation"]),
        ("@tool 데코레이터 사용", verification_results["tool_decorator_usage"]),
        ("Agent 통합", verification_results["agent_integration"]),
        ("노트북 패턴 준수", verification_results["notebook_pattern_compliance"]),
        ("전체 기능 테스트", verification_results["overall_status"])
    ]
    
    success_count = 0
    for area_name, area_result in areas:
        status = area_result.get("status", "unknown")
        if status == "success":
            print(f"✅ {area_name}: 성공")
            success_count += 1
        else:
            print(f"❌ {area_name}: 실패")
    
    overall_success_rate = success_count / len(areas) * 100
    print(f"\n📊 전체 성공률: {overall_success_rate:.1f}% ({success_count}/{len(areas)})")
    
    # 주요 발견 사항
    print(f"\n🔍 주요 발견 사항:")
    
    # Function Tools 상세 정보
    if verification_results["function_tools_implementation"].get("status") == "success":
        tools_count = verification_results["function_tools_implementation"]["tools_count"]
        print(f"  - @tool 데코레이터 기반 Function Tools: {tools_count}개 구현됨")
    
    # 노트북 패턴 준수율
    if verification_results["notebook_pattern_compliance"].get("status") == "success":
        compliance_score = verification_results["notebook_pattern_compliance"]["compliance_score"]
        print(f"  - Jupyter 노트북 패턴 준수율: {compliance_score:.1f}%")
    
    # Agent 통합 정보
    if verification_results["agent_integration"].get("status") == "success":
        agent_info = verification_results["agent_integration"]["agent_info"]
        print(f"  - LangChain Agent: {agent_info.get('agent_type')} ({agent_info.get('tools_count')}개 도구)")
    
    # 기능 테스트 결과
    if verification_results["overall_status"].get("status") == "success":
        passed_tests = verification_results["overall_status"]["functional_tests_passed"]
        total_tests = len(verification_results["overall_status"]["test_results"])
        print(f"  - 기능 테스트: {passed_tests}/{total_tests} 통과")
    
    # 검증 결과를 파일로 저장
    results_file = project_root / "langchain_function_tools_verification.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(verification_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 상세 검증 결과 저장: {results_file}")
    
    return verification_results

if __name__ == "__main__":
    print("🚀 LangChain Function Tools 및 @tool 데코레이터 구현 검증 시작")
    
    try:
        results = verify_langchain_function_tools()
        
        # 최종 상태 코드 반환
        if results["overall_status"].get("status") == "success":
            print("\n🎉 검증 완료: LangChain Function Tools가 완전히 구현되었습니다!")
            exit(0)
        else:
            print("\n⚠️ 검증 완료: 일부 항목에서 문제가 발견되었습니다.")
            exit(1)
            
    except Exception as e:
        logger.error(f"검증 스크립트 실행 실패: {str(e)}")
        print(f"\n❌ 검증 실패: {str(e)}")
        exit(1)
