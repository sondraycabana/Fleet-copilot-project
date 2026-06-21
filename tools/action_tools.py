from services.audit_service import AuditService
import uuid
import json
import os

class ActionProposalEngine:
    def __init__(self, log_path: str = "logs/audit.log"):
        self.log_path = log_path
        self.audit = AuditService(log_path=log_path)

    def _stage_payload(self, company_id: str, operator_id: str, action_type: str, details: dict, justification: str) -> dict:
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
        # Enforce non-repudiation logging to physical storage file lines
        self.audit.log_event(
            company_id=company_id,
            operator_id=operator_id,
            action_type=action_type,
            status="STAGED_AWAITING_HUMAN_SIGN_OFF",
            payload=proposal_payload
        )
        return proposal_payload

    def create_upgrade_order(self, company_id: str, operator_id: str, device_id: str, component: str, spec: str) -> dict:
        """Proposes a hardware upgrade order for a fleet asset resource bottleneck."""
        details = {"device_id": device_id, "component": component, "spec": spec}
        justification = f"Automated trigger addressing critical resource constraints verified on asset {device_id}."
        return self._stage_payload(company_id, operator_id, "create_upgrade_order", details, justification)

    def open_remediation_ticket(self, company_id: str, operator_id: str, device_id: str, check_id: str, note: str) -> dict:
        """Registers an explicit tracking item within the IT service compliance remediation lane."""
        details = {"device_id": device_id, "check_id": check_id, "note": note}
        justification = f"Security workflow patch execution staging triggered by failing rule validation block {check_id}."
        return self._stage_payload(company_id, operator_id, "open_remediation_ticket", details, justification)

    def flag_device_for_replacement(self, company_id: str, operator_id: str, device_id: str, reason: str) -> dict:
        """Flags an end-of-life asset threshold breach, scheduling standard hardware retirement cycles."""
        details = {"device_id": device_id, "reason": reason}
        justification = f"Severe hardware degradation detected across tracking milestones. Replacement lifecycle required."
        return self._stage_payload(company_id, operator_id, "flag_device_for_replacement", details, justification)

    def notify_employee(self, company_id: str, operator_id: str, employee_id: str, message: str) -> dict:
        """Dispatches an enterprise outbox notification layout event prompting urgent local action."""
        details = {"employee_id": employee_id, "message": message}
        justification = f"IT compliance command requesting client-side runtime environment reboots or patches."
        return self._stage_payload(company_id, operator_id, "notify_employee", details, justification)

# Expose a singleton instance mapping tool calls cleanly
fleet_action_broker = ActionProposalEngine()
