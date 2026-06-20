from agent.state import CopilotAgentState
from typing import Dict, Any

def approval_node(state: CopilotAgentState) -> Dict[str, Any]:
    requires_hold = len(state.get("staged_proposals", [])) > 0
    return {
        "requires_approval": requires_hold,
        "current_agent_turn": "response_node"
    }
