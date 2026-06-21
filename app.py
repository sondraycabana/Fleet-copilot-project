import os
import json
from services.telemetry_service import TelemetryService

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # Mocking sample ingestion dataset matching target specs
    sample_records = [
        {"device_id": "1LYSSFD074BB", "company_id": "acme-001", "employee_id": "emp-acme-1001", "collected_at": "2026-05-14T09:54:00Z", "agent_version": "42.0.0", "os": {"platform": "darwin", "product_name": "macOS", "product_version": "14.5", "build_version": "23F79", "architecture": "arm64", "kernel_name": "Darwin", "kernel_release": "23.5.0", "hostname": "acme-macbook-2"}, "device_identity": {"serial_number": "1LYSSFD074BB", "model_name": "MacBook Pro", "model_identifier": "Mac15,7", "processor": "Apple M3 Pro", "hardware_uuid": "1c648816-7449-5767-6337-f37c716525f7", "total_memory": "32 GB"}, "memory": {"ram_bytes": 34359738368, "total_memory_bytes": 34359738368, "used_memory_bytes": 17833013725, "free_memory_bytes": 16526724643, "page_size_bytes": 16384}, "disk_volumes": [{"volume_name": "Macintosh HD", "file_system": "apfs", "mount_point": "/", "size_bytes": 1099511627776, "available_bytes": 603423018844, "encrypted": true}], "battery": {"battery_present": true, "charging_status": "charging", "percentage": 45, "condition": "Normal", "cycle_count": 512, "full_charge_capacity": 6163}, "network": [{"address": "192.168.4.28", "family": "IPv4", "interface_name": "en0", "internal": false, "mac": "84:1b:a2:38:73:f1"}], "installed_software": [{"name": "Google Chrome", "version": "126.0", "publisher": "Google LLC"}, {"name": "Slack", "version": "4.39", "publisher": "Slack Technologies"}], "compliance_results": [{"check_id": "disk_encryption", "status": "pass", "severity": "high"}, {"check_id": "screen_lock", "status": "pass", "severity": "medium"}, {"check_id": "os_up_to_date", "status": "fail", "severity": "medium"}]}
    ]
    
    with open("data/telemetry.jsonl", "w") as f:
        for r in sample_records:
            f.write(json.dumps(r) + "\n")
            
    svc = TelemetryService()
    count = svc.ingest_jsonl("data/telemetry.jsonl")
    print(f"Successfully processed and indexed {count} analytics snapshot rows into DuckDB.")
