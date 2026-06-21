import pytest
import httpx

BASE_URL = "http://localhost:8000/api/v1/copilot"

def test_battery_end_of_life_trend_query():
    """Validates that battery lifecycle alerts return proper tool context mapping fields."""
    headers = {
        "X-Company-Id": "acme-001",
        "X-Operator-Id": "admin-qa-01"
    }
    payload = {
        "message": "Identify devices with battery degradation or severe cycle counts."
    }
    
    with httpx.Client() as client:
        response = client.post(f"{BASE_URL}/query", headers=headers, json=payload, timeout=20.0)
        
    assert response.status_code == 200
    res_data = response.json()
    
    assert "response" in res_data
    assert "gathered_evidence" in res_data
    assert len(res_data["gathered_evidence"]) > 0
    assert res_data["gathered_evidence"][0]["source_tool"] == "analyze_battery_degradation_tool"

def test_chronic_ram_constraint_trend_query():
    """Validates that memory saturation trends route to the memory tool engine."""
    headers = {
        "X-Company-Id": "acme-001",
        "X-Operator-Id": "admin-qa-01"
    }
    payload = {
        "message": "Show me workstations that are consistently constrained by RAM utilization spikes."
    }
    
    with httpx.Client() as client:
        response = client.post(f"{BASE_URL}/query", headers=headers, json=payload, timeout=20.0)
        
    assert response.status_code == 200
    res_data = response.json()
    
    assert "response" in res_data
    assert "gathered_evidence" in res_data
    assert len(res_data["gathered_evidence"]) > 0
    assert res_data["gathered_evidence"][0]["source_tool"] == "detect_memory_saturation_tool"

def test_historical_compliance_drift_trend_query():
    """Validates that chronological security compliance drift trends execute correctly."""
    headers = {
        "X-Company-Id": "acme-001",
        "X-Operator-Id": "admin-qa-01"
    }
    payload = {
        "message": "Analyze the fleet compliance drift over time across our snapshot logs."
    }
    
    with httpx.Client() as client:
        response = client.post(f"{BASE_URL}/query", headers=headers, json=payload, timeout=20.0)
        
    assert response.status_code == 200
    res_data = response.json()
    
    assert "response" in res_data
    assert "gathered_evidence" in res_data
    assert len(res_data["gathered_evidence"]) > 0
    assert res_data["gathered_evidence"][0]["source_tool"] == "calculate_compliance_drift_tool"
