"""
OpenAI Embeddings Provider for Text-to-SQL application.
"""

from typing import Dict, Any, Optional, List
import logging
from openai import AsyncOpenAI

from .base_embeddings import BaseEmbeddings

logger = logging.getLogger(__name__)

class OpenAIEmbeddings(BaseEmbeddings):
    """
    OpenAI embeddings provider implementation.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize OpenAI embeddings provider.
        
        Args:
            config: Configuration dictionary containing OpenAI settings
        """
        super().__init__(config)
        self.client: Optional[AsyncOpenAI] = None
        self.model = config.get("model", "text-embedding-ada-002")
    
    async def initialize(self) -> None:
        """Initialize the OpenAI client."""
        try:
            self.client = AsyncOpenAI(
                api_key=self.config["api_key"]
            )
            logger.info("OpenAI embeddings provider initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI embeddings provider: {e}")
            raise
    
    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embeddings for a single text using OpenAI.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of embedding values
        """
        if not self.client:
            await self.initialize()
        
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=text
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"OpenAI embedding failed: {e}")
            raise
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts using OpenAI.
        
        Args:
            texts: List of input texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not self.client:
            await self.initialize()
        
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            
            return [data.embedding for data in response.data]
            
        except Exception as e:
            logger.error(f"OpenAI batch embedding failed: {e}")
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
        elif "text-embedding-3-small" in self.model:
            return 1536
        elif "text-embedding-3-large" in self.model:
            return 3072
        # Default fallback
        return 1536
    
    async def validate_connection(self) -> bool:
        """
        Validate connection to OpenAI embeddings.
        
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
            logger.error(f"OpenAI embeddings connection validation failed: {e}")
            return False 