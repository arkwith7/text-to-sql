"""
Azure OpenAI Provider for Text-to-SQL application.
"""

from typing import Dict, Any, Optional, List
import logging
from openai import AsyncAzureOpenAI

from .base_provider import BaseLLMProvider

logger = logging.getLogger(__name__)

class AzureOpenAIProvider(BaseLLMProvider):
    """
    Azure OpenAI provider implementation.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Azure OpenAI provider.
        
        Args:
            config: Configuration dictionary containing Azure OpenAI settings
        """
        super().__init__(config)
        self.client: Optional[AsyncAzureOpenAI] = None
    
    async def initialize(self) -> None:
        """Initialize the Azure OpenAI client."""
        try:
            self.client = AsyncAzureOpenAI(
                api_key=self.config["api_key"],
                api_version=self.config["api_version"],
                azure_endpoint=self.config["endpoint"]
            )
            logger.info("Azure OpenAI provider initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Azure OpenAI provider: {e}")
            raise
    
    async def generate_completion(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> str:
        """
        Generate text completion using Azure OpenAI.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional parameters
            
        Returns:
            Generated text completion
        """
        if not self.client:
            await self.initialize()
        
        try:
            response = await self.client.completions.create(
                model=self.config["deployment_name"],
                prompt=prompt,
                max_tokens=max_tokens or 1000,
                temperature=temperature or 0.1,
                **kwargs
            )
            
            return response.choices[0].text.strip()
            
        except Exception as e:
            logger.error(f"Azure OpenAI completion failed: {e}")
            raise
    
    async def generate_chat_completion(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        return_usage_info: bool = False,
        **kwargs
    ) -> str | Dict[str, Any]:
        """
        Generate chat completion using Azure OpenAI.
        
        Args:
            messages: List of chat messages
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            return_usage_info: If True, returns dict with content and token usage
            **kwargs: Additional parameters
            
        Returns:
            Generated chat completion (str) or dict with content and usage info
        """
        if not self.client:
            await self.initialize()
        
        try:
            response = await self.client.chat.completions.create(
                model=self.config["deployment_name"],
                messages=messages,
                max_tokens=max_tokens or 1000,
                temperature=temperature or 0.1,
                **kwargs
            )
            
            content = response.choices[0].message.content.strip()
            
            if return_usage_info:
                # Extract token usage information
                usage_info = {
                    "content": content,
                    "token_usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    },
                    "model": response.model,
                    "finish_reason": response.choices[0].finish_reason
                }
                
                logger.info(
                    f"Azure OpenAI token usage - Prompt: {usage_info['token_usage']['prompt_tokens']}, "
                    f"Completion: {usage_info['token_usage']['completion_tokens']}, "
                    f"Total: {usage_info['token_usage']['total_tokens']}"
                )
                
                return usage_info
            
            return content
            
        except Exception as e:
            logger.error(f"Azure OpenAI chat completion failed: {e}")
            raise
    
    async def validate_connection(self) -> bool:
        """
        Validate connection to Azure OpenAI.
        
        Returns:
            True if connection is valid, False otherwise
        """
        try:
            if not self.client:
                await self.initialize()
            
            # Test with a simple completion
            await self.generate_chat_completion([
                {"role": "user", "content": "Hello"}
            ], max_tokens=5)
            
            return True
            
        except Exception as e:
            logger.error(f"Azure OpenAI connection validation failed: {e}")
            return False 