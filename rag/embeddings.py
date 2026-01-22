"""
Embedding service using Google's text-embedding model.

For small datasets, we use Google's embedding model directly
which provides high-quality embeddings for semantic search.
"""

from langchain_google_genai import GoogleGenerativeAIEmbeddings

from core.config import GOOGLE_API_KEY, RAG_CONFIG


class EmbeddingService:
    """
    Embedding service using Google's text-embedding model.
    
    Usage:
        service = EmbeddingService()
        embedding = service.embed_text("Hello world")
        embeddings = service.embed_texts(["text1", "text2"])
    """
    
    def __init__(self):
        """Initialize the embedding service."""
        self.model_name = RAG_CONFIG.get("embedding_model", "models/text-embedding-004")
        
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=self.model_name,
            google_api_key=GOOGLE_API_KEY,
        )
        print(f"   📐 Embedding model initialized: {self.model_name}")
    
    def embed_text(self, text: str) -> list[float]:
        """
        Create embedding for a single text.
        
        Args:
            text: Text string to embed
            
        Returns:
            Embedding vector as list of floats
        """
        return self.embeddings.embed_query(text)
    
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Create embeddings for multiple texts.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
        """
        return self.embeddings.embed_documents(texts)


# Singleton instance
_embedding_service = None


def get_embedding_service() -> EmbeddingService:
    """Get the singleton embedding service instance."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
