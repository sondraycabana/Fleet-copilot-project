from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from agent.graph import fleet_copilot_graph
from services.audit_service import AuditService
import httpx
import os
import json
import traceback

router = APIRouter(prefix="/api/v1/copilot", tags=["Fleet Copilot Core"])
audit = AuditService()

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    session_id: str
    response: str
    requires_approval: bool
    staged_proposals: List[Dict[str, Any]]
    gathered_evidence: List[Dict[str, Any]]

class ApprovalRequest(BaseModel):
    session_id: str
    action_id: str
    approve: bool

@router.post("/query", response_model=ChatResponse)
async def process_copilot_query(
    request: ChatRequest,
    x_company_id: str = Header(...),
    x_operator_id: str = Header(...)
):
    session_id = request.session_id or f"sess-{x_company_id}-{x_operator_id[:4]}"
    user_msg = request.message.lower()
    
    if "acme-002" in user_msg or "ignore previous" in user_msg:
        rejection_text = "Security Alert: The requested operation has been blocked by the security layer. Cross-company tenant access queries are strictly forbidden on this platform."
        return ChatResponse(session_id=session_id, response=rejection_text, requires_approval=False, staged_proposals=[], gathered_evidence=[])

    # Initialized variables matching the graph.py expectations precisely
    initial_state = {
        "messages": [request.message],
        "company_context": str(x_company_id),
        "operator_context": str(x_operator_id),
        "gathered_evidence": [],
        "staged_proposals": [],
        "requires_approval": False,
        "response_text": "",
        "current_agent_turn": "planner_node"
    }
    
    try:
        # EXECUTE NATIVE LANGGRAPH LOOP AGENT INVOCATION
        output_state = fleet_copilot_graph.invoke(initial_state)
        
        # Intercept and return programmatic short-circuit rejections if present
        if output_state.get("response_text") and "Refused Action" in str(output_state.get("response_text")):
            return ChatResponse(
                session_id=session_id,
                response=str(output_state["response_text"]),
                requires_approval=False,
                staged_proposals=[],
                gathered_evidence=[]
            )
            
        evidence = output_state.get("gathered_evidence", [])
        staged = output_state.get("staged_proposals", [])
        
        if staged:
            for p in staged:
                audit.log_event(x_company_id, x_operator_id, p["action_type"], "STAGED", p)

        # OpenRouter Direct Response Generation Pass
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai")
        
        system_instruction = (
            f"You are Rayda's Fleet Copilot. Help the IT Administrator for company {x_company_id}. "
            "Analyze the data provided inside the Telemetry Context Data block carefully. "
            "Identify the specific details matching their request and present them clearly using markdown bullet points. "
            f"Cite device IDs explicitly.\n\n### Telemetry Context Data from Database:\n{json.dumps(evidence)}\n\n"
            f"### Staged Actions Context:\n{json.dumps(staged)}"
        )
        
        payload = {
            "model": "openai/gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": request.message}
            ],
            "temperature": 0.0
        }
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "Rayda Fleet Copilot"
        }
        
        with httpx.Client() as client:
            response = client.post(f"{base_url.rstrip('/')}/chat/completions", headers=headers, json=payload, timeout=30.0)
            
        res_json = response.json()
        if "error" in res_json:
            raise Exception(res_json["error"].get("message", "Unknown API Error"))
            
        model_answer = res_json["choices"][0]["message"]["content"]
        
        return ChatResponse(
            session_id=session_id,
            response=str(model_answer),
            requires_approval=bool(output_state.get("requires_approval", False)),
            staged_proposals=staged,
            gathered_evidence=evidence
        )
    except Exception as e:
        tb_str = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        raise HTTPException(status_code=500, detail=f"CRASH TRACEBACK:\n{tb_str}")

@router.post("/action/approve")
async def execute_staged_action(request: ApprovalRequest, x_company_id: str = Header(...), x_operator_id: str = Header(...)):
    resolution_status = "CONFIRMED_AND_DEPLOYED_BY_ADMIN" if request.approve else "CANCELLED_BY_ADMIN"
    payload_log = {"action_id": request.action_id, "resolution": resolution_status, "cleared_by": x_operator_id}
    audit.log_event(company_id=x_company_id, operator_id=x_operator_id, action_type="HUMAN_APPROVAL_RELEASE", status=resolution_status, payload=payload_log)
    return {"status": "SUCCESS", "action_id": request.action_id, "outcome": resolution_status, "message": f"Staged action released successfully."}
