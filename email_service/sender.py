"""
Email Sender Service - Sends HTML emails via SMTP.

Uses Gmail SMTP with TLS for secure email delivery.
Credentials should be stored in environment variables.
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


# Email configuration
# ═══════════════════════════════════════════════════════════════════
# IMPORTANT: Gmail requires an App Password (NOT your regular password!)
# 
# How to get an App Password:
# 1. Go to https://myaccount.google.com/security
# 2. Enable 2-Step Verification (if not already)
# 3. Go to https://myaccount.google.com/apppasswords
# 4. Create a new App Password for "Mail" on "Mac"
# 5. Copy the 16-character password (e.g., "abcd efgh ijkl mnop")
# 6. Add to .env: EMAIL_APP_PASSWORD=abcdefghijklmnop (no spaces)
# ═══════════════════════════════════════════════════════════════════

EMAIL_SENDER = os.getenv("EMAIL_SENDER", "kan077bct056@kec.edu.np")
EMAIL_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")  # Must be App Password!
DEFAULT_RECEIVER = os.getenv("EMAIL_RECEIVER", "khatiwadaprajwal22@gmail.com")

# SMTP Server settings
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))


def send_html_email(
    to_email: str,
    subject: str,
    html_content: str,
    sender_email: Optional[str] = None,
    sender_password: Optional[str] = None,
) -> dict:
    """
    Send an HTML email via SMTP.
    
    Args:
        to_email: Recipient email address
        subject: Email subject line
        html_content: HTML content of the email
        sender_email: Sender email (uses env var if not provided)
        sender_password: Sender password/app password (uses env var if not provided)
        
    Returns:
        dict with success status and message
    """
    sender = EMAIL_SENDER
    password = EMAIL_PASSWORD
    
    if not sender or not password:
        return {
            "success": False,
            "error": "Email credentials not configured. Set EMAIL_SENDER and EMAIL_APP_PASSWORD in .env"
        }
    
    try:
        # Create HTML message
        msg = MIMEText(html_content, _subtype='html')  # 'html' not 'plain'!
        msg["From"] = sender
        msg["To"] = to_email
        msg["Subject"] = subject
        
        # Send via SMTP
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
            smtp.starttls()  # Enable TLS
            smtp.login(sender, password)
            smtp.sendmail(sender, to_email, msg.as_string())
        
        print(f"   ✅ Email sent to {to_email}")
        
        return {
            "success": True,
            "message": f"Email sent to {to_email}",
            "timestamp": datetime.now().isoformat()
        }
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"   ❌ Auth Error: {e}")
        return {
            "success": False,
            "error": f"SMTP authentication failed: {e}. For Gmail, use App Password."
        }
    except smtplib.SMTPException as e:
        print(f"   ❌ SMTP Error: {e}")
        return {
            "success": False,
            "error": f"SMTP error: {str(e)}"
        }
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": f"Failed to send email: {str(e)}"
        }


def send_retention_report(
    analysis_results: list[dict],
    to_email: str,
    cs_rep_name: str = "CS Team",
    sender_email: Optional[str] = None,
    sender_password: Optional[str] = None,
) -> dict:
    """
    Send a complete retention analysis report email.
    
    Args:
        analysis_results: List of client analysis dicts from Analysis Agent
        to_email: Recipient email address
        cs_rep_name: Name of the CS representative
        sender_email: Optional sender email override
        sender_password: Optional sender password override
        
    Returns:
        dict with success status and details
    """
    from email_service.templates import generate_email_html
    
    # Count risks for subject line
    high_risk = sum(1 for c in analysis_results if c.get("risk_factor") == "high")
    medium_risk = sum(1 for c in analysis_results if c.get("risk_factor") == "medium")
    
    # Generate subject
    if high_risk > 0:
        subject = f"🚨 Retention Alert: {high_risk} High Risk Clients Detected"
    elif medium_risk > 0:
        subject = f"⚠️ Retention Report: {medium_risk} Clients Need Attention"
    else:
        subject = "✅ Retention Report: All Clients Healthy"
    
    # Generate HTML
    html_content = generate_email_html(analysis_results, cs_rep_name)
    
    # Send email
    return send_html_email(
        to_email=to_email,
        subject=subject,
        html_content=html_content,
        sender_email=sender_email,
        sender_password=sender_password,
    )


def test_email_connection() -> dict:
    """Test if email credentials are properly configured."""
    if not EMAIL_SENDER or not EMAIL_PASSWORD:
        return {
            "success": False,
            "configured": False,
            "message": "Email not configured."
        }
    
    print(f"   🔌 Testing SMTP: {SMTP_SERVER}:{SMTP_PORT}")
    print(f"   📧 Sender: {EMAIL_SENDER}")
    
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
            print("   ✓ Connected to SMTP server")
            smtp.starttls()
            print("   ✓ TLS enabled")
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            print("   ✓ Login successful")
        
        return {
            "success": True,
            "configured": True,
            "message": f"Email configured and authenticated: {EMAIL_SENDER}"
        }
    except smtplib.SMTPAuthenticationError as e:
        print(f"   ❌ Login failed: {e}")
        return {
            "success": False,
            "configured": True,
            "message": f"Authentication failed. For Gmail use App Password: {str(e)}"
        }
    except Exception as e:
        print(f"   ❌ Connection error: {e}")
        return {
            "success": False,
            "configured": True,
            "message": f"Connection failed: {str(e)}"
        }

