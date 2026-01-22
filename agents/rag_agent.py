"""
RAG Preparation Agent - Uses LLM to convert JSON data to text for embeddings.

This agent runs in PARALLEL with the Analysis Agent.
It:
1. Takes usage data and JIRA tickets as input
2. Sends both JSONs to LLM with RAG_PROMPT
3. LLM converts to structured textual format with multiple sections
4. Parses into focused chunks (overview, weekly, modules, bugs, trends)
5. Stores documents in ChromaDB for retrieval
"""

import json
import re
from datetime import datetime

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

from core.config import GOOGLE_API_KEY, MODEL_NAME, RAG_CONFIG
from core.prompts import RAG_SYSTEM_PROMPT, build_rag_prompt


def get_llm() -> ChatGoogleGenerativeAI:
    """Initialize the Gemini model for RAG text conversion."""
    return ChatGoogleGenerativeAI(
        model=MODEL_NAME,
        google_api_key=GOOGLE_API_KEY,
        temperature=0.2,
    )


def convert_json_to_text_with_llm(usage_data: list[dict], jira_tickets: list[dict]) -> str:
    """Use LLM to convert JSON data to structured text for RAG."""
    prompt = build_rag_prompt(
        usage_data=json.dumps(usage_data, indent=2),
        jira_tickets=json.dumps(jira_tickets, indent=2)
    )
    
    llm = get_llm()
    messages = [
        SystemMessage(content=RAG_SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ]
    
    response = llm.invoke(messages)
    return response.content


def parse_llm_text_to_documents(llm_output: str, usage_data: list[dict], jira_tickets: list[dict] = None) -> list[dict]:
    """
    Parse the LLM output into focused document chunks for ChromaDB.
    
    Creates separate chunks for:
    - Client overview
    - Weekly usage details
    - Module analysis
    - Bug impact
    - Trend analysis
    - Representatives
    - JIRA tickets (direct from data)
    """
    documents = []
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Define section patterns to extract
    section_patterns = [
        (r'\[CLIENT OVERVIEW: ([^\]]+)\](.*?)(?=\[|$)', 'overview', 'Client overview and summary'),
        (r'\[WEEKLY USAGE: ([^\]]+)\](.*?)(?=\[|$)', 'weekly', 'Weekly usage breakdown and patterns'),
        (r'\[MODULE USAGE: ([^\]]+)\](.*?)(?=\[|$)', 'modules', 'Module-specific usage analysis'),
        (r'\[BUGS AFFECTING: ([^\]]+)\](.*?)(?=\[|$)', 'bugs', 'Bug tickets and issues'),
        (r'\[USAGE TREND: ([^\]]+)\](.*?)(?=\[|$)', 'trends', 'Usage trends over time'),
        (r'\[REPRESENTATIVE: ([^\]]+)\](.*?)(?=\[|$)', 'representative', 'Client representative info'),
    ]
    
    for pattern, section_type, description in section_patterns:
        matches = re.findall(pattern, llm_output, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            client_name = match[0].strip()
            content = match[1].strip()
            
            if content and len(content) > 50:  # Only add non-empty sections
                doc_id = f"{client_name.replace(' ', '_').lower()}_{section_type}_{timestamp}"
                
                # Add client name to content for better matching
                full_content = f"Client: {client_name}\nSection: {description}\n\n{content}"
                
                documents.append({
                    "id": doc_id,
                    "content": full_content,
                    "metadata": {
                        "client_name": client_name,
                        "section_type": section_type,
                        "description": description,
                        "source": "rag_agent",
                        "generated_at": datetime.now().isoformat(),
                    }
                })
    
    # If no sections were parsed, try to extract client sections the old way
    if not documents:
        print("   ⚠️ Section parsing failed, using fallback method...")
        sections = llm_output.split("===== CLIENT:")
        
        for section in sections[1:]:
            if "=====" in section:
                lines = section.strip().split("\n")
                client_name = lines[0].replace("=====", "").strip()
                content = section.strip()
                
                documents.append({
                    "id": f"client_{client_name.replace(' ', '_').lower()}_{timestamp}",
                    "content": f"Client: {client_name}\n\n{content}",
                    "metadata": {
                        "client_name": client_name,
                        "section_type": "full",
                        "source": "rag_agent",
                        "generated_at": datetime.now().isoformat(),
                    }
                })
    
    # If still no documents, create single document from LLM output
    if not documents:
        print("   ⚠️ Fallback failed, creating single document...")
        documents.append({
            "id": f"full_analysis_{timestamp}",
            "content": llm_output,
            "metadata": {
                "section_type": "full",
                "source": "rag_agent",
                "generated_at": datetime.now().isoformat(),
            }
        })
    
    # === CREATE DIRECT JIRA TICKET DOCUMENTS ===
    # This ensures JIRA data is always searchable regardless of LLM output
    if jira_tickets:
        from core.data_loader import simplify_jira_tickets
        simplified_tickets = simplify_jira_tickets(jira_tickets)
        
        # Group tickets by client
        client_tickets = {}
        for ticket in simplified_tickets:
            client = ticket.get("client_name", "Unknown")
            if client not in client_tickets:
                client_tickets[client] = []
            client_tickets[client].append(ticket)
        
        # Create a document per client's JIRA tickets
        for client_name, tickets in client_tickets.items():
            ticket_texts = []
            for t in tickets:
                ticket_text = f"""
JIRA Ticket: {t.get('key', 'N/A')}
Summary: {t.get('summary', 'N/A')}
Priority: {t.get('priority', 'Unknown')}
Status: {t.get('status', 'Unknown')}
Module: {t.get('affected_module', 'N/A')}
Created: {t.get('created', 'N/A')}
Updated: {t.get('updated', 'N/A')}
Description: {t.get('description', 'No description')}
Labels: {', '.join(t.get('labels', []))}
"""
                ticket_texts.append(ticket_text.strip())
            
            jira_content = f"""Client: {client_name}
Section: JIRA Bug Reports

This client has {len(tickets)} JIRA bug ticket(s):

{"---".join(ticket_texts)}

Total JIRA tickets for {client_name}: {len(tickets)}
"""
            documents.append({
                "id": f"{client_name.replace(' ', '_').lower()}_jira_direct_{timestamp}",
                "content": jira_content,
                "metadata": {
                    "client_name": client_name,
                    "section_type": "jira_tickets",
                    "description": "JIRA bug tickets for this client",
                    "source": "jira_direct",
                    "ticket_count": len(tickets),
                    "generated_at": datetime.now().isoformat(),
                }
            })
        
        # Create a summary document of all JIRA tickets
        all_tickets_text = f"""JIRA Bug Reports Summary

Total Tickets: {len(simplified_tickets)}
Clients with JIRA Data: {', '.join(client_tickets.keys())}

Breakdown by Client:
"""
        for client_name, tickets in client_tickets.items():
            all_tickets_text += f"- {client_name}: {len(tickets)} tickets\n"
        
        all_tickets_text += "\nNote: Only Development, Construction KaT, and UB Civil have JIRA bug data.\n"
        
        documents.append({
            "id": f"jira_summary_{timestamp}",
            "content": all_tickets_text,
            "metadata": {
                "section_type": "jira_summary",
                "description": "Summary of all JIRA tickets",
                "source": "jira_direct",
                "total_tickets": len(simplified_tickets),
                "generated_at": datetime.now().isoformat(),
            }
        })
        
        print(f"   📋 Created {len(client_tickets) + 1} JIRA-specific documents")
    
    # === CREATE CLIENT REPRESENTATIVES DOCUMENT ===
    rep_lines = ["Client Representatives Summary\n"]
    clients_with_reps = 0
    clients_without_reps = 0
    
    for client in usage_data:
        client_name = client.get("client_name", "Unknown")
        reps = client.get("client_representatives", [])
        
        if reps:
            clients_with_reps += 1
            for rep in reps:
                rep_lines.append(f"Client: {client_name}")
                rep_lines.append(f"  Representative: {rep.get('full_name', 'N/A')}")
                rep_lines.append(f"  Email: {rep.get('email', 'N/A')}")
                rep_lines.append("")
        else:
            clients_without_reps += 1
            rep_lines.append(f"Client: {client_name}")
            rep_lines.append("  Representative: Not assigned yet")
            rep_lines.append("")
    
    rep_lines.append(f"\nTotal clients: {len(usage_data)}")
    rep_lines.append(f"Clients with representatives: {clients_with_reps}")
    rep_lines.append(f"Clients without representatives: {clients_without_reps}")
    
    documents.append({
        "id": f"representatives_summary_{timestamp}",
        "content": "\n".join(rep_lines),
        "metadata": {
            "section_type": "representatives",
            "description": "Client representatives summary",
            "source": "usage_data",
            "generated_at": datetime.now().isoformat(),
        }
    })
    
    # === CREATE ALL CLIENTS USAGE SUMMARY ===
    # This document answers "List all clients and their usage" type questions
    all_clients_lines = [
        "ALL CLIENTS USAGE SUMMARY",
        "=" * 50,
        f"Total Clients: {len(usage_data)}",
        "",
        "CLIENTS WITH FULL DATA (Usage + JIRA):",
        "- Development",
        "- Construction KaT",  
        "- UB Civil",
        "",
        "ALL CLIENTS USAGE TABLE:",
        "",
        "| Client Name | Total Usage | Modules Used | Weeks | Has JIRA |",
        "|-------------|-------------|--------------|-------|----------|",
    ]
    
    # Full data clients
    full_data_clients = ["development", "construction kat", "contruction kat", "ub civil"]
    
    for client in usage_data:
        client_name = client.get("client_name", "Unknown")
        
        # Calculate total usage
        total_usage = 0
        modules_used = set()
        weeks_count = len(client.get("usage", []))
        
        for week in client.get("usage", []):
            for activity in week.get("activities", []):
                total_usage += activity.get("count", 0)
                modules_used.add(activity.get("name", ""))
        
        has_jira = "Yes" if client_name.lower() in full_data_clients else "No"
        
        all_clients_lines.append(
            f"| {client_name} | {total_usage} | {len(modules_used)} | {weeks_count} | {has_jira} |"
        )
    
    all_clients_lines.append("")
    all_clients_lines.append("Note: Only Development, Construction KaT, and UB Civil have JIRA bug data.")
    all_clients_lines.append(f"All {len(usage_data)} clients have usage data available.")
    
    documents.append({
        "id": f"all_clients_usage_{timestamp}",
        "content": "\n".join(all_clients_lines),
        "metadata": {
            "section_type": "all_clients",
            "description": "Complete list of all clients with usage summary",
            "source": "usage_data",
            "total_clients": len(usage_data),
            "generated_at": datetime.now().isoformat(),
        }
    })
    
    # === CREATE DETAILED CLIENT LIST ===
    # Simple list format for "how many clients" and "list clients" questions
    client_list_content = f"""Varicon Client List

Total Number of Clients: {len(usage_data)}

List of All Clients:
"""
    for i, client in enumerate(usage_data, 1):
        client_name = client.get("client_name", "Unknown")
        reps = client.get("client_representatives", [])
        rep_names = ", ".join([r.get("full_name", "N/A") for r in reps]) if reps else "Not assigned"
        client_list_content += f"{i}. {client_name} (Representative: {rep_names})\n"
    
    client_list_content += f"""
Summary:
- Total clients: {len(usage_data)}
- Clients with JIRA data: 3 (Development, Construction KaT, UB Civil)
- Clients with usage data only: {len(usage_data) - 3}
"""
    
    documents.append({
        "id": f"client_list_{timestamp}",
        "content": client_list_content,
        "metadata": {
            "section_type": "client_list",
            "description": "Simple list of all Varicon clients",
            "source": "usage_data",
            "total_clients": len(usage_data),
            "generated_at": datetime.now().isoformat(),
        }
    })
    
    return documents


def store_in_chromadb(documents: list[dict]) -> int:
    """Store documents in ChromaDB."""
    from rag.vector_store import get_vector_store
    
    store = get_vector_store()
    
    # Clear existing documents to avoid duplicates
    if store.count() > 0:
        print(f"   🔄 Clearing {store.count()} existing documents...")
        store.delete_all()
    
    return store.add_documents(documents)


def rag_prep_agent(state: dict) -> dict:
    """
    RAG Preparation Agent Node for LangGraph.
    
    Runs in PARALLEL with Analysis Agent.
    Creates focused document chunks for better retrieval.
    """
    print("\n" + "=" * 70)
    print("📝 [RAG AGENT] Converting JSON to text using LLM...")
    print("=" * 70)
    
    usage_data = state.get("usage_data", [])
    jira_tickets = state.get("jira_tickets", [])
    
    print(f"   📊 Processing {len(usage_data)} clients")
    print(f"   🎫 Processing {len(jira_tickets)} JIRA tickets")
    
    try:
        # Step 1: LLM converts JSON to text
        print("   🤖 Sending to LLM for text conversion...")
        llm_text_output = convert_json_to_text_with_llm(usage_data, jira_tickets)
        print(f"   ✅ LLM generated {len(llm_text_output)} characters of text")
        
        # Step 2: Parse into focused documents (also creates direct JIRA documents)
        documents = parse_llm_text_to_documents(llm_text_output, usage_data, jira_tickets)
        
        # Count by section type
        section_counts = {}
        for doc in documents:
            section = doc["metadata"].get("section_type", "unknown")
            section_counts[section] = section_counts.get(section, 0) + 1
        
        print(f"   📄 Created {len(documents)} document chunks:")
        for section, count in sorted(section_counts.items()):
            print(f"      - {section}: {count} chunks")
        
        # Step 3: Store in ChromaDB
        if RAG_CONFIG.get("enabled", True):
            print("\n   💾 Storing in ChromaDB...")
            docs_stored = store_in_chromadb(documents)
            print(f"   ✅ Stored {docs_stored} documents in ChromaDB")
        
        print("=" * 70)
        
        # Return ONLY the new keys
        return {
            "rag_documents": documents,
            "rag_text": llm_text_output,
            "rag_ready": True,
        }
        
    except Exception as e:
        print(f"   ❌ Error in RAG Agent: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 70)
        
        return {
            "rag_documents": [],
            "rag_text": "",
            "rag_ready": False,
            "errors": [f"RAG Agent Error: {str(e)}"],
        }
