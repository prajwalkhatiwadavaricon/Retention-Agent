"""LangGraph workflow definition for Retention Analysis."""

from langgraph.graph import StateGraph, END, START

from graph.state import RetentionState
from agents.analysis_agent import analysis_agent
from agents.rag_agent import rag_prep_agent
from agents.email_agent import email_agent, should_send_emails


def create_workflow() -> StateGraph:
    """
    Create the LangGraph workflow for retention analysis.
    
    Workflow Structure (TRUE PARALLEL):
    
                      ┌─────────────────┐
                      │      START      │
                      └────────┬────────┘
                               │
           ┌───────────────────┴───────────────────┐
           │                                       │
           ▼                                       ▼
    ┌─────────────────┐                   ┌─────────────────┐
    │ Analysis Agent  │    (PARALLEL)     │   RAG Agent     │
    │  (LLM → Risk)   │                   │ (JSON → Text)   │
    └────────┬────────┘                   └────────┬────────┘
             │                                     │
             ▼                                     ▼
    ┌─────────────────┐                   ┌─────────────────┐
    │ Check for Risks │                   │   Embeddings    │
    │  (Conditional)  │                   │  (ChromaDB)     │
    └────────┬────────┘                   └────────┬────────┘
             │                                     │
      ┌──────┴──────┐                              │
      │             │                              │
      ▼             ▼                              │
  (has risks)   (no risks)                         │
      │             │                              │
      ▼             │                              │
┌─────────────────┐ │                              │
│  Email Agent    │ │                              │
│ (Templates+LLM) │ │                              │
└────────┬────────┘ │                              │
         │          │                              │
         └────┬─────┘                              │
              │                                    │
              └────────────────┬───────────────────┘
                               │
                               ▼
                         ┌───────────┐
                         │    END    │
                         └───────────┘
    """
    
    # Create the graph
    workflow = StateGraph(RetentionState)
    
    # Add all agent nodes
    workflow.add_node("analysis", analysis_agent)
    workflow.add_node("rag_prep", rag_prep_agent)
    workflow.add_node("email", email_agent)
    
    # PARALLEL EXECUTION: Both branches start from START
    # Branch 1: START → analysis → (conditional) → email → END
    # Branch 2: START → rag_prep → END
    
    workflow.add_edge(START, "analysis")
    workflow.add_edge(START, "rag_prep")
    
    # RAG branch goes directly to END
    workflow.add_edge("rag_prep", END)
    
    # Analysis branch has conditional routing
    workflow.add_conditional_edges(
        "analysis",
        should_send_emails,
        {
            "send_emails": "email",
            "skip_emails": END,
        }
    )
    
    # Email agent goes to END
    workflow.add_edge("email", END)
    
    return workflow


def run_retention_analysis(
    usage_data: list[dict],
    jira_tickets: list[dict]
) -> RetentionState:
    """
    Run the complete retention analysis workflow.
    
    Args:
        usage_data: 12-week client usage data
        jira_tickets: JIRA bug ticket data
    
    Returns:
        Final state with all analysis results
    """
    # Create and compile the workflow
    workflow = create_workflow()
    app = workflow.compile()
    
    # Initialize state with input data
    initial_state: RetentionState = {
        "usage_data": usage_data,
        "jira_tickets": jira_tickets,
        "workflow_status": "started",
        "errors": [],
    }
    
    print("\n🚀 Starting LangGraph Workflow (Parallel Execution)...")
    print("=" * 50)
    print("   📊 Branch 1: Analysis Agent → Email Agent")
    print("   📝 Branch 2: RAG Agent → Embeddings")
    print("=" * 50)
    
    # Run the workflow
    final_state = app.invoke(initial_state)
    
    print("\n" + "=" * 50)
    print("✅ Workflow Complete!")
    
    return final_state
