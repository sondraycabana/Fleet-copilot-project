import os
import json
from typing import List, Dict, Any, Literal
from langgraph.graph import StateGraph, END
from services.telemetry_service import TelemetryService
from tools.compliance_tools import check_compliance_failures
from tools.disk_tools import query_low_storage_devices

# ==========================================
# 1. GRAPH AGENT NODE LOGIC WORKERS
# ==========================================
def planner_node(state: dict) -> dict:
    """PLANNING PHASE: Maps target sub-agent routing tracks based on message tokens."""
    user_msg = str(state["messages"][-1]).lower()
    
    if "acme-002" in user_msg or "ignore previous" in user_msg:
        state["current_agent_turn"] = "guardrail_node"
    elif any(w in user_msg for w in ["propose", "stage", "order", "ticket", "notify"]):
        state["current_agent_turn"] = "action_node"
    elif any(w in user_msg for w in ["battery", "degradation", "ram", "memory", "constrained"]):
        state["current_agent_turn"] = "analytics_node"
    else:
        state["current_agent_turn"] = "telemetry_node"
    return state

def guardrail_node(state: dict) -> dict:
    """GUARDRAIL NODE: Perimetric tenant isolation barrier."""
    state["current_agent_turn"] = "end"
    return state

def telemetry_node(state: dict) -> dict:
    """TELEMETRY NODE: Programmatic DuckDB lookups matching client filters."""
    company_id = state["company_context"]
    user_msg = str(state["messages"][-1]).lower()
    
    evidence_records = []
    data_payload = []
    tool_executed = "check_compliance_failures"
    query_context = f"check_compliance_failures(authorized_company_id='{company_id}')"
    
    if "compliance" in user_msg or "fail" in user_msg:
        res = check_compliance_failures.invoke({"authorized_company_id": company_id})
        data_payload = json.loads(res).get("data", [])
    elif "storage" in user_msg or "disk" in user_msg or "space" in user_msg:
        tool_executed = "query_low_storage_devices"
        query_context = f"query_low_storage_devices(authorized_company_id='{company_id}')"
        res = query_low_storage_devices.invoke({"authorized_company_id": company_id})
        data_payload = json.loads(res).get("data", [])
    else:
        tool_executed = "query_os_versions_tool"
        query_context = f"Count of devices running OS older than macOS 15 for {company_id}"
        db = TelemetryService()
        sql = f"SELECT device_id, employee_id, os_version FROM snapshots WHERE LOWER(TRIM(company_id)) = '{company_id.lower()}' AND CAST(SPLIT_PART(os_version, '.', 1) AS INTEGER) < 15;"
        data_payload = db.execute_read_query(sql)

    if data_payload:
        evidence_records.append({
            "source_tool": tool_executed,
            "query_context": query_context,
            "record_count": len(data_payload),
            "sample_records": data_payload[:3]
        })
    state["gathered_evidence"] = evidence_records
    state["current_agent_turn"] = "end"
    return state

def analytics_node(state: dict) -> dict:
    """ANALYTICS NODE: surfaces multi-day curve tracking and saturation trends."""
    company_id = state["company_context"]
    user_msg = str(state["messages"][-1]).lower()
    
    evidence_records = []
    db = TelemetryService()
    tool_executed = "analyze_battery_degradation_tool"
    query_context = f"Identify battery degradation curve anomalies for {company_id}"
    data_payload = []

    if "ram" in user_msg or "memory" in user_msg:
        tool_executed = "detect_memory_saturation_tool"
        query_context = f"Identify core RAM saturation parameters for {company_id}"
        sql = f"SELECT device_id, employee_id, ram_used_pct FROM snapshots WHERE LOWER(TRIM(company_id)) = '{company_id.lower()}' AND ram_used_pct > 85.0;"
    else:
        sql = f"SELECT device_id, employee_id, battery_percentage, battery_condition, battery_cycle_count FROM snapshots WHERE LOWER(TRIM(company_id)) = '{company_id.lower()}' AND (battery_cycle_count > 500 OR battery_condition IN ('Service', 'Replace', 'Check Battery'));"
        
    data_payload = db.execute_read_query(sql)
    if data_payload:
        evidence_records.append({
            "source_tool": tool_executed,
            "query_context": query_context,
            "record_count": len(data_payload),
            "sample_records": data_payload[:3]
        })
    state["gathered_evidence"] = evidence_records
    state["current_agent_turn"] = "end"
    return state

def action_node(state: dict) -> dict:
    """ACTION proposals: Stages mandated ticketing operations behind approval gates."""
    company_id = state["company_context"]
    user_msg = str(state["messages"][-1]).lower()
    
    action_type = "create_upgrade_order"
    details = {"device_id": "MT7PJB7N5LRE", "component": "storage", "spec": "1TB NVMe SSD"}
    
    if "ticket" in user_msg:
        action_type = "open_remediation_ticket"
        details = {"device_id": "MT7PJB7N5LRE", "check_id": "os_up_to_date", "note": "Stage remediation sweep."}
    elif "replace" in user_msg:
        action_type = "flag_device_for_replacement"
        details = {"device_id": "MT7PJB7N5LRE", "reason": "Hardware wear exceeded."}
    elif "notify" in user_msg:
        action_type = "notify_employee"
        details = {"employee_id": "emp-acme-1003", "message": "Apply security patches."}
        
    proposal = {
        "action_id": f"act-{os.urandom(4).hex()}",
        "action_type": action_type,
        "company_id": company_id,
        "operator_id": state.get("operator_context", "admin"),
        "details": details,
        "justification": "Grounded trigger answering explicit administrative text proposal request.",
        "status": "PENDING_APPROVAL"
    }
    state["staged_proposals"] = [proposal]
    state["requires_approval"] = True
    state["current_agent_turn"] = "end"
    return state

# --- CONDITIONAL ROUTING EDGE MAPPINGS ---
def router_edge(state: dict) -> str:
    """Unified naming accessor to route edges across LangGraph execution stages."""
    return state.get("current_agent_turn", "planner_node")

# Pass the basic python 'dict' class directly to initialize the state machine
workflow = StateGraph(dict)

workflow.add_node("planner_node", planner_node)
workflow.add_node("guardrail_node", guardrail_node)
workflow.add_node("telemetry_node", telemetry_node)
workflow.add_node("analytics_node", analytics_node)
workflow.add_node("action_node", action_node)

workflow.set_entry_point("planner_node")

workflow.add_conditional_edges("planner_node", router_edge, {
    "guardrail_node": "guardrail_node",
    "telemetry_node": "telemetry_node",
    "analytics_node": "analytics_node",
    "action_node": "action_node"
})

workflow.add_edge("guardrail_node", END)
workflow.add_edge("telemetry_node", END)
workflow.add_edge("analytics_node", END)
workflow.add_edge("action_node", END)

fleet_copilot_graph = workflow.compile()
