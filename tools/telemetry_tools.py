from langchain_core.tools import tool
from services.telemetry_service import TelemetryService
from guards.tenant_guard import TenantGuard
import json

@tool
def execute_fleet_query(sql_query: str, authorized_company_id: str) -> str:
    """
    Executes a read-only DuckDB SQL query against the 'snapshots' database table.
    The table contains metrics: device_id, company_id, employee_id, collected_at, 
    os_version, ram_used_pct, disk_available_bytes, disk_used_pct, disk_encrypted, 
    battery_percentage, battery_condition, battery_cycle_count, compliance_fails.
    Queries must explicitly filter by company_id to maintain security isolation.
    """
    try:
        sanitized_query = TenantGuard.validate_query_isolation(sql_query, authorized_company_id)
        service = TelemetryService()
        results = service.execute_read_query(sanitized_query)
        return json.dumps({"status": "SUCCESS", "query_executed": sanitized_query, "data": results})
    except Exception as e:
        return json.dumps({"status": "ERROR", "message": str(e)})
