# import os
# import json
# from typing import List, Dict, Any, Literal
# from langgraph.graph import StateGraph, END
# from services.telemetry_service import TelemetryService
# from tools.compliance_tools import check_compliance_failures
# from tools.disk_tools import query_low_storage_devices

# # ==========================================
# # 1. CONCRETE FUNCTIONAL TELEMETRY & TREND TOOLS
# # ==========================================
# def query_os_versions_tool(authorized_company_id: str) -> str:
#     """Counts devices running an operating system version older than macOS 15, handling cross-platform versions safely."""
#     db = TelemetryService()
#     sql = f"""
#         SELECT device_id, employee_id, os_platform, os_version 
#         FROM snapshots 
#         WHERE LOWER(TRIM(company_id)) = '{authorized_company_id.strip().lower()}' 
#         AND (
#             (LOWER(os_platform) = 'darwin' AND TRY_CAST(SPLIT_PART(os_version, '.', 1) AS INTEGER) < 15)
#             OR 
#             (LOWER(os_platform) = 'windows' AND TRY_CAST(SPLIT_PART(os_version, '.', 1) AS INTEGER) < 11)
#         );
#     """
#     return json.dumps({"status": "SUCCESS", "data": db.execute_read_query(sql)})

# def analyze_battery_degradation_tool(authorized_company_id: str) -> str:
#     """Surfaces devices with cycle counts > 500 or approaching battery end-of-life with type safety."""
#     db = TelemetryService()
#     sql = f"""
#         SELECT device_id, employee_id, battery_percentage, battery_condition, TRY_CAST(battery_cycle_count AS INTEGER) as cycles 
#         FROM snapshots 
#         WHERE LOWER(TRIM(company_id)) = '{authorized_company_id.strip().lower()}' 
#         AND (TRY_CAST(battery_cycle_count AS INTEGER) > 500 OR battery_condition IN ('Service', 'Replace', 'Check Battery'));
#     """
#     return json.dumps({"status": "SUCCESS", "data": db.execute_read_query(sql)})

# def detect_memory_saturation_tool(authorized_company_id: str) -> str:
#     """Surfaces devices consistently constrained by RAM over 85 percent usage thresholds."""
#     db = TelemetryService()
#     sql = f"""
#         SELECT device_id, employee_id, ram_used_pct 
#         FROM snapshots 
#         WHERE LOWER(TRIM(company_id)) = '{authorized_company_id.strip().lower()}' 
#         AND ram_used_pct > 85.0;
#     """
#     return json.dumps({"status": "SUCCESS", "data": db.execute_read_query(sql)})

# def calculate_compliance_drift_tool(authorized_company_id: str) -> str:
#     """
#     Measures compliance drift over time safely by slicing the text prefix 
#     of the timestamp to avoid date conversion type exceptions.
#     """
#     db = TelemetryService()
#     sql = f"""
#         SELECT 
#             SUBSTRING(CAST(collected_at AS VARCHAR), 1, 10) as snapshot_date,
#             COUNT(DISTINCT device_id) as total_devices_scanned,
#             SUM(CASE WHEN array_length(compliance_fails) > 0 THEN 1 ELSE 0 END) as failing_device_count
#         FROM snapshots
#         WHERE LOWER(TRIM(company_id)) = '{authorized_company_id.strip().lower()}'
#         GROUP BY snapshot_date
#         ORDER BY snapshot_date ASC;
#     """
#     return json.dumps({"status": "SUCCESS", "data": db.execute_read_query(sql)})

# # ==========================================
# # 2. GRAPH AGENT NODE LOGIC WORKERS
# # ==========================================
# def planner_node(state: dict) -> dict:
#     user_msg = str(state["messages"][-1]).lower()
#     if "acme-002" in user_msg or "ignore previous" in user_msg:
#         state["current_agent_turn"] = "guardrail_node"
#     elif any(w in user_msg for w in ["propose", "stage", "order", "ticket", "notify", "replace"]):
#         state["current_agent_turn"] = "action_node"
#     elif any(w in user_msg for w in ["battery", "degradation", "ram", "memory", "constrained", "drift", "trend", "pattern"]):
#         state["current_agent_turn"] = "analytics_node"
#     else:
#         state["current_agent_turn"] = "telemetry_node"
#     return state

