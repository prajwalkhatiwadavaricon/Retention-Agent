"""
RAG Query Engine - Generates proper LLM responses from retrieved documents.

Handles various query types:
- Client-specific: "Tell me about CS Team"
- Date/Week range: "What happened in week 3?"
- Usage questions: "Which client has highest usage?"
- Bug questions: "What bugs are affecting clients?"
- Trend questions: "Which clients have declining trends?"
- Module questions: "Who uses Timesheets the most?"
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

from core.config import GOOGLE_API_KEY, MODEL_NAME
from rag.vector_store import get_vector_store


RAG_QUERY_SYSTEM_PROMPT = """You are a knowledgeable Customer Success Assistant for Varicon, a civil construction SaaS platform.
You have access to detailed client usage data, bug reports, and trend analysis.

## DATA AVAILABILITY - IMPORTANT:

**FULL DATA CLIENTS (Usage + JIRA Bugs):**
- Development
- Construction KaT (also "Contruction KaT")
- UB Civil

These 3 clients have complete data. Answer ALL questions about them including bugs/issues.

**USAGE DATA ONLY CLIENTS (19 others):**
All other clients have usage data but NO JIRA bug reports.
When asked about bugs/issues for these clients, respond: "I have usage data for [client], but no JIRA bug reports are available. Only Development, Construction KaT, and UB Civil have bug tracking data."

**TOTAL CLIENTS: 22**

## CLIENT REPRESENTATIVES:
Each client may have assigned representatives in their data. If not assigned, say: "This client does not have an assigned representative yet."

YOUR ROLE:
- Answer questions accurately based ONLY on the provided context
- Be specific with numbers, dates, percentages, and client names
- If comparing clients, provide concrete metrics
- If asked about a specific client, focus entirely on that client
- If the context doesn't have the answer, say "I don't have that specific information"
- For bug/JIRA questions about non-full-data clients, explain the data limitation

RESPONSE STYLE:
- Be conversational but professional
- Lead with the direct answer, then provide supporting details
- Use bullet points for lists
- Include specific numbers to back up statements
- Keep responses focused and concise (2-4 paragraphs max)

NEVER:
- Make up data that isn't in the context
- Give vague answers when specific data is available
- Ignore the question and just summarize everything
- Claim bug data exists for clients that don't have it
"""

RAG_QUERY_TEMPLATE = """
## Retrieved Client Data:
{context}

## Question:
{question}

## Instructions:
Answer the question directly based on the context above.

**General Questions:**
- "How many clients?" → 22 total (3 with full data, 19 usage-only)
- "List all clients" → Use the ALL CLIENTS USAGE SUMMARY table from context
- "List clients in tabular format" → Format as a table with: Client Name | Total Usage | Modules | Has JIRA
- "Which client assigned to whom?" → Check client_representatives field

**Client-Specific:**
- If asking about a specific client → focus on that client's data
- If asking "which client" → compare and identify the one that matches

**Bug/JIRA Questions:**
- If asking about bugs for Development/Construction KaT/UB Civil → provide full details
- If asking about bugs for OTHER clients → "No JIRA data available for this client"
- "How many JIRA cards for [client]?" → Count if available, else explain limitation

**Analysis Questions:**
- If asking about trends → describe the pattern with numbers
- If asking about modules → name the modules with usage counts
- If asking about a time period/week → cite data from that specific period

**Representatives:**
- If client has representatives → list name and email
- If no representatives assigned → "Not assigned yet"

