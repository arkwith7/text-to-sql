"""
LangChain Agent for Text-to-SQL application.
Based on successful patterns from Jupyter notebook testing.
Uses latest LangChain APIs and patterns that have been proven to work.
Includes LLM token usage tracking functionality.
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
from utils.logging_config import setup_logging
from services.token_usage_service import TokenUsageService

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
        
        # Initialize token usage service (지연 로딩)
        self.db_manager = db_manager
        self.token_usage_service = None
        
        # 설정 로깅
        logger.info(f"LangChain Agent 초기화 시작")
        logger.info(f"  - 시뮬레이션 모드: {enable_simulation}")
        logger.info(f"  - 모델 온도: {model_temperature}")
        logger.info(f"  - 최대 반복: {max_iterations}")
        logger.info(f"  - 상세 모드: {verbose}")
        logger.info(f"  - 토큰 추적: {'활성화' if db_manager else '비활성화'}")
        
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
        
        # System prompt 정의 (주피터 노트북에서 성공한 패턴 + 보안 강화)
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
                logger.info("✅ LangChain Token Usage Service 연동 완료")
            except ImportError as e:
                logger.warning(f"Token Usage Service 로딩 실패: {e}")
        return self.token_usage_service
    
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
        
        try:
            logger.info(
                f"🤖 LangChain Agent 쿼리 실행 시작",
                extra={
                    'user_id': user_id,
                    'question': question[:100] + '...' if len(question) > 100 else question,
                    'database': database,
                    'include_debug': include_debug_info
                }
            )
            
            # Context가 있으면 질문에 추가
            enhanced_question = question
            if context:
                enhanced_question = f"{question}\n\n추가 조건: {context}"
            
            # Azure OpenAI 호출 시 토큰 사용량 추적을 위해 콜백 사용
            try:
                from langchain_community.callbacks import get_openai_callback
                logger.info("✅ LangChain Community 콜백 로드 성공")
            except ImportError:
                try:
                    from langchain.callbacks import get_openai_callback
                    logger.info("✅ LangChain Core 콜백 로드 성공")
                except ImportError:
                    logger.warning("⚠️ OpenAI 콜백을 찾을 수 없음")
                    # 콜백 없이 실행
                    result = await self.agent_executor.ainvoke({"input": enhanced_question})
                    execution_time = time.time() - start_time
                    output = result.get('output', '')
                    intermediate_steps = result.get('intermediate_steps', [])
                    
                    logger.info(f"🔍 Agent 출력 길이: {len(output)} 문자")
                    logger.info(f"🔍 Agent 출력 내용: '{output[:100]}...' " if len(output) > 100 else f"'{output}'")
                    logger.info(f"🔍 중간 단계 수: {len(intermediate_steps)}")
                    
                    # Check if agent failed due to iteration/time limit and provide user-friendly message
                    is_agent_limit_error = (
                        "Agent stopped due to iteration limit or time limit" in output or
                        output.strip() == "Agent stopped due to iteration limit or time limit."
                    )
                    
                    if is_agent_limit_error:
                        logger.warning("⚠️ Agent가 iteration/time limit으로 인해 중단됨 (콜백 없음)")
                        output = "질문이 너무 복잡하거나 데이터베이스 구조에 맞는 답변을 찾지 못했습니다. 질문을 더 구체적으로 입력해 주세요."
                    
                    # 중간 단계에서 SQL 쿼리와 결과 추출
                    executed_sql = None
                    sql_results = []
                    
                    for i, (agent_action, observation) in enumerate(intermediate_steps, 1):
                        observation_str = str(observation)
                        logger.info(f"🔍 단계 {i}: 도구={agent_action.tool}, 관찰={observation_str[:200]}...")
                        
                        # execute_sql_query_sync 도구의 결과에서 SQL과 데이터 추출
                        if agent_action.tool == "execute_sql_query_sync":
                            try:
                                # 관찰이 딕셔너리인지 확인
                                if isinstance(observation, dict):
                                    obs_dict = observation
                                elif isinstance(observation, str):
                                    # 문자열이면 JSON 파싱 시도
                                    import json
                                    try:
                                        obs_dict = json.loads(observation)
                                    except json.JSONDecodeError:
                                        logger.warning(f"❌ JSON 파싱 실패: {observation[:100]}...")
                                        continue
                                else:
                                    logger.warning(f"❌ 알 수 없는 관찰 타입: {type(observation)}")
                                    continue
                                
                                # SQL 쿼리와 결과 추출
                                if obs_dict.get('success'):
                                    if obs_dict.get('sql_query'):
                                        executed_sql = obs_dict.get('sql_query')
                                        sql_results = obs_dict.get('results', [])
                                        logger.info(f"🎯 SQL 쿼리 추출 성공: {executed_sql[:100]}...")
                                        logger.info(f"🎯 결과 행 수: {len(sql_results)}")
                                        break  # 첫 번째 성공한 SQL 실행 결과 사용
                                    else:
                                        logger.warning(f"⚠️ SQL 쿼리가 없음: {obs_dict}")
                                else:
                                    logger.warning(f"⚠️ SQL 실행 실패: {obs_dict}")
                            except Exception as e:
                                logger.error(f"❌ SQL 추출 중 오류: {e}, 관찰: {observation_str[:100]}...")
                    
                    # 토큰 정보 없이 응답 생성
                    logger.info("⚠️ 토큰 사용량 추적 없음")
                    
                    response = {
                        "success": True,
                        "question": question,
                        "answer": output,
                        "sql_query": executed_sql or "",
                        "results": sql_results or [],
                        "execution_time": execution_time,
                        "agent_type": "langchain_openai_functions",
                        "model": self.settings.azure_openai_deployment_name,
                        "simulation_mode": self.enable_simulation,
                        "explanation": output  # Agent의 답변을 설명으로도 사용
                    }
                    
                    if include_debug_info:
                        response.update({
                            "debug_info": {
                                "intermediate_steps": intermediate_steps,
                                "tool_count": len(self.tools),
                                "max_iterations": self.agent_executor.max_iterations,
                                "executed_sql": executed_sql,
                                "sql_results_count": len(sql_results) if sql_results else 0
                            }
                        })
                    
                    logger.info(
                        f"✅ LangChain Agent 실행 완료 (콜백 없음) - 시간: {execution_time:.3f}s",
                        extra={
                            'user_id': user_id,
                            'execution_time': execution_time,
                            'output_length': len(output),
                            'success': True
                        }
                    )
                    
                    return response
            
            logger.info("🔍 토큰 콜백 시작 - Agent 실행 전")
            
            with get_openai_callback() as cb:
                # Agent 실행 (비동기로 변경)
                logger.info("🤖 Agent executor ainvoke 시작")
                result = await self.agent_executor.ainvoke({"input": enhanced_question})
                logger.info(f"🤖 Agent executor ainvoke 완료 - 결과 키: {list(result.keys())}")
                
                execution_time = time.time() - start_time
                
                # 결과 처리
                output = result.get('output', '')
                intermediate_steps = result.get('intermediate_steps', [])
                
                logger.info(f"🔍 Agent 출력 길이: {len(output)} 문자")
                logger.info(f"🔍 Agent 출력 내용: '{output[:100]}...' " if len(output) > 100 else f"'{output}'")
                logger.info(f"🔍 중간 단계 수: {len(intermediate_steps)}")
                
                # Check if agent failed due to iteration/time limit and provide user-friendly message
                is_agent_limit_error = (
                    "Agent stopped due to iteration limit or time limit" in output or
                    output.strip() == "Agent stopped due to iteration limit or time limit."
                )
                
                if is_agent_limit_error:
                    logger.warning("⚠️ Agent가 iteration/time limit으로 인해 중단됨")
                    output = "질문이 너무 복잡하거나 데이터베이스 구조에 맞는 답변을 찾지 못했습니다. 질문을 더 구체적으로 입력해 주세요."
                
                # 중간 단계에서 SQL 쿼리와 결과 추출
                executed_sql = None
                sql_results = []
                
                for i, (agent_action, observation) in enumerate(intermediate_steps, 1):
                    observation_str = str(observation)
                    logger.info(f"🔍 단계 {i}: 도구={agent_action.tool}, 관찰={observation_str[:200]}...")
                    
                    # execute_sql_query_sync 도구의 결과에서 SQL과 데이터 추출
                    if agent_action.tool == "execute_sql_query_sync":
                        try:
                            # 관찰이 딕셔너리인지 확인
                            if isinstance(observation, dict):
                                obs_dict = observation
                            elif isinstance(observation, str):
                                # 문자열이면 JSON 파싱 시도
                                import json
                                try:
                                    obs_dict = json.loads(observation)
                                except json.JSONDecodeError:
                                    logger.warning(f"❌ JSON 파싱 실패: {observation[:100]}...")
                                    continue
                            else:
                                logger.warning(f"❌ 알 수 없는 관찰 타입: {type(observation)}")
                                continue
                            
                            # SQL 쿼리와 결과 추출
                            if obs_dict.get('success'):
                                if obs_dict.get('sql_query'):
                                    executed_sql = obs_dict.get('sql_query')
                                    sql_results = obs_dict.get('results', [])
                                    logger.info(f"🎯 SQL 쿼리 추출 성공: {executed_sql[:100]}...")
                                    logger.info(f"🎯 결과 행 수: {len(sql_results)}")
                                    break  # 첫 번째 성공한 SQL 실행 결과 사용
                                else:
                                    logger.warning(f"⚠️ SQL 쿼리가 없음: {obs_dict}")
                            else:
                                logger.warning(f"⚠️ SQL 실행 실패: {obs_dict}")
                        except Exception as e:
                            logger.error(f"❌ SQL 추출 중 오류: {e}, 관찰: {observation_str[:100]}...")
                
                # 토큰 사용량 정보 추출 및 기록
                logger.info(f"🔍 콜백 객체 타입: {type(cb)}")
                logger.info(f"🔍 콜백 토큰 사용량: {cb.total_tokens} (prompt: {cb.prompt_tokens}, completion: {cb.completion_tokens})")
                logger.info(f"🔍 콜백 successful_requests: {getattr(cb, 'successful_requests', 'N/A')}")
                logger.info(f"🔍 콜백 total_cost: {getattr(cb, 'total_cost', 'N/A')}")
                logger.info(f"🔍 사용자 ID: {user_id}")
                
                if user_id and cb.total_tokens > 0:
                    token_usage = {
                        "prompt_tokens": cb.prompt_tokens,
                        "completion_tokens": cb.completion_tokens,
                        "total_tokens": cb.total_tokens
                    }
                    logger.info(f"💰 토큰 사용량 기록 시작: {token_usage}")
                    
                    # 토큰 사용량 기록 (비동기 버전)
                    try:
                        token_service = self._get_token_usage_service()
                        logger.info(f"🔧 토큰 서비스: {token_service is not None}")
                        
                        if token_service:
                            query_id = str(uuid.uuid4())
                            model_name = self.settings.azure_openai_deployment_name
                            
                            logger.info(f"📝 토큰 기록 시작 - Query ID: {query_id}, Model: {model_name}")
                            
                            # 비동기 메서드 호출
                            await token_service.record_token_usage(
                                user_id=user_id,
                                session_id="langchain_session",
                                message_id=query_id,
                                token_usage=token_usage,
                                model_name=model_name,
                                query_type="text_to_sql",
                                additional_metadata={
                                    "question": question,
                                    "agent_type": "langchain_openai_functions",
                                    "execution_time": execution_time
                                }
                            )
                            
                            logger.info(
                                f"🔢 토큰 사용량 기록 완료 - 총: {token_usage['total_tokens']}, "
                                f"입력: {token_usage['prompt_tokens']}, 출력: {token_usage['completion_tokens']}"
                            )
                    except Exception as token_error:
                        logger.error(f"토큰 사용량 기록 실패: {token_error}")
                else:
                    logger.warning(f"토큰 사용량 기록 조건 미충족 - user_id: {user_id}, tokens: {cb.total_tokens if 'cb' in locals() else 'N/A'}")
            
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
                "sql_query": executed_sql or "",
                "results": sql_results or [],
                "execution_time": execution_time,
                "agent_type": "langchain_openai_functions",
                "model": self.settings.azure_openai_deployment_name,
                "simulation_mode": self.enable_simulation,
                "explanation": output  # Agent의 답변을 설명으로도 사용
            }
            
            if include_debug_info:
                response.update({
                    "debug_info": {
                        "intermediate_steps": intermediate_steps,
                        "tool_count": len(self.tools),
                        "max_iterations": self.agent_executor.max_iterations,
                        "executed_sql": executed_sql,
                        "sql_results_count": len(sql_results) if sql_results else 0
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
        동기 버전의 쿼리 실행 (배치 처리용).
        
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
        
        try:
            logger.info(
                f"🤖 LangChain Agent 동기 쿼리 실행 시작",
                extra={
                    'user_id': user_id,
                    'question': question[:100] + '...' if len(question) > 100 else question,
                    'database': database,
                    'include_debug': include_debug_info
                }
            )
            
            # Context가 있으면 질문에 추가
            enhanced_question = question
            if context:
                enhanced_question = f"{question}\n\n추가 조건: {context}"
            
            # Azure OpenAI 호출 시 토큰 사용량 추적을 위해 콜백 사용
            try:
                from langchain_community.callbacks import get_openai_callback
            except ImportError:
                from langchain.callbacks import get_openai_callback
            
            with get_openai_callback() as cb:
                # Agent 실행 (동기 버전)
                result = self.agent_executor.invoke({"input": enhanced_question})
                
                execution_time = time.time() - start_time
                
                # 결과 처리
                output = result.get('output', '')
                
                # 토큰 사용량 정보 추출
                logger.info(f"🔍 콜백 토큰 사용량: {cb.total_tokens} (prompt: {cb.prompt_tokens}, completion: {cb.completion_tokens})")
                
                # 토큰 사용량 기록은 동기 버전에서 생략 (복잡성 방지)
                if user_id and cb.total_tokens > 0:
                    logger.info(f"💰 토큰 사용량 기록 생략 (동기 버전) - 사용자: {user_id}, 토큰: {cb.total_tokens}")
            
            logger.info(
                f"✅ LangChain Agent 동기 실행 완료 - 시간: {execution_time:.3f}s",
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
                "agent_type": "langchain_openai_functions_sync",
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
                f"❌ LangChain Agent 동기 실행 실패 - 시간: {execution_time:.3f}s",
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
                "agent_type": "langchain_openai_functions_sync",
                "model": self.settings.azure_openai_deployment_name,
                "simulation_mode": self.enable_simulation
            }

    async def execute_query_async(
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
            
            # Azure OpenAI 호출 시 토큰 사용량 추적을 위해 콜백 사용
            try:
                from langchain_community.callbacks import get_openai_callback
            except ImportError:
                from langchain.callbacks import get_openai_callback
            
            with get_openai_callback() as cb:
                # 비동기 실행
                result = await self.agent_executor.ainvoke({"input": question})
                
                # 토큰 사용량 정보 추출
                token_usage = {
                    "prompt_tokens": cb.prompt_tokens,
                    "completion_tokens": cb.completion_tokens,
                    "total_tokens": cb.total_tokens
                }
                
                # 토큰 사용량 기록
                token_service = self._get_token_usage_service()
                if user_id and token_service and cb.total_tokens > 0:
                    query_id = str(uuid.uuid4())
                    model_name = self.settings.azure_openai_deployment_name
                    
                    await token_service.record_token_usage(
                        user_id=user_id,
                        session_id="langchain_session",  # 세션 ID 생성 로직 필요
                        message_id=query_id,
                        token_usage=token_usage,
                        model_name=model_name,
                        query_type="text_to_sql",
                        additional_metadata={
                            "question": question,
                            "agent_type": "langchain_openai_functions",
                            "execution_time": time.time() - start_time
                        }
                    )
                    
                    logger.info(
                        f"🔢 토큰 사용량 기록 완료 - 총: {token_usage['total_tokens']}, "
                        f"입력: {token_usage['prompt_tokens']}, 출력: {token_usage['completion_tokens']}"
                    )
            
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
                "simulation_mode": self.enable_simulation,
                "token_usage": token_usage  # 토큰 사용량 정보 포함
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
            
            result = self.execute_query_sync(
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
            result = self.execute_query_sync(question, user_id="test_user", include_debug_info=False)
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