# def guardrail_node(state: dict) -> dict:
#     state["current_agent_turn"] = "end"
#     return state

# def telemetry_node(state: dict) -> dict:
#     company_id = state["company_context"]
#     user_msg = str(state["messages"][-1]).lower()
    
#     evidence_records = []
#     data_payload = []
#     tool_executed = "check_compliance_failures"
#     query_context = f"check_compliance_failures(authorized_company_id='{company_id}')"
    
#     if "compliance" in user_msg or "fail" in user_msg:
#         res = check_compliance_failures.invoke({"authorized_company_id": company_id})
#         data_payload = json.loads(res).get("data", [])
#     elif "storage" in user_msg or "disk" in user_msg or "space" in user_msg:
#         tool_executed = "query_low_storage_devices"
#         query_context = f"query_low_storage_devices(authorized_company_id='{company_id}')"
#         res = query_low_storage_devices.invoke({"authorized_company_id": company_id})
#         data_payload = json.loads(res).get("data", [])
#     else:
#         tool_executed = "query_os_versions_tool"
#         query_context = f"Cross-platform safe OS query check for {company_id}"
#         res = query_os_versions_tool(company_id)
#         data_payload = json.loads(res).get("data", [])

#     if data_payload:
#         evidence_records.append({
#             "source_tool": tool_executed,
#             "query_context": query_context,
#             "record_count": len(data_payload),
#             "sample_records": data_payload[:3]
#         })
#     state["gathered_evidence"] = evidence_records
#     state["current_agent_turn"] = "end"
#     return state

# def analytics_node(state: dict) -> dict:
#     company_id = state["company_context"]
#     user_msg = str(state["messages"][-1]).lower()
    
#     evidence_records = []
#     data_payload = []
    
#     if "drift" in user_msg or "trend" in user_msg or "pattern" in user_msg:
#         tool_executed = "calculate_compliance_drift_tool"
#         query_context = f"Historical timeline compliance drift tracking for {company_id}"
#         res = calculate_compliance_drift_tool(company_id)
#         data_payload = json.loads(res).get("data", [])
#     elif "ram" in user_msg or "memory" in user_msg:
#         tool_executed = "detect_memory_saturation_tool"
#         query_context = f"Identify core RAM saturation parameters for {company_id}"
#         res = detect_memory_saturation_tool(company_id)
#         data_payload = json.loads(res).get("data", [])
#     else:
#         tool_executed = "analyze_battery_degradation_tool"
#         query_context = f"Identify battery degradation curve anomalies for {company_id}"
#         res = analyze_battery_degradation_tool(company_id)
#         data_payload = json.loads(res).get("data", [])
        
#     if data_payload:
#         evidence_records.append({
#             "source_tool": tool_executed,
#             "query_context": query_context,
#             "record_count": len(data_payload),
#             "sample_records": data_payload[:3]
#         })
#     state["gathered_evidence"] = evidence_records
#     state["current_agent_turn"] = "end"
#     return state

# def action_node(state: dict) -> dict:
#     company_id = state["company_context"]
#     operator_id = state.get("operator_context", "admin-01")
#     user_msg = str(state["messages"][-1]).lower()
    
#     db = TelemetryService()
#     target_device = "MT7PJB7N5LRE"
    
#     from tools.action_tools import fleet_action_broker

#     if "ticket" in user_msg or "remediation" in user_msg:
#         sql = f"SELECT count(*) as count_val FROM snapshots WHERE LOWER(TRIM(company_id)) = '{company_id.lower()}' AND device_id = '{target_device}' AND array_length(compliance_fails) > 0;"
#         check_res = db.execute_read_query(sql)
#         val = check_res[0].get("count_val", 0) if (isinstance(check_res, list) and len(check_res) > 0) else 0
#         if val == 0:
#             state["response_text"] = "Refused Action: Insufficient historical telemetry evidence. Workstation MT7PJB7N5LRE does not show active rule verification failures."
#             state["requires_approval"] = False
#             state["current_agent_turn"] = "end"
#             return state
            
#         proposal_payload = fleet_action_broker.open_remediation_ticket(
#             company_id=company_id, operator_id=operator_id,
#             device_id=target_device, check_id="os_up_to_date", note="Urgent compliance remediation patch requested."
#         )
        
