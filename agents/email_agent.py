"""
Email Agent - Generates and sends emails from analysis results.

This agent is triggered AFTER the Analysis Agent if risky clients exist.
It does TWO things:
1. Sends CS Team Report - Analysis summary for the customer success team
2. Sends Client Engagement Emails - Personalized emails to risky clients
   promoting features they haven't been using
"""

import os
from datetime import datetime
from pathlib import Path

from email_service.templates import generate_email_html
from email_service.sender import send_retention_report, test_email_connection
from email_service.client_engagement import send_all_client_engagement_emails


def should_send_emails(state: dict) -> str:
    """Conditional edge function for LangGraph."""
    risky_clients = state.get("risky_clients", [])
    
    if risky_clients:
        high_count = sum(1 for c in risky_clients if c.get("risk_factor") == "high")
        medium_count = len(risky_clients) - high_count
        print(f"\n📧 [ROUTER] Found {len(risky_clients)} risky clients ({high_count} high, {medium_count} medium)")
        print("   → Routing to Email Agent")
        return "send_emails"
    
    print("\n✅ [ROUTER] No risky clients found")
    print("   → Skipping Email Agent")
    return "skip_emails"


def email_agent(state: dict) -> dict:
    """
    Email Agent Node for LangGraph.
    
    Generates HTML emails from templates - NO LLM needed!
    Much faster and more consistent than LLM-generated emails.
    """
    print("\n" + "=" * 70)
    print("📧 [EMAIL AGENT] Generating HTML emails from templates...")
    print("=" * 70)
    
    # Get ALL analysis results (not just risky)
    analysis_results = state.get("analysis_results", [])
    risky_clients = state.get("risky_clients", [])
    
    if not analysis_results:
        print("   ⚠️ No analysis results found")
        return {
            "emails_to_send": [],
            "email_summary": "No analysis results available.",
            "emails_generated": False,
        }
    
    # Count risks
    high_risk = sum(1 for c in analysis_results if c.get("risk_factor") == "high")
    medium_risk = sum(1 for c in analysis_results if c.get("risk_factor") == "medium")
    low_risk = sum(1 for c in analysis_results if c.get("risk_factor") == "low")
    
    print(f"   📊 Total clients: {len(analysis_results)}")
    print(f"      🔴 High Risk: {high_risk}")
    print(f"      🟡 Medium Risk: {medium_risk}")
    print(f"      🟢 Low Risk: {low_risk}")
    
    # Generate HTML email from templates
    print("\n   🎨 Generating HTML email from template...")
    html_content = generate_email_html(
        analysis_results=analysis_results,
        cs_rep_name="Varicon CS Team"
    )
    print(f"   ✅ Generated HTML email ({len(html_content)} characters)")
    
    # Determine subject based on risk
    if high_risk > 0:
        subject = f"🚨 Retention Alert: {high_risk} High Risk Clients Detected"
        priority = "high"
    elif medium_risk > 0:
        subject = f"⚠️ Retention Report: {medium_risk} Clients Need Attention"
        priority = "normal"
    else:
        subject = "✅ Retention Report: All Clients Healthy"
        priority = "low"
    
    # Create email object
    email = {
        "subject": subject,
        "html_content": html_content,
        "priority": priority,
        "metadata": {
            "total_clients": len(analysis_results),
            "high_risk": high_risk,
            "medium_risk": medium_risk,
            "low_risk": low_risk,
            "generated_at": datetime.now().isoformat(),
        }
    }
    
    # Check if email sending is configured
    email_config = test_email_connection()
    
    if email_config["configured"] and email_config["success"]:
        print("\n   📤 Email SMTP is configured")
        
        # Get receiver from env
        receiver = os.getenv("EMAIL_RECEIVER")
        
        if receiver:
            print(f"   📧 Sending to: {receiver}")
            result = send_retention_report(
                analysis_results=analysis_results,
                to_email=receiver,
                cs_rep_name="Varicon CS Team"
            )
            
            if result["success"]:
                print(f"   ✅ Email sent successfully!")
                email["sent"] = True
                email["sent_to"] = receiver
            else:
                print(f"   ❌ Failed to send: {result.get('error', 'Unknown error')}")
                email["sent"] = False
                email["error"] = result.get("error")
        else:
            print("   ⚠️ EMAIL_RECEIVER not set in .env - email not sent")
            email["sent"] = False
    else:
        print("\n   ⏸️ Email SMTP not configured")
        print("   To enable email sending, add to .env:")
        print("      EMAIL_SENDER=your@gmail.com")
        # print("      EMAIL_APP_PASSWORD=your_app_password")
        print("      EMAIL_RECEIVER=recipient@email.com")
        email["sent"] = False
    
    # Save HTML to file for preview
    BASE_DIR = Path(__file__).resolve().parents[1]  # project root
    DATA_DIR = BASE_DIR / "data_request"
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    html_file = DATA_DIR / "email_report.html"
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"\n   💾 HTML preview saved to: {html_file}")
    
    # =========================================================================
    # STEP 2: Send Client Engagement Emails
    # =========================================================================
    print("\n" + "-" * 70)
    print("📬 [EMAIL AGENT] Sending Client Engagement Emails...")
    print("-" * 70)
    
    # Client templates directory
    CLIENT_TEMPLATES_DIR = BASE_DIR / "client_templates"
    
    client_email_results = {"sent": [], "skipped": [], "failed": []}
    
    if CLIENT_TEMPLATES_DIR.exists():
        # Get receiver (same for testing)
        receiver = os.getenv("EMAIL_RECEIVER")
        
        if receiver and email_config.get("success"):
            client_email_results = send_all_client_engagement_emails(
                analysis_results=analysis_results,
                templates_dir=CLIENT_TEMPLATES_DIR,
                to_email=receiver,  # Same receiver for testing
            )
            
            sent_count = len(client_email_results.get("sent", []))
            skipped_count = len(client_email_results.get("skipped", []))
            
            print(f"\n   📊 Client Engagement Summary:")
            print(f"      ✅ Sent: {sent_count}")
            print(f"      ⏭️  Skipped (no template): {skipped_count}")
        else:
            print("   ⚠️ SMTP not configured or EMAIL_RECEIVER not set")
    else:
        print(f"   ⚠️ Client templates directory not found: {CLIENT_TEMPLATES_DIR}")
        print("   Create this folder with HTML templates to enable client emails")
    
    print("-" * 70)
    
    # Generate summary
    summary_lines = [
        "=" * 50,
        "EMAIL REPORT SUMMARY",
        "=" * 50,
        f"Total Clients Analyzed: {len(analysis_results)}",
        f"High Risk: {high_risk}",
        f"Medium Risk: {medium_risk}",
        f"Low Risk: {low_risk}",
        "",
        "CS Team Report:",
        f"  Subject: {subject}",
        f"  Sent: {'Yes' if email.get('sent') else 'No'}",
        "",
        "Client Engagement Emails:",
        f"  Sent: {len(client_email_results.get('sent', []))}",
        f"  Skipped: {len(client_email_results.get('skipped', []))}",
        "=" * 50,
    ]
    
    print("=" * 70)
    
    # Return ONLY the new keys
    return {
        "emails_to_send": [email],
        "client_engagement_results": client_email_results,
        "email_summary": "\n".join(summary_lines),
        "emails_generated": True,
    }
