import pytest
import httpx

BASE_URL = "http://localhost:8000/api/v1/copilot"

def test_grounded_compliance_query():
    headers = {"X-Company-Id": "acme-001", "X-Operator-Id": "admin-qa-01"}
    payload = {"message": "Which devices at acme-001 are currently failing compliance checks?"}
    
    with httpx.Client() as client:
        response = client.post(f"{BASE_URL}/query", headers=headers, json=payload, timeout=15.0)
        
    assert response.status_code == 200
    res_data = response.json()
    
    assert "response" in res_data
    assert "gathered_evidence" in res_data
    assert len(res_data["gathered_evidence"]) > 0
    
    # Target index 0 of the verified evidence list payload structure block
    assert res_data["gathered_evidence"][0]["source_tool"] == "check_compliance_failures"