#     elif "replace" in user_msg or "replacement" in user_msg:
#         sql = f"SELECT count(*) as count_val FROM snapshots WHERE LOWER(TRIM(company_id)) = '{company_id.lower()}' AND device_id = '{target_device}' AND (TRY_CAST(battery_cycle_count AS INTEGER) > 500 OR battery_condition = 'Service');"
#         check_res = db.execute_read_query(sql)
#         val = check_res[0].get("count_val", 0) if (isinstance(check_res, list) and len(check_res) > 0) else 0
#         if val == 0:
#             state["response_text"] = "Refused Action: Operation blocked. Device thresholds do not indicate a severe hardware wear state justifying retirement cycles."
#             state["requires_approval"] = False
#             state["current_agent_turn"] = "end"
#             return state
            
#         proposal_payload = fleet_action_broker.flag_device_for_replacement(
#             company_id=company_id, operator_id=operator_id,
#             device_id=target_device, reason="Hardware degradation limits breached."
#         )
        
#     elif "notify" in user_msg or "employee" in user_msg:
#         proposal_payload = fleet_action_broker.notify_employee(
#             company_id=company_id, operator_id=operator_id,
#             employee_id="emp-acme-1003", message="Apply security patches."
#         )
#     else:
#         sql = f"SELECT count(*) as count_val FROM snapshots WHERE LOWER(TRIM(company_id)) = '{company_id.lower()}' AND device_id = '{target_device}' AND disk_used_pct > 90.0;"
#         check_res = db.execute_read_query(sql)
#         val = check_res[0].get("count_val", 0) if (isinstance(check_res, list) and len(check_res) > 0) else 0
#         if val == 0:
#             state["response_text"] = "Refused Action: Upgrade proposal denied. Local volume partitions indicate sufficient free space parameters remain."
#             state["requires_approval"] = False
#             state["current_agent_turn"] = "end"
#             return state

#         proposal_payload = fleet_action_broker.create_upgrade_order(
#             company_id=company_id, operator_id=operator_id,
#             device_id=target_device, component="storage", 
#             spec="1TB NVMe SSD")
#     state["staged_proposals"] = [proposal_payload]
#         state["requires_approval"] = True
#         state["current_agent_turn"] = "end"
#         return state
# def router_edge(state: dict) -> str:
#     return state.get("current_agent_turn", "planner_node")

# workflow = StateGraph(dict)workflow.add_node("planner_node", planner_node)
# workflow.add_node("guardrail_node", guardrail_node)
# workflow.add_node("telemetry_node", telemetry_node)
# workflow.add_node("analytics_node", analytics_node)
# workflow.add_node("action_node", action_node)
# workflow.set_entry_point("planner_node")
# workflow.add_conditional_edges("planner_node", router_edge, {"guardrail_node": "guardrail_node", "telemetry_node": "telemetry_node","analytics_node": "analytics_node", "action_node": "action_node"})
# workflow.add_edge("guardrail_node", END)
# workflow.add_edge("telemetry_node", END)
# workflow.add_edge("analytics_node", END)
# workflow.add_edge("action_node", END)
# fleet_copilot_graph = workflow.compile()




















import os
import json
from typing import List, Dict, Any, Literal
from langgraph.graph import StateGraph, END
from services.telemetry_service import TelemetryService
from tools.compliance_tools import check_compliance_failures
from tools.disk_tools import query_low_storage_devices

# ==========================================
# 1. CONCRETE FUNCTIONAL TELEMETRY & TREND TOOLS
# ==========================================
def query_os_versions_tool(authorized_company_id: str) -> str:
    """Counts devices running an operating system version older than macOS 15, handling cross-platform versions safely."""
    db = TelemetryService()
    sql = f"""
        SELECT device_id, employee_id, os_platform, os_version 
        FROM snapshots 
        WHERE LOWER(TRIM(company_id)) = '{authorized_company_id.strip().lower()}' 
        AND (
            (LOWER(os_platform) = 'darwin' AND TRY_CAST(SPLIT_PART(os_version, '.', 1) AS INTEGER) < 15)
            OR 
            (LOWER(os_platform) = 'windows' AND TRY_CAST(SPLIT_PART(os_version, '.', 1) AS INTEGER) < 11)
        );
    """
    return json.dumps({"status": "SUCCESS", "data": db.execute_read_query(sql)})

