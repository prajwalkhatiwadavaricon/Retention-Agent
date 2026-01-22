"""
RAG (Retrieval Augmented Generation) Module

This module handles:
1. Text embeddings using Google's text-embedding-004 model
2. Vector store management with ChromaDB
3. Document storage and semantic search
4. LLM-powered query responses

Components:
- embeddings.py: Google embedding service
- vector_store.py: ChromaDB wrapper
- query_engine.py: LLM-powered RAG responses

Usage:
    from rag.vector_store import get_vector_store, store_documents
    from rag.query_engine import query_rag, chat_with_rag
    
    # Store documents
    store_documents(documents)
    
    # Query with LLM response
    result = query_rag("Which client has the highest usage?")
    print(result["answer"])
    
    # Simple chat
    answer = chat_with_rag("Tell me about CS Team")
"""

from rag.embeddings import EmbeddingService, get_embedding_service
from rag.vector_store import ChromaStore, get_vector_store, store_documents
from rag.query_engine import query_rag, chat_with_rag

__all__ = [
    # Embeddings
    "EmbeddingService",
    "get_embedding_service",
    # Vector Store
    "ChromaStore",
    "get_vector_store",
    "store_documents",
    # Query Engine
    "query_rag",
    "chat_with_rag",
]
