"""
SQL validation utilities for security and safety
"""
import re
from typing import Dict, Any, List
import structlog

logger = structlog.get_logger(__name__)


class SQLValidator:
    """Validates SQL queries for security and safety"""
    
    # Dangerous SQL keywords that should be blocked
    DANGEROUS_KEYWORDS = [
        'DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE', 
        'TRUNCATE', 'REPLACE', 'MERGE', 'GRANT', 'REVOKE'
    ]
    
    # Allowed SQL keywords for SELECT queries
    ALLOWED_KEYWORDS = [
        'SELECT', 'FROM', 'WHERE', 'JOIN', 'INNER', 'LEFT', 'RIGHT', 
        'OUTER', 'ON', 'GROUP', 'BY', 'ORDER', 'HAVING', 'UNION', 
        'DISTINCT', 'AS', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END',
        'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'LIMIT', 'OFFSET'
    ]
    
    def validate_query(self, query: str) -> Dict[str, Any]:
        """
        Comprehensive SQL query validation
        Returns validation result with details
        """
        try:
            # Clean and normalize query
            cleaned_query = query.strip()
            if not cleaned_query:
                return {'is_valid': False, 'error': 'Empty query'}
            
            # Basic format validation
            basic_check = self._basic_validation(cleaned_query)
            if not basic_check['is_valid']:
                return basic_check
            
            # Security validation
            security_check = self._security_validation(cleaned_query)
            if not security_check['is_valid']:
                return security_check
            
            # Syntax validation
            syntax_check = self._syntax_validation(cleaned_query)
            if not syntax_check['is_valid']:
                return syntax_check
            
            return {
                'is_valid': True,
                'cleaned_query': cleaned_query,
                'validation_notes': []
            }
            
        except Exception as e:
            logger.error("Query validation error", query=query, error=str(e))
            return {'is_valid': False, 'error': f'Validation error: {str(e)}'}
    
    def _basic_validation(self, query: str) -> Dict[str, Any]:
        """Basic query format validation"""
        query_upper = query.upper().strip()
        
        # Must start with SELECT
        if not query_upper.startswith('SELECT'):
            return {
                'is_valid': False,
                'error': 'Only SELECT queries are allowed'
            }
        
        # Check for SQL injection patterns
        injection_patterns = [
            r';\s*(DROP|DELETE|UPDATE|INSERT)',
            r'UNION\s+ALL\s+SELECT',
            r'--\s*\w+',
            r'/\*.*?\*/',
            r'xp_cmdshell',
            r'sp_executesql'
        ]
        
        for pattern in injection_patterns:
            if re.search(pattern, query_upper, re.IGNORECASE):
                return {
                    'is_valid': False,
                    'error': 'Potential SQL injection detected'
                }
        
        return {'is_valid': True}
    
    def _security_validation(self, query: str) -> Dict[str, Any]:
        """Security-focused validation"""
        query_upper = query.upper()
        
        # Check for dangerous keywords
        for keyword in self.DANGEROUS_KEYWORDS:
            if re.search(r'\b' + keyword + r'\b', query_upper):
                return {
                    'is_valid': False,
                    'error': f'Dangerous keyword detected: {keyword}'
                }
        
        # Check for system functions
        system_functions = [
            'USER', 'CURRENT_USER', 'SESSION_USER', 'SYSTEM_USER',
            'VERSION', 'DATABASE', 'SCHEMA'
        ]
        
        for func in system_functions:
            if re.search(r'\b' + func + r'\s*\(', query_upper):
                return {
                    'is_valid': False,
                    'error': f'System function not allowed: {func}'
                }
        
        return {'is_valid': True}
    
    def _syntax_validation(self, query: str) -> Dict[str, Any]:
        """Basic SQL syntax validation"""
        # Check for balanced parentheses
        if query.count('(') != query.count(')'):
            return {
                'is_valid': False,
                'error': 'Unbalanced parentheses'
            }
        
        # Check for balanced quotes
        single_quotes = query.count("'")
        if single_quotes % 2 != 0:
            return {
                'is_valid': False,
                'error': 'Unbalanced single quotes'
            }
        
        double_quotes = query.count('"')
        if double_quotes % 2 != 0:
            return {
                'is_valid': False,
                'error': 'Unbalanced double quotes'
            }
        
        return {'is_valid': True}


class DataValidator:
    """Validates data formats and types"""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_password(password: str) -> Dict[str, Any]:
        """Validate password strength"""
        if len(password) < 8:
            return {'is_valid': False, 'error': 'Password must be at least 8 characters'}
        
        if not re.search(r'[A-Za-z]', password):
            return {'is_valid': False, 'error': 'Password must contain letters'}
        
        if not re.search(r'\d', password):
            return {'is_valid': False, 'error': 'Password must contain numbers'}
        
        return {'is_valid': True}
    
    @staticmethod
    def sanitize_input(input_str: str) -> str:
        """Sanitize user input"""
        if not isinstance(input_str, str):
            return str(input_str)
        
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\';]', '', input_str)
        return sanitized.strip()
