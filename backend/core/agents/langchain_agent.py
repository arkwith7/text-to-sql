"""
LangChain Agent for Text-to-SQL application.
Based on successful patterns from Jupyter notebook testing.
Uses latest LangChain APIs and patterns that have been proven to work.
"""

import logging
import time
from typing import Dict, Any, Optional, List, TYPE_CHECKING

from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import AzureChatOpenAI

# TYPE_CHECKING을 사용하여 순환 import 방지
if TYPE_CHECKING:
    from database.connection_manager import DatabaseManager

from core.tools.langchain_tools import setup_langchain_tools, get_langchain_tools
from core.config import get_settings
from utils.logging_config import setup_logging

logger = logging.getLogger(__name__)

class LangChainTextToSQLAgent:
    """
    LangChain 기반 Text-to-SQL Agent.
    주피터 노트북에서 성공한 패턴을 적용하여 구현됨.
    """
    
    def __init__(
        self,
        db_manager: Optional["DatabaseManager"] = None,
        enable_simulation: bool = True,
        model_temperature: float = 0.1,
        max_iterations: int = 5,
        verbose: bool = True
    ):
        """
        LangChain Agent 초기화.
        
        Args:
            db_manager: 데이터베이스 매니저 (Optional, 순환 import 방지)
            enable_simulation: 시뮬레이션 모드 활성화
            model_temperature: LLM 온도 설정
            max_iterations: 최대 반복 횟수
            verbose: 상세 로그 출력
        """
        self.db_manager = db_manager
        self.enable_simulation = enable_simulation
        self.settings = get_settings()
        
        # 설정 로깅
        logger.info(f"LangChain Agent 초기화 시작")
        logger.info(f"  - 시뮬레이션 모드: {enable_simulation}")
        logger.info(f"  - 모델 온도: {model_temperature}")
        logger.info(f"  - 최대 반복: {max_iterations}")
        logger.info(f"  - 상세 모드: {verbose}")
        
        try:
            # Azure OpenAI LLM 초기화
            self.llm = AzureChatOpenAI(
                azure_endpoint=self.settings.azure_openai_endpoint,
                api_key=self.settings.azure_openai_api_key,
                api_version=self.settings.azure_openai_api_version,
                azure_deployment=self.settings.azure_openai_deployment_name,
                temperature=model_temperature,
                max_tokens=2000
            )
            logger.info("✅ Azure OpenAI LLM 초기화 완료")
            
            # LangChain Tools 설정 (지연 import 방지를 위해 None으로 전달)
            setup_langchain_tools(None, enable_simulation)
            self.tools = get_langchain_tools()
            logger.info(f"✅ LangChain Tools 초기화 완료 - {len(self.tools)}개 도구")
            
            # System prompt 정의 (주피터 노트북에서 성공한 패턴)
            self.system_prompt = """
당신은 PostgreSQL Northwind 데이터베이스 전문가입니다. 
자연어 질문을 분석하여 적절한 SQL 쿼리를 생성하고 실행하여 정확한 답변을 제공합니다.

작업 순서:
1. get_database_schema 도구로 데이터베이스 스키마를 확인
2. generate_sql_from_question 도구로 SQL 쿼리 생성  
3. execute_sql_query_sync 도구로 쿼리 실행
4. 결과를 한국어로 명확하게 설명

주의사항:
- 항상 스키마를 먼저 확인하세요
- SQL 쿼리는 PostgreSQL Northwind 스키마에 맞게 정확해야 합니다
- 테이블명: customers, products, orders, categories, employees, suppliers, shippers, orderdetails
- 결과는 사용자가 이해하기 쉽게 한국어로 설명하세요
- 에러가 발생하면 원인을 분석하고 해결 방법을 제시하세요

PostgreSQL Northwind 데이터베이스 정보:
- 고객(customers): 91개
- 제품(products): 77개  
- 주문(orders): 196개
- 카테고리(categories): 8개
- 직원(employees): 10명
- 공급업체(suppliers): 29개
- 배송업체(shippers): 3개
"""
            
            # Chat prompt 템플릿 생성
            self.prompt = ChatPromptTemplate.from_messages([
                ("system", self.system_prompt),
                ("user", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ])
            
            # Agent 생성 (최신 API 사용)
            self.agent = create_openai_functions_agent(
                self.llm, 
                self.tools, 
                self.prompt
            )
            
            # Agent Executor 생성
            self.agent_executor = AgentExecutor(
                agent=self.agent,
                tools=self.tools,
                verbose=verbose,
                handle_parsing_errors=True,
                max_iterations=max_iterations
            )
            
            logger.info("✅ LangChain Agent 완전 초기화 완료")
            logger.info(f"  - Agent Type: OpenAI Functions")
            logger.info(f"  - LLM Model: {self.settings.azure_openai_deployment_name}")
            logger.info(f"  - Available Tools: {len(self.tools)}개")
            
        except Exception as e:
            logger.error(f"❌ LangChain Agent 초기화 실패: {str(e)}")
            raise
    
    def execute_query(
        self,
        question: str,
        user_id: Optional[str] = None,
        include_debug_info: bool = False
    ) -> Dict[str, Any]:
        """
        자연어 질문을 처리하여 SQL 결과를 반환합니다.
        
        Args:
            question: 자연어 질문
            user_id: 사용자 ID (로깅용)
            include_debug_info: 디버그 정보 포함 여부
            
        Returns:
            실행 결과 딕셔너리
        """
        start_time = time.time()
        
        try:
            logger.info(
                f"🤖 LangChain Agent 쿼리 실행 시작",
                extra={
                    'user_id': user_id,
                    'question': question[:100] + '...' if len(question) > 100 else question,
                    'include_debug': include_debug_info
                }
            )
            
            # Agent 실행 (최신 invoke 메서드 사용)
            result = self.agent_executor.invoke({"input": question})
            
            execution_time = time.time() - start_time
            
            # 결과 처리
            output = result.get('output', '')
            
            logger.info(
                f"✅ LangChain Agent 실행 완료 - 시간: {execution_time:.3f}s",
                extra={
                    'user_id': user_id,
                    'execution_time': execution_time,
                    'output_length': len(output),
                    'success': True
                }
            )
            
            response = {
                "success": True,
                "question": question,
                "answer": output,
                "execution_time": execution_time,
                "agent_type": "langchain_openai_functions",
                "model": self.settings.azure_openai_deployment_name,
                "simulation_mode": self.enable_simulation
            }
            
            if include_debug_info:
                response.update({
                    "debug_info": {
                        "intermediate_steps": result.get('intermediate_steps', []),
                        "tool_count": len(self.tools),
                        "max_iterations": self.agent_executor.max_iterations
                    }
                })
            
            return response
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            
            logger.error(
                f"❌ LangChain Agent 실행 실패 - 시간: {execution_time:.3f}s",
                extra={
                    'user_id': user_id,
                    'execution_time': execution_time,
                    'error': error_msg,
                    'question': question[:100] + '...' if len(question) > 100 else question
                }
            )
            
            return {
                "success": False,
                "question": question,
                "error": error_msg,
                "execution_time": execution_time,
                "agent_type": "langchain_openai_functions",
                "model": self.settings.azure_openai_deployment_name,
                "simulation_mode": self.enable_simulation
            }
    
    async def execute_query_async(
        self,
        question: str,
        user_id: Optional[str] = None,
        include_debug_info: bool = False
    ) -> Dict[str, Any]:
        """
        비동기 버전의 쿼리 실행.
        
        Args:
            question: 자연어 질문
            user_id: 사용자 ID (로깅용)
            include_debug_info: 디버그 정보 포함 여부
            
        Returns:
            실행 결과 딕셔너리
        """
        start_time = time.time()
        
        try:
            logger.info(f"🤖 비동기 LangChain Agent 실행 시작 - 질문: {question[:50]}...")
            
            # 비동기 실행
            result = await self.agent_executor.ainvoke({"input": question})
            
            execution_time = time.time() - start_time
            output = result.get('output', '')
            
            logger.info(f"✅ 비동기 실행 완료 - 시간: {execution_time:.3f}s")
            
            response = {
                "success": True,
                "question": question,
                "answer": output,
                "execution_time": execution_time,
                "agent_type": "langchain_openai_functions_async",
                "model": self.settings.azure_openai_deployment_name,
                "simulation_mode": self.enable_simulation
            }
            
            if include_debug_info:
                response["debug_info"] = {
                    "intermediate_steps": result.get('intermediate_steps', []),
                    "tool_count": len(self.tools)
                }
            
            return response
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            
            logger.error(f"❌ 비동기 실행 실패: {error_msg}")
            
            return {
                "success": False,
                "question": question,
                "error": error_msg,
                "execution_time": execution_time,
                "agent_type": "langchain_openai_functions_async"
            }
    
    def batch_execute(
        self,
        questions: List[str],
        user_id: Optional[str] = None,
        max_concurrent: int = 3
    ) -> List[Dict[str, Any]]:
        """
        여러 질문을 배치로 처리합니다.
        
        Args:
            questions: 질문 목록
            user_id: 사용자 ID
            max_concurrent: 최대 동시 실행 수
            
        Returns:
            결과 목록
        """
        start_time = time.time()
        results = []
        
        logger.info(f"📋 배치 실행 시작 - {len(questions)}개 질문")
        
        for i, question in enumerate(questions, 1):
            logger.info(f"🔄 배치 진행: {i}/{len(questions)} - {question[:30]}...")
            
            result = self.execute_query(
                question=question,
                user_id=user_id,
                include_debug_info=False
            )
            
            # 배치 정보 추가
            result["batch_info"] = {
                "batch_index": i,
                "total_questions": len(questions),
                "is_batch": True
            }
            
            results.append(result)
        
        total_time = time.time() - start_time
        successful_count = sum(1 for r in results if r.get('success', False))
        
        logger.info(
            f"✅ 배치 실행 완료 - 총 시간: {total_time:.3f}s, 성공: {successful_count}/{len(questions)}"
        )
        
        return results
    
    def get_agent_info(self) -> Dict[str, Any]:
        """
        Agent 정보를 반환합니다.
        
        Returns:
            Agent 정보 딕셔너리
        """
        return {
            "agent_type": "LangChain OpenAI Functions",
            "model": self.settings.azure_openai_deployment_name,
            "api_version": self.settings.azure_openai_api_version,
            "tools_count": len(self.tools),
            "tools": [tool.name for tool in self.tools],
            "simulation_mode": self.enable_simulation,
            "max_iterations": self.agent_executor.max_iterations,
            "database": "PostgreSQL Northwind",
            "supported_languages": ["Korean", "English"],
            "initialization_status": "완료"
        }
    
    def test_agent(self) -> Dict[str, Any]:
        """
        Agent의 기본 기능을 테스트합니다.
        
        Returns:
            테스트 결과
        """
        test_questions = [
            "고객 수를 알려주세요",
            "제품 수는 몇 개인가요?",
            "카테고리별 제품 수를 보여주세요"
        ]
        
        logger.info("🧪 Agent 기본 기능 테스트 시작")
        
        test_results = []
        start_time = time.time()
        
        for question in test_questions:
            result = self.execute_query(question, user_id="test_user", include_debug_info=False)
            test_results.append({
                "question": question,
                "success": result.get("success", False),
                "execution_time": result.get("execution_time", 0),
                "has_answer": bool(result.get("answer", "").strip())
            })
        
        total_time = time.time() - start_time
        success_rate = sum(1 for r in test_results if r["success"]) / len(test_results) * 100
        
        test_summary = {
            "test_completed": True,
            "total_tests": len(test_questions),
            "success_rate": f"{success_rate:.1f}%",
            "total_time": f"{total_time:.3f}초",
            "avg_time": f"{total_time/len(test_questions):.3f}초",
            "results": test_results,
            "agent_info": self.get_agent_info()
        }
        
        logger.info(f"✅ Agent 테스트 완료 - 성공률: {success_rate:.1f}%")
        
        return test_summary 