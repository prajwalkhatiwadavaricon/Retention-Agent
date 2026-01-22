"""Core utilities for the Retention Analysis Agent."""

from core.config import (
    GOOGLE_API_KEY,
    MODEL_NAME,
    TEMPERATURE,
    DATA_DIR,
    USAGE_DATA_FILE,
    JIRA_TICKETS_FILE,
    CORE_MODULES,
    EMAIL_CONFIG,
    RAG_CONFIG,
)
from core.llm import get_llm, chat, analyze_with_llm, validate_api_key
from core.prompts import (
    ANALYSIS_SYSTEM_PROMPT,
    ANALYSIS_PROMPT,
    RAG_SYSTEM_PROMPT,
    RAG_CONVERSION_PROMPT,
    EMAIL_SYSTEM_PROMPT,
    build_analysis_prompt,
    build_rag_prompt,
    build_email_prompt,
)
from core.data_loader import (
    load_json_file,
    load_usage_data,
    load_jira_tickets,
    simplify_jira_tickets,
    get_usage_summary,
)
from core.models import RiskLevel, Activity, WeeklyUsage, ClientUsage, JiraTicket

__all__ = [
    # Config
    "GOOGLE_API_KEY",
    "MODEL_NAME",
    "TEMPERATURE",
    "DATA_DIR",
    "USAGE_DATA_FILE",
    "JIRA_TICKETS_FILE",
    "CORE_MODULES",
    "EMAIL_CONFIG",
    "RAG_CONFIG",
    # LLM
    "get_llm",
    "chat",
    "analyze_with_llm",
    "validate_api_key",
    # Prompts
    "ANALYSIS_SYSTEM_PROMPT",
    "ANALYSIS_PROMPT",
    "RAG_SYSTEM_PROMPT",
    "RAG_CONVERSION_PROMPT",
    "EMAIL_SYSTEM_PROMPT",
    "build_analysis_prompt",
    "build_rag_prompt",
    "build_email_prompt",
    # Data Loader
    "load_json_file",
    "load_usage_data",
    "load_jira_tickets",
    "simplify_jira_tickets",
    "get_usage_summary",
    # Models
    "RiskLevel",
    "Activity",
    "WeeklyUsage",
    "ClientUsage",
    "JiraTicket",
]
