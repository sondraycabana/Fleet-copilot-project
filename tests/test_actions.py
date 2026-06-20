import pytest
import httpx

BASE_URL = "http://localhost:8000/api/v1/copilot"

def test_action_staging_and_approval_gate_lifecycle():
    """Validates the complete lifecycle of staging an action and releasing it via approval."""
    headers = {
        "X-Company-Id": "acme-001",
        "X-Operator-Id": "admin-qa-01"
    }
    payload = {
        "message": "Please propose a storage hardware upgrade order for device MT7PJB7N5LRE."
    }
    
    with httpx.Client() as client:
        # Step 1: Stage the action
        query_response = client.post(f"{BASE_URL}/query", headers=headers, json=payload, timeout=15.0)
        assert query_response.status_code == 200
        query_data = query_response.json()
        
        assert query_data["requires_approval"] is True
        assert len(query_data["staged_proposals"]) > 0
        
        action_id = query_data["staged_proposals"][0]["action_id"]
        assert action_id.startswith("act-")
        
        # Step 2: Release the action through the manual human gate route
        approval_payload = {
            "session_id": query_data["session_id"],
            "action_id": action_id,
            "approve": True
        }
        approve_response = client.post(f"{BASE_URL}/action/approve", headers=headers, json=approval_payload, timeout=15.0)
        assert approve_response.status_code == 200
        
        approve_data = approve_response.json()
        assert approve_data["status"] == "SUCCESS"
        assert approve_data["outcome"] == "CONFIRMED_AND_DEPLOYED_BY_ADMIN"
