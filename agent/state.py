from typing import TypedDict, List, Dict, Any

class CopilotAgentState(TypedDict):
    """
    Standard native state dict holding plain Python primitives.
    This eliminates any internal LangGraph list reducer or Pydantic serialization bugs.
    """
    conversation_history: List[str]
    company_context: str
    operator_context: str
    gathered_evidence: List[Dict[str, Any]]
    staged_proposals: List[Dict[str, Any]]
    requires_approval: bool
    security_violation: bool
    response_text: str
    current_agent_turn: str
