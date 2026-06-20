import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from agent.state import CopilotAgentState
from tools.action_tools import propose_fleet_action
from typing import Dict, Any

def action_node(state: CopilotAgentState) -> Dict[str, Any]:
    company_id = state["company_context"]
    operator_id = state.get("operator_context", "admin-default")
    llm = ChatOpenAI(model="gpt-4o", temperature=0.0)
    llm_with_tools = llm.bind_tools([propose_fleet_action])
    system_instruction = f"You are the Operations Action Agent for company '{company_id}'."
    messages = [SystemMessage(content=system_instruction)] + list(state["messages"])
    response = llm_with_tools.invoke(messages)
    staged_proposals = []
    requires_approval = False
    if response.tool_calls:
        for call in response.tool_calls:
            args = call["args"]
            res_str = propose_fleet_action.invoke({
                "action_type": args.get("action_type"),
                "company_id": company_id,
                "operator_id": operator_id,
                "details": args.get("details"),
                "justification": args.get("justification")
            })
            parsed = json.loads(res_str)
            if parsed.get("status") == "STAGED":
                staged_proposals.append(parsed)
                requires_approval = True
    return {
        "messages": [response],
        "staged_proposals": staged_proposals,
        "requires_approval": requires_approval,
        "current_agent_turn": "approval_node" if requires_approval else "response_node"
    }
