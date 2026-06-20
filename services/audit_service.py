import os
import json
from datetime import datetime, timezone

class AuditService:
    def __init__(self, log_path: str = "logs/audit.log"):
        self.log_path = log_path
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

    def log_event(self, company_id: str, operator_id: str, action_type: str, status: str, payload: dict):
        """Appends a structured log payload cleanly to the physical audit trail."""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "company_id": company_id,
            "operator_id": operator_id,
            "action_type": action_type,
            "status": status,
            "payload": payload
        }
        with open(self.log_path, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
