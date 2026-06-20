from langchain_core.tools import tool
from services.telemetry_service import TelemetryService
import json

@tool
def analyze_battery_degradation(authorized_company_id: str) -> str:
    """
    Scans the 30-day snapshot history to surface devices showing signs of battery degradation.
    Flags devices with a cycle count > 500 or a condition state marked as 'Service' or 'Replace'.
    """
    query = f"""
        WITH latest_snapshots AS (
            SELECT *, ROW_NUMBER() OVER(PARTITION BY device_id ORDER BY collected_at DESC) as rn
            FROM snapshots
            WHERE company_id = '{authorized_company_id}'
        )
        SELECT device_id, employee_id, battery_percentage, battery_condition, battery_cycle_count
        FROM latest_snapshots
        WHERE rn = 1 AND (battery_cycle_count > 500 OR battery_condition IN ('Service', 'Replace', 'Check Battery', 'Service Battery'))
        ORDER BY battery_cycle_count DESC;
    """
    try:
        service = TelemetryService()
        results = service.execute_read_query(query)
        return json.dumps({"status": "SUCCESS", "data": results})
    except Exception as e:
        return json.dumps({"status": "ERROR", "message": str(e)})
