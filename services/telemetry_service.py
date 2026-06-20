import json
import os
import duckdb
import pandas as pd
from typing import List, Dict, Any

class TelemetryService:
    def __init__(self, db_path: str = "data/fleet_telemetry.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.conn = duckdb.connect(self.db_path)
        self._initialize_schema()

    def _initialize_schema(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS snapshots (
                device_id VARCHAR,
                company_id VARCHAR,
                employee_id VARCHAR,
                collected_at TIMESTAMP,
                agent_version VARCHAR,
                os_platform VARCHAR,
                os_version VARCHAR,
                os_build VARCHAR,
                model_name VARCHAR,
                processor VARCHAR,
                ram_total_bytes BIGINT,
                ram_used_bytes BIGINT,
                ram_used_pct DOUBLE,
                disk_total_bytes BIGINT,
                disk_available_bytes BIGINT,
                disk_used_pct DOUBLE,
                disk_encrypted BOOLEAN,
                battery_present BOOLEAN,
                battery_status VARCHAR,
                battery_percentage INTEGER,
                battery_condition VARCHAR,
                battery_cycle_count INTEGER,
                compliance_fails VARCHAR[],
                raw_json TEXT
            );
        """)

    def ingest_jsonl(self, jsonl_path: str) -> int:
        if not os.path.exists(jsonl_path):
            raise FileNotFoundError(f"Source data file not found at: {jsonl_path}")

        records = []
        with open(jsonl_path, "r") as f:
            for line in f:
                if not line.strip():
                    continue
                raw_data = json.loads(line)
                
                ram_total = raw_data.get("memory", {}).get("total_memory_bytes", 1)
                ram_used = raw_data.get("memory", {}).get("used_memory_bytes", 0)
                ram_pct = (ram_used / ram_total) * 100
                
                # Dynamic safe parsing for dict vs list variants of disk volumes
                disk_input = raw_data.get("disk_volumes", {})
                if isinstance(disk_input, list) and len(disk_input) > 0:
                    volumes = disk_input[0]
                elif isinstance(disk_input, dict):
                    volumes = disk_input
                else:
                    volumes = {}
                    
                disk_total = volumes.get("size_bytes", 1)
                disk_avail = volumes.get("available_bytes", 0)
                disk_pct = ((disk_total - disk_avail) / disk_total) * 100
                disk_enc = volumes.get("encrypted", False)
                
                comp_results = raw_data.get("compliance_results", [])
                fails = [check.get("check_id") for check in comp_results if check.get("status") == "fail"]
                
                records.append({
                    "device_id": raw_data.get("device_id"),
                    "company_id": raw_data.get("company_id"),
                    "employee_id": raw_data.get("employee_id"),
                    "collected_at": raw_data.get("collected_at"),
                    "agent_version": raw_data.get("agent_version"),
                    "os_platform": raw_data.get("os", {}).get("platform"),
                    "os_version": raw_data.get("os", {}).get("product_version"),
                    "os_build": raw_data.get("os", {}).get("build_version"),
                    "model_name": raw_data.get("device_identity", {}).get("model_name"),
                    "processor": raw_data.get("device_identity", {}).get("processor"),
                    "ram_total_bytes": ram_total,
                    "ram_used_bytes": ram_used,
                    "ram_used_pct": round(ram_pct, 2),
                    "disk_total_bytes": disk_total,
                    "disk_available_bytes": disk_avail,
                    "disk_used_pct": round(disk_pct, 2),
                    "disk_encrypted": disk_enc,
                    "battery_present": raw_data.get("battery", {}).get("battery_present", False),
                    "battery_status": raw_data.get("battery", {}).get("charging_status"),
                    "battery_percentage": raw_data.get("battery", {}).get("percentage", 0),
                    "battery_condition": raw_data.get("battery", {}).get("condition"),
                    "battery_cycle_count": raw_data.get("battery", {}).get("cycle_count", 0),
                    "compliance_fails": fails,
                    "raw_json": json.dumps(raw_data)
                })
        
        if records:
            df = pd.DataFrame(records)
            self.conn.execute("DELETE FROM snapshots")
            self.conn.execute("INSERT INTO snapshots SELECT * FROM df")
        
        return len(records)

    def execute_read_query(self, sql_query: str) -> List[Dict[str, Any]]:
        return self.conn.execute(sql_query).fetchdf().to_dict(orient="records")
