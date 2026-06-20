from services.audit_service import AuditService
import uuid
import json

class ActionProposalTool:
    def __init__(self, log_path: str = "logs/audit.log"):
        self.audit = AuditService(log_path=log_path)

    def invoke(self, args: dict) -> str:
        action_type = args.get("action_type", "unknown_action")
        company_id = args.get("company_id", "unknown_tenant")
        operator_id = args.get("operator_id", "system")
        details = args.get("details", {})
        justification = args.get("justification", "")
        
        # Generate a distinct, trackable cryptographic token for the human gate hook
        action_id = f"act-{uuid.uuid4().hex[:8]}"
        
        proposal_payload = {
            "action_id": action_id,
            "action_type": action_type,
            "company_id": company_id,
            "operator_id": operator_id,
            "details": details,
            "justification": justification,
            "status": "PENDING_APPROVAL"
        }
        
        # Enforce hard persistence into the physical audit log ledger
        self.audit.log_event(
            company_id=company_id,
            operator_id=operator_id,
            action_type=action_type,
            status="STAGED_AWAITING_HUMAN_SIGN_OFF",
            payload=proposal_payload
        )
        
        return json.dumps({
            "status": "STAGED",
            "action_id": action_id,
            "payload": proposal_payload
        })

propose_fleet_action = ActionProposalTool()
