from fastapi import FastAPI
from api.routes import router
from services.telemetry_service import TelemetryService
from dotenv import load_dotenv
import os

# Explicitly load the local .env configuration variables
load_dotenv()

app = FastAPI(
    title="Rayda Agentic Fleet Copilot API Interface Engine",
    version="1.0.0",
    description="Production Ready Multi-Agent Framework orchestrating secure enterprise telemetry insights."
)

@app.on_event("startup")
def startup_event():
    db_path = os.getenv("DATABASE_PATH", "data/fleet_telemetry.db")
    telemetry_source = "data/telemetry.jsonl"
    
    print(f"Initializing DuckDB target data layer storage engine: {db_path}")
    svc = TelemetryService(db_path=db_path)
    
    if os.path.exists(telemetry_source):
        print(f"Ingesting time-series log patterns from source file: {telemetry_source}")
        count = svc.ingest_jsonl(telemetry_source)
        print(f"Ingestion successful. {count} rows indexed for analytical tasks.")
    else:
        print("Warning: Source data file not found at startup. Table initialized empty.")

@app.get("/health")
def health_check():
    return {"status": "ONLINE", "framework": "LangGraph Active Integration Engine"}

app.include_router(router)
