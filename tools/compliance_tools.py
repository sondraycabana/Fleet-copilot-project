import duckdb
import json

class ComplianceCheckTool:
    def __init__(self, db_path: str = "data/fleet_telemetry.db"):
        self.db_path = db_path

    def invoke(self, args: dict) -> str:
        authorized_company_id = args.get("authorized_company_id", "")
        
        # Open a thread-safe context connection to the verified DuckDB binary
        conn = duckdb.connect(self.db_path)
        
        # Use your verified parameterized SQL logic
        sql = """
        SELECT DISTINCT
            device_id,
            company_id,
            compliance_fails
        FROM snapshots
        WHERE LOWER(TRIM(company_id)) = LOWER(TRIM(?))
        AND array_length(compliance_fails) > 0
        """
        try:
            rows = conn.execute(sql, [authorized_company_id]).fetchall()
            results = []
            
            for device_id, company_id, failures in rows:
                results.append({
                    "device_id": device_id,
                    "company_id": company_id,
                    "failed_checks": failures
                })
            
            # Close the file handle context safely
            conn.close()
            return json.dumps({"status": "SUCCESS", "data": results})
            
        except Exception as e:
            try:
                conn.close()
            except:
                pass
            return json.dumps({"status": "ERROR", "message": str(e)})

# Expose the tool as a callable module instance mapped to your api route hooks
check_compliance_failures = ComplianceCheckTool()
