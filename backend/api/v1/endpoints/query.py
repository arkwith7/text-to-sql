"""
Query endpoints for Text-to-SQL application.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import asyncio
import logging
import uuid

from services.auth_dependencies import get_current_user
from services.auth_service import UserResponse
from core.agents.sql_agent import SQLAgent

logger = logging.getLogger(__name__)

router = APIRouter()

class QueryRequest(BaseModel):
    question: str = Field(
        ..., 
        description="자연어로 된 비즈니스 질문",
        example="가장 많이 팔린 제품 5개는?",
        min_length=1,
        max_length=500
    )
    database: str = Field(
        default="northwind", 
        description="조회할 데이터베이스 이름 (현재는 northwind만 지원)",
        example="northwind"
    )
    context: Optional[str] = Field(
        None, 
        description="추가 컨텍스트나 제약조건 (선택사항)",
        example="2023년 1월부터 6월까지의 데이터만",
        max_length=1000
    )
    include_explanation: bool = Field(
        default=True, 
        description="SQL 쿼리 설명 포함 여부",
        example=True
    )
    max_rows: Optional[int] = Field(
        default=100, 
        description="반환할 최대 행 수 (1-1000 범위)",
        example=100,
        ge=1,
        le=1000
    )

    class Config:
        schema_extra = {
            "examples": [
                {
                    "question": "고객 수를 알려주세요",
                    "database": "northwind",
                    "context": None,
                    "include_explanation": True,
                    "max_rows": 100
                },
                {
                    "question": "카테고리별 제품 수를 보여줘",
                    "database": "northwind", 
                    "context": "제품이 많은 순서대로 정렬",
                    "include_explanation": True,
                    "max_rows": 50
                },
                {
                    "question": "가장 비싼 제품 10개는?",
                    "database": "northwind",
                    "context": None,
                    "include_explanation": False,
                    "max_rows": 10
                },
                {
                    "question": "국가별 고객 분포를 알려줘",
                    "database": "northwind",
                    "context": "고객이 많은 국가 순으로",
                    "include_explanation": True,
                    "max_rows": 25
                },
                {
                    "question": "직원별 담당 주문 수는?",
                    "database": "northwind",
                    "context": "주문 수가 많은 직원부터",
                    "include_explanation": True,
                    "max_rows": 20
                }
            ]
        }

class TokenUsage(BaseModel):
    prompt_tokens: int = Field(description="입력 토큰 수")
    completion_tokens: int = Field(description="출력 토큰 수")
    total_tokens: int = Field(description="총 토큰 수")

class QueryResponse(BaseModel):
    question: str = Field(description="사용자가 입력한 원본 질문")
    sql_query: str = Field(description="생성된 SQL 쿼리문")
    results: List[Dict[str, Any]] = Field(description="쿼리 실행 결과 데이터")
    explanation: Optional[str] = Field(None, description="SQL 쿼리에 대한 자연어 설명")
    execution_time: float = Field(description="쿼리 실행 시간 (초)")
    row_count: int = Field(description="반환된 행의 개수")
    database: str = Field(description="조회한 데이터베이스 이름")
    success: bool = Field(description="쿼리 실행 성공 여부")
    error_message: Optional[str] = Field(None, description="오류 발생 시 오류 메시지")
    token_usage: Optional[TokenUsage] = Field(None, description="토큰 사용량 정보")

    class Config:
        schema_extra = {
            "example": {
                "question": "고객 수를 알려주세요",
                "sql_query": "SELECT COUNT(*) as customer_count FROM customers",
                "results": [{"customer_count": 91}],
                "explanation": "customers 테이블에서 전체 고객 수를 COUNT 함수로 집계하는 쿼리입니다.",
                "execution_time": 0.045,
                "row_count": 1,
                "database": "northwind",
                "success": True,
                "error_message": None,
                "token_usage": {
                    "prompt_tokens": 245,
                    "completion_tokens": 28,
                    "total_tokens": 273
                }
            }
        }

class QueryValidationRequest(BaseModel):
    sql_query: str = Field(
        ..., 
        description="검증할 SQL 쿼리문",
        example="SELECT * FROM customers WHERE country = 'Germany'",
        min_length=1,
        max_length=5000
    )
    database: str = Field(
        default="northwind", 
        description="대상 데이터베이스",
        example="northwind"
    )

    class Config:
        schema_extra = {
            "examples": [
                {
                    "sql_query": "SELECT COUNT(*) FROM customers",
                    "database": "northwind"
                },
                {
                    "sql_query": "SELECT c.categoryname, COUNT(p.productid) FROM categories c JOIN products p ON c.categoryid = p.categoryid GROUP BY c.categoryname",
                    "database": "northwind"
                }
            ]
        }

class QueryValidationResponse(BaseModel):
    is_valid: bool = Field(description="SQL 쿼리 유효성 여부")
    error_message: Optional[str] = Field(None, description="오류 메시지 (유효하지 않은 경우)")
    suggestions: Optional[List[str]] = Field(None, description="개선 제안 사항")

    class Config:
        schema_extra = {
            "example": {
                "is_valid": True,
                "error_message": None,
                "suggestions": ["테이블명을 명시적으로 지정하는 것을 권장합니다"]
            }
        }

@router.post("/", response_model=QueryResponse)
async def execute_query(
    query_request: QueryRequest,
    request: Request,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    자연어 질문을 SQL로 변환하고 실행하여 결과를 반환합니다.
    
    ## 지원하는 질문 유형:
    
    ### 📊 기본 집계 질문
    - "고객 수를 알려주세요"
    - "제품 수는 몇 개인가요?"
    - "총 주문 건수는?"
    
    ### 🏷️ 카테고리별 분석
    - "카테고리별 제품 수를 보여줘"
    - "카테고리별 매출을 알려줘"
    
    ### 🔝 TOP N 질문
    - "가장 비싼 제품 5개는?"
    - "가장 많이 팔린 제품 10개는?"
    - "주문이 많은 고객 상위 10명"
    
    ### 🌍 지역별 분석
    - "국가별 고객 수를 알려줘"
    - "국가별 매출 순위는?"
    
    ### 👥 직원/고객 분석
    - "직원별 담당 주문 수는?"
    - "고객별 주문 횟수를 알려줘"
    
    ## 매개변수 설명:
    
    - **question**: 자연어로 된 비즈니스 질문 (필수)
    - **database**: 조회할 데이터베이스 (기본값: "northwind")
    - **context**: 추가 조건이나 컨텍스트 (선택사항)
    - **include_explanation**: SQL 설명 포함 여부 (기본값: true)
    - **max_rows**: 최대 반환 행 수 (기본값: 100, 최대: 1000)
    
    ## 반환 데이터:
    
    - 생성된 SQL 쿼리
    - 실행 결과 데이터
    - 쿼리 설명 (요청 시)
    - 실행 시간 및 통계
    """
    sql_agent: SQLAgent = request.app.state.sql_agent
    
    try:
        # Execute the query using the agent
        result = await sql_agent.execute_query(
            question=query_request.question,
            database=query_request.database,
            context=query_request.context,
            user_id=current_user.get("id"),
            include_explanation=query_request.include_explanation,
            include_debug_info=True,  # 중간 단계 정보 포함
            max_rows=query_request.max_rows
        )
        
        # 디버그: LangChain Agent 응답 구조 확인
        logger.info(f"🔍 LangChain Agent 응답 키: {list(result.keys())}")
        if "debug_info" in result:
            debug_info = result["debug_info"]
            logger.info(f"🔍 Debug info 키: {list(debug_info.keys())}")
            if "intermediate_steps" in debug_info:
                steps = debug_info["intermediate_steps"]
                logger.info(f"🔍 Intermediate steps 수: {len(steps)}")
                for i, step in enumerate(steps):
                    logger.info(f"🔍 Step {i}: {type(step)}")
                    if isinstance(step, tuple) and len(step) >= 2:
                        action, observation = step[0], step[1]
                        logger.info(f"🔍 Action: {type(action)} - {action}")
                        logger.info(f"🔍 Observation (first 200 chars): {str(observation)[:200]}...")
                        
                        # 더 세부적인 action 정보
                        if hasattr(action, 'tool'):
                            logger.info(f"🔧 Tool name: {action.tool}")
                        if hasattr(action, 'tool_input'):
                            logger.info(f"🔧 Tool input: {action.tool_input}")
                    else:
                        logger.info(f"🔍 Full step: {step}")
        
        # LangChain Agent 응답을 SQL Agent 형식으로 변환
        if "answer" in result and "sql_query" not in result:
            # LangChain Agent 응답 변환
            sql_query = ""
            results = []
            
            # debug_info에서 intermediate_steps 확인
            debug_info = result.get("debug_info", {})
            intermediate_steps = debug_info.get("intermediate_steps", [])
            
            # intermediate_steps에서 SQL과 결과 추출
            for step in intermediate_steps:
                if isinstance(step, tuple) and len(step) >= 2:
                    action, observation = step[0], step[1]
                    
                    # 도구 이름 확인
                    tool_name = ""
                    if hasattr(action, 'tool'):
                        tool_name = str(action.tool)
                    
                    logger.info(f"🛠️ Processing tool: {tool_name}")
                    
                    # SQL 생성 도구 결과 처리
                    if 'generate_sql_from_question' in tool_name:
                        try:
                            import json
                            if isinstance(observation, str):
                                sql_data = json.loads(observation)
                                if "sql_query" in sql_data:
                                    sql_query = sql_data["sql_query"]
                                    logger.info(f"✅ SQL 추출 성공: {sql_query}")
                        except Exception as e:
                            logger.error(f"❌ SQL 추출 실패: {e}")
                    
                    # SQL 실행 도구 결과 처리
                    elif 'execute_sql_query' in tool_name:
                        try:
                            import json
                            if isinstance(observation, str):
                                exec_data = json.loads(observation)
                                if "results" in exec_data and exec_data.get("success"):
                                    results = exec_data["results"]
                                    logger.info(f"✅ 결과 추출 성공: {len(results)}행")
                            elif isinstance(observation, list):
                                results = observation
                                logger.info(f"✅ 직접 결과 추출: {len(results)}행")
                        except Exception as e:
                            logger.error(f"❌ 결과 추출 실패: {e}")
                            # 텍스트 결과를 dict로 변환
                            if isinstance(observation, str) and observation.strip():
                                results = [{"result": observation}]
                                logger.info(f"📝 텍스트 결과 변환: {len(results)}행")
            
            # Agent의 답변에서 SQL 추출 (fallback)
            answer = result.get("answer", "")
            if not sql_query and "```sql" in answer:
                try:
                    sql_start = answer.find("```sql") + 6
                    sql_end = answer.find("```", sql_start)
                    if sql_end > sql_start:
                        sql_query = answer[sql_start:sql_end].strip()
                except:
                    pass
            
            # 결과 변환
            result = {
                "success": result.get("success", True),
                "question": query_request.question,
                "sql_query": sql_query,
                "results": results,
                "answer": answer,  # 원본 답변 유지
                "explanation": answer if query_request.include_explanation else None,
                "execution_time": result.get("execution_time", 0),
                "agent_type": result.get("agent_type", "langchain"),
                "model": result.get("model", "unknown")
            }
        
        # 토큰 사용량 정보 처리
        token_usage_response = None
        if "token_usage" in result and result["token_usage"]:
            token_usage = result["token_usage"]
            token_usage_response = TokenUsage(
                prompt_tokens=token_usage.get("prompt_tokens", 0),
                completion_tokens=token_usage.get("completion_tokens", 0),
                total_tokens=token_usage.get("total_tokens", 0)
            )
            
            # Analytics service를 통해 쿼리 실행 기록
            if hasattr(request.app.state, 'analytics_service'):
                analytics_service = request.app.state.analytics_service
                await analytics_service.log_query_execution_with_tokens(
                    query_id=str(uuid.uuid4()),
                    user_id=current_user.get("id"),
                    question=query_request.question,
                    sql_query=result.get("sql_query", ""),
                    execution_time=result["execution_time"],
                    row_count=len(result.get("results", [])),
                    success=True,
                    error_message=None,
                    chart_type=None,
                    prompt_tokens=token_usage.get("prompt_tokens", 0),
                    completion_tokens=token_usage.get("completion_tokens", 0),
                    total_tokens=token_usage.get("total_tokens", 0),
                    llm_model=result.get("model", "gpt-4o-mini")
                )
        
        return QueryResponse(
            question=query_request.question,
            sql_query=result["sql_query"],
            results=result["results"],
            explanation=result.get("explanation"),
            execution_time=result["execution_time"],
            row_count=len(result["results"]),
            database=query_request.database,
            success=True,
            token_usage=token_usage_response
        )
        
    except Exception as e:
        logger.error(f"Query execution failed: {str(e)}")
        
        # 실패한 쿼리도 analytics에 기록 (토큰 사용량은 0으로)
        if hasattr(request.app.state, 'analytics_service'):
            analytics_service = request.app.state.analytics_service
            
            await analytics_service.log_query_execution_with_tokens(
                query_id=str(uuid.uuid4()),
                user_id=current_user.get("id"),
                question=query_request.question,
                sql_query="",
                execution_time=0.0,
                row_count=0,
                success=False,
                error_message=str(e),
                chart_type=None,
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                llm_model="gpt-4o-mini"
            )
        
        return QueryResponse(
            question=query_request.question,
            sql_query="",
            results=[],
            execution_time=0.0,
            row_count=0,
            database=query_request.database,
            success=False,
            error_message=str(e),
            token_usage=None
        )

