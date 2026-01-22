"""
Vector store using ChromaDB for document storage and retrieval.

For small datasets, we use ChromaDB's persistent local storage
which is simple to set up and efficient for our use case.
"""

import chromadb
from chromadb.config import Settings

from core.config import RAG_CONFIG
from rag.embeddings import get_embedding_service


class ChromaStore:
    """
    ChromaDB vector store for RAG documents.
    
    Usage:
        store = ChromaStore()
        store.add_documents(documents)
        results = store.search("query text", k=5)
    """
    
    def __init__(self, collection_name: str | None = None):
        """
        Initialize ChromaDB with persistent storage.
        
        Args:
            collection_name: Name of the collection (default from config)
        """
        self.collection_name = collection_name or RAG_CONFIG.get(
            "collection_name", "retention_documents"
        )
        
        # Use persistent storage in ./chroma_db folder
        self.client = chromadb.PersistentClient(
            path="./chroma_db",
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Check if collection exists and has wrong distance metric
        self._ensure_cosine_collection()
        
        # Initialize embedding service
        self.embedding_service = get_embedding_service()
    
    def _ensure_cosine_collection(self):
        """Ensure collection exists with cosine similarity metric."""
        try:
            # Try to get existing collection
            existing = self.client.get_collection(name=self.collection_name)
            metadata = existing.metadata or {}
            
            # Check if it's using cosine similarity
            if metadata.get("hnsw:space") != "cosine":
                print(f"   🔄 Recreating collection with cosine similarity...")
                self.client.delete_collection(name=self.collection_name)
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={
                        "description": "Varicon client retention analysis documents",
                        "hnsw:space": "cosine"
                    }
                )
            else:
                self.collection = existing
        except Exception:
            # Collection doesn't exist, create it
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={
                    "description": "Varicon client retention analysis documents",
                    "hnsw:space": "cosine"
                }
            )
        
        print(f"   💾 ChromaDB initialized: {self.collection_name}")
        print(f"   📊 Current documents: {self.collection.count()}")
    
    def add_documents(self, documents: list[dict]) -> int:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of dicts with:
                - id: unique identifier
                - content: text content
                - metadata: additional info
        
        Returns:
            Number of documents added
        """
        if not documents:
            return 0
        
        ids = []
        texts = []
        metadatas = []
        
        for doc in documents:
            ids.append(doc["id"])
            texts.append(doc["content"])
            metadatas.append(doc.get("metadata", {}))
        
        # Generate embeddings
        print(f"   🔄 Generating embeddings for {len(texts)} documents...")
        embeddings = self.embedding_service.embed_texts(texts)
        
        # Add to ChromaDB
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )
        
        print(f"   ✅ Added {len(documents)} documents to ChromaDB")
        return len(documents)
    
    def search(self, query: str, k: int = 5) -> list[dict]:
        """
        Search for similar documents using semantic search.
        
        Args:
            query: Search query text
            k: Number of results to return
            
        Returns:
            List of similar documents with scores
        """
        # Generate query embedding
        query_embedding = self.embedding_service.embed_text(query)
        
        # Search in ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        documents = []
        if results and results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                documents.append({
                    "id": doc_id,
                    "content": results["documents"][0][i] if results["documents"] else "",
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else 0,
                })
        
        return documents
    
    def search_by_client(self, client_name: str, k: int = 5) -> list[dict]:
        """
        Search for documents related to a specific client.
        
        Args:
            client_name: Name of the client
            k: Number of results
            
        Returns:
            Documents related to this client
        """
        return self.search(f"Client: {client_name}", k)
    
    def get_all_documents(self) -> list[dict]:
        """Get all documents in the collection."""
        results = self.collection.get(
            include=["documents", "metadatas"]
        )
        
        documents = []
        if results and results["ids"]:
            for i, doc_id in enumerate(results["ids"]):
                documents.append({
                    "id": doc_id,
                    "content": results["documents"][i] if results["documents"] else "",
                    "metadata": results["metadatas"][i] if results["metadatas"] else {},
                })
        
        return documents
    
    def delete_all(self) -> None:
        """Delete all documents in the collection."""
        # Get all IDs
        all_docs = self.collection.get()
        if all_docs and all_docs["ids"]:
            self.collection.delete(ids=all_docs["ids"])
            print(f"   🗑️ Deleted {len(all_docs['ids'])} documents")
    
    def count(self) -> int:
        """Get the number of documents in the collection."""
        return self.collection.count()


# Singleton instance
_vector_store = None


def get_vector_store(collection_name: str | None = None) -> ChromaStore:
    """Get the singleton vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = ChromaStore(collection_name)
    return _vector_store


def store_documents(documents: list[dict]) -> int:
    """
    Convenience function to store documents.
    
    Called by RAG agent after preparing documents.
    
    Args:
        documents: Documents from rag_prep_agent
        
    Returns:
        Number of documents stored
    """
    store = get_vector_store()
    return store.add_documents(documents)
