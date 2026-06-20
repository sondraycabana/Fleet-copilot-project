import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from agent.state import CopilotAgentState
from tools.battery_tools import analyze_battery_degradation
from tools.memory_tools import detect_memory_saturation
from services.evidence_service import EvidenceService
from typing import Dict, Any

def analytics_node(state: CopilotAgentState) -> Dict[str, Any]:
    company_id = state["company_context"]
    llm = ChatOpenAI(model="gpt-4o", temperature=0.0)
    tools = [analyze_battery_degradation, detect_memory_saturation]
    llm_with_tools = llm.bind_tools(tools)
    system_instruction = (
        f"You are the Trend Analytics Agent for company '{company_id}'. "
        "Analyze data patterns over time to find anomalies. "
    )
    messages = [SystemMessage(content=system_instruction)] + list(state["messages"])
    response = llm_with_tools.invoke(messages)
    evidence_records = []
    if response.tool_calls:
        for call in response.tool_calls:
            if call["name"] == "analyze_battery_degradation":
                res_str = analyze_battery_degradation.invoke({"authorized_company_id": company_id})
            else:
                res_str = detect_memory_saturation.invoke({"authorized_company_id": company_id})
            parsed = json.loads(res_str)
            if parsed.get("status") == "SUCCESS":
                evidence = EvidenceService.construct_evidence_block(
                    tool_name=call["name"],
                    query_executed=call["name"],
                    data_returned=parsed.get("data", [])
                )
                evidence_records.append(evidence)
    return {
        "messages": [response],
        "gathered_evidence": evidence_records,
        "current_agent_turn": "response_node"
    }
