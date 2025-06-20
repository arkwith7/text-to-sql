"""
LangChain Agent for Text-to-SQL application.
Clean implementation with tiktoken-based token estimation.
"""

import logging
import time
import uuid
from typing import Dict, Any, Optional, List, TYPE_CHECKING

from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import AzureChatOpenAI

# TYPE_CHECKING을 사용하여 순환 import 방지
if TYPE_CHECKING:
    from database.connection_manager import DatabaseManager

from core.tools.langchain_tools import setup_langchain_tools, get_langchain_tools
from core.config import get_settings
from core.utils.token_estimator import get_token_estimator
from utils.logging_config import setup_logging
from services.token_usage_service import TokenUsageService

logger = logging.getLogger(__name__)


class LangChainTextToSQLAgent:
    """
    LangChain 기반 Text-to-SQL Agent.
    tiktoken을 사용한 간단한 토큰 추정 기능 포함.
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
        
        # Initialize token usage service (지연 로딩)
        self.token_usage_service = None
        
        # 토큰 추정기 초기화
        self.token_estimator = get_token_estimator()
        
        # 설정 로깅
        logger.info(f"LangChain Agent 초기화 시작")
        logger.info(f"  - 시뮬레이션 모드: {enable_simulation}")
        logger.info(f"  - 모델 온도: {model_temperature}")
        logger.info(f"  - 최대 반복: {max_iterations}")
        logger.info(f"  - 상세 모드: {verbose}")
        logger.info(f"  - 토큰 추적: tiktoken 기반 추정")
        
        # Azure OpenAI LLM 초기화
        self.llm = AzureChatOpenAI(
            azure_endpoint=self.settings.azure_openai_endpoint,
            api_key=self.settings.azure_openai_api_key,
            api_version=self.settings.azure_openai_api_version,
            azure_deployment=self.settings.azure_openai_deployment_name,
            temperature=model_temperature,
            max_tokens=2000,
            streaming=False,  # 스트리밍 비활성화
            model_kwargs={"seed": 42}  # 일관된 결과를 위한 시드
        )
        logger.info("✅ Azure OpenAI LLM 초기화 완료")
        
        # LangChain Tools 설정 (지연 import 방지를 위해 None으로 전달)
        setup_langchain_tools(None, enable_simulation)
        self.tools = get_langchain_tools()
        logger.info(f"✅ LangChain Tools 초기화 완료 - {len(self.tools)}개 도구")
        
        # System prompt 정의
        self.system_prompt = """
당신은 PostgreSQL Northwind 데이터베이스 전문가입니다. 
자연어 질문을 분석하여 적절한 SQL 쿼리를 생성하고 실행하여 정확한 답변을 제공합니다.

🔒 중요한 보안 규칙:
- 이 시스템은 읽기 전용(READ-ONLY)입니다
- SELECT 쿼리만 허용됩니다
- INSERT, UPDATE, DELETE, DROP, ALTER 등의 데이터 변경 작업은 절대 금지됩니다
- 데이터베이스의 구조나 데이터를 변경하려는 시도를 하지 마세요

