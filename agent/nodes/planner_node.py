from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from agent.state import CopilotAgentState
from prompts.planner_prompt import PLANNER_SYSTEM_PROMPT
from typing import Dict, Any
import os

def planner_node(state: CopilotAgentState) -> Dict[str, Any]:
    company_id = state.get("company_context", "UNAUTHORIZED")
    if company_id == "UNAUTHORIZED" or not company_id:
        return {"security_violation": True, "current_agent_turn": "guardrail_node"}
    
    formatted_prompt = PLANNER_SYSTEM_PROMPT.format(company_id=company_id)
    
    llm = ChatOpenAI(
        model="openai/gpt-4o-mini",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_api_base=os.getenv("OPENAI_BASE_URL", "https://openrouter.ai"),
        temperature=0.0,
        default_headers={"HTTP-Referer": "http://localhost:8000", "X-Title": "Rayda Fleet Copilot"}
    )
    
    api_messages = [
        SystemMessage(content=formatted_prompt),
        HumanMessage(content="\n".join(state["conversation_history"]))
    ]
    response = llm.invoke(api_messages)
    text = response.content.lower()
    
    if "guardrail" in text or "violation" in text:
        next_turn = "guardrail_node"
    elif "action_node" in text or "propose" in text:
        next_turn = "action_node"
    elif "analytics_node" in text or "trend" in text or "degradation" in text:
        next_turn = "analytics_node"
    else:
        next_turn = "telemetry_node"
        
    return {
        "conversation_history": [f"Planner choice: {next_turn}"],
        "current_agent_turn": next_turn
    }
