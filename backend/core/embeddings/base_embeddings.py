"""
Base Embeddings Provider for Text-to-SQL application.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

class BaseEmbeddings(ABC):
    """
    Abstract base class for embedding providers.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the embeddings provider.
        
        Args:
            config: Configuration dictionary for the provider
        """
        self.config = config
        self.client = None
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the embeddings provider client."""
        pass
    
    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embeddings for a single text.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of embedding values
        """
        pass
    
    @abstractmethod
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of input texts to embed
            
        Returns:
            List of embedding vectors
        """
        pass
    
    @abstractmethod
    async def get_embedding_dimension(self) -> int:
        """
        Get the dimension of the embedding vectors.
        
        Returns:
            Embedding dimension
        """
        pass
    
    @abstractmethod
    async def validate_connection(self) -> bool:
        """
        Validate connection to the embeddings provider.
        
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
                logger.error(f"Error closing embeddings provider connection: {e}")
            finally:
                self.client = None 