작업 순서:
1. get_database_schema 도구로 데이터베이스 스키마를 확인
2. generate_sql_from_question 도구로 SQL 쿼리 생성  
3. execute_sql_query_sync 도구로 쿼리 실행
4. 결과를 한국어로 명확하게 설명
"""
        
        # Chat prompt 템플릿 생성
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Agent 생성 (최신 API 사용)
        self.agent = create_openai_functions_agent(
            self.llm, 
            self.tools, 
            prompt
        )
        
        # Agent Executor 생성
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=verbose,
            handle_parsing_errors=True,
            max_iterations=max_iterations,
            return_intermediate_steps=True  # 중간 단계 정보 반환
        )
        
        logger.info("✅ LangChain Agent 완전 초기화 완료")
    
    def _get_token_usage_service(self):
        """토큰 사용량 서비스를 지연 로딩합니다."""
        if self.token_usage_service is None and self.db_manager:
            try:
                self.token_usage_service = TokenUsageService(self.db_manager)
                logger.info("✅ Token Usage Service 연동 완료")
            except ImportError as e:
                logger.warning(f"Token Usage Service 로딩 실패: {e}")
        return self.token_usage_service
    
    def _estimate_token_usage(
        self, 
        question: str, 
        answer: str,
        tool_calls: Optional[List[Dict]] = None
    ) -> Dict[str, int]:
        """토큰 사용량을 추정합니다."""
        try:
            return self.token_estimator.estimate_from_question_and_answer(
                question=question,
                answer=answer,
                system_prompt=self.system_prompt,
                tool_calls=tool_calls
            )
        except Exception as e:
            logger.warning(f"토큰 추정 실패: {e}")
            # 기본값 반환
            return {
                "prompt_tokens": max(100, len(question) // 4),
                "completion_tokens": max(50, len(answer) // 4),
                "total_tokens": max(150, (len(question) + len(answer)) // 4)
            }
    
    async def execute_query(
        self,
        question: str,
        database: str = "northwind",
        context: Optional[str] = None,
        user_id: Optional[str] = None,
        include_explanation: bool = True,
        include_debug_info: bool = False,
        max_rows: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        자연어 질문을 처리하여 SQL 결과를 반환합니다.
        
        Args:
            question: 자연어 질문
            database: 대상 데이터베이스 (기본값: northwind)
            context: 추가 컨텍스트 (선택사항)
            user_id: 사용자 ID (로깅용)
            include_explanation: 설명 포함 여부
            include_debug_info: 디버그 정보 포함 여부
            max_rows: 최대 반환 행 수 (선택사항)
            
        Returns:
            실행 결과 딕셔너리
        """
        start_time = time.time()
        session_id = str(uuid.uuid4())[:8]
        
        try:
            logger.info(
                f"🚀 질문 처리 시작 (세션: {session_id}) - "
                f"사용자: {user_id or 'anonymous'}, "
                f"질문: '{question[:100]}...'"
            )
            
            # 컨텍스트가 있으면 질문에 추가
            full_question = question
            if context:
                full_question = f"컨텍스트: {context}\n\n질문: {question}"
                logger.info(f"컨텍스트 추가됨: {context[:100]}...")
            
            # Agent 실행
            logger.info(f"🤖 LangChain Agent 실행 중...")
            result = await self.agent_executor.ainvoke({
                "input": full_question
            })
            
            # 결과 추출
            answer = result.get("output", "답변을 생성할 수 없습니다.")
            intermediate_steps = result.get("intermediate_steps", [])
            
            # 실행 시간 계산
            execution_time = time.time() - start_time
            
            # 토큰 사용량 추정
            token_usage = self._estimate_token_usage(
                question=full_question,
                answer=answer,
                tool_calls=[step[0].tool for step in intermediate_steps if step and len(step) > 0]
            )
            
            logger.info(
                f"✅ 질문 처리 완료 (세션: {session_id}) - "
                f"실행시간: {execution_time:.3f}초, "
                f"토큰: {token_usage['total_tokens']} "
                f"(입력: {token_usage['prompt_tokens']}, 출력: {token_usage['completion_tokens']})"
            )
            
            # 토큰 사용량 기록 (데이터베이스에 저장)
            if user_id and self._get_token_usage_service():
                try:
                    await self.token_usage_service.record_usage(
                        user_id=user_id,
                        session_id=session_id,
                        question=question,
                        model_name=self.settings.azure_openai_deployment_name,
                        prompt_tokens=token_usage["prompt_tokens"],
                        completion_tokens=token_usage["completion_tokens"],
                        total_tokens=token_usage["total_tokens"]
                    )
                    logger.info(f"📊 토큰 사용량 기록 완료 - 사용자: {user_id}")
                except Exception as e:
                    logger.warning(f"토큰 사용량 기록 실패: {e}")
            
            # 중간 단계에서 SQL 쿼리와 결과 추출
            sql_query = ""
            sql_results = []
            
            logger.info(f"🔍 중간 단계 분석 중 - 총 {len(intermediate_steps)}개 단계")
            
            for i, step in enumerate(intermediate_steps):
                if step and len(step) >= 2:
                    action, observation = step[0], step[1]
                    
                    logger.info(f"📋 단계 {i+1}: action.tool = {getattr(action, 'tool', 'N/A')}")
                    logger.info(f"📋 단계 {i+1}: observation type = {type(observation)}")
                    logger.info(f"📋 단계 {i+1}: observation full content = {str(observation)}")
                    logger.info(f"📋 단계 {i+1}: observation preview = {str(observation)[:200]}...")
                    
                    # SQL 실행 단계에서 쿼리와 결과 추출
                    if hasattr(action, 'tool') and action.tool == 'execute_sql_query_sync':
                        if hasattr(action, 'tool_input'):
                            sql_query = action.tool_input.get('sql_query', '')
                            logger.info(f"🔍 SQL 쿼리 추출: {sql_query[:100]}...")
                        
                        # observation에서 결과 추출
                        if isinstance(observation, str):
                            try:
                                # observation이 JSON 문자열인 경우 파싱
                                import json
                                obs_data = json.loads(observation)
                                logger.info(f"🔍 파싱된 observation: {type(obs_data)}, keys: {list(obs_data.keys()) if isinstance(obs_data, dict) else 'N/A'}")
                                if isinstance(obs_data, dict):
                                    # SQL 실행 도구의 응답 형식: {"success": True, "results": [...]}
                                    if 'results' in obs_data:
                                        sql_results = obs_data['results']
                                        logger.info(f"🔍 results에서 데이터 추출: {len(sql_results)}행")
                                    elif 'data' in obs_data:
                                        sql_results = obs_data['data']
                                        logger.info(f"🔍 data에서 데이터 추출: {len(sql_results)}행")
                                elif isinstance(obs_data, list):
                                    sql_results = obs_data
                                    logger.info(f"🔍 리스트에서 데이터 추출: {len(sql_results)}행")
                            except (json.JSONDecodeError, ValueError) as e:
                                # JSON이 아닌 경우, 텍스트로 처리
                                logger.warning(f"🔍 JSON 파싱 실패: {e}")
                        elif isinstance(observation, (list, dict)):
                            if isinstance(observation, list):
                                sql_results = observation
                                logger.info(f"🔍 직접 리스트에서 데이터 추출: {len(sql_results)}행")
                            elif isinstance(observation, dict):
                                # SQL 실행 도구의 응답 형식: {"success": True, "results": [...]}
                                if 'results' in observation:
                                    sql_results = observation['results']
                                    logger.info(f"🔍 직접 results에서 데이터 추출: {len(sql_results)}행")
                                elif 'data' in observation:
                                    sql_results = observation['data']
                                    logger.info(f"🔍 직접 data에서 데이터 추출: {len(sql_results)}행")
            
            logger.info(
                f"🔍 SQL 정보 추출 완료 - "
                f"쿼리: {sql_query[:100]}{'...' if len(sql_query) > 100 else ''}, "
                f"결과: {len(sql_results)}행"
            )
            
            # 응답 구성
            response = {
                "success": True,
                "answer": answer,
                "sql_query": sql_query,
                "results": sql_results,
                "question": question,
                "session_id": session_id,
                "execution_time": round(execution_time, 3),
                "token_usage": token_usage,
                "database": database,
                "timestamp": time.time()
            }
            
            # 디버그 정보 추가 (요청 시)
            if include_debug_info:
                response["debug_info"] = {
                    "agent_steps": len(intermediate_steps),
                    "tools_used": [step[0].tool for step in intermediate_steps if step and len(step) > 0],
                    "model_config": {
                        "deployment": self.settings.azure_openai_deployment_name,
                        "temperature": self.llm.temperature,
                        "max_tokens": self.llm.max_tokens
                    },
                    "system_prompt_length": len(self.system_prompt)
                }
            
            return response
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"질문 처리 중 오류 발생: {str(e)}"
            
            logger.error(
                f"❌ 질문 처리 실패 (세션: {session_id}) - "
                f"오류: {error_msg}, 실행시간: {execution_time:.3f}초"
            )
            
            return {
                "success": False,
                "error": error_msg,
                "question": question,
                "session_id": session_id,
                "execution_time": round(execution_time, 3),
                "token_usage": None,
                "database": database,
                "timestamp": time.time()
            }
    
    def execute_query_sync(
        self,
        question: str,
        database: str = "northwind",
        context: Optional[str] = None,
        user_id: Optional[str] = None,
        include_explanation: bool = True,
        include_debug_info: bool = False,
        max_rows: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        동기식 질문 처리 (비동기 래퍼)
        """
        import asyncio
        
        try:
            # 이벤트 루프가 이미 실행 중인지 확인
            loop = asyncio.get_running_loop()
            # 이미 실행 중이면 새 스레드에서 실행
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    self.execute_query(
                        question, database, context, user_id,
                        include_explanation, include_debug_info, max_rows
                    )
                )
                return future.result()
        except RuntimeError:
            # 이벤트 루프가 없으면 직접 실행
            return asyncio.run(
                self.execute_query(
                    question, database, context, user_id,
                    include_explanation, include_debug_info, max_rows
                )
            )
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Agent 정보를 반환합니다."""
        return {
            "agent_type": "LangChain OpenAI Functions Agent",
            "model": self.settings.azure_openai_deployment_name,
            "temperature": self.llm.temperature,
            "max_tokens": self.llm.max_tokens,
            "tools": [tool.name for tool in self.tools],
            "tools_count": len(self.tools),  # 누락된 키 추가
            "simulation_mode": self.enable_simulation,
            "max_iterations": self.agent_executor.max_iterations,
            "database": "PostgreSQL Northwind",
            "supported_languages": ["Korean", "English"],
            "token_estimation": "tiktoken 기반",
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
            result = self.execute_query_sync(
                question, 
                user_id="test_user", 
                include_debug_info=False
            )
            test_results.append({
                "question": question,
                "success": result.get("success", False),
                "execution_time": result.get("execution_time", 0),
                "has_answer": bool(result.get("answer", "").strip()),
                "token_usage": result.get("token_usage")
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
