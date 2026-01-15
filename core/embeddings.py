"""
Embeddings Provider

- OpenAI Embeddings for LlamaIndex indexing
"""

import os
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core import Settings


def get_embedding_model(model: str = "text-embedding-3-small") -> OpenAIEmbedding:
    """
    Get OpenAI Embedding model for LlamaIndex.
    
    Args:
        model: text-embedding-3-small or text-embedding-3-large
    
    Returns:
        OpenAIEmbedding instance
    """
    embedding = OpenAIEmbedding(
        model=model,
        api_key=os.getenv("OPENAI_API_KEY"),
    )
    Settings.embed_model = embedding
    Settings.chunk_size = 512
    Settings.chunk_overlap = 50
    return embedding