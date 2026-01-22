"""State definitions for the LangGraph workflow."""

from typing import TypedDict, Annotated
from operator import add


def merge_errors(left: list[str] | None, right: list[str] | None) -> list[str]:
    """Merge error lists from multiple agents."""
    left = left or []
    right = right or []
    return left + right


class RetentionState(TypedDict, total=False):
    """
    State object that flows through the LangGraph workflow.
    
    This state is shared across all agents in parallel execution.
    
    IMPORTANT: Agents should only return NEW keys they produce,
    not spread the entire state. This prevents parallel execution conflicts.
    
    Flow:
    1. Input JSONs loaded into state (immutable during workflow)
    2. Analysis Agent + RAG Agent run in PARALLEL
       - Both read: usage_data, jira_tickets
       - Analysis writes: analysis_results, risky_clients, raw_llm_response
       - RAG writes: rag_documents, rag_text, rag_ready
    3. Email Agent runs if risky_clients exist
       - Reads: risky_clients
       - Writes: emails_to_send, email_summary, emails_generated
    """
    
    # ============== INPUT DATA ==============
    # Set at workflow start, read-only during execution
    usage_data: list[dict]      # Raw 12-week usage data from JSON
    jira_tickets: list[dict]    # Raw JIRA ticket data from JSON
    
    # ============== ANALYSIS AGENT OUTPUTS ==============
    # Uses: ANALYSIS_PROMPT + LLM
    # Produces risk assessment per client
    analysis_results: list[dict]    # Full analysis per client (from LLM)
    risky_clients: list[dict]       # Filtered: high/medium risk only
    raw_llm_response: str           # Raw LLM response for debugging
    
    # ============== RAG AGENT OUTPUTS ==============
    # Uses: RAG_PROMPT + LLM
    # Converts JSON to text for embeddings
    rag_documents: list[dict]   # Parsed documents ready for ChromaDB
    rag_text: str               # Full text output from LLM
    rag_ready: bool             # Flag: RAG prep complete
    
    # ============== EMAIL AGENT OUTPUTS ==============
    # Uses: EMAIL_PROMPT + templates + LLM
    # Generates personalized emails for risky clients
    emails_to_send: list[dict]  # Formatted email notifications
    email_summary: str          # Summary of email actions
    emails_generated: bool      # Flag: emails generated
    
    # ============== WORKFLOW METADATA ==============
    workflow_status: str        # Current workflow status
    # Use Annotated to allow multiple agents to append errors
    errors: Annotated[list[str], merge_errors]
