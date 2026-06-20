# # agent/nodes/response_node.py

# from langchain_openai import ChatOpenAI
# from langchain_core.messages import SystemMessage, HumanMessage
# from agent.state import CopilotAgentState
# from prompts.response_prompt import RESPONSE_SYSTEM_PROMPT
# from typing import Dict, Any


# def response_node(state: CopilotAgentState) -> Dict[str, Any]:
#     """Produces final grounded answer while preserving state."""

#     if state.get("security_violation", False):
#         return {
#             "response_text": "Request blocked by security policy.",
#             "current_agent_turn": "end"
#         }

#     company_id = state["company_context"]

#     evidence = state.get("gathered_evidence", [])
#     staged = state.get("staged_proposals", [])

#     prompt = RESPONSE_SYSTEM_PROMPT.format(
#         company_id=company_id
#     )

#     context = f"""
# Telemetry Evidence:

# {evidence}

# Staged Actions:

# {staged}
# """

#     user_question = state["conversation_history"][-1]

#     llm = ChatOpenAI(
#         model="gpt-4o",
#         temperature=0
#     )

#     response = llm.invoke(
#         [
#             SystemMessage(content=prompt),
#             SystemMessage(content=context),
#             HumanMessage(content=user_question)
#         ]
#     )

#     return {
#         "conversation_history": state["conversation_history"],
#         "gathered_evidence": evidence,
#         "staged_proposals": staged,
#         "requires_approval": state.get("requires_approval", False),
#         "response_text": response.content,
#         "current_agent_turn": "end"
#     }











# agent/nodes/response_node.py
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, AIMessage
from agent.state import CopilotAgentState
from prompts.response_prompt import RESPONSE_SYSTEM_PROMPT
from typing import Dict, Any

def response_node(state: CopilotAgentState) -> Dict[str, Any]:
    """Formats findings and empirical evidence into a final response for the user."""
    company_id = state["company_context"]
    
    if state.get("security_violation", False):
        return {"current_agent_turn": "end"}
        
    formatted_prompt = RESPONSE_SYSTEM_PROMPT.format(company_id=company_id)
    
    # Append structured evidence summaries to anchor the model's response context
    evidence_summary = "\n### Gathered Telemetry Evidence Context:\n" + str(state.get("gathered_evidence", []))
    if state.get("staged_proposals"):
        evidence_summary += "\n### Staged Actions Queue:\n" + str(state.get("staged_proposals"))
        
    llm = ChatOpenAI(model="gpt-4o", temperature=0.0)
    
    messages = [
        SystemMessage(content=formatted_prompt),
        SystemMessage(content=evidence_summary)
    ] + list(state["messages"])
    
    response = llm.invoke(messages)
    return {
        "messages": [AIMessage(content=response.content)],
        "current_agent_turn": "end"
    }