Provide a clear, helpful answer:"""


def get_llm() -> ChatGoogleGenerativeAI:
    """Initialize the Gemini model for RAG responses."""
    return ChatGoogleGenerativeAI(
        model=MODEL_NAME,
        google_api_key=GOOGLE_API_KEY,
        temperature=0.3,
    )


def determine_query_type(question: str) -> tuple[str, int]:
    """
    Determine the type of query and optimal number of documents to retrieve.
    
    Returns:
        (query_type, num_docs)
    """
    question_lower = question.lower()
    
    # List all clients queries - need the summary documents
    if any(list_keyword in question_lower for list_keyword in [
        "list all", "all clients", "all the clients", "how many clients",
        "list clients", "show all", "tabular format", "table format",
        "every client", "total clients", "client list"
    ]):
        return "all_clients", 3  # Get all_clients and client_list docs
    
    # Client-specific queries - need fewer but focused docs
    if any(client_keyword in question_lower for client_keyword in [
        "tell me about", "what about", "how is", "details on", "info on"
    ]):
        return "client_specific", 5  # Get all sections for that client
    
    # Comparison queries - need docs from multiple clients
    if any(compare_keyword in question_lower for compare_keyword in [
        "which client", "who has", "compare", "highest", "lowest", 
        "most", "least", "best", "worst"
    ]):
        return "comparison", 6
    
    # Bug-related queries
    if any(bug_keyword in question_lower for bug_keyword in [
        "bug", "issue", "problem", "error", "ticket", "jira"
    ]):
        return "bugs", 5
    
    # Trend queries
    if any(trend_keyword in question_lower for trend_keyword in [
        "trend", "declining", "increasing", "growing", "dropping",
        "over time", "pattern", "change"
    ]):
        return "trends", 5
    
    # Module queries
    if any(module_keyword in question_lower for module_keyword in [
        "timesheet", "claims", "tasks", "purchase order", "module",
        "feature", "delivery", "site diary", "bills"
    ]):
        return "modules", 5
    
    # Week/date range queries
    if any(date_keyword in question_lower for date_keyword in [
        "week", "month", "period", "date", "when", "november", "december", "january"
    ]):
        return "temporal", 4
    
    # Default
    return "general", 4


def query_rag(question: str, k: int = None) -> dict:
    """
    Query the RAG system and get an LLM-generated response.
    
    Args:
        question: User's question
        k: Number of documents to retrieve (auto-determined if not specified)
        
    Returns:
        dict with:
            - answer: LLM-generated response
            - sources: List of client names used as context
            - query_type: Type of query detected
            - success: Whether the query succeeded
    """
    try:
        # Step 1: Determine query type and doc count
        query_type, auto_k = determine_query_type(question)
        k = k or auto_k
        
        # Step 2: Retrieve relevant documents
        store = get_vector_store()
        
        if store.count() == 0:
            return {
                "answer": "No data available. Please run the retention analysis first to populate the knowledge base.",
                "sources": [],
                "query_type": query_type,
                "success": False
            }
        
        results = store.search(question, k=k)
        
        if not results:
            return {
                "answer": "I couldn't find any relevant information for your question. Try rephrasing or asking about specific clients, modules, or time periods.",
                "sources": [],
                "query_type": query_type,
                "success": False
            }
        
        # Step 3: Build context from retrieved documents
        context_parts = []
        sources = set()
        section_types = set()
        
        for doc in results:
            content = doc.get("content", "")
            metadata = doc.get("metadata", {})
            client_name = metadata.get("client_name", "Unknown")
            section_type = metadata.get("section_type", "general")
            
            # Add section header for clarity
            context_parts.append(f"--- {client_name} ({section_type}) ---\n{content}\n")
            sources.add(client_name)
            section_types.add(section_type)
        
        context = "\n".join(context_parts)
        
        # Step 4: Generate LLM response
        prompt = RAG_QUERY_TEMPLATE.format(
            context=context,
            question=question
        )
        
        llm = get_llm()
        messages = [
            SystemMessage(content=RAG_QUERY_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ]
        
        response = llm.invoke(messages)
        
        return {
            "answer": response.content,
            "sources": sorted(list(sources)),
            "query_type": query_type,
            "sections_used": sorted(list(section_types)),
            "success": True
        }
        
    except Exception as e:
        return {
            "answer": f"Error processing query: {str(e)}",
            "sources": [],
            "query_type": "error",
            "success": False
        }


def chat_with_rag(question: str) -> str:
    """
    Simple interface for chatting with RAG.
    
    Args:
        question: User's question
        
    Returns:
        LLM-generated answer string
    """
    result = query_rag(question)
    return result["answer"]


# Convenience functions for specific query types
def ask_about_client(client_name: str) -> str:
    """Get comprehensive info about a specific client."""
    return chat_with_rag(f"Tell me everything about {client_name}")


def get_highest_usage_client() -> str:
    """Find the client with highest usage."""
    return chat_with_rag("Which client has the highest total usage and activities?")


def get_at_risk_clients() -> str:
    """Get clients with concerning trends."""
    return chat_with_rag("Which clients have declining or decreasing usage trends?")


def get_bug_impact() -> str:
    """Get information about bugs affecting clients."""
    return chat_with_rag("What bugs are affecting clients and what is their impact?")
