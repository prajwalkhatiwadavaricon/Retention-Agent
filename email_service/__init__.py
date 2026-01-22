"""
Email Service - HTML email generation and SMTP sending.

Components:
- templates.py: Generate HTML emails from analysis data
- sender.py: Send emails via SMTP (Gmail)

Usage:
    from email_service import send_retention_report, test_email_connection
    
    # Test connection
    test_email_connection()
    
    # Send report
    send_retention_report(
        analysis_results=results,
        to_email="cs-team@company.com",
        cs_rep_name="Sarah Johnson"
    )
"""

from email_service.templates import generate_email_html
from email_service.sender import (
    send_html_email,
    send_retention_report,
    test_email_connection,
)

__all__ = [
    "generate_email_html",
    "send_html_email",
    "send_retention_report",
    "test_email_connection",
]

