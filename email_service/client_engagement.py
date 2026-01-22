"""
Client Engagement Email Service - Sends personalized emails to clients based on unused modules.

After the CS team receives the analysis report, this service sends
targeted engagement emails to individual high-risk clients promoting
features they haven't been using.
"""

import os
import random
from pathlib import Path
from typing import Optional

from email_service.sender import send_html_email, EMAIL_SENDER, EMAIL_PASSWORD, DEFAULT_RECEIVER


# Module to HTML template mapping
# Maps Varicon module names to their corresponding HTML template files
MODULE_TEMPLATE_MAP = {
    "Timesheets": "timesheet.html",
    "Claims": "claims.html",
    "Delivery Dockets": "deliveryDocket.html",
    "Site Diaries": "siteDiary.html",
    "Purchase Orders": "purchaseOrder.html",
    "Variations": "variations.html",
    # Additional mappings (these templates may not exist yet)
    "Bills": "accountPayable.html",
    "Projects": "projectInvitation.html",
}

# All available templates
AVAILABLE_TEMPLATES = [
    "accountPayable.html",
    "claims.html",
    "deliveryDocket.html",
    "projectInvitation.html",
    "purchaseOrder.html",
    "siteDiary.html",
    "timesheet.html",
    "variations.html",
]

# All Varicon modules
ALL_MODULES = [
    "Timesheets", "Claims", "Tasks", "Purchase Orders", "Delivery Dockets",
    "Site Diaries", "Cost Tracking", "Reports", "Bills", "Scheduling",
    "Dashboard", "Daywork Dockets", "Variations", "Custom Forms", "Suppliers"
]


def get_client_templates_dir() -> Path:
    """Get the path to client engagement email templates."""
    # Default: look in project root / client_templates
    base_dir = Path(__file__).resolve().parents[1]
    templates_dir = base_dir / "client_templates"
    
    # Fallback to env variable if set
    env_path = os.getenv("CLIENT_TEMPLATES_DIR")
    if env_path:
        templates_dir = Path(env_path)
    
    return templates_dir


def get_unused_modules(client: dict) -> list[str]:
    """Get list of modules the client is NOT using."""
    active_modules = set(client.get("active_modules", []))
    unused = [m for m in ALL_MODULES if m not in active_modules]
    return unused


def find_template_for_module(module_name: str, templates_dir: Path) -> Optional[Path]:
    """Find the HTML template file for a given module."""
    template_name = MODULE_TEMPLATE_MAP.get(module_name)
    
    if template_name:
        template_path = templates_dir / template_name
        if template_path.exists():
            return template_path
    
    return None


def select_engagement_template(client: dict, templates_dir: Path) -> Optional[tuple[str, Path]]:
    """
    Select an engagement email template based on client's unused modules.
    Falls back to any available template if no specific match found.
    
    Returns:
        Tuple of (module_name, template_path) or None if no templates exist
    """
    # TEMPORARY: Always use this specific template for testing
    test_template = templates_dir / "updated_delivery_docket.html"
    if test_template.exists():
        return ("Delivery Dockets", test_template)
    
    # Original logic (commented out for now)
    # unused_modules = get_unused_modules(client)
    # 
    # # Find templates that match unused modules
    # matching_templates = []
    # for module in unused_modules:
    #     template_path = find_template_for_module(module, templates_dir)
    #     if template_path:
    #         matching_templates.append((module, template_path))
    # 
    # if matching_templates:
    #     return random.choice(matching_templates)
    # 
    # # FALLBACK: If no specific match, pick any available template
    # available_templates = []
    # for template_name in AVAILABLE_TEMPLATES:
    #     template_path = templates_dir / template_name
    #     if template_path.exists():
    #         module_name = template_name.replace(".html", "").replace("_", " ").title()
    #         available_templates.append((module_name, template_path))
    # 
    # if available_templates:
    #     return random.choice(available_templates)
    
    return None


def send_client_engagement_email(
    client: dict,
    templates_dir: Optional[Path] = None,
    to_email: Optional[str] = None,
) -> dict:
    """
    Send a personalized engagement email to a client.
    
    Args:
        client: Client analysis dict with risk info
        templates_dir: Path to template files
        to_email: Recipient email (uses DEFAULT_RECEIVER for testing)
    
    Returns:
        dict with success status and details
    """
    if templates_dir is None:
        templates_dir = get_client_templates_dir()
    
    if to_email is None:
        to_email = DEFAULT_RECEIVER
    
    client_name = client.get("client_name", "Unknown")
    
    # Skip if not high risk
    risk_factor = client.get("risk_factor", "").lower()
    if risk_factor not in ["high", "medium"]:
        return {
            "success": False,
            "client": client_name,
            "reason": f"Client is {risk_factor} risk, skipping engagement email"
        }
    
    # Check if templates directory exists
    if not templates_dir.exists():
        return {
            "success": False,
            "client": client_name,
            "reason": f"Templates directory not found: {templates_dir}"
        }
    
    # Select template based on unused modules
    template_result = select_engagement_template(client, templates_dir)
    
    if template_result is None:
        return {
            "success": False,
            "client": client_name,
            "reason": "No matching template found for unused modules"
        }
    
    module_name, template_path = template_result
    
    # Read template HTML
    try:
        html_content = template_path.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "success": False,
            "client": client_name,
            "reason": f"Failed to read template: {e}"
        }
    
    # Generate subject line
    subject = f"🚀 {client_name} - Boost Your Productivity with {module_name}!"
    
    # Send the email
    result = send_html_email(
        to_email=to_email,
        subject=subject,
        html_content=html_content,
    )
    
    if result.get("success"):
        return {
            "success": True,
            "client": client_name,
            "module": module_name,
            "template": template_path.name,
            "sent_to": to_email,
        }
    else:
        return {
            "success": False,
            "client": client_name,
            "reason": result.get("error", "Unknown error")
        }


def send_all_client_engagement_emails(
    analysis_results: list[dict],
    templates_dir: Optional[Path] = None,
    to_email: Optional[str] = None,
) -> dict:
    """
    Send engagement emails to all high-risk clients.
    
    Args:
        analysis_results: List of client analysis dicts
        templates_dir: Path to template files
        to_email: Recipient email (same for all during testing)
    
    Returns:
        dict with summary of sent emails
    """
    if templates_dir is None:
        templates_dir = get_client_templates_dir()
    
    results = {
        "sent": [],
        "skipped": [],
        "failed": [],
    }
    
    # Filter to high/medium risk clients only
    risky_clients = [
        c for c in analysis_results
        if c.get("risk_factor", "").lower() in ["high", "medium"]
    ]
    
    print(f"\n   📧 Processing {len(risky_clients)} risky clients for engagement emails...")
    
        # TEMPORARY: Only send to first client for testing
    if risky_clients:
        client = risky_clients[1]  # Only first client
        client_name = client.get("client_name", "Unknown")
        result = send_client_engagement_email(client, templates_dir, to_email)
        
        if result.get("success"):
            results["sent"].append(result)
            print(f"      ✅ {client_name}: Sent '{result['module']}' template")
        elif "No matching template" in result.get("reason", ""):
            results["skipped"].append(result)
            print(f"      ⏭️  {client_name}: No matching template for unused modules")
        else:
            results["failed"].append(result)
            print(f"      ❌ {client_name}: {result.get('reason', 'Failed')}")
        
        print(f"      ⏸️  Skipping remaining {len(risky_clients) - 1} clients (test mode)")
    
    return results

