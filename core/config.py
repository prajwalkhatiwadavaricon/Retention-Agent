"""Configuration for the Retention Analysis Agent."""

import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# API Keys
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Model Settings
MODEL_NAME = "gemini-2.5-flash"
TEMPERATURE = 0.3  # Lower for more consistent analysis

# File Paths
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data_request"

USAGE_DATA_FILE = DATA_DIR / "retention_issues.json"
JIRA_TICKETS_FILE = DATA_DIR / "jira_bugs.json"

# Core Modules (for reference in prompts)
CORE_MODULES = [
    "Timesheets",
    "Claims",
    "Tasks",
    "Purchase Orders",
    "Delivery Dockets",
    "Site Diaries",
    "Cost Tracking",
    "Reports",
    "Bills",
    "Scheduling",
    "Dashboard",
    "Daywork Dockets",
    "Variations",
    "Custom Forms",
]

# Email Configuration (for Email Agent)
EMAIL_CONFIG = {
    "enabled": False,  # Set to True when email service is configured
    "smtp_host": os.getenv("SMTP_HOST", ""),
    "smtp_port": int(os.getenv("SMTP_PORT", "587")),
    "smtp_user": os.getenv("SMTP_USER", ""),
    "smtp_password": os.getenv("SMTP_PASSWORD", ""),
    "from_email": os.getenv("FROM_EMAIL", "retention-agent@varicon.com"),
    "cs_team_email": os.getenv("CS_TEAM_EMAIL", "cs-team@varicon.com"),
}

# RAG Configuration
RAG_CONFIG = {
    "enabled": True,  # Enable ChromaDB storage
    "embedding_model": "models/text-embedding-004",  # Google's embedding model
    "collection_name": "retention_documents",
    "chroma_path": "./chroma_db",  # Local persistent storage
}