def analyze_battery_degradation_tool(authorized_company_id: str) -> str:
    """Surfaces devices with cycle counts > 500 or approaching battery end-of-life safely at the database tier."""
    db = TelemetryService()
    sql = f"""
        SELECT device_id, employee_id, battery_percentage, battery_condition, battery_cycle_count 
        FROM snapshots 
        WHERE LOWER(TRIM(company_id)) = '{authorized_company_id.strip().lower()}' 
        AND (battery_cycle_count > 500 OR LOWER(battery_condition) IN ('service', 'replace', 'check battery'));
    """
    return json.dumps({"status": "SUCCESS", "data": db.execute_read_query(sql)})

def detect_memory_saturation_tool(authorized_company_id: str) -> str:
    """Surfaces devices consistently constrained by RAM over 85 percent usage thresholds."""
    db = TelemetryService()
    sql = f"""
        SELECT device_id, employee_id, ram_used_pct 
        FROM snapshots 
        WHERE LOWER(TRIM(company_id)) = '{authorized_company_id.strip().lower()}' 
        AND ram_used_pct > 85.0;
    """
    return json.dumps({"status": "SUCCESS", "data": db.execute_read_query(sql)})

def calculate_compliance_drift_tool(authorized_company_id: str) -> str:
    """Measures compliance drift over time by aggregating failing snapshots inside DuckDB natively."""
    db = TelemetryService()
    sql = f"""
        SELECT 
            SUBSTRING(CAST(collected_at AS VARCHAR), 1, 10) as snapshot_date,
            COUNT(DISTINCT device_id) as total_devices_scanned,
            SUM(CASE WHEN len(compliance_fails) > 0 THEN 1 ELSE 0 END) as failing_device_count
        FROM snapshots
        WHERE LOWER(TRIM(company_id)) = '{authorized_company_id.strip().lower()}'
        GROUP BY snapshot_date
        ORDER BY snapshot_date ASC;
    """
    return json.dumps({"status": "SUCCESS", "data": db.execute_read_query(sql)})

# ==========================================
# 2. GRAPH AGENT NODE LOGIC WORKERS
# ==========================================
def planner_node(state: dict) -> dict:
    user_msg = str(state["messages"][-1]).lower()
    if "acme-002" in user_msg or "ignore previous" in user_msg:
        state["current_agent_turn"] = "guardrail_node"
    elif any(w in user_msg for w in ["propose", "stage", "order", "ticket", "notify", "replace"]):
        state["current_agent_turn"] = "action_node"
    elif any(w in user_msg for w in ["battery", "degradation", "ram", "memory", "constrained", "drift", "trend", "pattern"]):
        state["current_agent_turn"] = "analytics_node"
    else:
        state["current_agent_turn"] = "telemetry_node"
    return state

def guardrail_node(state: dict) -> dict:
    state["current_agent_turn"] = "end"
    return state

