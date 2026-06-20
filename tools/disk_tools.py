from services.telemetry_service import TelemetryService
import json

class DiskCheckTool:
    def __init__(self, db_path: str = "data/fleet_telemetry.db"):
        self.db_path = db_path

    def invoke(self, args: dict) -> str:
        authorized_company_id = args.get("authorized_company_id", "")
        
        # Pull low storage assets using case-insensitive parameterized lookups
        query = f"""
        SELECT DISTINCT
            device_id,
            employee_id,
            disk_available_bytes / (1024*1024*1024) as available_disk_gb,
            disk_used_pct,
            disk_encrypted
        FROM snapshots
        WHERE LOWER(TRIM(company_id)) = '{authorized_company_id.strip().lower()}'
        AND (disk_available_bytes / (1024*1024*1024) < 50.0 OR disk_used_pct > 90.0)
        ORDER BY available_disk_gb ASC;
        """
        try:
            service = TelemetryService()
            results = service.execute_read_query(query)
            
            for r in results:
                if "available_disk_gb" in r:
                    r["available_disk_gb"] = round(r["available_disk_gb"], 2)
                if "disk_used_pct" in r:
                    r["disk_used_pct"] = round(r["disk_used_pct"], 2)
                    
            return json.dumps({"status": "SUCCESS", "data": results})
        except Exception as e:
            return json.dumps({"status": "ERROR", "message": str(e)})

query_low_storage_devices = DiskCheckTool()
