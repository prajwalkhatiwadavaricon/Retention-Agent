"""
FastAPI Server for Varicon Retention Analysis RAG.

Provides endpoints to:
1. Query the RAG system with natural language questions
2. Get client-specific information
3. Health check

Usage:
    uvicorn api.server:app --reload --port 8000
    
Or run via:
    python -m api.server
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import uvicorn
import uuid

from rag.query_engine import (
    query_rag, 
    chat_with_rag,
    ask_about_client,
    get_highest_usage_client,
    get_at_risk_clients,
    get_bug_impact,
)
from rag.vector_store import get_vector_store


# FastAPI app
app = FastAPI(
    title="Varicon Retention RAG API",
    description="""
    Query client retention data using natural language.
    
    ## Supported Query Types
    - **Client-specific**: "Tell me about CS Team", "What's happening with NEWMYOB?"
    - **Comparisons**: "Which client has the highest usage?", "Who is most at risk?"
    - **Trends**: "Which clients have declining usage?", "Show me usage patterns"
    - **Bugs**: "What bugs are affecting clients?", "Any issues with CS Team?"
    - **Modules**: "Who uses Timesheets the most?", "Which modules are popular?"
    - **Time-based**: "What happened in week 3?", "Recent activity?"
    """,
    version="1.0.0",
)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class QueryRequest(BaseModel):
    """Request model for RAG queries."""
    question: str = Field(..., description="Your question about client data", min_length=3)
    num_sources: Optional[int] = Field(None, description="Number of sources (auto-determined if not set)", ge=1, le=10)
    
    class Config:
        json_schema_extra = {
            "examples": [
                {"question": "Which client has the highest usage?"},
                {"question": "Tell me about CS Team"},
                {"question": "What bugs are affecting clients?"},
                {"question": "Which clients have declining trends?"},
            ]
        }


class QueryResponse(BaseModel):
    """Response model for RAG queries."""
    answer: str = Field(..., description="LLM-generated answer")
    sources: list[str] = Field(..., description="Client names used as context")
    query_type: str = Field(..., description="Detected query type")
    success: bool = Field(..., description="Whether the query succeeded")


class ChatRequest(BaseModel):
    """Simple chat request."""
    message: str = Field(..., description="Your message", min_length=3)


class ChatResponse(BaseModel):
    """Simple chat response with UUID."""
    id: str = Field(..., description="Unique response ID (UUID)")
    content: str = Field(..., description="Assistant's response")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    documents_count: int
    collection_name: str
    ready: bool


class ClientListResponse(BaseModel):
    """List of clients in the knowledge base."""
    clients: list[str]
    count: int


class ClientInfoRequest(BaseModel):
    """Request for client-specific info."""
    client_name: str = Field(..., description="Name of the client")


# Endpoints
@app.get("/", tags=["Info"])
async def root():
    """Welcome message with available endpoints."""
    return {
        "message": "🚀 Varicon Retention RAG API",
        "description": "Query client retention data using natural language",
        "docs": "/docs",
        "endpoints": {
            "POST /query": "Full query with sources and query type",
            "POST /chat": "Simple chat (message → response)",
            "POST /client": "Get info about a specific client",
            "GET /health": "Health check",
            "GET /clients": "List all clients",
            "GET /quick/highest-usage": "Quick: highest usage client",
            "GET /quick/at-risk": "Quick: at-risk clients",
            "GET /quick/bugs": "Quick: bug impact summary",
        },
        "example_questions": [
            "Which client has the highest usage?",
            "Tell me about CS Team",
            "What bugs are affecting clients?",
            "Which clients have declining trends?",
            "Who uses Timesheets the most?",
        ]
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Check if the RAG system is ready."""
    try:
        store = get_vector_store()
        count = store.count()
        
        return HealthResponse(
            status="healthy" if count > 0 else "empty",
            documents_count=count,
            collection_name=store.collection_name,
            ready=count > 0
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@app.get("/clients", response_model=ClientListResponse, tags=["Data"])
async def list_clients():
    """List all clients in the knowledge base."""
    try:
        store = get_vector_store()
        docs = store.get_all_documents()
        
        clients = []
        for doc in docs:
            client_name = doc.get("metadata", {}).get("client_name")
            if client_name and client_name not in clients:
                clients.append(client_name)
        
        return ClientListResponse(
            clients=sorted(clients),
            count=len(clients)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query", response_model=QueryResponse, tags=["RAG"])
async def query_endpoint(request: QueryRequest):
    """
    Query the RAG system with a natural language question.
    
    Returns an LLM-generated answer based on retrieved client data.
    The system automatically detects the query type and retrieves appropriate documents.
    
    **Supported query types:**
    - `client_specific`: Questions about a specific client
    - `comparison`: Comparing clients (highest, lowest, best, worst)
    - `bugs`: Bug-related questions
    - `trends`: Usage trend questions
    - `modules`: Module-specific questions
    - `temporal`: Time/week-based questions
    """
    result = query_rag(request.question, k=request.num_sources)
    
    return QueryResponse(
        answer=result["answer"],
        sources=result["sources"],
        query_type=result.get("query_type", "general"),
        success=result["success"]
    )


@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat_endpoint(request: ChatRequest):
    """
    Simple chat interface - just send a message and get a response.
    
    This is a simplified version of /query that only returns the answer.
    Returns a unique UUID with each response.
    """
    response = chat_with_rag(request.message)
    return ChatResponse(
        id=str(uuid.uuid4()),
        content=response
    )


@app.post("/client", response_model=ChatResponse, tags=["Client"])
async def client_info_endpoint(request: ClientInfoRequest):
    """
    Get comprehensive information about a specific client.
    
    Returns all available data about the client including:
    - Usage statistics
    - Active modules
    - Bug impact
    - Trends
    """
    response = ask_about_client(request.client_name)
    return ChatResponse(
        id=str(uuid.uuid4()),
        content=response
    )


# Quick access endpoints
@app.get("/quick/highest-usage", response_model=ChatResponse, tags=["Quick Queries"])
async def quick_highest_usage():
    """Quick query: Which client has the highest usage?"""
    response = get_highest_usage_client()
    return ChatResponse(
        id=str(uuid.uuid4()),
        content=response
    )


@app.get("/quick/at-risk", response_model=ChatResponse, tags=["Quick Queries"])
async def quick_at_risk():
    """Quick query: Which clients are at risk (declining trends)?"""
    response = get_at_risk_clients()
    return ChatResponse(
        id=str(uuid.uuid4()),
        content=response
    )


@app.get("/quick/bugs", response_model=ChatResponse, tags=["Quick Queries"])
async def quick_bugs():
    """Quick query: What bugs are affecting clients?"""
    response = get_bug_impact()
    return ChatResponse(
        id=str(uuid.uuid4()),
        content=response
    )


# Run server directly
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 Starting Varicon Retention RAG API Server")
    print("=" * 60)
    print("\n📍 Main Endpoints:")
    print("   POST /query  - Full query with sources")
    print("   POST /chat   - Simple chat")
    print("   POST /client - Client-specific info")
    print("\n⚡ Quick Queries:")
    print("   GET /quick/highest-usage")
    print("   GET /quick/at-risk")
    print("   GET /quick/bugs")
    print("\n📚 Docs: http://localhost:8000/docs")
    print("=" * 60 + "\n")
    
    uvicorn.run(
        "api.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