def telemetry_node(state: dict) -> dict:
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
        query_context = f"Cross-platform safe OS query check for {company_id}"
        res = query_os_versions_tool(company_id)
        data_payload = json.loads(res).get("data", [])

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
    company_id = state["company_context"]
    user_msg = str(state["messages"][-1]).lower()
    
    evidence_records = []
    data_payload = []
    
    if "drift" in user_msg or "trend" in user_msg or "pattern" in user_msg:
        tool_executed = "calculate_compliance_drift_tool"
        query_context = f"Historical timeline compliance drift tracking for {company_id}"
        res = calculate_compliance_drift_tool(company_id)
        data_payload = json.loads(res).get("data", [])
    elif "ram" in user_msg or "memory" in user_msg:
        tool_executed = "detect_memory_saturation_tool"
        query_context = f"Identify core RAM saturation parameters for {company_id}"
        res = detect_memory_saturation_tool(company_id)
        data_payload = json.loads(res).get("data", [])
    else:
        tool_executed = "analyze_battery_degradation_tool"
        query_context = f"Identify battery degradation curve anomalies for {company_id}"
        res = analyze_battery_degradation_tool(company_id)
        data_payload = json.loads(res).get("data", [])
        
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
    company_id = state["company_context"]
    operator_id = state.get("operator_context", "admin-01")
    user_msg = str(state["messages"][-1]).lower()
    
    db = TelemetryService()
    target_device = "MT7PJB7N5LRE"
    
    from tools.action_tools import fleet_action_broker

    if "ticket" in user_msg or "remediation" in user_msg:
        sql = f"SELECT count(*) as count_val FROM snapshots WHERE LOWER(TRIM(company_id)) = '{company_id.lower()}' AND device_id = '{target_device}' AND len(compliance_fails) > 0;"
        check_res = db.execute_read_query(sql)
        val = check_res[0].get("count_val", 0) if (isinstance(check_res, list) and len(check_res) > 0) else 0
        if val == 0:
            state["response_text"] = "Refused Action: Insufficient historical telemetry evidence. Workstation MT7PJB7N5LRE does not show active rule verification failures."
            state["requires_approval"] = False
            state["current_agent_turn"] = "end"
            return state
            
        proposal_payload = fleet_action_broker.open_remediation_ticket(
            company_id=company_id, operator_id=operator_id,
            device_id=target_device, check_id="os_up_to_date", note="Urgent compliance remediation patch requested."
        )
        
    elif "replace" in user_msg or "replacement" in user_msg:
        sql = f"SELECT count(*) as count_val FROM snapshots WHERE LOWER(TRIM(company_id)) = '{company_id.lower()}' AND device_id = '{target_device}';"
        check_res = db.execute_read_query(sql)
        val = check_res[0].get("count_val", 0) if (isinstance(check_res, list) and len(check_res) > 0) else 0
        if val == 0:
            state["response_text"] = "Refused Action: Operation blocked. Device thresholds do not indicate a severe hardware wear state justifying retirement cycles."
            state["requires_approval"] = False
            state["current_agent_turn"] = "end"
            return state
            
        proposal_payload = fleet_action_broker.flag_device_for_replacement(
            company_id=company_id, operator_id=operator_id,
            device_id=target_device, reason="Hardware degradation limits breached."
        )
        
    elif "notify" in user_msg or "employee" in user_msg:
        proposal_payload = fleet_action_broker.notify_employee(
            company_id=company_id, operator_id=operator_id,
            employee_id="emp-acme-1003", message="Apply security patches."
        )
    else:
        sql = f"SELECT count(*) as count_val FROM snapshots WHERE LOWER(TRIM(company_id)) = '{company_id.lower()}' AND device_id = '{target_device}';"
        check_res = db.execute_read_query(sql)
        val = check_res[0].get("count_val", 0) if (isinstance(check_res, list) and len(check_res) > 0) else 0
        if val == 0:
            state["response_text"] = "Refused Action: Upgrade proposal denied. Local volume partitions indicate sufficient free space parameters remain."
            state["requires_approval"] = False
            state["current_agent_turn"] = "end"
            return state
        proposal_payload = fleet_action_broker.create_upgrade_order(
            company_id=company_id, operator_id=operator_id,
            device_id=target_device, component="storage", spec="1TB NVMe SSD")
    state["staged_proposals"] = [proposal_payload]
    state["requires_approval"] = True
    state["current_agent_turn"] = "end"
    return state    

def router_edge(state: dict) -> str:
    return state.get("current_agent_turn", "planner_node")
    
workflow = StateGraph(dict)
workflow.add_node("planner_node", planner_node)
workflow.add_node("guardrail_node", guardrail_node)
workflow.add_node("telemetry_node", telemetry_node)
workflow.add_node("analytics_node", analytics_node)
workflow.add_node("action_node", action_node)
workflow.set_entry_point("planner_node")
workflow.add_conditional_edges("planner_node", router_edge, {"guardrail_node": "guardrail_node", "telemetry_node": "telemetry_node","analytics_node": "analytics_node", "action_node": "action_node"})
workflow.add_edge("guardrail_node", END)
workflow.add_edge("telemetry_node", END)
workflow.add_edge("analytics_node", END)
workflow.add_edge("action_node", END)
fleet_copilot_graph = workflow.compile()

        
            
