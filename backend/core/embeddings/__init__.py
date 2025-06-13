"""
Embeddings package for Text-to-SQL application.
Supports multiple embedding providers for semantic search and schema matching.
"""

from .openai_embeddings import OpenAIEmbeddings
from .azure_openai_embeddings import AzureOpenAIEmbeddings
from .base_embeddings import BaseEmbeddings

__all__ = ["OpenAIEmbeddings", "AzureOpenAIEmbeddings", "BaseEmbeddings"] 