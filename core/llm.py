"""LLM communication module for retention analysis."""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

from core.config import GOOGLE_API_KEY, MODEL_NAME, TEMPERATURE
from core.prompts import ANALYSIS_SYSTEM_PROMPT


def get_llm() -> ChatGoogleGenerativeAI:
    """Initialize and return the Gemini model."""
    return ChatGoogleGenerativeAI(
        model=MODEL_NAME,
        google_api_key=GOOGLE_API_KEY,
        temperature=TEMPERATURE,
    )


def chat(query: str) -> str:
    """Send a query to the LLM and get a response."""
    llm = get_llm()
    messages = [
        SystemMessage(content=ANALYSIS_SYSTEM_PROMPT),
        HumanMessage(content=query),
    ]
    response = llm.invoke(messages)
    return response.content


def analyze_with_llm(analysis_prompt: str) -> str:
    """
    Run retention analysis with the LLM.
    
    Args:
        analysis_prompt: The complete analysis prompt with data
        
    Returns:
        The LLM's analysis response
    """
    llm = get_llm()
    
    messages = [
        SystemMessage(content=ANALYSIS_SYSTEM_PROMPT),
        HumanMessage(content=analysis_prompt),
    ]
    
    response = llm.invoke(messages)
    return response.content


def validate_api_key() -> bool:
    """Check if the API key is configured."""
    if not GOOGLE_API_KEY:
        print("❌ Error: GOOGLE_API_KEY not found in environment variables.")
        print("   Please set it in your .env file:")
        print("   GOOGLE_API_KEY=your_api_key_here")
        return False
    return True
