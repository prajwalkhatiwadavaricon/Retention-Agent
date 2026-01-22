"""
Varicon Retention Analysis Agent

A LangGraph-based multi-agent system that:
1. Analyzes client usage data and JIRA tickets for churn risk
2. Prepares data for RAG (parallel)
3. Sends email notifications for risky clients

Usage:
    python main.py
"""

import json
from pathlib import Path

from core.config import USAGE_DATA_FILE, JIRA_TICKETS_FILE, GOOGLE_API_KEY
from core.data_loader import load_usage_data, load_jira_tickets
from graph.workflow import run_retention_analysis


def validate_setup() -> bool:
    """Validate that all required setup is complete."""
    if not GOOGLE_API_KEY:
        print("❌ Error: GOOGLE_API_KEY not found in environment variables.")
        print("   Please set it in your .env file:")
        print("   GOOGLE_API_KEY=your_api_key_here")
        return False
    return True


def format_analysis_output(analysis_results: list[dict]) -> str:
    """Format the analysis results for display."""
    output = []
    output.append("\n" + "=" * 60)
    output.append("🎯 CLIENT RETENTION ANALYSIS REPORT")
    output.append("=" * 60)
    
    # Sort by risk (high first)
    risk_order = {"high": 0, "medium": 1, "low": 2}
    sorted_results = sorted(
        analysis_results, 
        key=lambda x: risk_order.get(x.get("risk_factor", "low"), 3)
    )
    
    for client in sorted_results:
        risk = client.get("risk_factor", "unknown").upper()
        risk_emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(risk, "⚪")
        
        output.append(f"\n{risk_emoji} {client.get('client_name', 'Unknown')}")
        output.append("-" * 40)
        output.append(f"  Risk Factor: {risk}")
        output.append(f"  Churn Probability: {client.get('churn_probability', 0)}%")
        output.append(f"  Total Usage: {client.get('total_usage_count', 0)} activities")
        output.append(f"  Usage Trend: {client.get('usage_trend', 'unknown')}")
        output.append(f"  Health Score: {client.get('usage_health_score', 0)}/100")
        output.append(f"  Active Modules: {client.get('total_modules_used', 0)}")
        
        if client.get("active_modules"):
            output.append(f"  Modules: {', '.join(client['active_modules'][:5])}")
        
        if client.get("bug_tickets_affecting"):
            output.append(f"  Bug Tickets: {len(client['bug_tickets_affecting'])} affecting")
        
        if client.get("key_concerns"):
            output.append("  Concerns:")
            for concern in client["key_concerns"][:3]:
                output.append(f"    ⚠️  {concern}")
        
        if client.get("recommendations"):
            output.append("  Recommendations:")
            for rec in client["recommendations"][:2]:
                output.append(f"    💡 {rec}")
    
    output.append("\n" + "=" * 60)
    
    # Summary stats
    high_risk = sum(1 for c in analysis_results if c.get("risk_factor") == "high")
    medium_risk = sum(1 for c in analysis_results if c.get("risk_factor") == "medium")
    low_risk = sum(1 for c in analysis_results if c.get("risk_factor") == "low")
    
    output.append(f"\n📈 SUMMARY: {high_risk} High Risk | {medium_risk} Medium Risk | {low_risk} Low Risk")
    output.append("=" * 60)
    
    return "\n".join(output)


def main():
    """Run the LangGraph retention analysis workflow."""
    print("\n" + "=" * 60)
    print("🚀 VARICON RETENTION ANALYSIS AGENT")
    print("   Powered by LangGraph Multi-Agent System")
    print("=" * 60)
    
    # Validate setup
    if not validate_setup():
        return
    
    # Check for data files
    usage_path = Path(USAGE_DATA_FILE)
    jira_path = Path(JIRA_TICKETS_FILE)
    
    if not usage_path.exists():
        print(f"\n❌ Usage data file not found: {USAGE_DATA_FILE}")
        print("   Please ensure your 12-week usage data is in the data_request folder.")
        return
    
    # Load data
    print(f"\n📁 Loading data files...")
    print(f"   Usage: {USAGE_DATA_FILE}")
    
    usage_data = load_usage_data(str(usage_path))
    print(f"   ✅ Loaded {len(usage_data)} clients")
    
    jira_tickets = []
    if jira_path.exists():
        print(f"   JIRA: {JIRA_TICKETS_FILE}")
        jira_tickets = load_jira_tickets(str(jira_path))
        print(f"   ✅ Loaded {len(jira_tickets)} JIRA tickets")
    else:
        print(f"   ⚠️  JIRA file not found - proceeding without bug data")
    
    # Run the LangGraph workflow
    try:
        final_state = run_retention_analysis(
            usage_data=usage_data,
            jira_tickets=jira_tickets
        )
        
        # Display results
        analysis_results = final_state.get("analysis_results", [])
        
        if analysis_results:
            formatted_output = format_analysis_output(analysis_results)
            print(formatted_output)
            
            # Save analysis results
            # output_file = "data_request/analysis_results.json"
            BASE_DIR = Path(__file__).resolve().parents[2]  # project root
            DATA_DIR = BASE_DIR / "data_request"
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            output_file = DATA_DIR / "analysis_results.json"

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(analysis_results, f, indent=2)
            print(f"\n💾 Analysis saved to: {output_file}")
        
        # Show RAG prep status
        if final_state.get("rag_ready"):
            rag_docs = final_state.get("rag_documents", [])
            print(f"\n📝 RAG Documents Prepared: {len(rag_docs)} documents ready for embedding")
        
        # Show email status
        if final_state.get("emails_generated"):
            emails = final_state.get("emails_to_send", [])
            print(f"\n📧 Email Notifications: {len(emails)} emails generated")
            
            # Save emails to file for review
            if emails:
                email_file = DATA_DIR / "email_notifications.json"
                with open(email_file, "w", encoding="utf-8") as f:
                    json.dump(emails, f, indent=2)
                print(f"   Saved to: {email_file}")
        
        # Show any errors
        errors = final_state.get("errors", [])
        if errors:
            print(f"\n⚠️  Errors encountered:")
            for error in errors:
                print(f"   - {error}")
        
    except Exception as e:
        print(f"\n❌ Error during workflow: {e}")
        raise


if __name__ == "__main__":
    main()
