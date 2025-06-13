"""
Base LLM Provider for Text-to-SQL application.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the LLM provider.
        
        Args:
            config: Configuration dictionary for the provider
        """
        self.config = config
        self.client = None
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the LLM provider client."""
        pass
    
    @abstractmethod
    async def generate_completion(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> str:
        """
        Generate text completion.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Generated text completion
        """
        pass
    
    @abstractmethod
    async def generate_chat_completion(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> str:
        """
        Generate chat completion.
        
        Args:
            messages: List of chat messages
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Generated chat completion
        """
        pass
    
    @abstractmethod
    async def validate_connection(self) -> bool:
        """
        Validate connection to the LLM provider.
        
        Returns:
            True if connection is valid, False otherwise
        """
        pass
    
    async def close(self) -> None:
        """Close the provider connection."""
        if self.client:
            try:
                await self.client.close()
            except Exception as e:
                logger.error(f"Error closing LLM provider connection: {e}")
            finally:
                self.client = None 