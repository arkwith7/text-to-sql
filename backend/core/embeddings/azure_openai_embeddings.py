"""
Azure OpenAI Embeddings Provider for Text-to-SQL application.
"""

from typing import Dict, Any, Optional, List
import logging
from openai import AsyncAzureOpenAI

from .base_embeddings import BaseEmbeddings

logger = logging.getLogger(__name__)

class AzureOpenAIEmbeddings(BaseEmbeddings):
    """
    Azure OpenAI embeddings provider implementation.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Azure OpenAI embeddings provider.
        
        Args:
            config: Configuration dictionary containing Azure OpenAI settings
        """
        super().__init__(config)
        self.client: Optional[AsyncAzureOpenAI] = None
        self.model = config.get("model", "text-embedding-ada-002")
    
    async def initialize(self) -> None:
        """Initialize the Azure OpenAI client."""
        try:
            self.client = AsyncAzureOpenAI(
                api_key=self.config["api_key"],
                api_version=self.config["api_version"],
                azure_endpoint=self.config["endpoint"]
            )
            logger.info("Azure OpenAI embeddings provider initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Azure OpenAI embeddings provider: {e}")
            raise
    
    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embeddings for a single text using Azure OpenAI.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of embedding values
        """
        if not self.client:
            await self.initialize()
        
        try:
            response = await self.client.embeddings.create(
                model=self.config.get("deployment_name", self.model),
                input=text
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"Azure OpenAI embedding failed: {e}")
            raise
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts using Azure OpenAI.
        
        Args:
            texts: List of input texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not self.client:
            await self.initialize()
        
        try:
            response = await self.client.embeddings.create(
                model=self.config.get("deployment_name", self.model),
                input=texts
            )
            
            return [data.embedding for data in response.data]
            
        except Exception as e:
            logger.error(f"Azure OpenAI batch embedding failed: {e}")
            raise
    
    async def get_embedding_dimension(self) -> int:
        """
        Get the dimension of the embedding vectors.
        
        Returns:
            Embedding dimension
        """
        # text-embedding-ada-002 has 1536 dimensions
        if "ada-002" in self.model:
            return 1536
        # Default fallback
        return 1536
    
    async def validate_connection(self) -> bool:
        """
        Validate connection to Azure OpenAI embeddings.
        
        Returns:
            True if connection is valid, False otherwise
        """
        try:
            if not self.client:
                await self.initialize()
            
            # Test with a simple embedding
            await self.embed_text("test")
            
            return True
            
        except Exception as e:
            logger.error(f"Azure OpenAI embeddings connection validation failed: {e}")
            return False 