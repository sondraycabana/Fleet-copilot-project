# Agentic AI Fleet Copilot — Senior Assessment Submission

This repository contains a production-grade, multi-agent orchestrator for Rayda's enterprise IT fleet telemetry data. Built using LangGraph, FastAPI, and DuckDB, the system handles complex time-series queries while enforcing strict tenant isolation boundaries and safety guardrails.

## 🏗️ Core Agent Architecture & System Topology

The system uses a **Router-ReACT architecture with a State Graph** rather than a single linear prompt wrapper. This breaks complex user queries down into predictable execution paths.




### Specialized Agents Matrix
* **Planner Agent (Orchestrator)**: Parses natural language inputs, validates tenant metadata headers, and determines which sub-agent is best suited to handle the request.
* **Analytics Agent (Time-Series Explorer)**: Analyzes historical metrics to identify trends, performance anomalies, and progressive hardware degradation.
* **Action Agent (Operations Manager)**: Coordinates changes, alerts employees, and stages hardware orders while holding them for explicit human sign-off.

---

## 🔒 Security Architecture & Guardrails

The application enforces strict security boundaries at the data and code layer rather than relying on soft instructions inside a system prompt:

1. **Hard Tenant Isolation**: The active context session locks `company_context`. The `TenantGuard` intercepts raw queries and rejects execution at the tool boundary if a query references text outside this block.
2. **Deterministic Write Guardrails**: Modifying tasks (such as staging upgrade orders) trigger a state transition to `human_approval_gate`. This completely pauses the agent loop until an admin grants explicit manual verification.
3. **Structured Audit Logs**: Every execution change logs structured event records to `logs/audit.log` for debugging and accountability.

---

## 🛠️ Installation, Ingestion & Live Execution

### Prerequisites
* Python 3.11+
* A valid `OPENAI_API_KEY` exported in your system environment variables.

### Local Installation
```bash
# Clone and enter the project folder
git clone https://github.com
cd fleet-copilot

# Create and activate a clean virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies pinned for production safety
pip install -r requirements.txt
```

### Ingestion Setup
Before launching the server, place your dataset in the `data/` directory and run the initialization script to ingest records into DuckDB:
```bash
mkdir -p data logs
cp /path/to/your/telemetry.jsonl data/telemetry.jsonl

# Ingest records to initialize data structures
python -c "from services.telemetry_service import TelemetryService; TelemetryService().ingest_jsonl('data/telemetry.jsonl')"
```

### Running the API Endpoint Server
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 🧪 Runnable Evaluation Suite

The testing layout runs deterministic assertions alongside **LLM-as-a-Judge semantic scoring** to thoroughly verify response accuracy and safety guardrails.

```bash
# Execute the complete automated verification suite via pytest
pytest tests/ -v --asyncio-mode=auto
```

### Key Validation Tracks Covered
* `test_grounding.py`: Verifies responses match data parameters perfectly to prevent hallucinations.
* `test_guardrails.py`: Confirms cross-tenant queries are blocked at the perimeter.
* `test_actions.py`: Assures state-changing workflows are safely staged and paused for admin approval.
* `test_trends.py`: Validates historical queries calculate metrics over time rather than looking at single snapshots.

---

## 📈 Key Design Decisions & Architectural Trade-offs

### 1. Embedded Analytical Storage (DuckDB) vs. Vector RAG Over Raw JSON Lines
* **Decision**: We ingest all time-series snapshots into an index-optimized local DuckDB instance.
* **Trade-off**: This adds a minor validation step during startup, but completely avoids context window bloat and eliminates hallucinations when running complex trend calculations (like multi-day battery or RAM aggregations).

### 2. Multi-Agent Routing vs. Unified Single Prompt ReACT Loops
* **Decision**: We separate specialized tasks into isolated nodes (`telemetry_node`, `analytics_node`, `action_node`).
* **Trade-off**: This requires maintaining explicit schemas between graph transitions, but provides predictable execution paths and allows you to place deterministic security guards around specific sub-agent behaviors.