@router.post("/validate", response_model=QueryValidationResponse)
async def validate_query(
    validation_request: QueryValidationRequest,
    request: Request,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    SQL 쿼리의 문법과 구조를 검증합니다.
    
    ## 기능:
    - SQL 문법 검증
    - 테이블 및 컬럼 존재 여부 확인
    - 쿼리 구조 분석
    - 개선 제안 제공
    
    ## 사용 예시:
    ```sql
    SELECT COUNT(*) FROM customers
    SELECT c.categoryname, COUNT(p.productid) 
    FROM categories c 
    JOIN products p ON c.categoryid = p.categoryid 
    GROUP BY c.categoryname
    ```
    
    ## 검증 항목:
    - 문법 오류
    - 테이블/컬럼 존재 여부
    - JOIN 조건 유효성
    - 성능 최적화 제안
    """
    sql_agent: SQLAgent = request.app.state.sql_agent
    
    try:
        result = await sql_agent.validate_query(
            sql_query=validation_request.sql_query,
            database=validation_request.database
        )
        
        return QueryValidationResponse(
            is_valid=result["is_valid"],
            error_message=result.get("error_message"),
            suggestions=result.get("suggestions", [])
        )
        
    except Exception as e:
        logger.error(f"Query validation failed: {str(e)}")
        return QueryValidationResponse(
            is_valid=False,
            error_message=str(e)
        )

@router.get("/history")
async def get_query_history(
    request: Request,
    current_user: UserResponse = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0
):
    """Get user's query history."""
    try:
        # This would typically fetch from a database
        # For now, return a placeholder response
        return {
            "queries": [],
            "total": 0,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch query history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch query history"
        )

@router.delete("/history/{query_id}")
async def delete_query_from_history(
    query_id: int,
    request: Request,
    current_user: UserResponse = Depends(get_current_user)
):
    """Delete a query from user's history."""
    try:
        # This would typically delete from a database
        # For now, return a success response
        return {"message": "Query deleted from history"}
        
    except Exception as e:
        logger.error(f"Failed to delete query from history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete query from history"
        )