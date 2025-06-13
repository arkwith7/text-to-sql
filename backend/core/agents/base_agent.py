"""
Base Agent for Text-to-SQL application.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime

from core.config import get_settings

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """
    Abstract base class for AI agents.
    """
    
    def __init__(self, db_manager=None):
        """
        Initialize the base agent.
        
        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
        self.settings = get_settings()
    
    @abstractmethod
    async def execute_query(
        self,
        question: str,
        database: str = "northwind",
        context: Optional[str] = None,
        user_id: Optional[int] = None,
        include_explanation: bool = True,
        max_rows: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute a natural language query and return results.
        
        Args:
            question: Natural language question
            database: Target database name
            context: Additional context for the query
            user_id: User ID for logging and analytics
            include_explanation: Whether to include SQL explanation
            max_rows: Maximum number of rows to return
            
        Returns:
            Dictionary containing query results and metadata
        """
        pass
    
    @abstractmethod
    async def validate_query(
        self,
        sql_query: str,
        database: str = "northwind"
    ) -> Dict[str, Any]:
        """
        Validate SQL query syntax and structure.
        
        Args:
            sql_query: SQL query to validate
            database: Target database name
            
        Returns:
            Dictionary containing validation results
        """
        pass 