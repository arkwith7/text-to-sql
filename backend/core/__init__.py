"""
Core package for Text-to-SQL application.
Enhanced with successful patterns from Jupyter notebook testing.

This package provides:
- SQL Agent with PostgreSQL Northwind optimization
- LangChain Function Tools with proven patterns
- Schema Analyzer with real database schema
- SQL Execution Tool with simulation mode
- Latest LangChain Agent implementation
"""

# Configuration은 순환 import 없이 먼저 import
from .config import get_settings

# Tools는 database manager 의존성이 낮으므로 먼저 import
from .tools import (
    SchemaAnalyzerTool,
    SQLExecutionTool,
    setup_langchain_tools,
    get_langchain_tools,
    create_agent_compatible_tools,
    get_tool_descriptions,
    get_database_schema,
    generate_sql_from_question,
    execute_sql_query_sync,
    validate_sql_query
)

# Agents는 database manager 의존성을 Optional로 처리했으므로 나중에 import
try:
    from .agents import BaseAgent, SQLAgent
    _basic_agents_available = True
except ImportError as e:
    _basic_agents_available = False
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Basic agents import 실패: {e}")

# LangChain Agent는 더 복잡한 의존성이 있으므로 가장 나중에 import
try:
    from .agents import LangChainTextToSQLAgent
    _langchain_agent_available = True
except ImportError as e:
    _langchain_agent_available = False
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"LangChain agent import 실패: {e}")

__version__ = "2.0.0"
__author__ = "Text-to-SQL Team"
__description__ = "Enhanced Text-to-SQL Core Package with Jupyter Notebook Proven Patterns"

# 기본 exports (항상 사용 가능)
__all__ = [
    # Configuration
    "get_settings",
    
    # Tools (항상 사용 가능)
    "SchemaAnalyzerTool",
    "SQLExecutionTool",
    "setup_langchain_tools",
    "get_langchain_tools",
    "create_agent_compatible_tools", 
    "get_tool_descriptions",
    
    # LangChain Function Tools
    "get_database_schema",
    "generate_sql_from_question", 
    "execute_sql_query_sync",
    "validate_sql_query",
    
    # Package info
    "__version__",
    "__author__",
    "__description__"
]

# 조건부 exports (import 성공한 경우만)
if _basic_agents_available:
    __all__.extend(["BaseAgent", "SQLAgent"])

if _langchain_agent_available:
    __all__.append("LangChainTextToSQLAgent")

# 패키지 로딩 시 로그 출력
import logging
logger = logging.getLogger(__name__)
logger.info(f"Text-to-SQL Core Package {__version__} 로드 완료")
logger.info("✅ 주피터 노트북에서 검증된 패턴 적용됨")
logger.info("✅ PostgreSQL Northwind 데이터베이스 최적화됨")
logger.info("✅ 최신 LangChain API 지원")

if not _basic_agents_available:
    logger.warning("⚠️ Basic Agents 일부 사용 불가 (의존성 문제)")
if not _langchain_agent_available:
    logger.warning("⚠️ LangChain Agent 사용 불가 (의존성 문제)") 