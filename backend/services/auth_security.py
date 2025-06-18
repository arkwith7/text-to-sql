"""
Authentication security utilities for Text-to-SQL application.
"""

from typing import Dict, Any

def get_openapi_security_schemes() -> Dict[str, Any]:
    """
    Get OpenAPI security schemes for JWT authentication.
    
    Returns:
        Dictionary containing security scheme definitions
    """
    return {
        "JWTBearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter JWT token (without 'Bearer ' prefix)"
        }
    }
