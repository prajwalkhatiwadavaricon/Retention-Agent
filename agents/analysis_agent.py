"""
Analysis Agent - Uses LLM to analyze client usage data and JIRA tickets for churn risk.

This agent:
1. Takes usage data and JIRA tickets as input
2. Sends both JSONs to LLM with ANALYSIS_PROMPT
3. LLM returns structured risk assessment per client
4. Filters risky clients for Email Agent
"""

import json

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

from core.config import GOOGLE_API_KEY, MODEL_NAME, TEMPERATURE
from core.prompts import ANALYSIS_SYSTEM_PROMPT, build_analysis_prompt
from core.data_loader import simplify_jira_tickets


def get_llm() -> ChatGoogleGenerativeAI:
    """Initialize the Gemini model for analysis."""
    return ChatGoogleGenerativeAI(
        model=MODEL_NAME,
        google_api_key=GOOGLE_API_KEY,
        temperature=TEMPERATURE,
    )


def parse_llm_response(result: str) -> list[dict]:
    """Parse the LLM JSON response with robust error handling."""
    import re
    
    try:
        clean_result = result.strip()
        
        # Remove markdown code blocks
        if clean_result.startswith("```json"):
            clean_result = clean_result[7:]
        elif clean_result.startswith("```"):
            clean_result = clean_result[3:]
        
        if clean_result.endswith("```"):
            clean_result = clean_result[:-3]
        
        clean_result = clean_result.strip()
        
        # Find the JSON array
        start_idx = clean_result.find("[")
        end_idx = clean_result.rfind("]") + 1
        
        if start_idx != -1 and end_idx > start_idx:
            json_str = clean_result[start_idx:end_idx]
            
            # Try parsing as-is first
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
            
            # Fix common LLM JSON errors
            fixed_json = json_str
            
            # Fix trailing commas before ] or }
            fixed_json = re.sub(r',\s*]', ']', fixed_json)
            fixed_json = re.sub(r',\s*}', '}', fixed_json)
            
            # Fix missing commas between objects: }{ or }  {
            fixed_json = re.sub(r'}\s*{', '},{', fixed_json)
            
            # Fix missing commas after strings before keys: "value""key" or "value" "key"
            fixed_json = re.sub(r'"\s*\n\s*"([a-z_])', r'",\n"\1', fixed_json, flags=re.IGNORECASE)
            
            # Try parsing the fixed JSON
            try:
                return json.loads(fixed_json)
            except json.JSONDecodeError as e:
                print(f"   ⚠️ JSON fix attempt failed: {e}")
                
                # Last resort: try to extract individual objects
                objects = []
                obj_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
                matches = re.findall(obj_pattern, json_str, re.DOTALL)
                
                for match in matches:
                    try:
                        # Fix trailing commas in individual objects
                        obj_fixed = re.sub(r',\s*}', '}', match)
                        obj_fixed = re.sub(r',\s*]', ']', obj_fixed)
                        obj = json.loads(obj_fixed)
                        if isinstance(obj, dict) and 'client_name' in obj:
                            objects.append(obj)
                    except json.JSONDecodeError:
                        continue
                
                if objects:
                    print(f"   🔧 Recovered {len(objects)} client objects from malformed JSON")
                    return objects
        
        return json.loads(clean_result)
        
    except json.JSONDecodeError as e:
        print(f"   ⚠️ Could not parse JSON result: {e}")
        # Save raw response for debugging
        try:
            from pathlib import Path
            debug_file = Path(__file__).parent.parent / "data_request" / "debug_llm_response.txt"
            with open(debug_file, "w") as f:
                f.write(result)
            print(f"   📝 Raw LLM response saved to: {debug_file}")
        except Exception:
            pass
        return []


def analysis_agent(state: dict) -> dict:
    """
    Analysis Agent Node for LangGraph.
    
    Uses LLM with ANALYSIS_PROMPT to assess client churn risk.
    
    IMPORTANT: Only returns NEW keys, not the full state.
    This allows parallel execution with RAG agent.
    """
    print("\n" + "=" * 70)
    print("🔍 [ANALYSIS AGENT] Starting risk analysis using LLM...")
    print("=" * 70)
    
    usage_data = state.get("usage_data", [])
    jira_tickets_raw = state.get("jira_tickets", [])
    
    print(f"   📊 Clients to analyze: {len(usage_data)}")
    print(f"   🎫 JIRA tickets: {len(jira_tickets_raw)}")
    
    jira_tickets = simplify_jira_tickets(jira_tickets_raw)
    
    prompt = build_analysis_prompt(
        usage_data=json.dumps(usage_data, indent=2),
        jira_tickets=json.dumps(jira_tickets, indent=2)
    )
    
    print("   🤖 Sending to LLM for risk assessment...")
    llm = get_llm()
    messages = [
        SystemMessage(content=ANALYSIS_SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ]
    
    response = llm.invoke(messages)
    raw_response = response.content
    
    analysis_results = parse_llm_response(raw_response)
    
    if analysis_results:
        print(f"\n   ✅ Successfully analyzed {len(analysis_results)} clients")
    else:
        print("   ❌ Failed to parse analysis results")
        # Return ONLY the new keys this agent produces
        return {
            "analysis_results": [],
            "risky_clients": [],
            "raw_llm_response": raw_response,
            "errors": [f"Failed to parse analysis response"],
        }
    
    risky_clients = [
        client for client in analysis_results
        if client.get("risk_factor", "").lower() in ["high", "medium"]
    ]
    
    high_risk = sum(1 for c in risky_clients if c.get("risk_factor") == "high")
    medium_risk = sum(1 for c in risky_clients if c.get("risk_factor") == "medium")
    low_risk = len(analysis_results) - high_risk - medium_risk
    
    print(f"\n   📈 Risk Distribution:")
    print(f"      🔴 High Risk: {high_risk}")
    print(f"      🟡 Medium Risk: {medium_risk}")
    print(f"      🟢 Low Risk: {low_risk}")
    
    if risky_clients:
        print(f"\n   ⚠️ {len(risky_clients)} risky clients will be sent to Email Agent")
    
    print("=" * 70)
    
    # Return ONLY the new keys this agent produces
    # Do NOT spread **state - this causes parallel execution conflicts
    return {
        "analysis_results": analysis_results,
        "risky_clients": risky_clients,
        "raw_llm_response": raw_response,
    }
