"""Data loading utilities for usage and JIRA data."""

import json
from pathlib import Path
from typing import Any


def load_json_file(file_path: str | Path) -> Any:
    """Load and parse a JSON file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_usage_data(file_path: str | Path) -> list[dict]:
    """Load client usage data."""
    return load_json_file(file_path)


def load_jira_tickets(file_path: str | Path) -> list[dict]:
    """Load JIRA bug ticket data."""
    data = load_json_file(file_path)
    
    # Handle { "issues": [...] } structure from JIRA API
    if isinstance(data, dict) and "issues" in data:
        return data["issues"]
    
    # Handle array of tickets
    if isinstance(data, list):
        return data
    
    # Single ticket as dict
    if isinstance(data, dict):
        return [data]
    
    return []


def extract_ticket_text(description: dict) -> str:
    """Extract plain text from JIRA description format."""
    if not description or not isinstance(description, dict):
        return ""
    
    text_parts = []
    content = description.get("content", [])
    
    for block in content:
        if block.get("type") == "paragraph":
            for item in block.get("content", []):
                if item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
    
    return " ".join(text_parts)


def extract_affected_modules(ticket: dict) -> list[str]:
    """Extract affected modules from JIRA ticket custom field."""
    modules = []
    custom_field = ticket.get("fields", {}).get("customfield_10370", [])
    
    if custom_field:
        for item in custom_field:
            if isinstance(item, dict) and "value" in item:
                modules.append(item["value"])
    
    return modules


def extract_client_from_description(description_text: str) -> str:
    """Extract client name from description text like 'Client: Construction KaT'."""
    import re
    
    if not description_text:
        return ""
    
    # Match "Client: ClientName" pattern
    match = re.search(r'Client:\s*([^\n]+)', description_text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    return ""


def extract_module_from_description(description_text: str) -> str:
    """Extract module name from description text like 'Module: Claims'."""
    import re
    
    if not description_text:
        return ""
    
    # Match "Module: ModuleName" pattern
    match = re.search(r'Module:\s*([^\n]+)', description_text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    return ""


def simplify_jira_tickets(tickets: list[dict]) -> list[dict]:
    """Simplify JIRA ticket data for LLM consumption."""
    simplified = []
    
    for ticket in tickets:
        fields = ticket.get("fields", {})
        description_text = extract_ticket_text(fields.get("description", {}))
        
        # Try custom field first, then extract from description
        client_name = fields.get("customfield_10159", "")
        if not client_name or client_name == "Unknown":
            client_name = extract_client_from_description(description_text)
        if not client_name:
            # Try extracting from summary (e.g., "Claims export format inconsistent (Construction KaT)")
            import re
            summary = fields.get("summary", "")
            match = re.search(r'\(([^)]+)\)\s*$', summary)
            if match:
                client_name = match.group(1).strip()
        if not client_name:
            client_name = "Unknown"
        
        # Extract module from description or labels
        module = extract_module_from_description(description_text)
        labels = fields.get("labels", [])
        if not module and labels:
            module = labels[0] if labels else ""
        
        simplified.append({
            "key": ticket.get("key", ""),
            "id": ticket.get("id", ""),
            "client_name": client_name,
            "summary": fields.get("summary", ""),
            "description": description_text,
            "priority": fields.get("priority", {}).get("name", "Unknown"),
            "status": fields.get("status", {}).get("name", "Unknown"),
            "created": fields.get("created", ""),
            "updated": fields.get("updated", ""),
            "affected_module": module,
            "affected_modules": extract_affected_modules(ticket),
            "labels": labels
        })
    
    return simplified


def get_usage_summary(usage_data: list[dict]) -> dict:
    """Get a quick summary of usage data for debugging."""
    summary = {}
    
    for client in usage_data:
        client_name = client.get("client_name", "Unknown")
        total_activities = 0
        modules_used = set()
        
        for week in client.get("usage", []):
            for activity in week.get("activities", []):
                total_activities += activity.get("count", 0)
                modules_used.add(activity.get("name", ""))
        
        summary[client_name] = {
            "total_activities": total_activities,
            "modules_used": list(modules_used),
            "weeks_of_data": len(client.get("usage", []))
        }
    
    return summary

