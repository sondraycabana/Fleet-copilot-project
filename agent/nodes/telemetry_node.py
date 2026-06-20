import json
from agent.state import CopilotAgentState
from tools.compliance_tools import check_compliance_failures
from tools.disk_tools import query_low_storage_devices
from services.evidence_service import EvidenceService
from typing import Dict, Any

def telemetry_node(state: CopilotAgentState) -> Dict[str, Any]:
    company_id = state["company_context"]
    user_message = state["conversation_history"][-2].lower() if len(state["conversation_history"]) > 1 else ""
    
    evidence_records = []
    tool_executed = "execute_fleet_query"
    query_context = "Fallback structural scan query"
    data_payload = []

    if "compliance" in user_message or "failing" in user_message:
        tool_executed = "check_compliance_failures"
        query_context = f"check_compliance_failures(authorized_company_id='{company_id}')"
        res_str = check_compliance_failures.invoke({"authorized_company_id": company_id})
        parsed = json.loads(res_str)
        data_payload = parsed.get("data", [])
    elif "storage" in user_message or "disk" in user_message or "space" in user_message:
        tool_executed = "query_low_storage_devices"
        query_context = f"query_low_storage_devices(authorized_company_id='{company_id}')"
        res_str = query_low_storage_devices.invoke({"authorized_company_id": company_id})
        parsed = json.loads(res_str)
        data_payload = parsed.get("data", [])

    if data_payload:
        evidence = EvidenceService.construct_evidence_block(
            tool_name=tool_executed,
            query_executed=query_context,
            data_returned=data_payload
        )
        evidence_records.append(evidence)
                
    return {
        "conversation_history": ["Telemetry Agent fetched data logs from DuckDB database successfully."],
        "gathered_evidence": evidence_records,
        "current_agent_turn": "response_node"
    }
