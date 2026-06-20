from langchain_core.messages import AIMessage
from agent.state import CopilotAgentState
from typing import Dict, Any

def guardrail_node(state: CopilotAgentState) -> Dict[str, Any]:
    rejection_message = (
        "Security Alert: The requested operation has been blocked by the security layer. "
        "Cross-company tenant access queries are strictly forbidden on this platform."
    )
    return {
        "messages": [AIMessage(content=rejection_message)],
        "security_violation": True,
        "current_agent_turn": "response_node"
    }
