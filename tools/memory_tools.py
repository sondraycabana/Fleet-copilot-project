from langchain_core.tools import tool
from services.telemetry_service import TelemetryService
import json

@tool
def detect_memory_saturation(authorized_company_id: str) -> str:
    """
    Identifies devices where the average RAM utilization exceeds 85% across all recorded historical snapshots,
    indicating a potential need for hardware upgrades.
    """
    query = f"""
        SELECT device_id, employee_id, AVG(ram_used_pct) as avg_ram_utilization_pct, max(ram_total_bytes)/(1024*1024*1024) as ram_total_gb
        FROM snapshots
        WHERE company_id = '{authorized_company_id}'
        GROUP BY device_id, employee_id
        HAVING avg_ram_utilization_pct > 85.0
        ORDER BY avg_ram_utilization_pct DESC;
    """
    try:
        service = TelemetryService()
        results = service.execute_read_query(query)
        return json.dumps({"status": "SUCCESS", "data": results})
    except Exception as e:
        return json.dumps({"status": "ERROR", "message": str(e)})
