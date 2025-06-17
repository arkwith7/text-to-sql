"""
Core agents package for Text-to-SQL application.
Enhanced with successful patterns from Jupyter notebook testing.
"""

from .base_agent import BaseAgent
from .sql_agent import SQLAgent

try:
    from .langchain_agent import LangChainTextToSQLAgent
    _langchain_available = True
except ImportError as e:
    _langchain_available = False
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"LangChain agent not available: {e}")

__all__ = [
    "BaseAgent", 
    "SQLAgent"
]

if _langchain_available:
    __all__.append("LangChainTextToSQLAgent")